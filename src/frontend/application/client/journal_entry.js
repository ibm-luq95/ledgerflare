/**
 * @fileoverview Journal Entry Form Controller
 * Handles dynamic row management, validation, and user interactions
 * for the client journal entry form.
 * @module journalEntryModule
 */

// =================================================================================
// 🔒 CONSTANTS & ENUMS (Frozen for safety)
// =================================================================================

/**
 * @typedef {Object} JournalRowData
 * @property {string} id - Unique row identifier
 * @property {string} account
 * @property {string} debit
 * @property {string} credit
 * @property {string} description
 * @property {string} name
 * @property {string} store
 */

/**
 * @enum {string}
 * @readonly
 */
const UI_TEXT = Object.freeze({
  PLACEHOLDER_ACCOUNT: "Account",
  PLACEHOLDER_DEBIT: "0.00",
  PLACEHOLDER_CREDIT: "0.00",
  PLACEHOLDER_DESCRIPTION: "Description",
  PLACEHOLDER_NAME: "Name",
  PLACEHOLDER_STORE: "Store",
  CONFIRM_DISCARD_TITLE: "Discard Changes?",
  CONFIRM_DISCARD_MESSAGE:
    "Are you sure you want to discard all unsaved changes?",
  BUTTON_CONFIRM: "Yes, Discard",
  BUTTON_CANCEL: "Cancel",
});

/**
 * @enum {string}
 * @readonly
 */
const SELECTORS = Object.freeze({
  ROOT: "#clientJournalEntry",
  TABLE_BODY: "#journal-rows",
  ADD_ROW_BTN: "#addRowBtn",
  CLEAN_ROWS_BTN: "#cleanRowsBtn",
  CALCULATE_BTN: "#calculateBtn",
  SAVE_BTN: "#saveBtn",
  CANCEL_BTN: "#cancelBtn",
});

/**
 * @enum {number}
 * @readonly
 */
const CONFIG = Object.freeze({
  MIN_ROWS: 1,
});

// =================================================================================
// 🛡️ UTILITIES
// =================================================================================

/**
 * Generates a cryptographically stronger pseudo-random ID using timestamp + randomness.
 * Uses `crypto.getRandomValues` if available for better entropy.
 * @returns {string} Unique ID string
 */
function generateRowId() {
  const timestamp = Date.now().toString(36);
  const randomPart = (() => {
    try {
      const arr = new Uint32Array(1);
      crypto.getRandomValues(arr);
      return arr[0].toString(36);
    } catch {
      return Math.floor(Math.random() * Number.MAX_SAFE_INTEGER).toString(36);
    }
  })();
  return `${timestamp}-${randomPart}`;
}

/**
 * Validates that a value is a non-empty string.
 * @param {*} value - Value to validate
 * @returns {boolean}
 */
function isValidString(value) {
  return typeof value === "string" && value.trim() !== "";
}

/**
 * Parses a numeric string safely (e.g., "1,234.50" → 1234.5).
 * @param {string} value - Input string
 * @returns {number|null} Parsed number or null if invalid
 */
function parseNumericInput(value) {
  if (!isValidString(value)) return null;
  const cleaned = value.trim().replace(/[^0-9.-]/g, "");
  const num = Number(cleaned);
  return isNaN(num) || !isFinite(num) ? null : num;
}

/**
 * Updates row numbers in the table body sequentially.
 * @param {HTMLElement} tableBody - The tbody element
 */
function updateRowNumbers(tableBody) {
  const rows = tableBody.querySelectorAll("tr");
  rows.forEach((row, index) => {
    const numberCell = row.querySelector("td:first-child");
    if (numberCell) {
      numberCell.textContent = String(index + 1);
    }
  });
}

// =================================================================================
// 🧩 MODAL CONTROLLER (Fixed)
// =================================================================================

/**
 * Creates and manages a custom confirmation modal.
 */
