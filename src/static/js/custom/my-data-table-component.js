/**
 * @fileoverview Data Table Web Component with sorting, editing, and card styling.
 * @module components/DataTable
 */

/**
 * Custom error classes for the data table component.
 * @enum {Function}
 */
const DataTableError = Object.freeze({
  ValidationError: class ValidationError extends Error {
    /**
     * @param {string} message
     */
    constructor(message) {
      super(message);
      this.name = "ValidationError";
    }
  },
  RenderError: class RenderError extends Error {
    /**
     * @param {string} message
     */
    constructor(message) {
      super(message);
      this.name = "RenderError";
    }
  },
});

/**
 * Sort direction constants.
 * @enum {string}
 */
const SortDirection = Object.freeze({
  ASC: "asc",
  DESC: "desc",
  NONE: "none",
});

/**
 * Event names emitted by the component.
 * @enum {string}
 */
const DataTableEvent = Object.freeze({
  SORT: "sort",
  CELL_EDIT_START: "cell-edit-start",
  CELL_EDIT: "cell-edit",
  ROW_ACTION: "row-action",
  LOAD_START: "load-start",
  LOAD_END: "load-end",
});

/**
 * Default configuration constants.
 * @enum {*}
 */
const DefaultConfig = Object.freeze({
  SKELETON_ROWS: 5,
  SKELETON_COLUMNS: 4,
});

/**
 * Data Table Web Component.
 * @extends HTMLElement
 */
class MyDataTableComponent extends HTMLElement {
  /** @type {ShadowRoot} */
  #shadowRoot;

  /** @type {Array<Object>} */
  #data = [];

  /** @type {Array<Object>} */
  #columns = [];

  /** @type {string} */
  #sortColumn = "";

  /** @type {string} */
  #sortDirection = SortDirection.NONE;

  /** @type {boolean} */
  #isEditing = false;

  /** @type {AbortController} */
  #eventAbortController;

  /** @type {boolean} */
  #isConnected = false;

  /**
   * Observed attributes for reactive updates.
   * @returns {!Array<string>}
   */
  static get observedAttributes() {
    return ["data", "columns", "loading", "card"];
  }

  constructor() {
    super();
    this.#shadowRoot = this.attachShadow({ mode: "open" });
    this.#eventAbortController = new AbortController();
  }

  /**
   * Lifecycle: Element added to DOM.
   */
  connectedCallback() {
    this.#isConnected = true;

    // Parse initial attributes
    this.#parseInitialAttributes();

    this.#render();
    this.#attachEventListeners();
  }

  /**
   * Lifecycle: Element removed from DOM.
   */
  disconnectedCallback() {
    this.#isConnected = false;
    this.#eventAbortController.abort();
  }

  /**
   * Parse attributes when component connects.
   * @private
   */
  #parseInitialAttributes() {
    // Parse data attribute
    const dataAttr = this.getAttribute("data");
    if (dataAttr) {
      try {
        const parsedData = JSON.parse(dataAttr);
        this.#validateData(parsedData);
        this.#data = parsedData;
      } catch (error) {
        console.error("Failed to parse data attribute:", error);
        this.#data = [];
      }
    }

