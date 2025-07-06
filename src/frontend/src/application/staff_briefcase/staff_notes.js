"use strict";

import { sendRequest } from "../../utils/apis/apis";
import { bwCleanApiError } from "../../utils/apis/clean_errors";
import { RequestHandler } from "../../utils/apis/request_handler";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers";
import { showToastNotification } from "../../utils/toasts";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const createBriefcaseNoteForm = document.querySelector("form#createBriefcaseNoteForm");
  if (createBriefcaseNoteForm) {
    createBriefcaseNoteForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      const formInputs = formInputSerializer({
        formElement: currentTarget,
        excludedFields: ["_method"],
      });
      disableAndEnableFieldsetItems({
        formElement: createBriefcaseNoteForm,
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
          showToastNotification("staff note created successfully", "success");
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
                "error",
              );
            });
          } else {
            showToastNotification(`Error adding staff note!`, "error");
          }
          console.error(error);
        })
        .finally(() => {
          disableAndEnableFieldsetItems({
            formElement: createBriefcaseNoteForm,
            state: "enable",
          });
        });
    });
  }
});
