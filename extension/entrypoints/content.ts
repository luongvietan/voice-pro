export default defineContentScript({
  matches: ["*://*/*"],
  main() {
    console.info("[voice-pro] content script loaded");
  },
});
