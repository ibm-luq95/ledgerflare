"use strict";

/**
 * Staff Job Workstation Interactive Controller
 * Handles view switching (Calendar, Kanban, Agenda) and task accordions without inline eval/CSP issues.
 */
export function initWorkstation() {
  const container = document.getElementById("workstation-content-container");
  if (!container) {
    return;
  }

  const currentView = container.dataset.activeView || "calendar";
  const viewButtons = container.querySelectorAll("[data-view-btn]");
  const viewPanes = container.querySelectorAll("[data-view-pane]");
  const viewInput = document.getElementById("workstation-active-view-input");

  function setActiveView(targetView) {
    viewButtons.forEach((btn) => {
      const isCurrent = btn.dataset.viewBtn === targetView;
      if (isCurrent) {
        btn.classList.add(
          "bg-white",
          "text-blue-600",
          "shadow-2xs",
          "dark:bg-neutral-800",
          "dark:text-blue-400",
          "font-semibold"
        );
        btn.classList.remove("text-gray-600", "dark:text-neutral-400");
      } else {
        btn.classList.remove(
          "bg-white",
          "text-blue-600",
          "shadow-2xs",
          "dark:bg-neutral-800",
          "dark:text-blue-400",
          "font-semibold"
        );
        btn.classList.add("text-gray-600", "dark:text-neutral-400");
      }
    });

    viewPanes.forEach((pane) => {
      if (pane.dataset.viewPane === targetView) {
        pane.classList.remove("hidden");
      } else {
        pane.classList.add("hidden");
      }
    });

    container.dataset.activeView = targetView;
    if (viewInput) {
      viewInput.value = targetView;
    }
  }

  // Set initial view state
  setActiveView(currentView);

  // Bind view switcher buttons
  viewButtons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = btn.dataset.viewBtn;
      if (targetView) {
        setActiveView(targetView);
      }
    });
  });

  // Bind task accordion toggles
  const accordionToggles = container.querySelectorAll("[data-task-toggle]");
  accordionToggles.forEach((toggle) => {
    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = toggle.dataset.taskToggle;
      const targetEl = container.querySelector(
        `[data-task-list="${targetId}"]`
      );
      const chevron = toggle.querySelector(
        ".fa-chevron-down, .fa-chevron-right"
      );
      if (targetEl) {
        const isHidden = targetEl.classList.contains("hidden");
        if (isHidden) {
          targetEl.classList.remove("hidden");
          if (chevron) {
            chevron.classList.add("rotate-180");
          }
        } else {
          targetEl.classList.add("hidden");
          if (chevron) {
            chevron.classList.remove("rotate-180");
          }
        }
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initWorkstation();
});

document.body.addEventListener("htmx:afterSwap", (evt) => {
  const target = evt.detail && evt.detail.target;
  if (
    target &&
    (target.id === "workstation-content-container" ||
      target.closest("#workstation-content-container"))
  ) {
    initWorkstation();
    if (window.HSStaticMethods) {
      window.HSStaticMethods.autoInit();
    }
  }
});
