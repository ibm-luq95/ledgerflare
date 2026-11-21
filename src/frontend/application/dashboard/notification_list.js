"use strict";

import { showToastNotification } from "../utils/toasts.js";

document.addEventListener("DOMContentLoaded", () => {
  const csrfToken =
    window.csrfToken ||
    document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");

  /* Mark all as read button handler */
  const markAllBtn = document.getElementById("markAllReadPageBtn");
  if (markAllBtn) {
    markAllBtn.addEventListener("click", async () => {
      try {
        const response = await fetch(
          "/notifications/api/notifications/mark_all_read/",
          {
            method: "POST",
            headers: {
              "X-CSRFToken": csrfToken,
              "Content-Type": "application/json",
            },
          }
        );
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        window.location.reload();
      } catch (error) {
        console.error("Notification mark_all_read error traceback:", error);
        if (error.stack) {
          console.error("Stack trace:", error.stack);
        }
        showToastNotification(
          "Failed to mark notifications as read. Please try again.",
          "danger"
        );
      }
    });
  }

  /* Handle notification row item click */
  document.querySelectorAll(".notification-item-row").forEach((row) => {
    row.addEventListener("click", async (e) => {
      if (e.target.closest("button")) return;

      const pk = row.dataset.pk;
      const url = row.dataset.url;

      try {
        const response = await fetch(`/notifications/api/notifications/${pk}/mark_read/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
          },
        });
        if (!response.ok) {
          console.warn(`Mark read returned status ${response.status}`);
        }
      } catch (error) {
        console.error(`Notification row click traceback (PK: ${pk}):`, error);
        if (error.stack) {
          console.error("Stack trace:", error.stack);
        }
        showToastNotification(
          "Unable to update notification status. Redirecting to item...",
          "warning"
        );
      } finally {
        if (url && url !== "#") {
          window.location.href = url;
        }
      }
    });
  });

  /* Single mark as read button click */
  document.querySelectorAll(".mark-single-read-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const pk = btn.dataset.pk;
      try {
        const response = await fetch(
          `/notifications/api/notifications/${pk}/mark_read/`,
          {
            method: "POST",
            headers: {
              "X-CSRFToken": csrfToken,
              "Content-Type": "application/json",
            },
          }
        );
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        window.location.reload();
      } catch (error) {
        console.error(`Mark single read traceback (PK: ${pk}):`, error);
        if (error.stack) {
          console.error("Stack trace:", error.stack);
        }
        showToastNotification(
          "Failed to mark notification as read. Please refresh.",
          "danger"
        );
      }
    });
  });
});
