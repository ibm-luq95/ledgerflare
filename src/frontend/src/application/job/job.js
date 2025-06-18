"use strict";

import { sendRequest } from "../../utils/apis/apis";
import { bwCleanApiError } from "../../utils/apis/clean_errors";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers";
import FilterPersistence from "../../utils/forms/filterform";
import { showToastNotification } from "../../utils/toasts";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const filterForm = document.getElementById("jobFilterForm");
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(filterForm, "jobFilter");

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
  const createJobModalElement = document.querySelector("div#createJobModal");
  if (createJobModalElement) {
    const createJobForm = createJobModalElement.querySelector("form#createJobForm");
    if (createJobForm) {
      createJobForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const currentTarget = event.currentTarget;
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method"],
        });
        disableAndEnableFieldsetItems({
          formElement: createJobForm,
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
        const request = sendRequest(requestOptions);
        request
          .then((data) => {
            // console.log(bwI18Helper.t("jobs"));
            // showToastNotification(bwI18Helper.t("key"), "success");
            showToastNotification("Job created successfully", "success");
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
                const errorInput = createJobForm.elements[erElement["attr"]];
                // if (errorInput) {
                //   console.log(errorInput.classList);
                //   errorInput.classList.remove("border-gray-200");
                //   errorInput.classList.add(...["border-red-500","focus:border-red-500","focus:ring-red-500"]);
                // }
              });
            } else {
              showToastNotification(`Error while add new job `, "danger");
            }
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: createJobForm,
              state: "en",
            });
          });
      });
    }
  }

  const initJobPeriodInputs = () => {
    const periodYearInput = document.querySelector("select#id_period_year");
    const periodMonthInput = document.querySelector("select#id_period_month");

    if (startDateInput.value) {
      const currentStartDate = startDateInput.value;
      const parsedDate = Date.parse(currentStartDate);
      const dateObj = new Date(parsedDate);
      const month = `${dateObj.getMonth() + 1}`;
      const year = dateObj.getFullYear().toString();
      for (let index = 0; index < periodYearInput.options.length; index++) {
        const element = periodYearInput.options[index];
        if (element.value === year) {
          periodYearInput.selectedIndex = index;
          break;
        }
      }
      for (let index = 0; index < periodMonthInput.options.length; index++) {
        const element = periodMonthInput.options[index];
        if (element.value === month) {
          periodMonthInput.selectedIndex = index;
          break;
        }
      }
    }
  };

  const startDateInput = document.querySelector("input#id_start_date");
  if (startDateInput) {
    initJobPeriodInputs();
    startDateInput.addEventListener("change", (event) => {
      initJobPeriodInputs();
    });
  }
});
