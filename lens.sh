#!/bin/bash
# ===== Lens Search: Cmd+F for Images =====

F=/tmp/lens_capture.png
H=/tmp/lens_submit.html

rm -f $F $H

# 1. 영역 선택 캡처
/usr/sbin/screencapture -i $F

# 캡처 안됐으면 종료
test -f $F || exit 0

# 2. base64 인코딩 (python 없이)
B=$(/usr/bin/base64 -i $F)

# 3. HTML 생성
/bin/cat > $H << HTMLEOF
<form id=f method=POST enctype=multipart/form-data action=https://lens.google.com/v3/upload><input type=file name=encoded_image id=img></form><script>var b="${B}";var c=atob(b);var a=new Uint8Array(c.length);for(var i=0;i<c.length;i++)a[i]=c.charCodeAt(i);var bl=new Blob([a],{type:"image/png"});var d=new DataTransfer();d.items.add(new File([bl],"c.png",{type:"image/png"}));document.getElementById("img").files=d.files;document.getElementById("f").submit();</script>
HTMLEOF

# 4. Chrome에서 열기
/usr/bin/open -a "Google Chrome" $H

# 5. 정리
(sleep 5 && rm -f $F $H) &
exit 0
