"use strict";

import { showToastNotification } from "../toasts";

/**
 * Represents a request for uploading files.
 * This class handles the creation and management of an AJAX request for file uploads.
 * It includes setting headers, handling various events like progress, error, and abort,
 * and managing the response.
 *
 * @class
 * @param {string} url - The URL endpoint to which the file will be uploaded.
 * @param {FormData} formDataObject - The FormData object containing the file and other data to be uploaded.
 * @param {string} csrfToken - A CSRF token required for validating the request on the server side.
 * @param {string} [requestMethod="POST"] - The HTTP method to be used for the request. Defaults to "POST".
 * @param {boolean} [isDebugging=false] - Flag to enable logging of debugging information.
 */
class UploadFileRequest {
  constructor(url, formDataObject, csrfToken, requestMethod, isDebugging = false) {
    this.url = url;
    this.formData = formDataObject;
    this.csrfToken = csrfToken;
    this.requestMethod = requestMethod ?? "POST";
    this.ajaxObject = new XMLHttpRequest();
    this.isDebugging = isDebugging;
  }

  /**
   * Sets the necessary HTTP headers for the AJAX request.
   * This includes the CSRF token and headers for AJAX, caching, and expected response type.
   * Throws an error if the CSRF token is not provided.
   */
  setHeaders() {
    try {
      if (this.csrfToken == "") {
        throw new Error("CSRF Token Required!");
      }
      // this.ajaxObject.setRequestHeader("Content-Type", "multipart/form-data");
      // this.ajaxObject.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
      this.ajaxObject.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      this.ajaxObject.setRequestHeader("Accept", "application/json");
      // this.ajaxObject.setRequestHeader("Cache-Control", "no-cache");
      this.ajaxObject.setRequestHeader("Cache-Control", "no-cache");
      // this.ajaxObject.setRequestHeader("Access-Control-Allow-Origin", "*");
      this.ajaxObject.setRequestHeader("X-CSRFToken", this.csrfToken);
      const authToken = window.AUTH_TOKEN;
      if (authToken) {
        this.ajaxObject.setRequestHeader("Authorization", `Token ${authToken}`);
      }
      // console.log(this.csrfToken);
      this.ajaxObject.withCredentials = true;
      // this.ajaxObject.timeout = 60;
      this.ajaxObject.responseType = "json";
    } catch (error) {
      console.error(error);
      showToastNotification(error, "danger");
    }
  }
  /**
   * Sends the AJAX request to upload the file.
   * This method sets up event listeners for progress, error, abort, and load events,
   * and sends the FormData object through the AJAX request.
   * @returns {Promise} A promise that resolves with the server's response message if the upload is successful,
   * or rejects with an error if the request fails.
   */
  sendRequest() {
    return new Promise((resolve, reject) => {
      try {
        // set upload progress handler

        if (this.isDebugging === true) {
          // this.ajaxObject.addEventListener("progress", this.uploadProgressHandler, false);
          this.ajaxObject.upload.addEventListener(
            "progress",
            this.uploadProgressHandler,
            false
          );
          // set upload error handler
        }

        // open the connection
        this.ajaxObject.open(this.requestMethod, this.url, true);

        // call setHeader method
        this.setHeaders();

        // this.ajaxObject.addEventListener("error", this.errorHandler, false);
        this.ajaxObject.addEventListener("error", this.errorHandler, false);
        // set upload abort handler
        // this.ajaxObject.addEventListener("abort", this.abortHandler, false);
        this.ajaxObject.addEventListener("abort", this.abortHandler, false);

        // set upload complete handler
        this.ajaxObject.addEventListener(
          "load",
          (event) => {
            console.warn("Load event!");
            console.log(event);
          },
          false
        );
        this.ajaxObject.send(this.formData);
        // eslint-disable-next-line no-unused-vars
        this.ajaxObject.addEventListener("readystatechange", (event) => {
          if (this.ajaxObject.readyState === 4) {
            const response = this.ajaxObject.response;
            if (this.ok() === true) {
              resolve(response["msg"]);
            } else {
              console.error(this.ajaxObject.response);
              reject(response);
            }
          }
        });
      } catch (error) {
        console.error(error);
        showToastNotification(error, "danger");
        reject(error);
      }
    });
  }
  /**
   * Checks if the HTTP response status is within the successful range (200-399).
   * @returns {boolean} True if the status is within the successful range, false otherwise.
   */
  ok() {
    // console.log(this.ajaxObject.status);
    if (this.ajaxObject.status >= 200 && this.ajaxObject.status < 400) {
      return true;
    } else {
      return false;
    }
  }
  /**
   * Handles the progress event of the upload.
   * Logs the percentage of the upload completed.
   * @param {ProgressEvent} event - The progress event object.
   */
  uploadProgressHandler(event) {
    const percent = (event.loaded / event.total) * 100;
    console.log(Math.round(percent) + "%");
  }

  /**
   * Handles errors during the upload process.
   * Logs the error and shows a toast notification.
   * @param {Event} event - The error event object.
   */
  errorHandler(event) {
    showToastNotification("Error while uploading!", "danger");
    console.error(event);
  }
  // eslint-disable-next-line no-unused-vars
  /**
   * Handles the abort event when the upload is manually aborted.
   * Aborts the AJAX request and shows a toast notification.
   * @param {Event} event - The abort event object.
   */
  abortHandler(event) {
    this.ajaxObject.abort();
    showToastNotification("Abort uploading!", "danger");
  }
}

export { UploadFileRequest };
