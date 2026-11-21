"use strict";

import { bwCleanApiError } from "../utils/apis/clean_errors.js";
import { RequestHandler } from "../utils/apis/request_handler.js";
import { CSRFINPUTNAME } from "../utils/constants.js";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../utils/form_helpers.js";
import { showToastNotification } from "../utils/toasts.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const filterCategoryForms = document.querySelectorAll(
    "form.filterCategoryForms",
  );
  if (filterCategoryForms.length > 0) {
    filterCategoryForms.forEach((form) => {
      form.addEventListener("submit", (submitEvent) => {
        submitEvent.preventDefault();
        const currentTarget = submitEvent.currentTarget;
        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method"],
        });
        disableAndEnableFieldsetItems({
          formElement: form,
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
            const categoryName = formInputs["name"] || data?.name;
            const categoryId = data?.id || data?.pk;

            showToastNotification(`Category "${categoryName}" created successfully!`, "success");

            // Reset form input
            form.reset();

            // Dynamically append new category row into categoriesModalList
            const listEl = document.getElementById("categoriesModalList");
            const emptyEl = document.getElementById("categoriesModalEmptyState");
            const countEl = document.getElementById("categoriesModalCount");

            if (listEl) {
              listEl.classList.remove("hidden");
              if (emptyEl) emptyEl.classList.add("hidden");

              const newRow = document.createElement("div");
              newRow.className =
                "flex items-center justify-between p-2.5 rounded-lg border border-gray-100 bg-gray-50/50 hover:bg-gray-50 dark:bg-neutral-800/40 dark:border-neutral-800 dark:hover:bg-neutral-800/80 transition-colors animate__animated animate__fadeInDown";

              const leftDiv = document.createElement("div");
              leftDiv.className = "flex items-center gap-2 min-w-0";

              const dotSpan = document.createElement("span");
              dotSpan.className = "size-2 rounded-full bg-blue-500 shrink-0";

              const nameSpan = document.createElement("span");
              nameSpan.className =
                "text-xs font-medium text-gray-800 dark:text-neutral-200 truncate";
              nameSpan.textContent = categoryName;

              leftDiv.appendChild(dotSpan);
              leftDiv.appendChild(nameSpan);

              const rightDiv = document.createElement("div");
              rightDiv.className = "flex items-center gap-2 shrink-0";
              rightDiv.innerHTML = `
                <span class="inline-flex items-center py-0.5 px-2 rounded-full text-[10px] font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                  0 items
                </span>
              `;

              newRow.appendChild(leftDiv);
              newRow.appendChild(rightDiv);
              listEl.prepend(newRow);

              if (countEl) {
                const currentCount = parseInt(countEl.textContent || "0", 10) || 0;
                countEl.textContent = `${currentCount + 1}`;
              }
            }

            // Dynamically update any categories select/multi-select on the page
            const categorySelects = document.querySelectorAll(
              'select[name="categories"], select[name="category"], select#id_categories'
            );
            categorySelects.forEach((sel) => {
              if (categoryId && categoryName) {
                const opt = document.createElement("option");
                opt.value = categoryId;
                opt.textContent = categoryName;
                sel.appendChild(opt);
              }
            });
          })
          .catch((error) => {
            const er = bwCleanApiError(error);
            if (er) {
              er.forEach((erElement) => {
                showToastNotification(
                  `Error: ${erElement["detail"]} - ${erElement["attr"]}`,
                  "danger",
                );
              });
            } else {
              showToastNotification("Error adding category!", "danger");
            }
            console.error(error);
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: form,
              state: "enable",
            });
          });
      });
    });
  }
});
