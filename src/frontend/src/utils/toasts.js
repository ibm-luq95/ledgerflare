"use strict";

import { TOASTSTIMEOUTSECS } from "./constants.js";
import { getIconForToasts } from "./icons.js";

/**
 * Displays a toast notification with the given message and notification type.
 *
 * @param {string} msg - The message to be displayed in the toast notification.
 * @param {string} [notificationType="success"] - The type of the toast notification. Possible values are "success", "error", "danger", "info", and "warning".
 * @throws {Error} If the specified notification type does not exist.
 * @returns {void}
 */
const showToastNotification = (msg, notificationType = "success") => {
  const toastsWrapperElement = document.querySelector("div#toasts-wrapper");
  const iconWrapper = toastsWrapperElement.querySelector("div#iconWrapper");
  const msgElement = toastsWrapperElement.querySelector("p#msg");
  msgElement.textContent = msg;
  const color = getIconForToasts(notificationType);
  iconWrapper.innerHTML = color["icon"];

  toastsWrapperElement.classList.remove("hidden");
  toastsWrapperElement.classList.add(
    ...["animate__animated", "animate__fadeInRight", "animate__faster"],
  );

  setTimeout(() => {
    toastsWrapperElement.classList.add(...["animate__animated", "animate__fadeOutRight"]);
  }, TOASTSTIMEOUTSECS);
  toastsWrapperElement.classList.remove(...["animate__fadeOutRight"]);
};

export { showToastNotification };
