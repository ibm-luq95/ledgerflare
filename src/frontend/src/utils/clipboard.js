"use strict";

import { capitalizedFirstLetter } from "./helpers.js";
import { showToastNotification } from "./toasts.js";

/**
 * Copies the given text to the clipboard and displays a notification.
 *
 * @param {Object} options - The options for copying text and displaying the notification.
 * @param {string} options.textWillCopy - The text to be copied to the clipboard.
 * @param {string} options.label - The label for the copied text.
 * @param {boolean} [options.isNotify=true] - Whether to display a notification or not.
 * @param {string} [options.notificationMsg=null] - The custom notification message.
 * @param {string} [options.notificationType="success"] - The type of notification.
 * @returns {void}
 */
const addTxtToClipboardWithNotification = ({
  textWillCopy,
  label,
  isNotify = true,
  notificationMsg = null,
  notificationType = "success",
}) => {
  navigator.clipboard.writeText(textWillCopy);
  const msg = notificationMsg
    ? capitalizedFirstLetter(notificationMsg)
    : capitalizedFirstLetter(`${label} copied successfully!`);
  if (isNotify === true) {
    showToastNotification(msg, notificationType);
  }
};

export { addTxtToClipboardWithNotification };
