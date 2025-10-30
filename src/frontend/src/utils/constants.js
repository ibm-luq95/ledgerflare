"use strict";

/**
 * This code snippet defines a method called getConstructorName on the Object prototype.
 * The method is used to retrieve the constructor name of an object.
 * It checks if the object has a prototype and uses that constructor, otherwise it uses the object's constructor.
 * The method then extracts the constructor name from the function's string representation.
 * It handles some aliases for anonymous functions and returns the constructor name.
 */
Object.prototype.getConstructorName = function () {
  const str = (this.prototype ? this.prototype.constructor : this.constructor).toString();
  const cname = str.match(/function\s(\w*)/)[1];
  const aliases = ["", "anonymous", "Anonymous"];
  return aliases.indexOf(cname) > -1 ? "Function" : cname;
};

const baseUrl = window.location.origin;  // the base url for the project

const isDisabledCssClass = "is-disabled";  // custom css class for disabled
const CSRFINPUTNAME = "csrfmiddlewaretoken";  // django csrf input name
const eyeSlashIconHTMLCode = `<i class="fa-solid fa-eye-slash"></i>`;  // font awesome eye slash icon
const eyeIconHTMLCode = `<i class="fa-solid fa-eye"></i>`;  // font awesome eye slash icon
const SUCCESSTIMEOUTSECS = 1000; // Success timeout for API requests.
const TOASTSTIMEOUTSECS = 2500; // Toasts notifications timeout
// console.log(global.window.settings);
// const DEBUG = window.settings["DEBUG"];
const DEBUG = true; // Check if the code in debugging mode
// alert(window.settings["FETCHURLNAMEURL"])
// const FETCHURLNAMEURL = window.settings["FETCHURLNAMEURL"];
const FETCHURLNAMEURL = new URL(process.env.FETCHURLNAMEURL, baseUrl); // This url will use in any time need to grab custom url from backend
const CURRENTUSER = "";

export {
  isDisabledCssClass,
  eyeSlashIconHTMLCode,
  eyeIconHTMLCode,
  DEBUG,
  FETCHURLNAMEURL,
  CURRENTUSER,
  CSRFINPUTNAME,
  SUCCESSTIMEOUTSECS,
  TOASTSTIMEOUTSECS,
};
