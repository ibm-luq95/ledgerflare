"use strict";
/* 
This file will handle all tasks related api requests
*/
import { sendRequest } from "../../utils/apis/apis";
import { bwCleanApiError } from "../../utils/apis/clean_errors";
import { RequestHandler } from "../../utils/apis/request_handler";
import { CSRFINPUTNAME } from "../../utils/constants";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers";
import FilterPersistence from "../../utils/forms/filterform";
import { showToastNotification } from "../../utils/toasts";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const filterForm = document.getElementById("tasksFilterForm");
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(filterForm, "tasksFilter");

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
  const createTaskModalForm = document.querySelector("form#createTaskForm"); // Grab the task form element
  // Check if the form element exists in the page
  if (createTaskModalForm) {
    const fieldset = createTaskModalForm.querySelector("fieldset");
    createTaskModalForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      const formInputs = formInputSerializer({
        formElement: currentTarget,
        excludedFields: ["_method"],
      });
      disableAndEnableFieldsetItems({
        formElement: createTaskModalForm,
        state: "disable",
      });
      const requestOptions = {
        method: currentTarget["_method"]
          ? currentTarget["_method"].value.toUpperCase()
          : "POST",
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
          showToastNotification("Task created successfully", "success");
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        })
        .catch((error) => {
          const er = bwCleanApiError(error);
          if (er) {
            er.forEach((erElement) => {
              showToastNotification(
                `Error: ${erElement["detail"]} - ${erElement["attr"]}`,
                "danger",
              );
            });
          } else {
            showToastNotification(`Error adding task!`, "danger");
          }
          console.error(error);
        })
        .finally(() => {
          disableAndEnableFieldsetItems({
            formElement: createTaskModalForm,
            state: "enable",
          });
        });
    });
  }
});
