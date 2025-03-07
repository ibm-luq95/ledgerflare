// This is the scss entry file
import $ from "jquery";
window.jQuery = $;
window.$ = $;
import _ from "lodash";
import Dropzone from "dropzone";
import "../styles/index.scss";
import "../styles/dashboard.scss";
import "simplelightbox/dist/simple-lightbox.css";
import SimpleLightbox from "simplelightbox";
// import "preline";
import "../../node_modules/preline/dist/preline.js";
// import "../styles/tinymce.scss";
// import * as editor from "../utils/rich_editor.js";
import "../utils/rich_editor.js";
import "animate.css";
import "@fortawesome/fontawesome-free/js/all.js";
import "@fortawesome/fontawesome-free/css/all.min.css";
import hljs from "highlight.js";
import "highlight.js/styles/default.css";
import NiceSelect from "nice-select2/dist/js/nice-select2.js";
import "nice-select2/dist/css/nice-select2.css";
import Toastify from "toastify-js";
import "toastify-js/src/toastify.css";

// import pdfMake from "pdfmake/build/pdfmake";
// import pdfFonts from "pdfmake/build/vfs_fonts";
// pdfMake.vfs = pdfFonts.pdfMake.vfs;
// import "pdfmake/build/vfs_fonts";

import "jszip";

// import ClassicEditor from "@ckeditor/ckeditor5-build-classic";
// import "css.gg/icons/all.css";
// import "css.gg/icons/css/al"
import tableSort from "table-sort-js/table-sort.js";
// eslint-disable-next-line no-unused-vars
import Chart from "chart.js/auto";
import "datatables.net-fixedheader";
import "datatables.net-buttons";
import "datatables.net-buttons/js/buttons.html5.js";
import "./dashboard/dashboard.js";
import "./job/details.js";
import "./special_assignment/details.js";
import "./special_assignment/special_assignment.js";
import "./task/task.js";
import "./document/document.js";
import "./note/note.js";
import "./cfo/dashboard.js";
import "./discussion/discussion.js";
import "./job/job.js";
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
import "./beach_wood_user/assistant.js";
import "./beach_wood_user/bookkeeper.js";
import "./beach_wood_user/manager.js";
import "./beach_wood_user/cfo.js";
import "./dashboard/notifications.js";
import { setFormInputsReadOnly } from "../utils/form_helpers";
import { HSTabs } from "../../node_modules/preline/dist/preline.js";
// import { HSTabs } from "../../node_modules/preline/dist/preline.js";

window.document.addEventListener("DOMContentLoaded", function () {
  window.HSStaticMethods.autoInit();
  // Datatables config
  const dataTablesInputs = document.querySelectorAll(".dt-container thead input");

  dataTablesInputs.forEach((input) => {
    input.addEventListener("keydown", function (evt) {
      if ((evt.metaKey || evt.ctrlKey) && evt.key === "a") this.select();
    });
  });
  const niceSelectElements = document.querySelectorAll("select.nice-select");
  if (niceSelectElements.length > 0) {
    niceSelectElements.forEach((element) => {
      new NiceSelect(element, { searchable: true });
    });
  }
  hljs.highlightAll();
  let gallery = new SimpleLightbox(".gallery a", {
    overlayOpacity: 0.9,
    download: true,
  });
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
  const formBackBtn = document.querySelector("button#formBackBtn");
  if (formBackBtn) {
    formBackBtn.addEventListener("click", (event) => {
      window.history.back();
    });
  }

  // Modal Events
  /* const mo = document.querySelector("#hs-static-backdrop-modal");
  mo.addEventListener("open.hs.overlay", (evt) => {
    // console.log(evt);
    console.log("open");
  });
  mo.addEventListener("close.hs.overlay", (evt) => {
    // console.log(evt);
    console.log("Close");
  }); */
  const staffDetailsPermissionsTabs = HSTabs.getInstance("#staffDetailsPermissionsTabs");
  if (staffDetailsPermissionsTabs) {
    staffDetailsPermissionsTabs.on(
      "change",
      ({ staffDetailsPermissionsTabs, prev, current }) => {
        const btn = document.querySelector("button#updatePermissionsStaffDetailsBtn");
        if (current === "#permissions-tab") {
          btn.classList.remove("hidden");
        } else {
          btn.classList.add("hidden");
        }
      },
    );
  }
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
});
