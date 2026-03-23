#!/bin/bash
echo ""
echo "  =========================="
echo "   Lens Search 설치 시작"
echo "  =========================="
echo ""

# 1. 다운로드 + 압축해제
cd ~/Downloads
curl -sLO https://github.com/eonun197/lens-search/raw/main/LensSearch.zip
unzip -o -q LensSearch.zip -d ~/LensSearch
rm -f LensSearch.zip
echo "  [OK] 다운로드 완료: ~/LensSearch"

# 2. chrome://extensions 자동 오픈
open -a "Google Chrome" "chrome://extensions"
echo ""
echo "  =========================="
echo "   아래 2가지만 해주세요!"
echo "  =========================="
echo ""
echo '  1. "개발자 모드" 켜기 (우측 상단 토글)'
echo '  2. "압축해제된 확장 프로그램을 로드합니다" 클릭'
echo "     → ~/LensSearch 폴더 선택"
echo ""
echo "  그 다음 chrome://extensions/shortcuts 에서"
echo "  Cmd+Shift+L 단축키 설정하면 끝!"
echo ""
