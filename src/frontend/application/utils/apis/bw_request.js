"use strict";

import { CSRFINPUTNAME } from "../constants.js";
import { getCookie } from "../cookie.js";
import { disableAndEnableFieldsetItems, formInputSerializer } from "../form_helpers.js";
import { capitalizeFirstLetter } from "../helpers.js";

class BWRequestApi {
  #requestOptions = {
    method: "",
    dataToSend: null,
    url: "",
    token: null,
  };
  constructor({
    formHTMLElement,
    url = null,
    token = null,
    method = "POST",
    excludedFields = [],
    formElementsAsFormData = false,
    isUploadRequest = false,
    appLabel = "",
    operationName = null,
  }) {
    this.formElementObject = formHTMLElement;
    this.url = url;
    this.token = token;
    this.method = method;
    this.excludedFields = excludedFields;
    this.formInputs = null;
    this.isUploadRequest = isUploadRequest;
    this.formElementsAsFormData = formElementsAsFormData;
    this.appLabel = capitalizeFirstLetter(appLabel);
    this.operationName = operationName;
    const successMsg = `${this.appLabel} ${this.operationName} successfully!`;
    const failedMsg = `The operation ${this.operationName} failed`;
    this.successMsg = successMsg;
    this.failedMsg = failedMsg;
    this.initFormUrl();
    this.initFormToken();
    this.initFormMethod();
    this.initFormInputs();
    this.initRequestOptions();
  }

  get getRequestOptions() {
    return this.#requestOptions;
  }

  initFormInputs() {
    this.formInputs = formInputSerializer({
      formElement: this.formElementObject,
      excludedFields: ["_method"],
    });
    console.log(`initFormInputs-> ${this.formInputs}`);
  }

  initFormUrl() {
    if (this.url) {
      this.url = this.url;
    } else {
      if (this.formElementObject) {
        if (this.formElementObject.action) {
          this.url = this.formElementObject.action;
        } else {
          throw new Error("No action passed!");
        }
      } else {
        throw new Error("No form passed!");
      }
    }
    console.warn(`initFormUrl-> ${this.url}`);
  }
  initFormToken() {
    if (this.token) {
      this.token = this.token;
    } else {
      if (this.formElementObject) {
        if (this.formElementObject[CSRFINPUTNAME]) {
          this.token = this.formElementObject[CSRFINPUTNAME].value;
        } else {
          this.token = getCookie("csrftoken");
        }
      } else {
        throw new Error("No form passed!");
      }
    }
    console.warn(`initFormToken-> ${this.token}`);
  }
  initFormMethod() {
    if (this.method) {
      this.method = this.method;
    } else {
      if (this.formElementObject) {
        if (this.formElementObject["_method"]) {
          this.method = this.formElementObject["_method"].value;
        } else {
          throw new Error("No method passed!");
        }
      } else {
        throw new Error("No form passed!");
      }
    }
    console.warn(`initFormMethod-> ${this.method}`);
  }
  initRequestOptions() {
    this.#requestOptions["method"] = this.method;
    this.#requestOptions["token"] = this.token;
    this.#requestOptions["url"] = this.url;
    this.#requestOptions["dataToSend"] = this.formInputs;
    console.log(`initRequestOptions-> ${this.getRequestOptions}`);
  }

  #sendRequest() {
    const requestPromise = new Promise((resolve, reject) => {
      try {
        const url = this.#requestOptions["url"];
        const controller = new AbortController(); // the AbortController
        const { signal } = controller;
        const headers = new Headers({
          "Content-Type": "application/json;charset=utf-8",
          // "Content-Type": `Content-Type: application/pdf`,
          // "Content-Type": "application/x-www-form-urlencoded",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": this.#requestOptions["token"],
        });
        // const formData = Object.fromEntries(options["dataToSend"].entries());
        const fetchOptions = {
          method: this.#requestOptions["method"],
          mode: "same-origin",
          credentials: "include",
          cache: "no-cache",
          body: JSON.stringify(this.#requestOptions["dataToSend"]),
          // body: formData,
        };
        const request = new Request(url, {
          headers: headers,
          signal: signal,
        });
        const fetchObj = fetch(request, fetchOptions);
        fetchObj
          .then((response) => {
            if (!response.ok) {
              return response.text().then((text) => {
                reject(JSON.parse(text));
              });
            }
            resolve(response.json());
          })
          .catch((error) => {
            reject(error);
          });
      } catch (error) {
        reject(error);
      } finally {
        // here 
      }
    });
    return requestPromise;
  }

  #updateFormState(state) {
    disableAndEnableFieldsetItems({
      formElement: this.formElementObject,
      state: state,
    });
  }

  #beforeSend() {}
  #afterSend() {}
}

export { BWRequestApi };
