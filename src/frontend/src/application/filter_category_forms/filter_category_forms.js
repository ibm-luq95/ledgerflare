"use strict";

import { bwCleanApiError } from "../../utils/apis/clean_errors.js";
import { RequestHandler } from "../../utils/apis/request_handler.js";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants.js";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers.js";
import { showToastNotification } from "../../utils/toasts.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const filterCategoryForms = document.querySelectorAll(
    "form.filterCategoryForms",
  );
  if (filterCategoryForms.length > 0) {
    filterCategoryForms.forEach((form) => {
      form.addEventListener("submit", (submitEvent) => {
        submitEvent.preventDefault();
        const currentTarget = submitEvent.currentTarget;
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method"],
        });
        disableAndEnableFieldsetItems({
          formElement: form,
          state: "disable",
        });
        const requestOptions = {
          method: currentTarget["_method"]
            ? currentTarget["_method"].value.toUpperCase()
            : currentTarget.method,
          dataToSend: formInputs,
          url: currentTarget.action,
          token: currentTarget[CSRFINPUTNAME].value,
          djangoRequest: true,
        };
        // console.log(requestOptions);
        const request = RequestHandler.sendRequest(requestOptions);
        request
          .then((data) => {
            // console.log(bwI18Helper.t("jobs"));
            // showToastNotification(bwI18Helper.t("key"), "success");
            showToastNotification("Category created successfully", "success");
            setTimeout(() => {
              window.location.reload();
            }, SUCCESSTIMEOUTSECS);
          })
          .catch((error) => {
            const er = bwCleanApiError(error);
            // console.warn(er);
            // console.warn(error);

            if (er) {
              er.forEach((erElement) => {
                showToastNotification(
                  `Error: ${erElement["detail"]} - ${erElement["attr"]}`,
                  "error",
                );
              });
            } else {
              showToastNotification(`Error adding category!`, "error");
            }
            console.error(error);
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: form,
              state: "enable",
            });
          });
      });
    });
  }
});
