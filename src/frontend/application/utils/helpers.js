"use strict";
/**
 * Capitalizes the first letter of a given string.
 *
 * @param {string} text - The input string to capitalize the first letter of.
 * @returns {string} The input string with the first letter capitalized.
 */
const capitalizedFirstLetter = (text) => {
  const capitalized = text.charAt(0).toUpperCase() + text.slice(1);
  return capitalized;
};

/**
 * Orders the items of an object alphabetically by their keys.
 *
 * @param {Object} unorderedObject - The object whose items need to be ordered.
 * @returns {Object} The ordered object with its items sorted alphabetically by keys.
 */
const orderObjectItems = (unorderedObject) => {
  const orderedObject = Object.keys(unorderedObject)
    .sort()
    .reduce((obj, key) => {
      obj[key] = unorderedObject[key];
      return obj;
    }, {});
  return orderedObject;
};

/**
 * Check if the input is a single HTML element or a RadioNodeList.
 *
 * @param {HTMLElement|RadioNodeList} htmlElement - The input element to check.
 * @returns {string} Returns "single" if the input is a single HTML element, or "multiple" if it is a RadioNodeList.
 */
const checkIfInputSingleOrList = (htmlElement) => {
  // RadioNodeList, HTMLInputElement
  if (htmlElement.getConstructorName() === "RadioNodeList") {
    // in case multiple inputs
    return "multiple";
  } else if (htmlElement.getConstructorName() === "HTMLInputElement") {
    // in case single input
    return "single";
  }
};

/**
 * Converts a string to a boolean value.
 *
 * @param {string} text - The input string to convert.
 * @returns {boolean} The boolean value converted from the input string.
 */
const convertStrToBool = (text) => {
  const boolValue = /true/i.test(text);
  if (boolValue === true) {
    return true;
  } else {
    return false;
  }
};

/**
 * Capitalizes the first letter of a given string.
 *
 * @param {string} string - The input string to capitalize the first letter of.
 * @return {string} The input string with the first letter capitalized.
 */
const capitalizeFirstLetter = (string) => {
  return string.charAt(0).toUpperCase() + string.slice(1);
};

/**
 * Escapes special HTML characters to prevent XSS vulnerabilities.
 *
 * @param {string} str - The raw string to escape.
 * @returns {string} The HTML-encoded string.
 */
const escapeHTML = (str) => {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

export {
  capitalizedFirstLetter,
  orderObjectItems,
  checkIfInputSingleOrList,
  convertStrToBool,
  capitalizeFirstLetter,
  escapeHTML,
};
