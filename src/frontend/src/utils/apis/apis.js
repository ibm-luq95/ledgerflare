"use strict";

import { FETCHURLNAMEURL } from "../constants";
import { getCookie } from "../cookie";

// alert(csrfToken);

/**
 * @typedef {Object} ErrorDetails
 * @property {number} status - HTTP status code
 * @property {string} statusText - HTTP status text
 * @property {string} url - Request URL
 * @property {string} [cloudflareRay] - Cloudflare Ray ID if present
 * @property {string} [responseBody] - Raw response body
 * @property {Object} [parsedError] - Parsed JSON error object
 */

/**
 * @typedef {Object} CSRFDebugInfo
 * @property {boolean} exists - Whether CSRF token exists
 * @property {number} length - Length of CSRF token
 * @property {string} value - Truncated CSRF token value for debugging
 */

/**
 * @typedef {Object} FetchRequestData
 * @property {string} urlName - The URL name to fetch
 * @property {string} [pk] - Optional primary key
 */

/**
 * Fetches the URL path by name from backend with enhanced CSRF debugging.
 * Uses modern ES6+ syntax with comprehensive error handling.
 *
 * @param {string} urlName - The name of the URL to fetch
 * @param {string|null} [pk=null] - Optional primary key
 * @returns {Promise<Object>} Promise that resolves to the fetched data
 * @throws {Error} Throws error if CSRF token is invalid or HTTP request fails
 */
const fetchUrlPathByName = async (urlName, pk = null) => {
  try {
    // Create abort controller for request cancellation
    const controller = new AbortController();
    const { signal } = controller;

    // Get and validate CSRF token with comprehensive debugging
    const csrfToken = getCSRFToken();
    // const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    // const metaCsrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

    const debugInfo = generateCSRFDebugInfo(csrfToken);

    console.log("CSRF Token Debug:", debugInfo);

    // Validate CSRF token existence and format
    validateCSRFToken(csrfToken);

    // Prepare request headers with modern Map-like approach
    const headers = new Headers({
      "Content-Type": "application/json;charset=utf-8",
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
      "Cache-Control": "no-cache",
    });

    // Prepare request data using object spread and conditional assignment
    const requestData = {
      urlName,
      ...(pk && { pk }), // Only add pk if it exists
    };

    // Configure fetch options with modern syntax
    const fetchOptions = {
      method: "POST",
      mode: "same-origin",
      credentials: "include",
      cache: "no-cache",
      headers,
      signal,
      body: JSON.stringify(requestData),
      referrerPolicy: "same-origin",
    };

    // Optional rate limiting delay using Promise with arrow function
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Execute fetch request
    const response = await fetch(FETCHURLNAMEURL, fetchOptions);

    // Handle non-OK responses with detailed error information
    if (!response.ok) {
      await handleFetchError(response);
    }

    // Parse and return JSON response
    const data = await response.json();
    return data;
  } catch (error) {
    handleRequestError(error);
    throw error; // Re-throw for caller to handle
  }
};

/**
 * Generates comprehensive CSRF token debugging information.
 *
 * @param {string|null} token - The CSRF token to debug
 * @returns {CSRFDebugInfo} Debug information object
 */
const generateCSRFDebugInfo = (token) => ({
  exists: Boolean(token),
  length: token?.length ?? 0,
  value: token ? `${token.substring(0, 8)}...` : "null/undefined",
});

/**
 * Validates Django CSRF token format and throws descriptive errors.
 * Django CSRF tokens should be exactly 64 characters long.
 *
 * @param {string|null} token - The CSRF token to validate
 * @throws {Error} Throws error if token is invalid or not Django format
 */
