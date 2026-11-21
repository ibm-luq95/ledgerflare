"use strict";

import { DEBUG } from "./constants.js";
import { orderObjectItems } from "./helpers.js";
import { SessionStorageManagement } from "./storage.js";

/**
 * Enable or disable form fieldset items with form's submit button
 * @typedef param
 * @param {Object} param - this is object param
 * @param {HTMLFormElement} param.formElement HTML form element
 * @param {string} param.state this will enable or disable
 */
const removeBGInputsColors = ({ formElement, state }) => {};

/**
 * Enable or disable form fieldset items with form's submit button
 * @param {HTMLInputElement} param.input HTML checkbox input element
 */
const castBooleanCheckboxElement = (input) => {
  // const trueArray = [/true/i, /on/i];
  /* const booleanMap = new Map();
  booleanMap.set("true", /\b(on|true)\b/i);
  booleanMap.set("false", /\b(off|false)\b/i);
  if(booleanMap.get("true").test(input.value) === true){
    console.warn(booleanMap.get("true").match(input.value));
    return true;
  } */
  const inputValue = input.value.toLowerCase();
  if (input.value === "on" || input.value === "true") {
    return true;
  } else if (input.value === "false" || input.value === "off") {
    return false;
  } else {
    return input.value;
  }
};

/**
 * Serializes form elements into an object or FormData with Django compatibility.
 * @param {Object} config - Configuration object
 * @param {HTMLFormElement} config.formElement - Form element to serialize
 * @param {string[]} [config.excludedFields=[]] - Field names to exclude
 * @param {boolean} [config.isOrdered=false] - Alphabetically order keys
 * @param {boolean} [config.returnAsFormData=false] - Return FormData instead
 * @param {string[]} [config.filesArray=[]] - File input names to include
 * @returns {Object|FormData} Serialized form data
 */
const formInputSerializer = ({
  formElement,
  excludedFields = [],
  isOrdered = false,
  returnAsFormData = false,
  filesArray = [],
}) => {
  /** @type {Record<string, any>} */
  const formData = {};
  const elements = Array.from(formElement.elements);

  // Group special elements
  const groupedElements = elements.reduce(
    (acc, el) => {
      if (!el.name || excludedFields.includes(el.name)) return acc;

      if (el.type === "checkbox") {
        const current = acc.checkboxes.get(el.name) || [];
        acc.checkboxes.set(el.name, [...current, el]);
      } else if (el.type === "radio") {
        const current = acc.radios.get(el.name) || [];
        acc.radios.set(el.name, [...current, el]);
      }
      return acc;
    },
    { checkboxes: new Map(), radios: new Map() },
  );

  // Process regular inputs
  elements.forEach((el) => {
    if (!el.name || excludedFields.includes(el.name)) return;

    if (["checkbox", "radio", "file"].includes(el.type)) return;

    if (el instanceof HTMLSelectElement && el.multiple) {
      formData[el.name] = Array.from(el.selectedOptions).map((opt) => opt.value);
    } else if (el.name && !formData.hasOwnProperty(el.name)) {
      formData[el.name] = el.value;
    }
  });

  // Process radio groups
  groupedElements.radios.forEach((radios, name) => {
    const checked = radios.find((radio) => radio.checked);
    if (checked) formData[name] = checked.value;
  });

  // Process checkboxes (Django compatibility)
  groupedElements.checkboxes.forEach((checkboxes, name) => {
    const checkedValues = checkboxes
      .filter((cb) => cb.checked)
      .map((cb) => cb.value || "on"); // Default to 'on' per HTML spec

    if (checkedValues.length === 0) return;

    // Handle single/multiple checkboxes
    formData[name] =
      checkboxes.length === 1
        ? handleDjangoCheckboxValue(checkedValues[0])
        : checkedValues;
  });

  // Order keys if requested
  const finalData = isOrdered
    ? Object.fromEntries(Object.entries(formData).sort(([a], [b]) => a.localeCompare(b)))
    : formData;
  // console.warn(finalData);
  // throw new Error("D");
  // Convert to FormData if required
  if (!returnAsFormData) return finalData;

  const formDataObj = new FormData();
  Object.entries(finalData).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((v) => formDataObj.append(key, v));
    } else {
      formDataObj.append(key, value);
    }
  });

  // Handle file inputs
  filesArray.forEach((name) => {
    const fileInput = formElement.querySelector(`[name='${name}']`);
    if (fileInput?.files?.length > 0) {
      Array.from(fileInput.files).forEach((file) => {
        formDataObj.append(name, file, file.name);
      });
    }
  });

  return formDataObj;
};

