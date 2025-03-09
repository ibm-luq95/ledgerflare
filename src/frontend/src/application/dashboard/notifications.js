"use strict";
import Worker from "worker-loader!./notifications_worker.js";
import { getCookie } from "../../utils/cookie";
document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const allNotificationItems = document.querySelectorAll("a.notificationsItem");
  const setAllNotificationsReadBtn = document.querySelector(
    "button#setAllNotificationsReadBtn",
  );
  if (setAllNotificationsReadBtn) {
    setAllNotificationsReadBtn.addEventListener("click", (event) => {
      alert("Soon");
    });
  }
  if (allNotificationItems.length > 0) {
    allNotificationItems.forEach((item) => {
      item.addEventListener("click", (event) => {
        // Destructure required event properties
        const { button, ctrlKey, metaKey, shiftKey, altKey, currentTarget } = event;

        // Ignore right-clicks or modified clicks
        if (button !== 0 || ctrlKey || metaKey || shiftKey || altKey) return;

        /** @type {HTMLAnchorElement} */
        const anchor = currentTarget;
        const { href, dataset } = anchor;

        // Validate href
        if (!href || href.startsWith("javascript:")) return;

        // Prevent default navigation
        event.preventDefault();
        // alert("Clicke");
        const workerOptions = {
          name: "NotificationsWorker", // Name for debugging
          type: "module", // Enable ES modules (modern browsers)
          credentials: "same-origin", // For CORS (omit, same-origin, include)
        };
        // const notificationsWorker = new Worker(
        //   require.resolve("./notifications_worker.js"),
        //   // workerOptions,
        // );
        const notificationsWorker = new Worker(workerOptions);
        // console.log(dataset);

        // const dataset = anchor.dataset;
        notificationsWorker.postMessage({
          pk: dataset["notificationPk"],
          url: document.querySelector("input#notificationUrl").value,
          token: getCookie("csrftoken"),
          user: dataset["user"],
          notificationType: dataset["notificationType"],
        });
        notificationsWorker.onmessage = (event) => {
          // console.log("Worker response:", event.data);
          // console.log("Worker response:", event);
          notificationsWorker.terminate();
          window.location.assign(href);
        };

        notificationsWorker.onerror = (error) => {
          console.error("Worker error:", error);
          console.error("Worker error:", error["message"]);
          notificationsWorker.terminate();
        };
      });
    });
  }
});
