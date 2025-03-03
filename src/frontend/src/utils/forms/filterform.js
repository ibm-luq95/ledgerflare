"use strict";

/**
 * @class FilterPersistence
 * @description Handles persistent form filters using localStorage and URL params
 */
class FilterPersistence {
  /**
   * @param {HTMLFormElement} form - Form element containing filters
   * @param {string} storagePrefix - Prefix for localStorage keys
   */
  constructor(form, storagePrefix = "filter_") {
    if (!form || !(form instanceof HTMLFormElement)) {
      throw new Error("Valid HTMLFormElement required");
    }

    this.form = form;
    this.storagePrefix = storagePrefix;
    this.inputListener = (e) => this.handleInputChange(e.target);

    this.initialize();
  }

  initialize() {
    this.loadFilters();
    this.form.addEventListener("input", this.inputListener);
    this.form.addEventListener("reset", () => this.safeResetFilters());
  }

  /**
   * Handles input changes and saves state
   * @param {HTMLInputElement} input - Changed input element
   */
  handleInputChange(input) {
    try {
      if (!input.name) return;

      const key = `${this.storagePrefix}${input.name}`;
      let value;

      switch (input.type) {
        case "checkbox":
          value = this.handleCheckboxChange(input);
          break;

        case "radio":
          if (!input.checked) return;
          value = input.value;
          break;

        case "select-multiple":
          value = Array.from(input.selectedOptions)
            .map((opt) => opt.value)
            .join(",");
          break;

        default:
          value = input.value;
          break;
      }

      this.updateStorage(key, value);
      this.updateUrlParams(input.name, value);
      this.form.dispatchEvent(new Event("filtersUpdated"));
    } catch (error) {
      console.error(`Error processing ${input.name}:`, error);
    }
  }

  /**
   * Handles checkbox state changes
   * @param {HTMLInputElement} checkbox - Changed checkbox element
   * @returns {string|null} - Stored value or null
   */
  handleCheckboxChange(checkbox) {
    const checkboxes = this.form.querySelectorAll(
      `input[type="checkbox"][name="${CSS.escape(checkbox.name)}"]`,
    );

    // Handle checkbox groups
    if (checkboxes.length > 1) {
      const values = Array.from(checkboxes)
        .filter((cb) => cb.checked)
        .map((cb) => cb.value || "on");
      return values.length > 0 ? values.join(",") : null;
    }

    // Handle single checkbox
    return checkbox.checked ? checkbox.value || "on" : null;
  }

  /**
   * Updates localStorage with new value
   * @param {string} key - Storage key
   * @param {string|null} value - Value to store
   */
  updateStorage(key, value) {
    if (value !== null) {
      localStorage.setItem(key, value);
    } else {
      localStorage.removeItem(key);
    }
  }

  /**
   * Updates URL parameters
   * @param {string} name - Parameter name
   * @param {string|null} value - Parameter value
   */
  updateUrlParams(name, value) {
    const url = new URL(window.location);
    if (value !== null) {
      url.searchParams.set(name, value);
    } else {
      url.searchParams.delete(name);
    }
    window.history.replaceState({}, "", url);
  }

  /**
   * Loads and applies saved filters
   */
  loadFilters() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const newParams = new URLSearchParams();
      let shouldReload = false;

      Array.from(this.form.elements).forEach((input) => {
        if (!input.name) return;

        const storedValue = urlParams.has(input.name)
          ? urlParams.get(input.name)
          : localStorage.getItem(`${this.storagePrefix}${input.name}`);

        if (storedValue === null) return;

        this.applyValueToInput(input, storedValue);

        // If the value came from URL params, sync it with localStorage
        if (urlParams.has(input.name)) {
          localStorage.setItem(`${this.storagePrefix}${input.name}`, storedValue);
          newParams.set(input.name, storedValue);
        } else {
          shouldReload = true; // Flag to indicate a potential reload is needed
          newParams.set(input.name, storedValue);
        }
      });

      // Check if the URL actually needs updating
      if (shouldReload && newParams.toString() !== urlParams.toString()) {
        window.location.search = newParams.toString(); // Only reload if URL is different
      }
    } catch (error) {
      console.error("Error loading filters:", error);
    }
  }

  /**
   * Applies stored value to form input
   * @param {HTMLInputElement} input - Form element
   * @param {string} value - Stored value
   */
  applyValueToInput(input, value) {
    switch (input.type) {
      case "checkbox":
        this.applyCheckboxValue(input, value);
        break;

      case "radio":
        input.checked = input.value === value;
        break;

      case "select-multiple":
        const values = value.split(",");
        Array.from(input.options).forEach((opt) => {
          opt.selected = values.includes(opt.value);
        });
        break;

      default:
        input.value = value;
        break;
    }
  }

  /**
   * Applies value to checkbox(s)
   * @param {HTMLInputElement} checkbox - Checkbox element
   * @param {string} value - Stored value
   */
  applyCheckboxValue(checkbox, value) {
    const checkboxes = this.form.querySelectorAll(
      `input[type="checkbox"][name="${CSS.escape(checkbox.name)}"]`,
    );

    if (checkboxes.length > 1) {
      const values = value.split(",");
      checkboxes.forEach((cb) => {
        cb.checked = values.includes(cb.value || "on");
      });
    } else {
      checkbox.checked = value === (checkbox.value || "on");
    }
  }

  /**
   * Resets all filters and clears storage
   */
  safeResetFilters() {
    try {
      // Clear localStorage
      Array.from(this.form.elements).forEach((input) => {
        if (input.name) {
          localStorage.removeItem(`${this.storagePrefix}${input.name}`);
        }
      });

      // Clear URL params
      const url = new URL(window.location);
      url.search = "";
      window.history.replaceState({}, "", url);

      // Reset form and inputs
      this.form.removeEventListener("input", this.inputListener);
      this.form.reset();

      // Force-uncheck checkboxes and radios
      setTimeout(() => {
        Array.from(this.form.elements).forEach((input) => {
          if (input.type === "checkbox" || input.type === "radio") {
            input.checked = false;
          } else if (input.multiple) {
            Array.from(input.options).forEach((opt) => (opt.selected = false));
          }
        });
        this.form.addEventListener("input", this.inputListener);
      }, 0);

      this.form.dispatchEvent(new Event("filtersReset"));
    } catch (error) {
      console.error("Error resetting filters:", error);
    }
  }
}

// Usage example:
// const filterForm = document.getElementById("filter-form");
// if (filterForm) new FilterPersistence(filterForm);

export default FilterPersistence;
