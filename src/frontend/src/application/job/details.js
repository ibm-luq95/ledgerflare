"use strict";

import { sendRequest } from "../../utils/apis/apis";
import { bwCleanApiError } from "../../utils/apis/clean_errors";
import { RequestHandler } from "../../utils/apis/request_handler";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers";
// import { bwI18Helper } from "../../utils/i18_helper";
import { showToastNotification } from "../../utils/toasts";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const updateJobStatusStateForm = document.querySelector(
    "form#updateJobStatusStateForm",
  );
  const addDiscussionFormInJob = document.querySelector("form#addDiscussionFormInJob");
  const updateJobForm = document.querySelector("form#updateJobForm");
  if (updateJobStatusStateForm) {
    updateJobStatusStateForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      const formInputs = formInputSerializer({
        formElement: currentTarget,
        excludedFields: ["_method"],
      });
      disableAndEnableFieldsetItems({
        formElement: updateJobStatusStateForm,
        state: "disable",
      });
      const requestOptions = {
        method: currentTarget["_method"].value.toUpperCase(),
        dataToSend: formInputs,
        url: currentTarget.action,
        token: currentTarget[CSRFINPUTNAME].value,
        djangoRequest: true,
      };
      try {
        const request = RequestHandler.sendRequest(requestOptions);
        request
          .then((data) => {
            showToastNotification("Job status/state updated successfully", "success");
            setTimeout(() => {
              window.location.reload();
            }, SUCCESSTIMEOUTSECS);
          })
          .catch((error) => {
            console.error(error);
            throw new Error(error.message);
          });
      } catch (error) {
        showToastNotification("Error while update job!", "danger");
      } finally {
        disableAndEnableFieldsetItems({
          formElement: updateJobStatusStateForm,
          state: "enable",
        });
      }

      // console.log(jobStatusInput.value);
    });

    if (addDiscussionFormInJob) {
      addDiscussionFormInJob.addEventListener("submit", (event) => {
        event.preventDefault();
        console.log("Add reply");
      });
    }

    if (updateJobForm) {
      updateJobForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const currentTarget = event.currentTarget;
        const fieldset = currentTarget.querySelector("fieldset");
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method"],
        });
        disableAndEnableFieldsetItems({ formElement: updateJobForm, state: "disable" });
        const requestOptions = {
          method: currentTarget["_method"]
            ? currentTarget["_method"].value.toUpperCase()
            : "POST",
          dataToSend: formInputs,
          url: currentTarget.action,
          djangoRequest: true,
          token: currentTarget[CSRFINPUTNAME].value,
        };
        if (formInputs["is_scheduled"]) {
          // console.log("Scheduled");
          formInputs["is_scheduled"] = true;
        } else {
          formInputs["is_scheduled"] = false;
        }
        // console.log(formInputs)
        // throw new Error("Error while updating job!");
        const request = RequestHandler.sendRequest(requestOptions);
        request
          .then((data) => {
            // console.log(bwI18Helper.t("jobs"));
            // showToastNotification(bwI18Helper.t("key"), "success");
            showToastNotification("Job updated successfully", "success");
            setTimeout(() => {
              window.location.reload();
            }, SUCCESSTIMEOUTSECS);
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
              showToastNotification(`Error while update job!`, "danger");
            }
            console.error(error);
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: updateJobForm,
              state: "enable",
            });
          });
      });
    }
  }
});
