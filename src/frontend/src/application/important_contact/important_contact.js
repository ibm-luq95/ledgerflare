"use strict";

import { bwCleanApiError } from "../../utils/apis/clean_errors.js";
import { RequestHandler } from "../../utils/apis/request_handler.js";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants.js";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers.js";
import FilterPersistence from "../../utils/forms/filterform.js";
import { showToastNotification } from "../../utils/toasts.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const filterForm = document.getElementById("importantContactFilterForm");
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(
      filterForm,
      "importantContactsFilter",
    );

    filterForm.addEventListener("filtersSaved", () => {
      console.log("Filters saved!");
    });
    resetFilterBtn.addEventListener("click", (event) => {
      event.preventDefault();
      filterPersistence.safeResetFilters();
      const href = resetFilterBtn.dataset["href"];
      window.location.reload();
    });
    filterForm.addEventListener("filtersReset", () => {
      console.log("Filters reset!");
    });
  }
  const createImportantContactModalElement = document.querySelector(
    "div#createImportantContactModal",
  );
  if (createImportantContactModalElement) {
    const createImportantContactForm = createImportantContactModalElement.querySelector(
      "form#createImportantContactForm",
    );
    if (createImportantContactForm) {
      createImportantContactForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const currentTarget = event.currentTarget;
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method"],
        });
        disableAndEnableFieldsetItems({
          formElement: createImportantContactForm,
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
        const request = RequestHandler.sendRequest(requestOptions);
        request
          .then((data) => {
            // console.log(bwI18Helper.t("jobs"));
            // showToastNotification(bwI18Helper.t("key"), "success");
            showToastNotification("Contact created successfully", "success");
            setTimeout(() => {
              window.location.reload();
            }, SUCCESSTIMEOUTSECS);
          })
          .catch((error) => {
            const er = bwCleanApiError(error);
            if (er) {
              er.forEach((erElement) => {
                console.warn(erElement);
                showToastNotification(
                  `Error: ${erElement["detail"]} - ${erElement["attr"]}`,
                  "danger",
                );
              });
            } else {
              showToastNotification("Error while add new contact!", "danger");
            }
            console.error(error);
            disableAndEnableFieldsetItems({
              formElement: createImportantContactForm,
              state: "enable",
            });
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: createImportantContactForm,
              state: "enable",
            });
          });
      });
    }
  }
});
