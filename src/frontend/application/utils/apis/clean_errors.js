"use strict";

/**
 * Cleans the API error object and returns an array of error details.
 *
 * @param {Object} error - The API error object.
 * @returns {Array|null} - An array of error details or null if it's not an API error.
 */
const bwCleanApiError = (error) => {
  console.log(error);
  const allErrorsArray = [];
  const apiArrayErrors = ["type", "errors"];
  const errorKeys = Object.keys(error);
  if (errorKeys.includes(apiArrayErrors[0]) && errorKeys.includes(apiArrayErrors[1])) {
    const allErrors = error["errors"];
    allErrors.forEach((element) => {
      allErrorsArray.push({
        detail: element["detail"],
        attr: element["attr"],
      });
    });
    return allErrorsArray;
  } else {
    console.warn("Not api error");
    return null;
  }
};

export { bwCleanApiError };
