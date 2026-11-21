"use strict";

/**
 * Class representing a SessionStorageManagement.
 * This class provides static methods to interact with the session storage of the browser.
 * It allows checking for the existence of items, retrieving items, setting or updating items, deleting items, and clearing all session storage.
 * @class
 */
class SessionStorageManagement {
  /**
   * Clears all data from sessionStorage.
   */
  static clear() {
    sessionStorage.clear();
  }

  /**
   * Checks if a specific key exists in sessionStorage.
   * @param {string} keyName - The name of the key to check in sessionStorage.
   * @returns {boolean} Returns true if the key exists, otherwise false.
   */
  static checkExists(keyName) {
    return sessionStorage.getItem(keyName) !== null;
  }

  /**
   * Retrieves the value associated with a specific key in sessionStorage.
   * @param {string} keyName - The name of the key whose value is to be retrieved.
   * @returns {string|null} Returns the value associated with the key if it exists, otherwise null.
   */
  static getItem(keyName) {
    if (SessionStorageManagement.checkExists(keyName)) {
      return sessionStorage.getItem(keyName);
    } else {
      return null;
    }
  }

  /**
   * Deletes a specific key and its associated value from sessionStorage.
   * @param {string} keyName - The name of the key to be deleted.
   */
  static deleteItem(keyName) {
    if (SessionStorageManagement.checkExists(keyName)) {
      sessionStorage.removeItem(keyName);
    } else {
      console.warn(`Item ${keyName} not exists in storage!`);
    }
  }

  /**
   * Sets or updates the value of a specific key in sessionStorage.
   * @param {string} keyName - The name of the key to set or update.
   * @param {*} keyValue - The value to be saved in sessionStorage.
   * @param {boolean} [replace=true] - If true, will replace or update the existing item. Currently, this parameter does not affect functionality as sessionStorage.setItem inherently replaces values.
   */
  static setItem(keyName, keyValue, replace = true) {
    sessionStorage.setItem(keyName, keyValue);
  }
}

export { SessionStorageManagement };