const validateCSRFToken = (token) => {
  if (!token || token.length === 0) {
    throw new Error("CSRF token is missing or empty. Please refresh the page.");
  }

  // Django CSRF tokens must be exactly 64 characters long
  if (token.length !== 64) {
    console.error(
      `Invalid Django CSRF token length: ${token.length} characters (expected 64)`
    );
    console.error("This might indicate:");
    console.error('1. Wrong cookie name (should be "csrftoken")');
    console.error("2. Token truncation during retrieval");
    console.error("3. Non-Django CSRF system in use");
    console.error("4. CSRF middleware configuration issue");

    throw new Error(
      `Invalid Django CSRF token length: ${token.length} characters. Django requires 64-character tokens. Please check your Django CSRF configuration.`
    );
  }

  // Django CSRF tokens should match the expected pattern
  const djangoTokenPattern = /^[a-zA-Z0-9]{64}$/;
  if (!djangoTokenPattern.test(token)) {
    throw new Error(
      "CSRF token format is invalid for Django. Expected 64 alphanumeric characters."
    );
  }

  console.log("✓ Valid Django CSRF token detected (64 characters)");
};

/**
 * Handles fetch response errors with detailed logging and error extraction.
 *
 * @param {Response} response - The failed fetch response
 * @throws {Error} Always throws an error with detailed information
 */
const handleFetchError = async (response) => {
  let errorMessage = `HTTP error! status: ${response.status}`;

  /** @type {ErrorDetails} */
  const errorDetails = {
    status: response.status,
    statusText: response.statusText,
    url: FETCHURLNAMEURL,
  };

  // Extract Cloudflare Ray ID if present
  const cfRay = response.headers.get("CF-Ray");
  if (cfRay) {
    errorDetails.cloudflareRay = cfRay;
  }

  // Extract and parse response body for detailed error information
  try {
    const errorBody = await response.text();
    errorDetails.responseBody = errorBody;

    // Attempt to parse JSON error response
    const parsedError = tryParseJSON(errorBody);
    if (parsedError) {
      errorDetails.parsedError = parsedError;

      // Extract specific error messages using optional chaining
      const errorDetail = parsedError.errors?.[0]?.detail;
      if (errorDetail) {
        errorMessage += ` - ${errorDetail}`;
      }
    }
  } catch (bodyError) {
    // Ignore errors when reading response body
    console.debug("Could not read response body:", bodyError.message);
  }

  console.error("Fetch error details:", errorDetails);
  throw new Error(errorMessage);
};

/**
 * Handles different types of request errors with appropriate logging.
 *
 * @param {Error} error - The error object to handle
 */
const handleRequestError = (error) => {
  const errorHandlers = {
    AbortError: () => console.error("Request was aborted"),
    NetworkError: () => console.error("Network error:", error),
    default: () => console.error("Request error:", error),
  };

  if (error.name === "AbortError") {
    errorHandlers.AbortError();
  } else if (error.message.includes("Failed to fetch")) {
    errorHandlers.NetworkError();
  } else {
    errorHandlers.default();
  }
};

/**
 * Safely attempts to parse JSON string without throwing errors.
 *
 * @param {string} jsonString - The JSON string to parse
 * @returns {Object|null} Parsed object or null if parsing fails
 */
const tryParseJSON = (jsonString) => {
  try {
    return JSON.parse(jsonString);
  } catch {
    return null;
  }
};

/**
 * Enhanced cookie getter specifically for Django CSRF tokens.
 * Includes additional debugging for Django-specific issues.
 *
 * @param {string} name - The cookie name to retrieve
 * @returns {string|null} The cookie value or null if not found
 */
const getCookieFetchUrlPathByName = (name) => {
  // Return null if no cookies exist
  if (!document.cookie) {
    console.log(`Cookie '${name}': No cookies found`);
    return null;
  }

  console.log("All cookies:", document.cookie);

  // Use modern array methods to find cookie
  const cookies = document.cookie.split(";");
  const targetCookie = cookies
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith(`${name}=`));

  if (!targetCookie) {
    console.log(`Cookie '${name}': Not found`);
    console.log(
      "Available cookies:",
      cookies.map((c) => c.split("=")[0].trim())
    );
    return null;
  }

  const cookieValue = decodeURIComponent(targetCookie.substring(name.length + 1));
  console.log(`Cookie '${name}': Found (${cookieValue.length} characters)`);

  // Additional Django-specific debugging
  if (name === "csrftoken") {
    console.log("Django CSRF Token Analysis:");
    console.log(`- Length: ${cookieValue.length} (Django expects 64)`);
    console.log(
      `- Format: ${/^[a-zA-Z0-9]{64}$/.test(cookieValue) ? "Valid Django format" : "Invalid Django format"}`
    );
    console.log(`- First 8 chars: ${cookieValue.substring(0, 8)}...`);
  }

  return cookieValue;
};

