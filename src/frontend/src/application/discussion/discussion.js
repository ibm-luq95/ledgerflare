"use strict";

import { bwCleanApiError } from "../../utils/apis/clean_errors.js";
import { UploadFileRequest } from "../../utils/apis/upload_file.js";
import { CSRFINPUTNAME, SUCCESSTIMEOUTSECS } from "../../utils/constants.js";
import {
  disableAndEnableFieldsetItems,
  formInputSerializer,
} from "../../utils/form_helpers.js";
import { showToastNotification } from "../../utils/toasts.js";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const chatbox = document.getElementById("chatbox");
  if (chatbox) {
    chatbox.scrollTop = chatbox.scrollHeight - chatbox.clientHeight;
    // chatbox.scrollTo({ top: chatbox.scrollHeight, behavior: "smooth" });
    // alert("Dd")
  }

  const discussionModalElement = document.querySelector("div#add-discussion-model-form");
  const discussionsResetBtn = document.querySelector("button#discussionsResetBtn");
  if (discussionsResetBtn) {
    discussionsResetBtn.addEventListener("click", (event) => {
      const replyElements = document.querySelectorAll("input[name='discussionID']");
      if (replyElements.length > 0) {
        replyElements.forEach((element) => {
          element.checked = false;
        });
      }
    });
  }
  if (discussionModalElement) {
    const discussionForm = discussionModalElement.querySelector(
      "form#createDiscussionForm",
    );
    if (discussionForm) {
      discussionForm.addEventListener("submit", (event) => {
        event.preventDefault();
        let submitType = "Discussion";
        const currentTarget = event.currentTarget;
        const replyElement = document.querySelector("input[name='discussionID']:checked");

        const formInputs = formInputSerializer({
          formElement: currentTarget,
          excludedFields: ["_method", "attachment"],
          returnAsFormData: true,
          filesArray: ["attachment"],
        });
        if (replyElement) {
          formInputs.append("replies", replyElement.value);
          submitType = "Reply";
        }
        console.log(formInputs);
        disableAndEnableFieldsetItems({
          formElement: discussionForm,
          state: "disable",
        });
        const uploadRequest = new UploadFileRequest(
          currentTarget.action,
          formInputs,
          currentTarget.elements[CSRFINPUTNAME].value,
          currentTarget.method,
          false,
        );
        const request = uploadRequest.sendRequest();
        request
          .then((data) => {
            console.log(data);
            showToastNotification(`${submitType} submitted successfully!`, "success");
            setTimeout(() => {
              window.location.reload();
            }, SUCCESSTIMEOUTSECS);
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
              showToastNotification("Error while add new reply!", "error");
            }
            console.error(error);
            disableAndEnableFieldsetItems({
              formElement: discussionForm,
              state: "enabled",
            });
          })
          .finally(() => {
            disableAndEnableFieldsetItems({
              formElement: discussionForm,
              state: "enabled",
            });
          });
      });
    }
  }
});
