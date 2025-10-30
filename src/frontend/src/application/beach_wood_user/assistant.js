"use strict";

import FilterPersistence from "../../utils/forms/filterform.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const filterForm = document.getElementById("assistantsFilterForm");
  const resetFilterBtn = document.querySelector("button#resetFilterBtn");

  if (filterForm) {
    const filterPersistence = new FilterPersistence(filterForm, "assistantsFilter");

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
});
