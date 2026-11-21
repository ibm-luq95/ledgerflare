"use strict";

import { bwCleanApiError } from "../utils/apis/clean_errors.js";
import { RequestHandler } from "../utils/apis/request_handler.js";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../utils/constants.js";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../utils/form_helpers.js";
import FilterPersistence from "../utils/forms/filterform";
import { showToastNotification } from "../utils/toasts.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  initJobListView();

  const filterForm = document.getElementById("jobFilterForm");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(filterForm, "jobFilter");

    const clearStorageJobFilters = () => {
      try {
        filterPersistence.safeResetFilters();
        Object.keys(localStorage).forEach((key) => {
          if (key.startsWith("jobFilter")) {
            localStorage.removeItem(key);
          }
        });
      } catch (e) {
        console.warn("Could not clear filter storage:", e);
      }
    };

    const resetButtons = document.querySelectorAll(
      ".reset-filters-btn, #resetFilterBtn, button#resetFilterBtn, a.reset-filters-btn"
    );
    resetButtons.forEach((btn) => {
      btn.addEventListener("click", (event) => {
        event.preventDefault();
        clearStorageJobFilters();
        const targetUrl =
          btn.getAttribute("href") ||
          btn.dataset["href"] ||
          window.location.pathname;
        window.location.href = targetUrl;
      });
    });

    filterForm.addEventListener("reset", () => {
      clearStorageJobFilters();
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
        const request = RequestHandler.sendRequest(requestOptions);
        request
          .then((data) => {
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
                  "danger"
                );
              });
            } else {
              showToastNotification(`Error while add new job `, "danger");
            }
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: createJobForm,
              state: "enable",
            });
          });
      });
    }
  }

  const initJobPeriodInputs = () => {
    const periodYearInput = document.querySelector("select#id_period_year");
    const periodMonthInput = document.querySelector("select#id_period_month");

    if (startDateInput && startDateInput.value && periodYearInput && periodMonthInput) {
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

function initJobListView() {
  const tableBtn = document.getElementById("jobViewTableBtn");
  const gridBtn = document.getElementById("jobViewGridBtn");
  const tableView = document.querySelector(".job-table-list");
  const gridView = document.getElementById("jobGridView");
  const toggleFilterBtn = document.getElementById("toggleFilterAccordionBtn");
  const filterPanel = document.getElementById("jobFilterPanel");
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
      localStorage.setItem("jobViewMode", mode);
    } catch (e) {
      console.warn("Could not save view mode preference:", e);
    }
  }

  if (tableBtn && gridBtn) {
    let savedMode = "table";
    try {
      savedMode = localStorage.getItem("jobViewMode") || "table";
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
            Failed to load job details. Please try again or open the full details.
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
    if (peekBtn && peekBtn.dataset.jobUrl) {
      e.preventDefault();
      openQuickPeek(peekBtn.dataset.jobUrl);
    }
  });

  if (closeQuickPeekBtn) {
    closeQuickPeekBtn.addEventListener("click", closeQuickPeek);
  }
  if (quickPeekBackdrop) {
    quickPeekBackdrop.addEventListener("click", closeQuickPeek);
  }
}
