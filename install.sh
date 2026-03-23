#!/bin/bash
# ===== Lens Search 설치 스크립트 =====

echo ""
echo "  ============================="
echo "   Lens Search 설치를 시작합니다"
echo "  ============================="
echo ""

# 1. 설치 폴더 생성
INSTALL_DIR="$HOME/lens-search"
mkdir -p "$INSTALL_DIR"

# 2. 스크립트 다운로드
curl -sL "https://raw.githubusercontent.com/eonun197/lens-search/main/lens.sh" -o "$INSTALL_DIR/lens.sh"
chmod +x "$INSTALL_DIR/lens.sh"

echo "  [OK] 스크립트 설치 완료: $INSTALL_DIR/lens.sh"
echo ""
echo "  ============================="
echo "   단축키 설정 방법"
echo "  ============================="
echo ""
echo "  1. Spotlight(Cmd+Space)에서 '단축어' 검색 후 열기"
echo "  2. + 버튼으로 새 단축어 만들기"
echo "  3. 'shell' 검색 → '셸 스크립트 실행' 선택"
echo "  4. 아래 경로를 스크립트에 붙여넣기:"
echo ""
echo "     $INSTALL_DIR/lens.sh"
echo ""
echo "  5. 단축어 이름을 'Lens Search'로 지정"
echo "  6. (i) 버튼 → '키보드 단축키 추가' → Cmd+Shift+L 입력"
echo ""
echo "  ============================="
echo "   주의사항"
echo "  ============================="
echo ""
echo "  - Chrome 브라우저 필수"
echo "  - 시스템 설정 → 개인정보 보호 및 보안 → 화면 기록"
echo "    → '단축어' 앱에 권한 허용 필요"
echo ""
echo "  설치가 완료되었습니다!"
echo ""
