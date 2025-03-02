/** @type {import('tailwindcss').Config} */
const Path = require("path");
// const fs = require("fs");
import chalk from "chalk";
const pwd = process.env.PWD;
const pwdParent = Path.dirname(pwd);
const srcDir = Path.join(pwdParent, "src");
const frontendDir = Path.join(srcDir, "frontend");

console.log("#########################################################");
console.warn(pwd);
console.log("#########################################################");

// We can add current project paths here
const projectPaths = [
  Path.join(pwdParent, "node_modules", "preline", "dist", "*.js"),
  Path.join(pwdParent, "templates", "**", "*.html"),
  Path.join(pwdParent, "static", "**", "*.js"),
  Path.join(pwdParent, "components", "**", "*.js"),
  Path.join(pwdParent, "components", "**", "*.html"),
  // add js file paths if you need
];

const contentPaths = [...projectPaths];
console.log(`tailwindcss will scan ${contentPaths}`);
module.exports = {
  darkMode: "class",
  content: contentPaths,
  theme: {
    extend: {},
  },
  corePlugins: {
    aspectRatio: false,
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("@tailwindcss/forms"),
    require("@tailwindcss/aspect-ratio"),
    require("@tailwindcss/container-queries"),
    require("preline/plugin"),
  ],
};
