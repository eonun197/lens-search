// 단축키 → 즉시 탭 캡처 → content script에 전달
chrome.commands.onCommand.addListener((command) => {
  if (command === "lens-search") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;

      // 즉시 캡처 (권한이 유효할 때)
      chrome.tabs.captureVisibleTab(null, { format: "png" }, (dataUrl) => {
        if (dataUrl) {
          chrome.tabs.sendMessage(tabs[0].id, {
            action: "selectArea",
            screenshot: dataUrl
          });
        }
      });
    });
  }
});
