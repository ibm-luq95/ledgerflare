// This is the scss entry file
import $ from "jquery";
window.jQuery = $;
window.$ = $;
import _ from "lodash";
import Dropzone from "dropzone";
import "../styles/base.css";
import "../styles/index.scss";
import "../styles/dashboard.scss";
// import SimpleLightbox from 'simplelightbox';
// import 'simplelightbox/dist/simple-lightbox.css';
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
import Choices from "choices.js";
import "choices.js/public/assets/styles/choices.min.css";
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
// import "./cfo/dashboard.js";
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
import "./dashboard/manager_dashboard.js";
import "./management/delete_staff.js";
import { initJournalEntryModule } from "./client/journal_entry.js";
// import "../styles/datatable.css";
import { setFormInputsReadOnly } from "../utils/form_helpers.js";
import { HSTabs } from "../../node_modules/preline/dist/preline.js";
// import { HSTabs } from "../../node_modules/preline/dist/preline.js";

window.document.addEventListener("DOMContentLoaded", function () {
  window.HSStaticMethods.autoInit();

  // Datatables config
  const dataTablesInputs = document.querySelectorAll(
    ".dt-container thead input",
  );
  initJournalEntryModule();
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
  // let gallery = new SimpleLightbox(".gallery a", {
  //   overlayOpacity: 0.9,
  //   download: true,
  // });
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
  const staffDetailsPermissionsTabs = HSTabs.getInstance(
    "#staffDetailsPermissionsTabs",
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
});
(function () {
  "use strict";

  // Country data
  const countryData = [
    {
      name: "United States",
      flag: "🇺🇸",
      terms: "united states us usa america american",
    },
    {
      name: "United Kingdom",
      flag: "🇬🇧",
      terms: "united kingdom uk england britain british",
    },
    { name: "Canada", flag: "🇨🇦", terms: "canada canadian" },
    { name: "Australia", flag: "🇦🇺", terms: "australia australian aussie" },
    { name: "Germany", flag: "🇩🇪", terms: "germany german deutschland" },
    { name: "France", flag: "🇫🇷", terms: "france french" },
    { name: "Japan", flag: "🇯🇵", terms: "japan japanese nippon" },
    { name: "South Korea", flag: "🇰🇷", terms: "south korea korean korea" },
    { name: "Brazil", flag: "🇧🇷", terms: "brazil brazilian brasil" },
    { name: "India", flag: "🇮🇳", terms: "india indian bharat" },
    { name: "China", flag: "🇨🇳", terms: "china chinese" },
    { name: "Mexico", flag: "🇲🇽", terms: "mexico mexican" },
    { name: "Spain", flag: "🇪🇸", terms: "spain spanish españa" },
    { name: "Italy", flag: "🇮🇹", terms: "italy italian italia" },
    { name: "Netherlands", flag: "🇳🇱", terms: "netherlands dutch holland" },
  ];

  // Get elements
  const searchInput = document.getElementById("search-input");
  const dropdownList = document.getElementById("dropdown-list");
  const countryList = document.getElementById("country-list");
  const noMatches = document.getElementById("no-matches");
  const displayValue = document.getElementById("display-value");
  const arrowIcon = document.getElementById("arrow-icon");

  let isDropdownOpen = false;
  let currentSelection = -1;
  let filteredData = [];

  // Build country option HTML
  function buildCountryOption(country, index) {
    return `
                    <div class="country-option py-2 px-3 cursor-pointer hover:bg-gray-100 flex items-center transition-colors duration-150" 
                         data-country="${country.name}" 
                         data-index="${index}">
                        <span class="text-2xl mr-3">${country.flag}</span>
                        <span class="text-sm font-medium text-gray-800">${country.name}</span>
                    </div>
                `;
  }

  // Filter and display countries
  function updateCountryList(searchTerm) {
    if (searchTerm.trim() === "") {
      filteredData = countryData.slice();
    } else {
      const term = searchTerm.toLowerCase();
      filteredData = countryData.filter(
        (country) => country.terms.toLowerCase().indexOf(term) !== -1,
      );
    }

    if (filteredData.length === 0) {
      countryList.innerHTML = "";
      noMatches.classList.remove("hidden");
    } else {
      if (noMatches) {
        noMatches.classList.add("hidden");
      }

      let html =
        '<div class="py-2 px-3 text-xs font-medium uppercase text-gray-800 bg-gray-100 sticky top-0">Actions</div>';
      filteredData.forEach((country, index) => {
        html += buildCountryOption(country, index);
      });
      if (countryList) {
        countryList.innerHTML = html;
      }
    }

    currentSelection = -1;
    updateSelection();
  }

  // Update visual selection
  function updateSelection() {
    if (countryList) {
      const options = countryList.querySelectorAll(".country-option");
      options.forEach((option, index) => {
        if (index === currentSelection) {
          option.classList.add("bg-blue-100");
          option.scrollIntoView({ block: "nearest" });
        } else {
          option.classList.remove("bg-blue-100");
        }
      });
    }
  }

  // Open/close dropdown
  function toggleDropdown(show) {
    isDropdownOpen = show;
    if (isDropdownOpen) {
      dropdownList.classList.remove("hidden");
      arrowIcon.style.transform = "rotate(180deg)";
    } else {
      dropdownList.classList.add("hidden");
      arrowIcon.style.transform = "rotate(0deg)";
      currentSelection = -1;
    }
  }

  // Select a country
  function selectCountry(countryName) {
    searchInput.value = countryName;
    // displayValue.textContent = countryName;
    alert(countryName);
    toggleDropdown(false);
  }

  if (searchInput) {
    // Event: Input focus
    searchInput.addEventListener("focus", function () {
      updateCountryList(this.value);
      toggleDropdown(true);
    });

    // Event: Input typing
    searchInput.addEventListener("input", function () {
      updateCountryList(this.value);
      if (!isDropdownOpen) {
        toggleDropdown(true);
      }
    });

    // Event: Keyboard navigation
    searchInput.addEventListener("keydown", function (e) {
      if (
        !isDropdownOpen &&
        (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter")
      ) {
        e.preventDefault();
        updateCountryList(this.value);
        toggleDropdown(true);
        return;
      }

      if (isDropdownOpen) {
        const maxIndex = filteredData.length - 1;

        switch (e.key) {
          case "ArrowDown":
            e.preventDefault();
            currentSelection =
              currentSelection < maxIndex ? currentSelection + 1 : maxIndex;
            updateSelection();
            break;

          case "ArrowUp":
            e.preventDefault();
            currentSelection =
              currentSelection > -1 ? currentSelection - 1 : -1;
            updateSelection();
            break;

          case "Enter":
            e.preventDefault();
            if (currentSelection >= 0 && filteredData[currentSelection]) {
              selectCountry(filteredData[currentSelection].name);
            }
            break;

          case "Escape":
            e.preventDefault();
            toggleDropdown(false);
            break;
        }
      }
    });
  }

  if (countryList) {
    // Event: Click on country option
    countryList.addEventListener("click", function (e) {
      const option = e.target.closest(".country-option");
      if (option) {
        const countryName = option.getAttribute("data-country");
        selectCountry(countryName);
      }
    });
  }

  // Event: Click outside to close
  document.addEventListener("click", function (e) {
    if (document.getElementById("combobox-wrapper")) {
      if (!document.getElementById("combobox-wrapper").contains(e.target)) {
        toggleDropdown(false);
      }
    }
  });

  // Initialize
  updateCountryList("");
})();
