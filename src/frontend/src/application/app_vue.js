import { createApp } from "vue";
import App from "../components/App.vue";
if (document.querySelector("#app")) {
  createApp(App).mount("#app");
}
