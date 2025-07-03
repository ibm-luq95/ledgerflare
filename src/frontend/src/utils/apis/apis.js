"use strict";

import { FETCHURLNAMEURL } from "../constants";
import { getCookie } from "../cookie";

/**
 * Fetches the URL path by name from backend.
 *
 * @param {string} urlName - The name of the URL.
 * @param {string|null} pk - The primary key (optional).
 * @returns {Promise} - A promise that resolves to the fetched data.
 * @throws {Error} - If there is an HTTP error.
 */
const fetchUrlPathByName = async (urlName, pk = null) => {
  try {
    const controller = new AbortController(); // the AbortController
    const { signal } = controller;
    const headers = new Headers({
      "Content-Type": "application/json;charset=utf-8",
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken"),
    });
    console.log(headers.get("X-CSRFToken"))
    const dataToSend = { urlName: urlName };
    if (pk) {
      dataToSend["pk"] = pk;
    }

    const fetchOptions = {
      method: "POST",
      mode: "same-origin",
      credentials: "include",
      cache: "no-cache",
      body: JSON.stringify(dataToSend),
    };
    const request = new Request(FETCHURLNAMEURL, {
      headers: headers,
      signal: signal,
    });
    const response = await fetch(request, fetchOptions);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(error);
  }
};
/**
 * Sends a request to the specified URL with the given options.
 *
 * @param {Object} options - The options for the request.
 * @param {string} options.url - The URL to send the request to.
 * @param {string} [options.contentType="application/json;charset=utf-8"] - The content type of the request.
 * @param {string} [options.token] - The CSRF token for the request.
 * @param {string} [options.method="GET"] - The HTTP method for the request.
 * @param {Object|FormData} [options.dataToSend] - The data to send with the request.
 * Can be a plain object (sent as JSON) or a FormData instance (for file uploads).
 * @param {boolean} [options.djangoRequest=false] - Enable Django/DRF-specific features.
 * @param {string} [options.environment="production"] - Environment name (development/production).
 * @param {boolean} [options.debug=false] - Enable console logging in development.
 * @param {boolean} [options.mockResponse=false] - Simulate a response without a real request.
 * @param {Object} [options.params] - Query parameters for GET requests.
 * @param {number} [options.timeout=60000] - Request timeout in milliseconds.
 * @param {number} [options.maxRetries=3] - Max number of retries in production.
 * @param {string} [options.baseUrl=''] - Base URL prepended to the request URL.
 * @param {string} [options.csrfToken] - Optional CSRF token override.
 * @returns {Promise} A promise that resolves with the response data or rejects with an error as a JSON object.
 */

// Helper function to get CSRF token from cookies
// function getCookie(name) {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         const cookies = document.cookie.split(';');
//         for (let i = 0; i < cookies.length; i++) {
//             const cookie = cookies[i].trim();
//             if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break;
//             }
//         }
//     }
//     return cookieValue;
// }

