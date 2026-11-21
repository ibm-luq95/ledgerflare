"use strict";
import i18next from "i18next";

const bwI18Helper = i18next.init({
  lng: "en", // if you're using a language detector, do not define the lng option
  debug: true,
  // objectNotation: true,
  globalInjection: true,
  resources: {
    en: {
      objectNotation: true,
      translation: {
        key: "hello world",
        jobs: {
          updateJobSuccessMsg: "Job updated successfully",
        },
      },
    },
  },
});
// bwI18Helper.configure({objectNotation: true});
export { bwI18Helper };
