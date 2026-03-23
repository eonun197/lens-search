#!/bin/bash
# ===== Lens Search: Cmd+F for Images =====
# 화면 영역을 캡처하고 즉시 Google Lens로 검색

TEMP_FILE="/tmp/lens_capture.png"

# 1. 기존 임시파일 삭제
rm -f "$TEMP_FILE"

# 2. 영역 선택 캡처
screencapture -i "$TEMP_FILE"

# 캡처 안됐으면 종료
if [ ! -f "$TEMP_FILE" ]; then
    exit 0
fi

# 3. base64 인코딩 후 HTML 파일 생성
python3 -c "
import base64

with open('$TEMP_FILE', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

html = '''<!DOCTYPE html>
<html>
<head><title>Lens Search</title></head>
<body style=\"display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;color:#666;\">
<p>Google Lens로 검색 중...</p>
<form id=\"f\" method=\"POST\" enctype=\"multipart/form-data\" action=\"https://lens.google.com/v3/upload\">
    <input type=\"file\" name=\"encoded_image\" id=\"img\" style=\"display:none\">
</form>
<script>
const b64 = \"''' + b64 + '''\";
const byteChars = atob(b64);
const byteArray = new Uint8Array(byteChars.length);
for (let i = 0; i < byteChars.length; i++) byteArray[i] = byteChars.charCodeAt(i);
const blob = new Blob([byteArray], {type: \"image/png\"});
const dt = new DataTransfer();
dt.items.add(new File([blob], \"capture.png\", {type: \"image/png\"}));
document.getElementById(\"img\").files = dt.files;
document.getElementById(\"f\").submit();
</script>
</body>
</html>'''

with open('/tmp/lens_submit.html', 'w') as f:
    f.write(html)
"

# 4. Chrome에서 열기
open -a "Google Chrome" "/tmp/lens_submit.html"

# 5. 정리
(sleep 5 && rm -f "$TEMP_FILE" "/tmp/lens_submit.html") &

exit 0