const sendRequest = (options) => {
  const environment =
    process.env.STAGE_ENVIRONMENT !== undefined
      ? process.env.STAGE_ENVIRONMENT
      : "production";
  const debug = process.env.DEBUG ? process.env.DEBUG === "true" : false;
  // Feature: Debugging and Logging
  if (environment === "development" && options.debug) {
    console.log(`[${options.method || "GET"}] Sending request to ${options.url}`, {
      headers: options.headers,
      body: options.dataToSend,
    });
  }

  // Feature: Mock Responses (only in development)
  if (environment === "development" && options.mockResponse) {
    return Promise.resolve(options.mockResponse);
  }

  // Feature: HTTPS Enforcement (only in production)
  if (
    environment === "production" &&
    options.url.startsWith("http://") &&
    !options.url.includes("localhost")
  ) {
    return Promise.reject({
      name: "SecurityError",
      message: "Insecure protocol detected. Use HTTPS in production.",
    });
  }

  // Feature: Configurable Base URL
  const baseUrl = options.baseUrl || "";
  let finalUrl = `${baseUrl}${options.url}`;

  // Feature: Query String Handling for GET Requests
  if ((options.method || "GET").toUpperCase() === "GET" && options.params) {
    const queryString = new URLSearchParams(options.params).toString();
    finalUrl = `${finalUrl}?${queryString}`;
  }

  // Feature: AbortController for Timeout and Cancellation
  const controller = new AbortController();
  const { signal } = controller;

  if (options.timeout) {
    setTimeout(() => controller.abort(), options.timeout);
  }

  // Feature: Dynamic Headers (Environment-Specific)
  const headers = new Headers({
    Accept: "application/json",
    "X-Requested-With": "XMLHttpRequest",
  });

  // Only set Content-Type if dataToSend is not FormData
  if (!(options.dataToSend instanceof FormData)) {
    headers.append(
      "Content-Type",
      options.contentType || "application/json;charset=utf-8"
    );
  }

  // FIXED: Always add CSRF token for Django requests (not just when djangoRequest is true)
  let credentials = "same-origin";

  // Add CSRF token for state-changing methods
  if (
    ["POST", "PUT", "PATCH", "DELETE"].includes((options.method || "GET").toUpperCase())
  ) {
    const csrfToken = options.csrfToken || getCookie("csrftoken");
    if (csrfToken) {
      headers.append("X-CSRFToken", csrfToken);
    }
  }

  // Apply Django/DRF-specific features only if djangoRequest is true
  if (options.djangoRequest) {
    // Add Authorization header for Token or JWT Authentication
    if (options.token) {
      headers.append("Authorization", `Bearer ${options.token}`);
    }

    // Include cookies for session-based authentication
    credentials = "include";

    // Add security headers in production
    if (environment === "production") {
      headers.append("X-Content-Type-Options", "nosniff");
      headers.append("X-XSS-Protection", "1; mode=block");
    }
  }

  // Feature: Retry Mechanism
  const maxRetries = options.maxRetries || (environment === "development" ? 1 : 3);
  const retryDelay = 1000;

  const retryRequest = async (attempt = 0) => {
    try {
      const fetchOptions = {
        method: options.method || "GET",
        mode: "cors", // POTENTIAL FIX: Consider changing to "same-origin" if all requests are to same domain
        cache: environment === "development" ? "no-cache" : "default",
        signal,
        headers,
        credentials,
      };

      // FIXED: Handle relative URLs properly
      if (options.url.startsWith("/") && !baseUrl) {
        finalUrl = options.url; // Use relative URL as-is
      }

      // Feature: Body Handling (JSON or FormData)
      if (
        ["POST", "PUT", "PATCH"].includes(fetchOptions.method.toUpperCase()) &&
        options.dataToSend
      ) {
        fetchOptions.body =
          options.dataToSend instanceof FormData
            ? options.dataToSend
            : JSON.stringify(options.dataToSend);
      }

      // DEBUGGING: Log the actual request being made
      if (environment === "development" && options.debug) {
        console.log("Final request options:", {
          url: finalUrl,
          method: fetchOptions.method,
          headers: Object.fromEntries(headers.entries()),
          credentials: fetchOptions.credentials,
          mode: fetchOptions.mode,
        });
      }

      const response = await fetch(finalUrl, fetchOptions);

      // Feature: Response Validation
      if (!response.ok) {
        const text = await response.text();
        let errorMessage = `HTTP error! Status: ${response.status}`;
        let errorData = {
          name: "HttpError",
          status: response.status,
          statusText: response.statusText,
          url: finalUrl,
          message: errorMessage,
        };

        try {
          const parsed = JSON.parse(text);
          Object.assign(errorData, parsed);
        } catch {
          errorData.body = text;
        }

        // ENHANCED: Better error logging for debugging
        if (environment === "development") {
          console.error("Request failed:", errorData);
          console.error("Request headers sent:", Object.fromEntries(headers.entries()));
        }

        throw errorData;
      }

      const contentType = response.headers.get("content-type");
      return contentType && contentType.includes("application/json")
        ? await response.json()
        : await response.text();
    } catch (error) {
      // If it's our custom HttpError, just pass it on
      if (error.status) {
        return Promise.reject(error);
      }

      // If it's a network error or timeout
      if (error.name === "AbortError") {
        return Promise.reject({
          name: "TimeoutError",
          message: `Request timed out after ${options.timeout}ms`,
          url: finalUrl,
        });
      }

      // Otherwise, generic fetch/network error
      if (attempt < maxRetries) {
        await new Promise((resolve) =>
          setTimeout(resolve, retryDelay * Math.pow(2, attempt))
        );
        return retryRequest(attempt + 1);
      }

      return Promise.reject({
        name: "NetworkError",
        message: error.message || "Network or fetch error occurred",
        url: finalUrl,
      });
    }
  };

  return retryRequest();
};

export { fetchUrlPathByName, sendRequest };
