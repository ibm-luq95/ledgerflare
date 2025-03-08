"use strict";
const sendRequest = async (options) => {
  try {
    if (!options.url) throw new Error("URL is required");
    if (options.token && typeof options.token !== "string") {
      throw new Error("CSRF token must be a string");
    }

    const headers = new Headers({
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": options.token,
    });

    if (!(options.dataToSend instanceof FormData)) {
      headers.set(
        "Content-Type",
        options.contentType || "application/json;charset=utf-8",
      );
    }

    const fetchOptions = {
      method: options.method || "GET",
      headers: headers,
      mode: "same-origin",
      credentials: "include",
      cache: "no-cache",
      signal: options.signal,
    };

    if (options.dataToSend) {
      fetchOptions.body =
        options.dataToSend instanceof FormData
          ? options.dataToSend
          : JSON.stringify(options.dataToSend);
    }

    const response = await fetch(options.url, fetchOptions);

    if (!response.ok) {
      // Merged error parsing logic
      let errorData;
      try {
        errorData = await response.json();
      } catch (jsonError) {
        errorData = { message: await response.text() };
      }

      throw new Error(
        errorData.message || errorData.detail || `HTTP error! status: ${response.status}`,
      );
    }

    return await response.json();
  } catch (error) {
    // Enhanced error normalization
    const errorPayload = {
      name: error.name,
      message: error.message,
      stack: error.stack?.split("\n").slice(0, 3).join("\n"), // Truncate stack
      status: error.status || error.response?.status || 500,
    };

    if (error.response) {
      try {
        errorPayload.responseData = await error.response.json();
      } catch {
        errorPayload.responseData = await error.response.text();
      }
    }

    throw errorPayload;
  }
};
onmessage = async (message) => {
  // Use async for cleaner promise handling
  try {
    const { pk, url, token, user, notificationType } = message.data; // ✅ Get token from main thread

    const requestOptions = {
      method: "POST",
      dataToSend: { pk, user, notificationType },
      url,
      token, // ✅ Token passed from main thread
    };

    const data = await sendRequest(requestOptions);
    self.postMessage({ status: "success", data }); // ✅ Send back to main thread
  } catch (error) {
    self.postMessage({
      // ✅ Structured error response
      status: "error",
      error: error.message || "Unknown error",
    });
  }
};
