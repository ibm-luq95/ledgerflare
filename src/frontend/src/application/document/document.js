"use strict";

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
  const createDocumentModal = document.querySelector("#createDocumentModal");
  const createDocumentForm = document.querySelector("form#createDocumentForm");

  if (createDocumentForm) {
    createDocumentForm.addEventListener("submit", (event) => {
      try {
        event.preventDefault();
        const currentTarget = event.currentTarget;
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method", "document_file"],
          returnAsFormData: true,
          filesArray: ["document_file"],
        });
        disableAndEnableFieldsetItems({
          formElement: createDocumentForm,
          state: "disable",
        });

        const uploadRequest = new UploadFileRequest(
          currentTarget.action,
          formInputs,
          currentTarget.elements[CSRFINPUTNAME].value,
          currentTarget.method,
          false,
        );
        const request = uploadRequest.sendRequest();
        request
          .then((data) => {
            // console.log(data);
            showToastNotification("Document created successfully!", "success");
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
                  "danger",
                );
              });
            } else {
              showToastNotification("Error adding new document!", "error");
            }
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: createDocumentForm,
              state: "enable",
            });
          });
      } catch (error) {
        console.error(error);
        showToastNotification("Error while add new document!");
      } finally {
        disableAndEnableFieldsetItems({
          formElement: createDocumentForm,
          state: "enable",
        });
      }
    });
  }
});
