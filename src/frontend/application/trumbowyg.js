// frontend/application/trumbowyg.js
// const { default: $ } = await import("jquery");

// window.$ = window.jQuery = $;

// await import("trumbowyg/dist/ui/trumbowyg.css");
await import("trumbowyg");
// await import("trumbowyg/dist/plugins/base64/trumbowyg.base64.js");

function initTrumbowyg() {
  $.noConflict();
  const editor = $(".wyswyg-editor");
  if (editor.length) {
    editor.trumbowyg();
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTrumbowyg);
} else {
  initTrumbowyg();
}
