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
  const createBriefcaseAccountForm = document.querySelector(
    "form#createBriefcaseAccountForm",
  );
  if (createBriefcaseAccountForm) {
    createBriefcaseAccountForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      const formInputs = formInputSerializer({
        formElement: currentTarget,
        excludedFields: ["_method"],
      });
      disableAndEnableFieldsetItems({
        formElement: createBriefcaseAccountForm,
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
      console.log(formInputs);
      const request = RequestHandler.sendRequest(requestOptions);
      request
        .then((data) => {
          // console.log(bwI18Helper.t("jobs"));
          // showToastNotification(bwI18Helper.t("key"), "success");
          showToastNotification("Staff account created successfully", "success");
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
            showToastNotification(`Error adding staff account!`, "danger");
          }
          console.error(error);
        })
        .finally(() => {
          disableAndEnableFieldsetItems({
            formElement: createBriefcaseAccountForm,
            state: "enable",
          });
        });
    });
  }
});
