"use strict";

/**
 * Retrieves the value of a cookie by its name. this from the official Django documentation
 * This method only used in API requests
 *
 * @param {string} name - The name of the cookie.
 * @returns {string|null} - The value of the cookie, or null if the cookie does not exist.
 */
const getCookie = (name) => {
  if (name === "csrftoken") {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.getAttribute("content")) {
      const metaToken = metaTag.getAttribute("content").trim();
      if (metaToken.length === 64) {
        return metaToken;
      }
    }
    const inputTag = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (inputTag && inputTag.value) {
      const inputToken = inputTag.value.trim();
      if (inputToken.length === 64) {
        return inputToken;
      }
    }
  }

  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

export { getCookie };