/**
 * Gets CSRF token from meta tag in document head.
 *
 * @returns {string|null} CSRF token from meta tag or null if not found
 */
const getCSRFTokenFromMeta = () => {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  return metaTag?.getAttribute("content") ?? null;
};

/**
 * Gets CSRF token from form input element.
 *
 * @returns {string|null} CSRF token from form or null if not found
 */
const getCSRFTokenFromForm = () => {
  const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return csrfInput?.value ?? null;
};

/**
 * Robust CSRF token getter with multiple fallback strategies.
 * Validates token length for Django compliance (64 chars).
 *
 * @returns {string|null} Valid CSRF token or null
 */
const getCSRFToken = () => {
  const tokenSources = [
    { name: "cookie", getter: () => getCookieFetchUrlPathByName("csrftoken") },
    { name: "meta tag", getter: getCSRFTokenFromMeta },
    { name: "form input", getter: getCSRFTokenFromForm },
  ];

  for (const { name, getter } of tokenSources) {
    try {
      const token = getter();
      if (token && token.length === 64) {
        console.log(`✅ CSRF token from ${name}:`, token.substring(0, 8) + "...");
        return token;
      } else if (token) {
        console.warn(`⚠️ Token from ${name} is invalid length: ${token.length}`);
      }
    } catch (e) {
      console.warn(`❌ Error reading CSRF token from ${name}:`, e);
    }
  }

  console.error("🚫 No valid CSRF token found");
  return document.querySelector('meta[name="csrf-token"]')?.content;
};

/**
 * Utility function to refresh Django CSRF token by making a request to Django's CSRF endpoint.
 * This should get you a proper 64-character Django CSRF token.
 *
 * @returns {Promise<string|null>} Promise that resolves to new Django CSRF token
 */
const refreshCSRFToken = async () => {
  try {
    // Try common Django CSRF refresh endpoints
    const possibleEndpoints = [
      "/csrf-token/",
      "/get-csrf-token/",
      "/api/csrf/",
      "/", // Sometimes getting the main page refreshes the token
    ];

    for (const endpoint of possibleEndpoints) {
      try {
        console.log(`Attempting to refresh CSRF token from: ${endpoint}`);

        const response = await fetch(endpoint, {
          method: "GET",
          credentials: "include",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        if (response.ok) {
          // Check if we now have a proper Django CSRF token
          const newToken = getCookieFetchUrlPathByName("csrftoken");
          if (newToken && newToken.length === 64) {
            console.log("✓ Successfully refreshed Django CSRF token");
            return newToken;
          }
        }
      } catch (endpointError) {
        console.log(`Failed to refresh from ${endpoint}:`, endpointError.message);
      }
    }

    throw new Error("All CSRF refresh endpoints failed");
  } catch (error) {
    console.error("CSRF token refresh failed:", error);
    return null;
  }
};

/**
 * Alternative method to get Django CSRF token by making a direct request to Django.
 * Use this if the cookie token is invalid or missing.
 *
 * @returns {Promise<string|null>} Promise that resolves to Django CSRF token
 */
const getDjangoCSRFToken = async () => {
  try {
    // First, try to get token from existing sources
    const existingToken = getCSRFToken();
    if (existingToken && existingToken.length === 64) {
      return existingToken;
    }

    console.log("Existing token invalid, requesting new Django CSRF token...");

    // If no valid token, refresh it
    const newToken = await refreshCSRFToken();
    if (newToken) {
      return newToken;
    }

    // Last resort: try to extract from a form submission to your Django app
    console.error("Could not obtain valid Django CSRF token");
    return null;
  } catch (error) {
    console.error("Failed to get Django CSRF token:", error);
    return null;
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

  // Feature: Dynamic Headers (Environment-Specific + Cloudflare-friendly)
  const headers = new Headers({
    Accept: "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (compatible; API-Client)", // Helps with Cloudflare
    "Cache-Control": "no-cache",
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
