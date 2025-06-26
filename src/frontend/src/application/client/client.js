"use strict";
import { sendRequest } from "../../utils/apis/apis";
import { bwCleanApiError } from "../../utils/apis/clean_errors";
import { UploadFileRequest } from "../../utils/apis/upload_file";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers";
import FilterPersistence from "../../utils/forms/filterform";
import { showToastNotification } from "../../utils/toasts";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const filterForm = document.getElementById("clientFilterForm");
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(filterForm, "clientFilter");

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
  const updateClientForm = document.querySelector("form#updateClientForm");
  if (updateClientForm) {
    updateClientForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const currentTarget = event.currentTarget;
      const fieldset = currentTarget.querySelector("fieldset");
      const formInputs = formInputSerializer({
        formElement: currentTarget,
        excludedFields: ["_method", "company_logo"],
        returnAsFormData: true,
        filesArray: ["company_logo"],
      });
      disableAndEnableFieldsetItems({
        formElement: updateClientForm,
        state: "disable",
      });
      const uploadRequest = new UploadFileRequest(
        currentTarget.action,
        formInputs,
        currentTarget.elements[CSRFINPUTNAME].value,
        currentTarget["_method"].value.toUpperCase(),
        false
      );
      const request = uploadRequest.sendRequest();
      request
        .then((data) => {
          console.log(data);
          showToastNotification(`Client updated successfully!`, "success");
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
            showToastNotification("Error update client!", "error");
          }
        })
        .finally(() => {
          disableAndEnableFieldsetItems({
            formElement: updateClientForm,
            state: "enable",
          });
        });
    });
  }

  const addBookkeeperModal = document.querySelector("#addBookkeeperModal");
  const assignCfoClientForm = document.querySelector("form#assignCfoClientForm");
  if (addBookkeeperModal) {
    const assignBookkeeperClientForm = addBookkeeperModal.querySelector(
      "form#assignBookkeeperClientForm"
    );
    if (assignBookkeeperClientForm) {
      assignBookkeeperClientForm.addEventListener("submit", (event) => {
        event.preventDefault();
        let cnfm = null;
        const currentTarget = event.currentTarget;
        const checked = assignBookkeeperClientForm.querySelectorAll(
          'input[type="checkbox"]:checked'
        );
        // console.warn(assignBookkeeperClientForm.action);
        // console.warn(assignBookkeeperClientForm.method);
        const bookkeepers = Array.from(checked).map((x) => x.value);
        if (bookkeepers.length === 0) {
          cnfm = confirm(
            "No bookkeeper selected, this will un-assign all bookkeepers for this client are you sure?"
          );
        }
        if (cnfm !== null) {
          // this mean the confirm dialog called
          // check if user click on cancel
          if (cnfm === false) {
            return;
          }
        }

        disableAndEnableFieldsetItems({
          formElement: currentTarget,
          state: "disable",
        });
        const requestOptions = {
          method: currentTarget["_method"]
            ? currentTarget["_method"].value.toUpperCase()
            : currentTarget.method,
          dataToSend: {
            bookkeepers: bookkeepers,
            client: assignBookkeeperClientForm.client.value,
          },
          url: currentTarget.action,
          token: currentTarget[CSRFINPUTNAME].value,
        };
        const request = sendRequest(requestOptions);
        request
          .then((data) => {
            showToastNotification(data["success_msg"], "success");
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
                  "danger"
                );
              });
            } else {
              // eslint-disable-next-line no-prototype-builtins
              if (error.hasOwnProperty("error")) {
                showToastNotification(`Error: ${error["error"]}`, "danger");
              } else {
                showToastNotification(`Error assign bookkeepers!`, "danger");
              }
            }
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: currentTarget,
              state: "enable",
            });
          });

        // alert("Add bookkeeper to client");
      });
    }

    if (assignCfoClientForm) {
      assignCfoClientForm.addEventListener("submit", (event) => {
        event.preventDefault();
        let cnfm = null;
        const currentTarget = event.currentTarget;
        const checked = assignCfoClientForm.querySelectorAll(
          'input[type="checkbox"]:checked'
        );
        // console.warn(assignBookkeeperClientForm.action);
        // console.warn(assignBookkeeperClientForm.method);
        const cfos = Array.from(checked).map((x) => x.value);
        if (cfos.length === 0) {
          cnfm = confirm(
            "No cfos selected, this will un-assign all cfoss for this client are you sure?"
          );
        }
        if (cnfm !== null) {
          // this mean the confirm dialog called
          // check if user click on cancel
          if (cnfm === false) {
            return;
          }
        }

        disableAndEnableFieldsetItems({
          formElement: currentTarget,
          state: "disable",
        });
        const requestOptions = {
          method: currentTarget["_method"]
            ? currentTarget["_method"].value.toUpperCase()
            : currentTarget.method,
          dataToSend: {
            cfos: cfos,
            client: assignCfoClientForm.client.value,
          },
          url: currentTarget.action,
          token: currentTarget[CSRFINPUTNAME].value,
        };
        const request = sendRequest(requestOptions);
        request
          .then((data) => {
            showToastNotification(data["success_msg"], "success");
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
                  "danger"
                );
              });
            } else {
              // eslint-disable-next-line no-prototype-builtins
              if (error.hasOwnProperty("error")) {
                showToastNotification(`Error: ${error["error"]}`, "danger");
              } else {
                showToastNotification(`Error assign bookkeepers!`, "danger");
              }
            }
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: currentTarget,
              state: "enable",
            });
          });

        // alert("Add bookkeeper to client");
      });
    }
  }
});
