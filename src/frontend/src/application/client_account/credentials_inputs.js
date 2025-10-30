"use strict";

import { addTxtToClipboardWithNotification } from "../../utils/clipboard.js";
import { convertStrToBool } from "../../utils/helpers.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const caCredentialsBtns = document.querySelectorAll("button.ca-credentials-btn");
  const caShowPasswordBtns = document.querySelectorAll("button.ca-show-password-btn");
  if (caCredentialsBtns.length > 0) {
    caCredentialsBtns.forEach((btn) => {
      btn.addEventListener("click", (event) => {
        const currentTarget = event.currentTarget;
        const credentialsInputId = currentTarget.dataset["credentialsId"];
        const credentialsInput = document.querySelector(`#${credentialsInputId}`);
        addTxtToClipboardWithNotification({
          textWillCopy: credentialsInput.value,
          label: credentialsInput.dataset["label"],
        });
      });
    });
  }

  if (caShowPasswordBtns.length > 0) {
    caShowPasswordBtns.forEach((btn) => {
      btn.addEventListener("click", (event) => {
        const currentTarget = event.currentTarget;
        const showStatus = convertStrToBool(currentTarget.dataset["isVisible"]);
        const credentialsInputId = currentTarget.dataset["credentialsId"];
        const credentialsInput = document.querySelector(`#${credentialsInputId}`);
        const eyeIcon = ["fa-solid", "fa-eye", "w-3", "h-3"];
        const eyeSlashIcon = ["fa-solid", "fa-eye-slash", "w-3", "h-3"];
        const spanIcon = currentTarget.querySelector("span.ca-icon");
        const icon = spanIcon.querySelector("svg");
        spanIcon.removeChild(icon);
        const newIcon = document.createElement("i");
        switch (showStatus) {
          case true:
            currentTarget.dataset["isVisible"] = false;
            credentialsInput.type = "password";
            newIcon.classList.add(...eyeIcon);
            break;
          case false:
            // this mean the password is not visible
            currentTarget.dataset["isVisible"] = true;
            credentialsInput.type = "text";
            newIcon.classList.add(...eyeSlashIcon);
            break;
        }
        spanIcon.appendChild(newIcon);
      });
    });
  }
});
