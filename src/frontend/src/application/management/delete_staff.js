"use strict";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const bookkeeperDeleteForm = document.querySelector("form#bookkeeperDeleteForm");
  if (bookkeeperDeleteForm) {
    bookkeeperDeleteForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const cnfmDelete = confirm(
        "Are you sure you want to delete this bookkeeper? this action cannot be undone, all entities assigned to this bookkeeper will be unplugged",
      );
      if (cnfmDelete) {
        bookkeeperDeleteForm.submit();
      }
    });
  }
});
