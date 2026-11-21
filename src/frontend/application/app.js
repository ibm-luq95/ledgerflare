import "./app.css";

import htmx from "htmx.org";
import Alpine from "alpinejs";

import "preline";
import "choices.js/public/assets/styles/choices.css";
import Choices from "choices.js";
import "animate.css";
import tableSort from "table-sort-js/table-sort.js";
import "./dashboard/dashboard.js";
import "./dashboard/manager_dashboard.js";
import "./job/details.js";
import "./special_assignment/details.js";
import "./special_assignment/special_assignment.js";
import "./task/task.js";
import "./document/document.js";
import "./note/note.js";
import "./discussion/discussion.js";
import "./job/job.js";
import "./job/workstation.js";
import "./important_contact/important_contact.js";
import "./client/client.js";
import "./client_account/client_account.js";
import "./client_account/credentials_inputs.js";
import "./beach_wood_user/details.js";
import "./staff_briefcase/staff_notes.js";
import "./staff_briefcase/staff_documents.js";
import "./staff_briefcase/staff_accounts.js";
import "./filter_category_forms/filter_category_forms.js";
import "./reports/new_report.js";
import "./reports/jobs_report.js";
import "./beach_wood_user/assistant.js";
import "./beach_wood_user/bookkeeper.js";
import "./beach_wood_user/manager.js";
import "./beach_wood_user/cfo.js";
import "./beach_wood_user/auth.js";
import "./dashboard/notifications.js";
import "./dashboard/notification_list.js";
import "./dashboard/manager_dashboard.js";
import "./management/delete_staff.js";
import "./utils/rich_editor.js";
import { initJournalEntryModule } from "./client/journal_entry.js";
// import "../styles/datatable.css";
import { setFormInputsReadOnly } from "./utils/form_helpers.js";
// import { HSTabs } from "../../node_modules/preline/dist/preline.js";
import "./utils/ldgf_pop_modal.js";
import HSTabs from "@preline/tabs/non-auto.mjs";

import { createApp } from "vue";
import Chatbox from "../components/discussion/Chatbox.vue";

window.htmx = htmx;
window.Alpine = Alpine;
Alpine.start();
window.document.addEventListener("DOMContentLoaded", function () {
  // Init Vue Chatbox components
  const vueChatboxContainers = document.querySelectorAll("[data-vue-chatbox]");
  vueChatboxContainers.forEach((el) => {
    const props = {
      objectId: el.dataset.objectId,
      objectType: el.dataset.objectType || "special_assignment",
      currentUserId: el.dataset.currentUserId,
      currentUserName: el.dataset.currentUserName,
      currentUserAvatar: el.dataset.currentUserAvatar,
      apiEndpoint: el.dataset.apiEndpoint || "/dashboard/discussions/api/discussion-api-router/",
      csrfToken: el.dataset.csrfToken,
    };
    createApp(Chatbox, props).mount(el);
  });

  // Init preline
  if (window.HSStaticMethods) {
    window.HSStaticMethods.autoInit();
  }
  // Init preline
  // readonly
  const bwfInputs = document.querySelectorAll(".bw-input");
  const bwDisabledLinks = document.querySelectorAll("a.bw-disabled-anchor");
  const allDisabledCssClassed = ["disabled:opacity-75", "cursor-not-allowed"];
  const readonlySelectElements = document.querySelectorAll(".readonly-select");
  if (readonlySelectElements.length > 0) {
    readonlySelectElements.forEach((element) => {
      element.addEventListener("change", (event) => {
        return false;
      });
    });
  }
  // TODO: temporary set it to readonly
  setFormInputsReadOnly("staffUpdateMiniForm");
  bwfInputs.forEach((input) => {
    const dataAttrs = input.dataset;
    const checkKeepDisabled = Object.prototype.hasOwnProperty.call(
      dataAttrs,
      "keepDisabled",
    );
    if (checkKeepDisabled === true) {
      const keepDisabled = dataAttrs["keepDisabled"];
      const keepDisabledValue = /true/.test(keepDisabled);
      if (keepDisabledValue === true) {
        input.disabled = true;
      }
    } else {
      input.disabled = false;
      input.classList.remove(...allDisabledCssClassed);
    }
  });
  bwDisabledLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
    });
  });
  // readonly

  // Back filter button
  const formBackBtn = document.querySelector("button#formBackBtn");
  if (formBackBtn) {
    formBackBtn.addEventListener("click", (event) => {
      window.history.back();
    });
  }
  // Back filter button

  // staff tab
  const staffDetailsPermissionsTabsElement = document.querySelector(
    "#staffDetailsPermissionsTabs",
  );
  if (staffDetailsPermissionsTabsElement) {
    const staffDetailsPermissionsTabs = HSTabs(
      staffDetailsPermissionsTabsElement,
    );
    if (staffDetailsPermissionsTabs) {
      staffDetailsPermissionsTabs.on(
        "change",
        ({ staffDetailsPermissionsTabs, prev, current }) => {
          const btn = document.querySelector(
            "button#updatePermissionsStaffDetailsBtn",
          );
          if (current === "#permissions-tab") {
            btn.classList.remove("hidden");
          } else {
            btn.classList.add("hidden");
          }
        },
      );
    }
  }
  // staff tab

  // reset filter button
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");
  if (resetFilterBtn) {
    resetFilterBtn.addEventListener("click", (event) => {
      event.preventDefault();
      const formId = event.currentTarget.dataset["form"];
      const url = event.currentTarget.dataset["href"];
      if (formId !== null || formId !== "None") {
        const filterForm = document.querySelector(`form#${formId}`);

        if (filterForm) {
          filterForm.reset();
          window.location.href = url;
        }
      }
    });
  }
  // reset filter button

  // Dark theme
  // This code should be added to <head>.
  // It's used to prevent page load glitches.
  const html = document.querySelector("html");
  const isLightOrAuto =
    localStorage.getItem("hs_theme") === "light" ||
    (localStorage.getItem("hs_theme") === "auto" &&
      !window.matchMedia("(prefers-color-scheme: dark)").matches);
  const isDarkOrAuto =
    localStorage.getItem("hs_theme") === "dark" ||
    (localStorage.getItem("hs_theme") === "auto" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  if (isLightOrAuto && html.classList.contains("dark"))
    html.classList.remove("dark");
  else if (isDarkOrAuto && html.classList.contains("light"))
    html.classList.remove("light");
  else if (isDarkOrAuto && !html.classList.contains("dark"))
    html.classList.add("dark");
  else if (isLightOrAuto && !html.classList.contains("light"))
    html.classList.add("light");

  const jsChoicesSelect = document.querySelectorAll(".js-choice-select");
  if (jsChoicesSelect.length > 0) {
    jsChoicesSelect.forEach((jsElement) => {
      const choices = new Choices(jsElement);
    });
  }
  // Dark theme
});