    // Parse columns attribute
    const columnsAttr = this.getAttribute("columns");
    if (columnsAttr) {
      try {
        const parsedColumns = JSON.parse(columnsAttr);
        this.#validateColumns(parsedColumns);
        this.#columns = parsedColumns;
      } catch (error) {
        console.error("Failed to parse columns attribute:", error);
        this.#columns = [];
      }
    }
  }

  /**
   * Lifecycle: Attribute changes.
   * @param {string} name - Attribute name.
   * @param {string} oldValue - Previous value.
   * @param {string} newValue - New value.
   */
  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue || !this.#isConnected) return;

    switch (name) {
      case "data":
        this.#handleDataChange(newValue);
        break;
      case "columns":
        this.#handleColumnsChange(newValue);
        break;
      case "loading":
        this.#handleLoadingChange();
        break;
      case "card":
        this.#handleCardChange();
        break;
      default:
        break;
    }
  }

  /**
   * Get data property.
   * @returns {!Array<Object>}
   */
  get data() {
    return this.#data;
  }

  /**
   * Set data property.
   * @param {!Array<Object>} value - Array of row objects.
   */
  set data(value) {
    this.#validateData(value);
    this.#data = value;
    if (this.#isConnected) {
      this.#renderTable();
    }
  }

  /**
   * Get columns property.
   * @returns {!Array<Object>}
   */
  get columns() {
    return this.#columns;
  }

  /**
   * Set columns property.
   * @param {!Array<Object>} value - Array of column definitions.
   */
  set columns(value) {
    this.#validateColumns(value);
    this.#columns = value;
    if (this.#isConnected) {
      this.#renderTable();
    }
  }

  /**
   * Get loading state.
   * @returns {boolean}
   */
  get loading() {
    return this.hasAttribute("loading");
  }

  /**
   * Set loading state.
   * @param {boolean} value - Whether to show loading skeleton.
   */
  set loading(value) {
    if (value) {
      this.setAttribute("loading", "");
      this.#emitEvent(DataTableEvent.LOAD_START);
    } else {
      this.removeAttribute("loading");
      this.#emitEvent(DataTableEvent.LOAD_END);
    }
  }

  /**
   * Get card wrapper state.
   * @returns {boolean}
   */
  get card() {
    return this.hasAttribute("card");
  }

  /**
   * Set card wrapper state.
   * @param {boolean} value - Whether to show card wrapper.
   */
  set card(value) {
    if (value) {
      this.setAttribute("card", "");
    } else {
      this.removeAttribute("card");
    }
  }

  /**
   * Validate data input.
   * @param {*} data - Data to validate.
   * @throws {ValidationError}
   * @private
   */
  #validateData(data) {
    if (!Array.isArray(data)) {
      throw new DataTableError.ValidationError("Data must be an array");
    }

    data.forEach((row, index) => {
      if (typeof row !== "object" || row === null) {
        throw new DataTableError.ValidationError(
          `Row at index ${index} must be an object`,
        );
      }
    });
  }

  /**
   * Validate columns input.
   * @param {*} columns - Columns to validate.
   * @throws {ValidationError}
   * @private
   */
  #validateColumns(columns) {
    if (!Array.isArray(columns)) {
      throw new DataTableError.ValidationError("Columns must be an array");
    }

    if (columns.length === 0) {
      throw new DataTableError.ValidationError("Columns array cannot be empty");
    }

    columns.forEach((col, index) => {
      if (typeof col !== "object" || col === null) {
        throw new DataTableError.ValidationError(
          `Column at index ${index} must be an object`,
        );
      }

      if (typeof col.key !== "string" || !col.key.trim()) {
        throw new DataTableError.ValidationError(
          `Column at index ${index} must have a string key`,
        );
      }

      if (typeof col.title !== "string" || !col.title.trim()) {
        throw new DataTableError.ValidationError(
          `Column at index ${index} must have a string title`,
        );
      }
    });
  }

  /**
   * Handle data attribute change.
   * @param {string} newValue - New attribute value.
   * @private
   */
  #handleDataChange(newValue) {
    try {
      const parsedData = newValue ? JSON.parse(newValue) : [];
      this.#validateData(parsedData);
      this.#data = parsedData;
      this.#renderTable();
    } catch (error) {
      console.error("Failed to parse data attribute:", error);
      this.#data = [];
    }
  }

  /**
   * Handle columns attribute change.
   * @param {string} newValue - New attribute value.
   * @private
   */
  #handleColumnsChange(newValue) {
    try {
      const parsedColumns = newValue ? JSON.parse(newValue) : [];
      this.#validateColumns(parsedColumns);
      this.#columns = parsedColumns;
      this.#renderTable();
    } catch (error) {
      console.error("Failed to parse columns attribute:", error);
      this.#columns = [];
    }
  }

  /**
   * Handle loading attribute change.
   * @private
   */
  #handleLoadingChange() {
    this.#renderTable();
  }

  /**
   * Handle card attribute change.
   * @private
   */
  #handleCardChange() {
    this.#render();
  }

  /**
   * Emit custom event.
   * @param {string} eventName - Event name from DataTableEvent.
   * @param {Object} detail - Event detail payload.
   * @private
   */
  #emitEvent(eventName, detail = {}) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  /**
   * Attach event listeners to shadow DOM.
   * @private
   */
  #attachEventListeners() {
    const { signal } = this.#eventAbortController;

    this.#shadowRoot.addEventListener(
      "click",
      (event) => {
        this.#handleClick(event);
      },
      { signal },
    );

    this.#shadowRoot.addEventListener(
      "dblclick",
      (event) => {
        this.#handleDoubleClick(event);
      },
      { signal },
    );

    this.#shadowRoot.addEventListener(
      "keydown",
      (event) => {
        this.#handleKeydown(event);
      },
      { signal },
    );
  }

  /**
   * Handle click events for sorting and actions.
   * @param {Event} event - Click event.
   * @private
   */
  #handleClick(event) {
    const headerCell = event.target.closest("[data-sortable]");
    if (headerCell && !this.loading && !this.#isEditing) {
      this.#handleSort(headerCell);
      return;
    }

    const actionButton = event.target.closest("[data-action]");
    if (actionButton) {
      this.#handleRowAction(actionButton);
    }
  }

  /**
   * Handle double-click events for cell editing.
   * @param {Event} event - Double-click event.
   * @private
   */
  #handleDoubleClick(event) {
    const cell = event.target.closest("[data-editable]");
    if (cell && !this.loading && !this.#isEditing) {
      this.#startCellEdit(cell);
    }
  }

  /**
   * Handle keydown events for edit mode.
   * @param {Event} event - Keydown event.
   * @private
   */
  #handleKeydown(event) {
    if (!this.#isEditing) return;

    const input = this.#shadowRoot.activeElement;
    if (!input || !input.hasAttribute("data-edit-input")) return;

    switch (event.key) {
      case "Enter":
        event.preventDefault();
        this.#commitCellEdit(input);
        break;
      case "Escape":
        event.preventDefault();
        this.#cancelCellEdit(input);
        break;
      default:
        break;
    }
  }

  /**
   * Handle column sorting.
   * @param {HTMLElement} headerCell - Clicked header cell.
   * @private
   */
  #handleSort(headerCell) {
    const columnKey = headerCell.dataset.column;
    let newDirection = SortDirection.ASC;

    if (this.#sortColumn === columnKey) {
      newDirection =
        this.#sortDirection === SortDirection.ASC
          ? SortDirection.DESC
          : SortDirection.NONE;
    }

    this.#sortColumn = newDirection === SortDirection.NONE ? "" : columnKey;
    this.#sortDirection = newDirection;

    this.#renderTable();
    this.#emitEvent(DataTableEvent.SORT, {
      column: columnKey,
      direction: newDirection,
    });
  }

  /**
   * Handle row actions.
   * @param {HTMLElement} button - Action button.
   * @private
   */
  #handleRowAction(button) {
    const action = button.dataset.action;
    const rowId = button.closest("tr").dataset.rowId;

    this.#emitEvent(DataTableEvent.ROW_ACTION, {
      action,
      rowId,
      rowData: this.#data.find((row) => row.id === rowId),
    });
  }

  /**
   * Start cell editing.
   * @param {HTMLElement} cell - Cell to edit.
   * @private
   */
  #startCellEdit(cell) {
    this.#isEditing = true;

    const rowId = cell.closest("tr").dataset.rowId;
    const columnKey = cell.dataset.column;
    const currentValue = cell.textContent?.trim() ?? "";

    const input = document.createElement("input");
    input.type = "text";
    input.value = currentValue;
    input.setAttribute("data-edit-input", "");
    input.className = "cell-edit-input";

    cell.textContent = "";
    cell.appendChild(input);
    input.focus();
    input.select();

    this.#emitEvent(DataTableEvent.CELL_EDIT_START, {
      rowId,
      columnKey,
      value: currentValue,
    });
  }

  /**
   * Commit cell edit.
   * @param {HTMLInputElement} input - Edit input.
   * @private
   */
  #commitCellEdit(input) {
    const cell = input.closest("td");
    const rowId = cell.closest("tr").dataset.rowId;
    const columnKey = cell.dataset.column;
    const newValue = input.value.trim();

    cell.textContent = newValue;
    this.#isEditing = false;

    this.#emitEvent(DataTableEvent.CELL_EDIT, {
      rowId,
      columnKey,
      oldValue: input.defaultValue,
      newValue,
    });
  }

  /**
   * Cancel cell edit.
   * @param {HTMLInputElement} input - Edit input.
   * @private
   */
  #cancelCellEdit(input) {
    const cell = input.closest("td");
    cell.textContent = input.defaultValue;
    this.#isEditing = false;
  }

  /**
   * Sort data based on current sort state.
   * @returns {!Array<Object>} Sorted data.
   * @private
   */
  #getSortedData() {
    if (this.#sortDirection === SortDirection.NONE) {
      return [...this.#data];
    }

    const column = this.#columns.find((col) => col.key === this.#sortColumn);
    if (!column?.sortable) {
      return [...this.#data];
    }

    return [...this.#data].sort((a, b) => {
      const aVal = a[this.#sortColumn];
      const bVal = b[this.#sortColumn];

      if (aVal === bVal) return 0;

      const modifier = this.#sortDirection === SortDirection.ASC ? 1 : -1;

      if (typeof aVal === "number" && typeof bVal === "number") {
        return (aVal - bVal) * modifier;
      }

      return String(aVal).localeCompare(String(bVal)) * modifier;
    });
  }

  /**
   * Render the complete component.
   * @private
   */
  #render() {
    // Clear existing content
    this.#shadowRoot.innerHTML = "";
    console.warn(this.card);
    // Create card wrapper if card attribute is present
    if (this.card) {
      const cardWrapper = document.createElement("div");
      cardWrapper.className =
        "flex flex-col bg-white border border-gray-200 shadow-2xs rounded-xl p-4 md:p-5 dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400";
      this.#shadowRoot.appendChild(cardWrapper);
      this.#renderTableContent(cardWrapper);
    } else {
      // Render directly to shadow root without card wrapper
      this.#renderTableContent(this.#shadowRoot);
    }
  }

  /**
   * Render table content into container.
   * @param {HTMLElement} container - Container element.
   * @private
   */
  #renderTableContent(container) {
    const table = document.createElement("table");
    table.setAttribute("part", "table");

    if (this.loading) {
      table.appendChild(this.#renderSkeleton());
    } else {
      if (this.#columns.length > 0) {
        table.appendChild(this.#renderHeader());
      }
      if (this.#data.length > 0) {
        table.appendChild(this.#renderBody());
      } else if (this.#columns.length > 0) {
        // Show empty state if we have columns but no data
        table.appendChild(this.#renderEmptyState());
      }
    }

    container.appendChild(table);
  }

  /**
   * Render table header.
   * @returns {HTMLTableSectionElement} Header element.
   * @private
   */
  #renderHeader() {
    const thead = document.createElement("thead");
    thead.setAttribute("part", "header");

    const headerRow = document.createElement("tr");
    headerRow.setAttribute("part", "header-row");

    this.#columns.forEach((column) => {
      const th = document.createElement("th");
      th.setAttribute("part", "header-cell");
      th.textContent = column.title;

      if (column.sortable) {
        th.setAttribute("data-sortable", "");
        th.setAttribute("data-column", column.key);
        th.style.cursor = "pointer";

        if (
          this.#sortColumn === column.key &&
          this.#sortDirection !== SortDirection.NONE
        ) {
          th.setAttribute("data-sort-direction", this.#sortDirection);
        }
      }

      headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    return thead;
  }

  /**
   * Render table body.
   * @returns {HTMLTableSectionElement} Body element.
   * @private
   */
  #renderBody() {
    const tbody = document.createElement("tbody");
    tbody.setAttribute("part", "body");

    const sortedData = this.#getSortedData();

    sortedData.forEach((row) => {
      const tr = document.createElement("tr");
      tr.setAttribute("part", "body-row");
      tr.setAttribute("data-row-id", row.id);

      this.#columns.forEach((column) => {
        const td = document.createElement("td");
        td.setAttribute("part", "data-cell");
        td.setAttribute("data-column", column.key);

        if (column.editable) {
          td.setAttribute("data-editable", "");
        }

        if (typeof column.render === "function") {
          try {
            const renderedContent = column.render(row[column.key], row);
            if (renderedContent instanceof HTMLElement) {
              td.appendChild(renderedContent);
            } else {
              td.textContent = String(renderedContent ?? "");
            }
          } catch (error) {
            console.error("Error rendering cell:", error);
            td.textContent = "Error";
          }
        } else {
          td.textContent = String(row[column.key] ?? "");
        }

        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });

    return tbody;
  }

  /**
   * Render empty state.
   * @returns {HTMLTableSectionElement} Empty state element.
   * @private
   */
  #renderEmptyState() {
    const tbody = document.createElement("tbody");
    tbody.setAttribute("part", "empty-state");

    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = this.#columns.length;
    td.textContent = "No data available";
    td.style.textAlign = "center";
    td.style.padding = "40px";
    td.style.color = "#6c757d";

    tr.appendChild(td);
    tbody.appendChild(tr);
    return tbody;
  }

  /**
   * Render loading skeleton.
   * @returns {HTMLTableSectionElement} Skeleton element.
   * @private
   */
  #renderSkeleton() {
    const tbody = document.createElement("tbody");
    tbody.setAttribute("part", "skeleton");

    for (let i = 0; i < DefaultConfig.SKELETON_ROWS; i++) {
      const tr = document.createElement("tr");
      tr.setAttribute("part", "skeleton-row");

      for (
        let j = 0;
        j < (this.#columns.length || DefaultConfig.SKELETON_COLUMNS);
        j++
      ) {
        const td = document.createElement("td");
        td.setAttribute("part", "skeleton-cell");

        const skeleton = document.createElement("div");
        skeleton.style.width = `${Math.random() * 50 + 50}px`;
        skeleton.style.height = "16px";
        skeleton.style.backgroundColor = "#e5e7eb";
        skeleton.style.borderRadius = "4px";
        skeleton.style.animation = "pulse 2s infinite";

        td.appendChild(skeleton);
        tr.appendChild(td);
      }

      tbody.appendChild(tr);
    }

    return tbody;
  }

  /**
   * Re-render table content.
   * @private
   */
  #renderTable() {
    if (!this.#isConnected) return;

    const container = this.card
      ? this.#shadowRoot.querySelector("div")
      : this.#shadowRoot;

    if (!container) {
      this.#render();
      return;
    }

    const oldTable = container.querySelector("table");
    if (oldTable) {
      oldTable.remove();
    }

    this.#renderTableContent(container);
  }
}

// Register the custom element
customElements.define("my-data-table-component", MyDataTableComponent);

export default MyDataTableComponent;