class ConfirmationModal {
  /**
   * @param {string} title
   * @param {string} message
   * @param {string} confirmText
   * @param {string} cancelText
   */
  constructor(title, message, confirmText, cancelText) {
    this.element = this.#createModalElement(
      title,
      message,
      confirmText,
      cancelText,
    );
    this.resolve = null;
    this.promise = new Promise((resolve) => {
      this.resolve = resolve;
    });
  }

  /**
   * @private
   */
  #createModalElement(title, message, confirmText, cancelText) {
    const modal = document.createElement("div");
    modal.className =
      "fixed inset-0 z-50 flex items-center justify-center bg-black/50 dark:bg-black/70";
    modal.innerHTML = `
      <div class="bg-white rounded-xl p-6 w-full max-w-md shadow-lg dark:bg-neutral-800">
        <h4 class="text-lg font-bold text-gray-800 dark:text-white mb-2">${title}</h4>
        <p class="text-sm text-gray-600 dark:text-neutral-300 mb-5">${message}</p>
        <div class="flex justify-end gap-3">
          <button type="button" data-action="cancel"
            class="py-2 px-4 text-sm font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 focus:outline-hidden dark:border-neutral-600 dark:text-neutral-200 dark:hover:bg-neutral-700">
            ${cancelText}
          </button>
          <button type="button" data-action="confirm"
            class="py-2 px-4 text-sm font-medium rounded-lg bg-red-500 text-white hover:bg-red-600 focus:outline-hidden">
            ${confirmText}
          </button>
        </div>
      </div>
    `;
    return modal;
  }

  /**
   * Shows the modal and returns a promise that resolves to boolean.
   * @returns {Promise<boolean>}
   */
  show() {
    document.body.appendChild(this.element);

    const handleClick = (e) => {
      if (e.target.closest?.('[data-action="confirm"]')) {
        this.#cleanup();
        this.resolve(true);
        return;
      }
      if (
        e.target.closest?.('[data-action="cancel"]') ||
        e.target === this.element
      ) {
        this.#cleanup();
        this.resolve(false);
        return;
      }
    };

    this.element.addEventListener("click", handleClick);

    const handleKey = (e) => {
      if (e.key === "Escape") {
        this.#cleanup();
        this.resolve(false);
      }
    };
    document.addEventListener("keydown", handleKey, { once: true });

    return this.promise;
  }

  /**
   * @private
   */
  #cleanup() {
    if (this.element.parentNode) {
      this.element.parentNode.removeChild(this.element);
    }
  }
}

// =================================================================================
// 🧠 MAIN CONTROLLER (Fully Enhanced)
// =================================================================================

/**
 * Manages the journal entry form lifecycle.
 */
class JournalEntryController {
  /**
   * @param {HTMLElement} rootElement
   */
  constructor(rootElement) {
    /** @type {HTMLElement} */
    this.root = rootElement;
    /** @type {HTMLElement} */
    this.tableBody = this.root.querySelector(SELECTORS.TABLE_BODY);
    /** @type {HTMLElement|null} */
    this.addRowBtn = this.root.querySelector(SELECTORS.ADD_ROW_BTN);
    /** @type {HTMLElement|null} */
    this.cleanRowsBtn = this.root.querySelector(SELECTORS.CLEAN_ROWS_BTN);
    /** @type {HTMLElement|null} */
    this.calculateBtn = this.root.querySelector(SELECTORS.CALCULATE_BTN);
    /** @type {HTMLElement|null} */
    this.saveBtn = this.root.querySelector(SELECTORS.SAVE_BTN);
    /** @type {HTMLElement|null} */
    this.cancelBtn = this.root.querySelector(SELECTORS.CANCEL_BTN);

    this._recalcTimeout = null;
    this.#bindEvents();
  }

