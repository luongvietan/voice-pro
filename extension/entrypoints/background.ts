export default defineBackground(() => {
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg?.type === "GET_TAB_AUDIO_STREAM_ID") {
      const tabId = sender.tab?.id;
      if (tabId === undefined) {
        sendResponse({ ok: false, error: "No sender tab" });
        return;
      }
      chrome.tabCapture.getMediaStreamId({ targetTabId: tabId }, (streamId) => {
        if (!streamId || chrome.runtime.lastError) {
          sendResponse({
            ok: false,
            error: chrome.runtime.lastError?.message ?? "Cannot get capture stream id",
          });
          return;
        }
        sendResponse({ ok: true, streamId });
      });
      return true;
    }
    return undefined;
  });
});
