"use strict";

import { bwCleanApiError } from "../../utils/apis/clean_errors.js";
import { UploadFileRequest } from "../../utils/apis/upload_file.js";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants.js";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers.js";
import { showToastNotification } from "../../utils/toasts.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const createBriefcaseDocumentForm = document.querySelector(
    "form#createBriefcaseDocumentForm"
  );
  if (createBriefcaseDocumentForm) {
    createBriefcaseDocumentForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      const formInputs = formInputSerializer({
        formElement: currentTarget,
        excludedFields: ["_method", "document_file"],
        returnAsFormData: true,
        filesArray: ["document_file"],
      });
      // console.log(formInputs);
      // throw new Error("D");
      disableAndEnableFieldsetItems({
        formElement: createBriefcaseDocumentForm,
        state: "disable",
      });
      const uploadRequest = new UploadFileRequest(
        currentTarget.action,
        formInputs,
        currentTarget.elements[CSRFINPUTNAME].value,
        currentTarget.method,
        false
      );
      const request = uploadRequest.sendRequest();
      request
        .then((data) => {
          // console.log(data);
          showToastNotification("Staff document created successfully!", "success");
          setTimeout(() => {
            window.location.reload();
          }, SUCCESSTIMEOUTSECS);
        })
        .catch((error) => {
          console.error(error);
          const er = bwCleanApiError(error);
          if (er) {
            er.forEach((erElement) => {
              showToastNotification(
                `Error: ${erElement["detail"]} - ${erElement["attr"]}`,
                "danger"
              );
            });
          } else {
            showToastNotification("Error adding new staff document!", "error");
          }
        })
        .finally(() => {
          disableAndEnableFieldsetItems({
            formElement: createBriefcaseDocumentForm,
            state: "enable",
          });
        });
    });
  }
});
