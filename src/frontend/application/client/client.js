"use strict";
import { bwCleanApiError } from "../utils/apis/clean_errors.js";
import { RequestHandler } from "../utils/apis/request_handler.js";
import { UploadFileRequest } from "../utils/apis/upload_file.js";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../utils/constants.js";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../utils/form_helpers.js";
import FilterPersistence from "../utils/forms/filterform";
import { showToastNotification } from "../utils/toasts.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  initClientListView();

  const filterForm = document.getElementById("clientFilterForm");
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(filterForm, "clientFilter");

    filterForm.addEventListener("filtersSaved", () => {
      console.log("Filters saved!");
    });
    if (resetFilterBtn) {
      resetFilterBtn.addEventListener("click", (event) => {
        event.preventDefault();
        filterPersistence.safeResetFilters();
        const href = resetFilterBtn.dataset["href"];
        window.location.reload();
      });
    }
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
          djangoRequest: true,
        };
        const request = RequestHandler.sendRequest(requestOptions);
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
          djangoRequest: true,
        };
        const request = RequestHandler.sendRequest(requestOptions);
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

function initClientListView() {
  const tableBtn = document.getElementById("clientViewTableBtn");
  const gridBtn = document.getElementById("clientViewGridBtn");
  const tableView = document.querySelector(".clients-table-list");
  const gridView = document.getElementById("clientGridView");
  const mobileStack = document.getElementById("clientMobileCardStack");
  const toggleFilterBtn = document.getElementById("toggleFilterAccordionBtn");
  const filterPanel = document.getElementById("clientFilterPanel");
  const filterChevron = document.getElementById("filterChevronIcon");
  const closeFilterBtn = document.getElementById("closeFilterAccordionBtn");

  const activeBtnClasses = [
    "bg-white",
    "text-gray-900",
    "shadow-2xs",
    "dark:bg-neutral-700",
    "dark:text-white",
  ];
  const inactiveBtnClasses = [
    "text-gray-500",
    "hover:text-gray-700",
    "dark:text-neutral-400",
    "dark:hover:text-neutral-200",
  ];

  function setViewMode(mode) {
    if (mode === "grid") {
      if (tableView) tableView.classList.add("hidden");
      if (mobileStack) mobileStack.classList.add("hidden");
      if (gridView) {
        gridView.classList.remove("hidden");
        gridView.classList.add("grid");
      }
      if (gridBtn && tableBtn) {
        activeBtnClasses.forEach((c) => gridBtn.classList.add(c));
        inactiveBtnClasses.forEach((c) => gridBtn.classList.remove(c));
        activeBtnClasses.forEach((c) => tableBtn.classList.remove(c));
        inactiveBtnClasses.forEach((c) => tableBtn.classList.add(c));
      }
    } else {
      if (tableView) tableView.classList.remove("hidden");
      if (mobileStack) mobileStack.classList.remove("hidden");
      if (gridView) {
        gridView.classList.add("hidden");
        gridView.classList.remove("grid");
      }
      if (gridBtn && tableBtn) {
        activeBtnClasses.forEach((c) => tableBtn.classList.add(c));
        inactiveBtnClasses.forEach((c) => tableBtn.classList.remove(c));
        activeBtnClasses.forEach((c) => gridBtn.classList.remove(c));
        inactiveBtnClasses.forEach((c) => gridBtn.classList.add(c));
      }
    }
    try {
      localStorage.setItem("clientViewMode", mode);
    } catch (e) {
      console.warn("Could not save view mode preference:", e);
    }
  }

  if (tableBtn && gridBtn) {
    let savedMode = "table";
    try {
      savedMode = localStorage.getItem("clientViewMode") || "table";
    } catch (e) {
      console.warn("Could not read view mode preference:", e);
    }
    setViewMode(savedMode);

    tableBtn.addEventListener("click", () => setViewMode("table"));
    gridBtn.addEventListener("click", () => setViewMode("grid"));
  }

  if (toggleFilterBtn && filterPanel) {
    toggleFilterBtn.addEventListener("click", () => {
      const isHidden = filterPanel.classList.contains("hidden");
      if (isHidden) {
        filterPanel.classList.remove("hidden");
        if (filterChevron) filterChevron.classList.add("rotate-180");
      } else {
        filterPanel.classList.add("hidden");
        if (filterChevron) filterChevron.classList.remove("rotate-180");
      }
    });
  }

  if (closeFilterBtn && filterPanel) {
    closeFilterBtn.addEventListener("click", () => {
      filterPanel.classList.add("hidden");
      if (filterChevron) filterChevron.classList.remove("rotate-180");
    });
  }

  // Quick Peek Slide-Over Drawer
  const quickPeekDrawer = document.getElementById("quickPeekDrawer");
  const quickPeekBackdrop = document.getElementById("quickPeekBackdrop");
  const quickPeekDrawerBody = document.getElementById("quickPeekDrawerBody");
  const closeQuickPeekBtn = document.getElementById("closeQuickPeekBtn");

  function openQuickPeek(url) {
    if (!quickPeekDrawer || !quickPeekBackdrop || !quickPeekDrawerBody) return;

    quickPeekDrawerBody.innerHTML = `
      <div class="flex items-center justify-center py-20 text-gray-400">
        <span class="animate-spin inline-block size-7 border-[3px] border-current border-t-transparent text-blue-600 rounded-full dark:text-blue-500" role="status" aria-label="loading"></span>
      </div>
    `;
    quickPeekBackdrop.classList.remove("hidden");
    quickPeekDrawer.classList.remove("translate-x-full");
    quickPeekDrawer.classList.add("translate-x-0");

    fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.text();
      })
      .then((html) => {
        quickPeekDrawerBody.innerHTML = html;
      })
      .catch((err) => {
        console.error("Quick Peek load error:", err);
        quickPeekDrawerBody.innerHTML = `
          <div class="p-4 rounded-lg bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 text-xs">
            Failed to load client details. Please try again or open the full profile.
          </div>
        `;
      });
  }

  function closeQuickPeek() {
    if (!quickPeekDrawer || !quickPeekBackdrop) return;
    quickPeekDrawer.classList.remove("translate-x-0");
    quickPeekDrawer.classList.add("translate-x-full");
    quickPeekBackdrop.classList.add("hidden");
  }

  document.addEventListener("click", (e) => {
    const peekBtn = e.target.closest(".quick-peek-btn");
    if (peekBtn && peekBtn.dataset.clientUrl) {
      e.preventDefault();
      openQuickPeek(peekBtn.dataset.clientUrl);
    }
  });

  if (closeQuickPeekBtn) {
    closeQuickPeekBtn.addEventListener("click", closeQuickPeek);
  }
  if (quickPeekBackdrop) {
    quickPeekBackdrop.addEventListener("click", closeQuickPeek);
  }
}


