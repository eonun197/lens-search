// 아이콘 클릭 → 작은 창 열기
chrome.action.onClicked.addListener(() => {
  chrome.windows.create({
    url: chrome.runtime.getURL("popup.html"),
    type: "popup",
    width: 360,
    height: 520,
    top: 100,
    left: 100
  });
});

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
