"use strict";

import Quill from "quill";
import "quill/dist/quill.snow.css";

document.addEventListener("DOMContentLoaded", () => {
  const editorElements = document.querySelectorAll(
    "textarea.wyswyg-editor, textarea.rich-editor",
  );

  if (editorElements && editorElements.length > 0) {
    editorElements.forEach((textareaElement) => {
      if (textareaElement.dataset.quillInitialized === "true") return;
      textareaElement.dataset.quillInitialized = "true";

      textareaElement.removeAttribute("required");
      textareaElement.style.display = "none";

      const quillContainer = document.createElement("div");
      quillContainer.className =
        "quill-editor-container bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-b-lg";
      quillContainer.style.minHeight = "200px";

      textareaElement.parentNode.insertBefore(
        quillContainer,
        textareaElement.nextSibling,
      );

      const quill = new Quill(quillContainer, {
        theme: "snow",
        modules: {
          toolbar: [
            [{ header: [1, 2, 3, 4, false] }],
            ["bold", "italic", "underline", "strike"],
            [{ color: [] }, { background: [] }],
            [{ list: "ordered" }, { list: "bullet" }],
            [{ align: [] }],
            ["link", "clean"],
          ],
        },
      });

      if (textareaElement.value) {
        quill.root.innerHTML = textareaElement.value;
      }

      quill.on("text-change", () => {
        textareaElement.value = quill.root.innerHTML;
      });

      const form = textareaElement.closest("form");
      if (form) {
        form.addEventListener("submit", () => {
          textareaElement.value = quill.root.innerHTML;
        });
      }
    });
  }
});
