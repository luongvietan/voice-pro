import { defineConfig } from "wxt";

export default defineConfig({
  modules: ["@wxt-dev/module-react"],
  manifest: {
    name: "Voice-Pro Dub",
    permissions: ["storage", "activeTab", "tabCapture", "identity", "tabs", "alarms"],
    host_permissions: ["http://localhost/*", "https://*/*"],
    oauth2: {
      client_id: process.env.GOOGLE_OAUTH_CLIENT_ID ?? "",
      scopes: ["openid", "email", "profile"],
    },
  },
});