/**
 * Converts checkbox values to Django-compatible types
 * @param {string} value - Raw checkbox value
 * @returns {boolean|string} Processed value
 */
const handleDjangoCheckboxValue = (value) => {
  if (value === "on") return true;
  if (value === "off") return false;
  return value;
};

/**
 * Sets the values of form inputs based on an object of values.
 *
 * @param {HTMLFormElement} formElement - The form element to set values on.
 * @param {Object} objectOfValues - An object containing the values to set on the form inputs.
 * @throws {Error} If the formElement is not an instance of HTMLFormElement.
 * @returns {void}
 */
const setFormInputValues = (formElement, objectOfValues) => {
  const wyswygCssClass = "wyswyg-textarea";
  // check the type of formElement is HTMLFormElement
  if (formElement.constructor.name !== "HTMLFormElement") {
    throw new Error("The element to set values not form element!!");
  }
  for (const name in objectOfValues) {
    try {
      if (Object.hasOwnProperty.call(objectOfValues, name)) {
        const inputValue = objectOfValues[name];
        const cleanValue = inputValue.replace(/(<([^>]+)>)/gi, "");
        const fElement = formElement.elements[name];
        fElement.value = cleanValue;
        // formElement.elements[name].value =
      }
    } catch (error) {
      if (error instanceof TypeError) {
        // in case the input or element not exists
        if (DEBUG === true) {
          console.warn(`The element ${name} not exists in the form ${formElement.id}`);
        }
      }
    }
  }
};

/**
 * Disables or enables the items within a fieldset based on the provided state.
 *
 * @param {Object} options - The options object.
 * @param {HTMLElement} options.formElement - The form element containing the fieldset.
 * @param {string} options.state - The state to set for the fieldset items. Can be "enable" or "disable".
 */
const disableAndEnableFieldsetItems = ({ formElement, state }) => {
  if (!formElement || !state) return;
  SessionStorageManagement.clear();
  const stateLower = state.toLowerCase();
  const fieldset = formElement.querySelector("fieldset");
  const disabledInputCssClasses = [
    "cursor-not-allowed",
    "opacity-70",
    "bg-gray-100",
  ];
  const allFormInputs = formElement.querySelectorAll("input, select, textarea, button");
  const submitBtn = formElement.id ? document.querySelector(`button[form="${formElement.id}"]`) : null;

  switch (stateLower) {
    case "enable":
    case "e":
    case "en":
      if (fieldset) fieldset.disabled = false;
      if (submitBtn) submitBtn.disabled = false;
      if (allFormInputs.length > 0) {
        allFormInputs.forEach((element) => {
          element.disabled = false;
          element.classList.remove(...disabledInputCssClasses);
        });
      }
      break;
    case "disable":
    case "dis":
    case "d":
      if (fieldset) fieldset.disabled = true;
      if (submitBtn) submitBtn.disabled = true;
      if (allFormInputs.length > 0) {
        allFormInputs.forEach((element) => {
          element.disabled = true;
          element.classList.add(...disabledInputCssClasses);
        });
      }
    default:
      console.warn(`${stateLower} not defined!`);
      break;
  }
};

/**
 * Sets the form inputs to read-only mode.
 *
 * @param {string} formID - The ID of the form element.
 * @returns {void}
 */
const setFormInputsReadOnly = (formID) => {
  const readOnlyFormElement = document.querySelector(`form#${formID}`);
  if (readOnlyFormElement) {
    const inputsArray = Array.from(readOnlyFormElement.elements);
    inputsArray.forEach((input) => {
      input.setAttribute("readonly", "readonly");
    });
  }
};

export {
  formInputSerializer,
  setFormInputValues,
  disableAndEnableFieldsetItems,
  removeBGInputsColors,
  setFormInputsReadOnly,
};
