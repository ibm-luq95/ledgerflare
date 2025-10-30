"use strict";

import { DEBUG } from "./constants.js";

/**
 * Debugging print only if DEBUG is enabled, development only
 * @param {string} text Message to print
 * @param {string} consoleType Console log type
 */
const debuggingPrint = (text, consoleType = "log") => {
  if (DEBUG === true) {
    switch (consoleType) {
      case "log":
        console.log(text);
        break;
      case "warn":
        console.warn(text);
        break;
      case "info":
        console.info(text);
        break;
      case "error":
        console.error(text);
        break;
      case "dir":
        console.dir(text);
        break;
      case "table":
        console.table(text);
        break;

      default:
        break;
    }
  }
};

export { debuggingPrint };
