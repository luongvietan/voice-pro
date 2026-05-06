import { defineConfig } from "wxt";

export default defineConfig({
  modules: ["@wxt-dev/module-react"],
  manifest: {
    name: "Voice-Pro Dub",
    permissions: ["storage", "activeTab", "tabCapture", "identity"],
    host_permissions: ["http://localhost/*", "https://*/*"],
  },
});