  /**
   * Binds all event listeners.
   * @private
   */
  #bindEvents() {
    this.addRowBtn?.addEventListener("click", () => this.#addRow());
    this.cleanRowsBtn?.addEventListener("click", () => this.#cleanRows());
    this.calculateBtn?.addEventListener("click", () =>
      this.#recalculateTotals(true),
    );
    this.saveBtn?.addEventListener("click", () => this.#handleSave());
    this.cancelBtn?.addEventListener("click", () => this.#handleCancel());

    this.tableBody?.addEventListener("input", (e) => this.#handleInput(e));
    this.tableBody?.addEventListener("blur", (e) => this.#handleBlur(e), true);
    this.tableBody?.addEventListener("keydown", (e) => this.#handleKeydown(e));
    this.tableBody?.addEventListener("click", (e) => {
      const removeBtn = e.target.closest(".remove-row");
      if (removeBtn) {
        const row = removeBtn.closest("tr");
        if (row) this.#removeRow(row);
      }
    });
  }

  /**
   * Creates a new row HTML string.
   * @param {number} rowNumber
   * @param {string} rowId
   * @returns {string}
   */
  #createRowHtml(rowNumber, rowId) {
    const p = UI_TEXT;
    return `
      <tr data-row-id="${rowId}">
        <td class="border border-gray-200 w-10 px-2 py-3 text-sm font-medium text-gray-800 dark:border-neutral-700 dark:text-neutral-200 text-center whitespace-nowrap">
          ${rowNumber}
        </td>
        <td class="border border-gray-200 w-32 px-3 py-3 text-sm text-gray-800 dark:border-neutral-700 dark:text-neutral-200">
          <input type="text" name="account_${rowId}" class="py-1.5 px-2 block w-full border-gray-200 rounded text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400 dark:placeholder-neutral-500" placeholder="${p.PLACEHOLDER_ACCOUNT}" />
        </td>
        <td class="border border-gray-200 w-32 px-3 py-3 text-sm text-gray-800 dark:border-neutral-700 dark:text-neutral-200">
          <input type="text" name="debit_${rowId}" class="py-1.5 px-2 block w-full border-gray-200 rounded text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400 dark:placeholder-neutral-500 text-end" placeholder="${p.PLACEHOLDER_DEBIT}" />
        </td>
        <td class="border border-gray-200 w-32 px-3 py-3 text-sm text-gray-800 dark:border-neutral-700 dark:text-neutral-200">
          <input type="text" name="credit_${rowId}" class="py-1.5 px-2 block w-full border-gray-200 rounded text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400 dark:placeholder-neutral-500 text-end" placeholder="${p.PLACEHOLDER_CREDIT}" />
        </td>
        <td class="border border-gray-200 w-32 px-3 py-3 text-sm text-gray-800 dark:border-neutral-700 dark:text-neutral-200">
          <input type="text" name="description_${rowId}" class="py-1.5 px-2 block w-full border-gray-200 rounded text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400 dark:placeholder-neutral-500" placeholder="${p.PLACEHOLDER_DESCRIPTION}" />
        </td>
        <td class="border border-gray-200 w-32 px-3 py-3 text-sm text-gray-800 dark:border-neutral-700 dark:text-neutral-200">
          <input type="text" name="name_${rowId}" class="py-1.5 px-2 block w-full border-gray-200 rounded text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400 dark:placeholder-neutral-500" placeholder="${p.PLACEHOLDER_NAME}" />
        </td>
        <td class="border border-gray-200 w-32 px-3 py-3 text-sm text-gray-800 dark:border-neutral-700 dark:text-neutral-200">
          <input type="text" name="store_${rowId}" class="py-1.5 px-2 block w-full border-gray-200 rounded text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400 dark:placeholder-neutral-500" placeholder="${p.PLACEHOLDER_STORE}" />
        </td>
        <td class="border border-gray-200 w-12 px-2 py-3 text-end text-sm font-medium dark:border-neutral-700">
          <button type="button" class="inline-flex items-center justify-center w-8 h-8 text-gray-500 hover:text-red-600 rounded-full hover:bg-red-50 focus:outline-none dark:text-neutral-400 dark:hover:text-red-500 dark:hover:bg-red-500/10 remove-row">
            <i class="fa-solid fa-trash text-xs"></i>
          </button>
        </td>
      </tr>
    `;
  }

  /**
   * Adds a new row to the table (FIXED: uses DOMParser for reliable parsing).
   */
  #addRow() {
    try {
      const newRowNumber = (this.tableBody?.children?.length ?? 0) + 1;
      const newRowId = generateRowId();
      const rowHtml = this.#createRowHtml(newRowNumber, newRowId);

      // ✅ FIX: Use DOMParser to avoid innerHTML quirks with <tr>
      const parser = new DOMParser();
      const doc = parser.parseFromString(
        `<table><tbody>${rowHtml}</tbody></table>`,
        "text/html",
      );
      const newRow = doc.querySelector("tr");

      if (newRow && this.tableBody) {
        this.tableBody.appendChild(newRow);
        updateRowNumbers(this.tableBody);
        this.#recalculateTotals();
      }
    } catch (error) {
      console.error("Failed to add journal row:", error);
    }
  }

  /**
   * Removes all rows except the minimum required.
   */
  #cleanRows() {
    try {
      if (!this.tableBody) return;
      while (this.tableBody.children.length > CONFIG.MIN_ROWS) {
        this.tableBody.removeChild(this.tableBody.lastElementChild);
      }
      updateRowNumbers(this.tableBody);
      this.#recalculateTotals();
    } catch (error) {
      console.error("Failed to clean journal rows:", error);
    }
  }

  /**
   * Removes a specific row if above minimum count.
   * @param {HTMLElement} row
   */
  #removeRow(row) {
    try {
      if (!this.tableBody) return;
      if (this.tableBody.children.length <= CONFIG.MIN_ROWS) return;
      row.remove();
      updateRowNumbers(this.tableBody);
      this.#recalculateTotals();
    } catch (error) {
      console.error("Failed to remove journal row:", error);
    }
  }

  /**
   * Handles input events for debit/credit fields with mutual exclusivity.
   * @param {InputEvent} event
   * @private
   */
  #handleInput(event) {
    const input = event.target;
    if (!input.matches?.('input[name^="debit_"], input[name^="credit_"]'))
      return;

    const value = input.value;
    const row = input.closest?.("tr");
    if (!row) return;

    const sanitized = value.replace(/[^0-9.-]/g, "");
    if (sanitized !== value) {
      input.value = sanitized;
    }

    const isDebit = input.name.startsWith("debit_");
    const oppositeField = row.querySelector(
      isDebit ? 'input[name^="credit_"]' : 'input[name^="debit_"]',
    );

    if (oppositeField && sanitized !== "" && parseFloat(sanitized) > 0) {
      oppositeField.value = "";
    }

    clearTimeout(this._recalcTimeout);
    this._recalcTimeout = setTimeout(() => {
      this.#recalculateTotals();
    }, 150);
  }

  /**
   * Handles blur event to format numeric inputs.
   * @param {FocusEvent} event
   * @private
   */
  #handleBlur(event) {
    const input = event.target;
    if (!input.matches?.('input[name^="debit_"], input[name^="credit_"]'))
      return;

    const rawValue = input.value.trim();
    if (rawValue === "") return;

    const num = parseNumericInput(rawValue);
    if (num === null) {
      input.value = "";
      return;
    }

    input.value = num.toFixed(2);
    this.#recalculateTotals();
  }

