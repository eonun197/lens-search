// ===== Lens Search: Chrome Extension =====

let isCapturing = false;
let startX, startY;
let overlay, selection, hint, screenshotData;

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "selectArea" && !isCapturing) {
    screenshotData = msg.screenshot;
    startCaptureMode();
  }
});

function startCaptureMode() {
  isCapturing = true;

  overlay = document.createElement("div");
  overlay.id = "lens-overlay";
  document.body.appendChild(overlay);

  hint = document.createElement("div");
  hint.id = "lens-hint";
  hint.textContent = "드래그해서 영역을 선택하세요 · ESC로 취소";
  document.body.appendChild(hint);

  selection = document.createElement("div");
  selection.id = "lens-selection";
  document.body.appendChild(selection);

  overlay.addEventListener("mousedown", onMouseDown);
  document.addEventListener("keydown", onKeyDown);
}

function onMouseDown(e) {
  startX = e.clientX;
  startY = e.clientY;
  selection.style.display = "block";

  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
}

function onMouseMove(e) {
  const x = Math.min(e.clientX, startX);
  const y = Math.min(e.clientY, startY);
  const w = Math.abs(e.clientX - startX);
  const h = Math.abs(e.clientY - startY);

  selection.style.left = x + "px";
  selection.style.top = y + "px";
  selection.style.width = w + "px";
  selection.style.height = h + "px";
}

function onMouseUp(e) {
  const x = Math.min(e.clientX, startX);
  const y = Math.min(e.clientY, startY);
  const w = Math.abs(e.clientX - startX);
  const h = Math.abs(e.clientY - startY);

  document.removeEventListener("mousemove", onMouseMove);
  document.removeEventListener("mouseup", onMouseUp);
  cleanup();

  if (w < 10 || h < 10) return;

  cropAndSearch(x, y, w, h);
}

function onKeyDown(e) {
  if (e.key === "Escape") {
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
    cleanup();
  }
}

function cleanup() {
  isCapturing = false;
  if (overlay) overlay.remove();
  if (selection) selection.remove();
  if (hint) hint.remove();
  document.removeEventListener("keydown", onKeyDown);
}

function cropAndSearch(x, y, w, h) {
  const img = new Image();
  img.onload = () => {
    const dpr = window.devicePixelRatio || 1;
    const canvas = document.createElement("canvas");
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, x * dpr, y * dpr, w * dpr, h * dpr, 0, 0, w * dpr, h * dpr);

    const base64 = canvas.toDataURL("image/png").split(",")[1];
    openLensSearch(base64);
  };
  img.src = screenshotData;
}

function openLensSearch(base64) {
  const html = `<!DOCTYPE html><html><body>
<form id="f" method="POST" enctype="multipart/form-data" action="https://lens.google.com/v3/upload">
<input type="file" name="encoded_image" id="img">
</form>
<script>
var b="${base64}";
var c=atob(b);
var a=new Uint8Array(c.length);
for(var i=0;i<c.length;i++)a[i]=c.charCodeAt(i);
var bl=new Blob([a],{type:"image/png"});
var d=new DataTransfer();
d.items.add(new File([bl],"c.png",{type:"image/png"}));
document.getElementById("img").files=d.files;
document.getElementById("f").submit();
<\/script></body></html>`;

  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}
