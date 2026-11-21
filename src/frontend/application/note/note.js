"use strict";

import { sendRequest } from "../utils/apis/apis.js";
import { BWRequestApi } from "../utils/apis/bw_request.js";
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
  initNoteListView();

  const filterForm = document.getElementById("notesFilterForm");
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(filterForm, "notesFilter");

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

  const createNoteForm = document.querySelector("form#createNoteForm");
  if (createNoteForm) {
    createNoteForm.addEventListener("submit", (event) => {
      try {
        event.preventDefault();
        const currentTarget = event.currentTarget;
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method"],
        });
        disableAndEnableFieldsetItems({
          formElement: createNoteForm,
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
            showToastNotification("Note created successfully", "success");
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
              showToastNotification(`Error adding note!`, "error");
            }
            console.error(error);
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: createNoteForm,
              state: "enable",
            });
          });
      } catch (error) {
        console.error(error);
        showToastNotification("Error while add new note!", "error");
      } finally {
        disableAndEnableFieldsetItems({
          formElement: createNoteForm,
          state: "enable",
        });
      }
    });
  }
});

function initNoteListView() {
  const root = document.getElementById("noteListRoot");
  if (!root) return;

  // 1. Table vs Card Grid View Switcher
  const tableBtn = document.getElementById("noteViewTableBtn");
  const gridBtn = document.getElementById("noteViewGridBtn");
  const tableContainer = document.getElementById("noteTableContainer");
  const gridContainer = document.getElementById("noteCardGridContainer");

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
      if (tableContainer) tableContainer.classList.add("hidden");
      if (gridContainer) gridContainer.classList.remove("hidden");
      if (gridBtn && tableBtn) {
        gridBtn.classList.add(...activeBtnClasses);
        gridBtn.classList.remove(...inactiveBtnClasses);
        tableBtn.classList.remove(...activeBtnClasses);
        tableBtn.classList.add(...inactiveBtnClasses);
      }
      localStorage.setItem("note_view_preference", "grid");
    } else {
      if (tableContainer) tableContainer.classList.remove("hidden");
      if (gridContainer) gridContainer.classList.add("hidden");
      if (tableBtn && gridBtn) {
        tableBtn.classList.add(...activeBtnClasses);
        tableBtn.classList.remove(...inactiveBtnClasses);
        gridBtn.classList.remove(...activeBtnClasses);
        gridBtn.classList.add(...inactiveBtnClasses);
      }
      localStorage.setItem("note_view_preference", "table");
    }
    if (window.HSStaticMethods) {
      window.HSStaticMethods.autoInit();
    }
  }

  const savedPreference = localStorage.getItem("note_view_preference") || "table";
  setViewMode(savedPreference);

  if (tableBtn) {
    tableBtn.addEventListener("click", () => setViewMode("table"));
  }
  if (gridBtn) {
    gridBtn.addEventListener("click", () => setViewMode("grid"));
  }

  // 2. Filter Accordion Toggle
  const toggleFilterBtn = document.getElementById("toggleNoteFilterBtn");
  const filterPanel = document.getElementById("noteFilterPanel");
  const filterChevron = document.getElementById("noteFilterChevronIcon");

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

  // 3. Slide-Over Quick Peek Drawer
  const quickPeekDrawer = document.getElementById("noteQuickPeekDrawer");
  const quickPeekBackdrop = document.getElementById("noteQuickPeekBackdrop");
  const quickPeekDrawerBody = document.getElementById("noteQuickPeekDrawerBody");
  const closeQuickPeekBtn = document.getElementById("closeNoteQuickPeekBtn");

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
        if (window.HSStaticMethods) {
          window.HSStaticMethods.autoInit();
        }
      })
      .catch((err) => {
        console.error("Note Quick Peek error:", err);
        quickPeekDrawerBody.innerHTML = `
          <div class="p-4 rounded-lg bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 text-xs">
            Failed to load note details. Please try again.
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
    const trigger = e.target.closest(".note-quick-peek-trigger");
    if (trigger && trigger.dataset.quickPeekUrl) {
      e.preventDefault();
      openQuickPeek(trigger.dataset.quickPeekUrl);
    }
  });

  if (closeQuickPeekBtn) {
    closeQuickPeekBtn.addEventListener("click", closeQuickPeek);
  }
  if (quickPeekBackdrop) {
    quickPeekBackdrop.addEventListener("click", closeQuickPeek);
  }
}
