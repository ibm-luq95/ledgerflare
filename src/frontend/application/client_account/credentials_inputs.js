"use strict";

import { addTxtToClipboardWithNotification } from "../utils/clipboard.js";
import { getCookie } from "../utils/cookie.js";
import { convertStrToBool } from "../utils/helpers.js";
import { showToastNotification } from "../utils/toasts.js";

async function fetchRevealedPassword(revealEndpoint) {
  const csrfToken = getCookie("csrftoken");
  const response = await fetch(revealEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken || "",
    },
    credentials: "same-origin",
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to reveal credentials");
  }
  const data = await response.json();
  return data.password;
}

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const caCredentialsBtns = document.querySelectorAll("button.ca-credentials-btn");
  const caShowPasswordBtns = document.querySelectorAll("button.ca-show-password-btn");
  if (caCredentialsBtns.length > 0) {
    caCredentialsBtns.forEach((btn) => {
      btn.addEventListener("click", async (event) => {
        const currentTarget = event.currentTarget;
        const credentialsInputId = currentTarget.dataset["credentialsId"];
        const credentialsInput = document.querySelector(`#${credentialsInputId}`);
        if (!credentialsInput) return;

        const revealEndpoint = currentTarget.dataset["revealEndpoint"];
        let textToCopy = credentialsInput.value;

        if (revealEndpoint && !credentialsInput.dataset["revealed"]) {
          try {
            currentTarget.disabled = true;
            textToCopy = await fetchRevealedPassword(revealEndpoint);
            credentialsInput.value = textToCopy;
            credentialsInput.dataset["revealed"] = "true";
          } catch (err) {
            showToastNotification(err.message || "Error retrieving credentials", "danger");
            return;
          } finally {
            currentTarget.disabled = false;
          }
        }

        addTxtToClipboardWithNotification({
          textWillCopy: textToCopy,
          label: credentialsInput.dataset["label"] || "Credentials",
        });
      });
    });
  }

  if (caShowPasswordBtns.length > 0) {
    caShowPasswordBtns.forEach((btn) => {
      btn.addEventListener("click", async (event) => {
        const currentTarget = event.currentTarget;
        const showStatus = convertStrToBool(currentTarget.dataset["isVisible"]);
        const credentialsInputId = currentTarget.dataset["credentialsId"];
        const credentialsInput = document.querySelector(`#${credentialsInputId}`);
        if (!credentialsInput) return;

        const eyeIcon = ["fa-solid", "fa-eye", "w-3", "h-3"];
        const eyeSlashIcon = ["fa-solid", "fa-eye-slash", "w-3", "h-3"];
        const spanIcon = currentTarget.querySelector("span.ca-icon");
        const revealEndpoint = currentTarget.dataset["revealEndpoint"];

        if (!showStatus) {
          if (revealEndpoint && !credentialsInput.dataset["revealed"]) {
            try {
              currentTarget.disabled = true;
              const decrypted = await fetchRevealedPassword(revealEndpoint);
              credentialsInput.value = decrypted;
              credentialsInput.dataset["revealed"] = "true";
            } catch (err) {
              showToastNotification(err.message || "Error retrieving credentials", "danger");
              return;
            } finally {
              currentTarget.disabled = false;
            }
          }
          currentTarget.dataset["isVisible"] = "true";
          credentialsInput.type = "text";
          if (spanIcon) {
            spanIcon.innerHTML = "";
            const newIcon = document.createElement("i");
            newIcon.classList.add(...eyeSlashIcon);
            spanIcon.appendChild(newIcon);
          }

          if (credentialsInput._hideTimer) {
            clearTimeout(credentialsInput._hideTimer);
          }
          credentialsInput._hideTimer = setTimeout(() => {
            currentTarget.dataset["isVisible"] = "false";
            credentialsInput.type = "password";
            if (spanIcon) {
              spanIcon.innerHTML = "";
              const revertIcon = document.createElement("i");
              revertIcon.classList.add(...eyeIcon);
              spanIcon.appendChild(revertIcon);
            }
          }, 15000);
        } else {
          currentTarget.dataset["isVisible"] = "false";
          credentialsInput.type = "password";
          if (credentialsInput._hideTimer) {
            clearTimeout(credentialsInput._hideTimer);
          }
          if (spanIcon) {
            spanIcon.innerHTML = "";
            const newIcon = document.createElement("i");
            newIcon.classList.add(...eyeIcon);
            spanIcon.appendChild(newIcon);
          }
        }
      });
    });
  }
});
