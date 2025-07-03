"use strict";

import { fetchUrlPathByName, sendRequest } from "../../utils/apis/apis";
import { bwCleanApiError } from "../../utils/apis/clean_errors";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers";
import { showToastNotification } from "../../utils/toasts";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const assignedClientsForm = document.querySelector("form#assignedClientsForm");
  const permissionsUpdateMiniForm = document.querySelector(
    "form#permissionsUpdateMiniForm",
  );
  if (assignedClientsForm) {
    assignedClientsForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      try {
        const assignedClientsInputs = document.querySelectorAll(
          "input[name='assignedClients']:checked",
        );
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method"],
        });
        const requestOptions = {
          method: currentTarget.method,
          dataToSend: formInputs,
          djangoRequest: true,
          url: currentTarget.action,
          token: currentTarget[CSRFINPUTNAME].value,
        };
        const request = sendRequest(requestOptions);
        request
          .then((data) => {
            // console.log(bwI18Helper.t("jobs"));
            // showToastNotification(bwI18Helper.t("key"), "success");
            showToastNotification("Clients assigned successfully", "success");
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
              showToastNotification(`Error while assign client to bookkeeper`, "danger");
            }
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: assignedClientsForm,
              state: "enable",
            });
          });
      } catch (error) {
        console.error(error);
        showToastNotification("Error while assign client to bookkeeper!");
      } finally {
        disableAndEnableFieldsetItems({
          formElement: assignedClientsForm,
          state: "enable",
        });
      }
    });
  }

  if (permissionsUpdateMiniForm) {
    permissionsUpdateMiniForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      const formInputs = formInputSerializer({
        formElement: currentTarget,
        excludedFields: ["_method"],
      });
      console.log(formInputs);
      disableAndEnableFieldsetItems({
        formElement: permissionsUpdateMiniForm,
        state: "disable",
      });
      const urlName = fetchUrlPathByName("dashboard:staff:update-permissions");
      urlName
        .then((urlData) => {
          const requestOptions = {
            method: currentTarget["_method"]
              ? currentTarget["_method"].value.toUpperCase()
              : currentTarget.method,
            dataToSend: formInputs,
            url: urlData["urlPath"],
            djangoRequest: true,
            token: currentTarget[CSRFINPUTNAME].value,
          };
          const request = sendRequest(requestOptions);
          request
            .then((data) => {
              showToastNotification("Permissions update successfully", "success");
              setTimeout(() => {
                window.location.reload();
              }, SUCCESSTIMEOUTSECS);
            })
            .catch((requestError) => {
              console.error(requestError);
              disableAndEnableFieldsetItems({
                formElement: permissionsUpdateMiniForm,
                state: "enable",
              });
            });
        })
        .catch((error) => {
          console.error(error);
          disableAndEnableFieldsetItems({
            formElement: permissionsUpdateMiniForm,
            state: "enable",
          });
        });
    });
  }

  // const el = window.HSTabs.getInstance("#details-tab");

  // el.on("change", ({ el, prev, current }) => {
  //   console.log(el);
  // });
});