  /**
   * Blocks non-numeric keys in debit/credit fields.
   * @param {KeyboardEvent} event
   * @private
   */
  #handleKeydown(event) {
    const input = event.target;
    if (!input.matches?.('input[name^="debit_"], input[name^="credit_"]'))
      return;

    const allowedKeys = [
      "Backspace",
      "Delete",
      "Tab",
      "Escape",
      "Enter",
      "ArrowLeft",
      "ArrowRight",
      "ArrowUp",
      "ArrowDown",
      "Home",
      "End",
    ];
    if (allowedKeys.includes(event.key)) return;

    if (event.key === "." && input.value.includes(".")) {
      event.preventDefault();
      return;
    }

    if (!/^\d$/.test(event.key)) {
      event.preventDefault();
    }
  }

  /**
   * Recalculates totals with optional visual feedback.
   * @param {boolean} [isManual=false] - Triggered by user click?
   */
  #recalculateTotals(isManual = false) {
    try {
      let totalDebits = 0;
      let totalCredits = 0;

      const rows = this.tableBody?.querySelectorAll("tr") ?? [];
      for (const row of rows) {
        const debitInput = row.querySelector('input[name^="debit_"]');
        const creditInput = row.querySelector('input[name^="credit_"]');

        const debitVal = debitInput
          ? parseNumericInput(debitInput.value)
          : null;
        const creditVal = creditInput
          ? parseNumericInput(creditInput.value)
          : null;

        if (debitVal !== null && debitVal > 0) totalDebits += debitVal;
        if (creditVal !== null && creditVal > 0) totalCredits += creditVal;
      }

      const debitTotalCell = this.root.querySelector("tfoot td:nth-child(3)");
      const creditTotalCell = this.root.querySelector("tfoot td:nth-child(4)");
      const balanceStatusCell = this.root.querySelector(
        'tfoot td[colspan="3"]',
      );

      if (debitTotalCell) {
        debitTotalCell.textContent = totalDebits.toFixed(2);
      }
      if (creditTotalCell) {
        creditTotalCell.textContent = totalCredits.toFixed(2);
      }

      const isBalanced = Math.abs(totalDebits - totalCredits) < 0.001;
      if (balanceStatusCell) {
        balanceStatusCell.textContent = isBalanced ? "Balanced" : "Unbalanced";
        balanceStatusCell.className =
          balanceStatusCell.className
            .replace(/text-(?:gray|red|green)-500/g, "")
            .trim() + (isBalanced ? " text-green-500" : " text-red-500");
      }
      // Optional: Add flash animation on manual calculate
      if (isManual && this.calculateBtn) {
        this.calculateBtn.classList.add("text-blue-800", "scale-110");
        setTimeout(() => {
          this.calculateBtn.classList.remove("text-blue-800", "scale-110");
        }, 300);
      }
    } catch (error) {
      console.error("Failed to recalculate totals:", error);
    }
  }

  /**
   * Collects all form data including header, lines, extra, and attachment metadata.
   * Does NOT upload files — only collects metadata for queued files.
   * @returns {Object} Full journal payload ready for submission
   * @private
   */
  #collectFullPayload() {
    // Header
    const dateInput = this.root.querySelector("#journal-date");
    const journalNumberInput = this.root.querySelector("#journal-number");
    const autoGenerateCheckbox = this.root.querySelector(
      "#auto-journal-number",
    );

    const header = {
      date: dateInput?.value || "",
      journalNumber: journalNumberInput?.value || "",
      autoGenerateNumber: autoGenerateCheckbox?.checked || false,
    };

    // Lines
    const lines = [];
    const rows = this.tableBody?.querySelectorAll("tr") ?? [];
    for (const row of rows) {
      const accountInput = row.querySelector('input[name^="account_"]');
      const debitInput = row.querySelector('input[name^="debit_"]');
      const creditInput = row.querySelector('input[name^="credit_"]');
      const descriptionInput = row.querySelector('input[name^="description_"]');
      const nameInput = row.querySelector('input[name^="name_"]');
      const storeInput = row.querySelector('input[name^="store_"]');

      const debitVal = debitInput ? parseNumericInput(debitInput.value) : 0;
      const creditVal = creditInput ? parseNumericInput(creditInput.value) : 0;

      // Skip empty lines (both debit and credit are zero)
      if (
        (debitVal === 0 || debitVal === null) &&
        (creditVal === 0 || creditVal === null)
      ) {
        continue;
      }

      lines.push({
        account: accountInput?.value.trim() || "",
        debit: debitVal !== null ? Number(debitVal.toFixed(2)) : 0,
        credit: creditVal !== null ? Number(creditVal.toFixed(2)) : 0,
        description: descriptionInput?.value.trim() || "",
        name: nameInput?.value.trim() || "",
        store: storeInput?.value.trim() || "",
      });
    }

    // Extra
    const memoTextarea = this.root.querySelector("#textarea-label");
    const extra = {
      memo: memoTextarea?.value.trim() || "",
    };

    // Attachments (metadata only)
    let attachments = [];
    const fileUploadEl = this.root.querySelector("#hs-file-upload-to-destroy");
    if (fileUploadEl && typeof fileUploadEl.dropzone !== "undefined") {
      const acceptedFiles = fileUploadEl.dropzone.getAcceptedFiles();
      attachments = acceptedFiles.map((file) => ({
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
      }));
    }

    return { header, lines, extra, attachments };
  }

  /**
   * Validates the journal payload for accounting rules and required fields.
   * @param {Object} payload - Journal payload from #collectFullPayload
   * @returns {boolean} True if valid
   * @private
   */
  #isValidJournal(payload) {
    // Validate date
    if (!payload.header.date) {
      console.warn("Journal date is required.");
      return false;
    }

    // Validate at least one line
    if (payload.lines.length === 0) {
      console.warn("At least one journal line is required.");
      return false;
    }

    // Validate mutual exclusivity per line
    for (const line of payload.lines) {
      const hasDebit = line.debit > 0;
      const hasCredit = line.credit > 0;
      if (hasDebit && hasCredit) {
        console.warn("A line cannot have both debit and credit:", line);
        return false;
      }
      if (!hasDebit && !hasCredit) {
        console.warn("A line must have either debit or credit:", line);
        return false;
      }
    }

    // Validate balance
    const totalDebits = payload.lines.reduce(
      (sum, line) => sum + line.debit,
      0,
    );
    const totalCredits = payload.lines.reduce(
      (sum, line) => sum + line.credit,
      0,
    );
    const isBalanced = Math.abs(totalDebits - totalCredits) < 0.001;
    if (!isBalanced) {
      console.warn(
        `Journal is unbalanced. Debits: ${totalDebits}, Credits: ${totalCredits}`,
      );
      return false;
    }

    return true;
  }

  /**
   * Handles save action: collects data, validates, and logs the payload.
   * (No upload — for debugging and future integration)
   */
  async #handleSave() {
    try {
      const payload = this.#collectFullPayload();
      console.log("Collected journal payload:", payload);

      if (!this.#isValidJournal(payload)) {
        console.error("Journal entry is invalid. Fix errors before saving.");
        // TODO: Show user-friendly error UI
        return;
      }

      console.info("✅ Journal entry is valid and ready to be sent.");
      // TODO: Later, send via FormData + fetch
    } catch (error) {
      console.error("Failed to collect or validate journal ", error);
    }
  }

  /**
   * Handles cancel action with custom modal confirmation (FIXED).
   */
  async #handleCancel() {
    try {
      const modal = new ConfirmationModal(
        UI_TEXT.CONFIRM_DISCARD_TITLE,
        UI_TEXT.CONFIRM_DISCARD_MESSAGE,
        UI_TEXT.BUTTON_CONFIRM,
        UI_TEXT.BUTTON_CANCEL,
      );
      const shouldDiscard = await modal.show();
      if (shouldDiscard) {
        window.history.back();
      }
    } catch (error) {
      console.error("Cancel confirmation failed:", error);
    }
  }
}

// =================================================================================
// 🚀 MODULE ENTRY POINT
// =================================================================================

/**
 * Initializes the journal entry controller if the root element exists.
 */
function initJournalEntryModule() {
  const root = document.querySelector(SELECTORS.ROOT);
  if (!root) {
    console.warn(
      "Journal entry root element not found. Skipping initialization.",
    );
    return;
  }
  new JournalEntryController(root);
}

// Export for potential reuse or testing
export { initJournalEntryModule, JournalEntryController, ConfirmationModal };
