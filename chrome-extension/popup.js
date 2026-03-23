const GEMINI_KEY = "AIzaSyCACtyiAu-HIfiG34xpbJd4_FXnBDoyihw";

const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

uploadArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleImage(e.target.files[0]); });

uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) handleImage(file);
});

document.addEventListener('paste', (e) => {
    const items = e.clipboardData.items;
    for (const item of items) {
        if (item.type.startsWith('image/')) { handleImage(item.getAsFile()); break; }
    }
});

function handleImage(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const src = e.target.result;
        uploadArea.classList.add('has-image');
        document.getElementById('uploadContent').innerHTML =
            `<img src="${src}" class="upload-preview"><div class="change-text">클릭하여 변경</div>`;
        analyzeFont(src);
    };
    reader.readAsDataURL(file);
}

async function analyzeFont(dataUrl) {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    loading.classList.add('visible');
    results.classList.remove('visible');

    const base64 = dataUrl.split(',')[1];

    try {
        const analysis = await callGemini(base64);
        loading.classList.remove('visible');
        showResults(analysis, dataUrl);
    } catch (e) {
        // API 실패 시 로컬 분석
        const localResult = await analyzeLocal(dataUrl);
        loading.classList.remove('visible');
        showResults(localResult, dataUrl);
    }
}

async function callGemini(base64) {
    const prompt = `너는 타이포그래피 전문가야. 이 이미지에서 보이는 텍스트의 폰트를 분석하고 찾아줘.

반드시 아래 형식으로만 답변해. 다른 텍스트 없이:

FONT_NAME:
(가장 유사한 폰트 이름, 확신도가 높은 것)

SIMILAR_FONTS:
폰트1, 폰트2, 폰트3

CLASSIFICATION:
(세리프 / 산세리프 / 슬래브세리프 / 스크립트 / 디스플레이 / 모노스페이스 중 하나)

WEIGHT:
(Thin / Light / Regular / Medium / Bold / Black 중 하나)

FEATURES:
(이 폰트의 시각적 특징을 한 줄로 — 자간, 둥근 정도, 획의 대비, x높이 등)

MOOD:
(이 폰트가 주는 분위기를 한 줄로)

USE_CASE:
(이 폰트가 적합한 사용 상황을 한 줄로 — 제목용, 본문용, 로고용 등)

FREE_ALTERNATIVE:
(무료로 사용 가능한 대안 폰트 이름과 다운로드 가능한 곳)

텍스트가 보이지 않으면 FONT_NAME에 "텍스트를 찾을 수 없습니다"라고 답변해.`;

    const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_KEY}`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{ parts: [{ text: prompt }, { inline_data: { mime_type: 'image/png', data: base64 } }] }],
                generationConfig: { temperature: 0.3, maxOutputTokens: 600 }
            })
        }
    );
    if (!resp.ok) throw new Error('API 한도 초과 — 잠시 후 다시 시도해주세요');
    const data = await resp.json();
    return data.candidates[0].content.parts[0].text;
}

// ===== 로컬 폰트 분석 (API 없이) =====
const FONT_DB = [
    { name: "Helvetica", classification: "산세리프", weight: "Regular", features: "균일한 획 굵기, 중립적이고 깔끔한 형태, 닫힌 자형", mood: "깔끔하고 모던하며 신뢰감 있는", useCase: "UI, 기업 브랜딩, 본문", free: "Inter (Google Fonts)", serif: false, geometric: false, contrast: "low", round: false },
    { name: "Futura", classification: "산세리프", weight: "Medium", features: "기하학적 원형 기반, 균일한 획, 높은 x높이", mood: "미래적이고 세련된", useCase: "로고, 제목, 패션 브랜딩", free: "Jost (Google Fonts)", serif: false, geometric: true, contrast: "low", round: true },
    { name: "Garamond", classification: "세리프", weight: "Regular", features: "가는 세리프, 높은 획 대비, 우아한 곡선", mood: "클래식하고 우아하며 문학적인", useCase: "책 본문, 에디토리얼, 고급 브랜딩", free: "EB Garamond (Google Fonts)", serif: true, geometric: false, contrast: "high", round: false },
    { name: "Bodoni", classification: "세리프", weight: "Bold", features: "극단적인 획 대비, 가는 헤어라인 세리프, 수직 축", mood: "강렬하고 고급스러우며 패셔너블한", useCase: "패션 잡지 제목, 럭셔리 브랜딩", free: "Libre Bodoni (Google Fonts)", serif: true, geometric: false, contrast: "extreme", round: false },
    { name: "Gotham", classification: "산세리프", weight: "Bold", features: "기하학적이면서 따뜻한 형태, 넓은 자폭, 높은 x높이", mood: "신뢰감 있고 현대적이며 힘 있는", useCase: "제목, 광고, 정치 캠페인", free: "Nunito Sans (Google Fonts)", serif: false, geometric: true, contrast: "low", round: false },
    { name: "Baskerville", classification: "세리프", weight: "Regular", features: "날카로운 세리프, 적절한 획 대비, 열린 자형", mood: "격식 있고 지적이며 전통적인", useCase: "학술 문서, 에디토리얼, 본문", free: "Libre Baskerville (Google Fonts)", serif: true, geometric: false, contrast: "medium", round: false },
    { name: "Avenir", classification: "산세리프", weight: "Regular", features: "기하학적이면서 휴머니스트 특성, 부드러운 곡선", mood: "부드럽고 모던하며 친근한", useCase: "앱 UI, 브랜딩, 제목/본문 겸용", free: "Nunito (Google Fonts)", serif: false, geometric: true, contrast: "low", round: true },
    { name: "Courier", classification: "모노스페이스", weight: "Regular", features: "고정 너비, 타자기 느낌, 세리프 있음", mood: "레트로하고 기술적이며 코딩 느낌", useCase: "코드, 타자기 감성, 레트로 디자인", free: "Courier Prime (Google Fonts)", serif: true, geometric: false, contrast: "low", round: false },
    { name: "나눔고딕", classification: "산세리프", weight: "Regular", features: "깔끔한 한글 고딕, 부드러운 곡선, 높은 가독성", mood: "깔끔하고 친근하며 현대적인", useCase: "웹, 앱, 본문, 프레젠테이션", free: "나눔고딕 (Google Fonts)", serif: false, geometric: false, contrast: "low", round: true },
    { name: "나눔명조", classification: "세리프", weight: "Regular", features: "전통적인 한글 명조, 가로획 가늘고 세로획 굵음", mood: "차분하고 격식 있으며 문학적인", useCase: "본문, 소설, 에디토리얼", free: "나눔명조 (Google Fonts)", serif: true, geometric: false, contrast: "high", round: false },
    { name: "Pretendard", classification: "산세리프", weight: "Regular", features: "모던한 한글 고딕, 균일한 획, 높은 x높이", mood: "테크니컬하고 깔끔하며 프로페셔널한", useCase: "UI, 웹, 앱, 브랜딩", free: "Pretendard (GitHub)", serif: false, geometric: false, contrast: "low", round: false },
    { name: "Brush Script", classification: "스크립트", weight: "Regular", features: "손으로 쓴 듯한 흘림체, 기울어진 형태, 연결된 글자", mood: "캐주얼하고 친근하며 자유로운", useCase: "초대장, 카드, 캐주얼 브랜딩", free: "Dancing Script (Google Fonts)", serif: false, geometric: false, contrast: "medium", round: true },
];

function analyzeLocal(dataUrl) {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.onload = () => {
            canvas.width = 100; canvas.height = 100;
            ctx.drawImage(img, 0, 0, 100, 100);
            const data = ctx.getImageData(0, 0, 100, 100).data;

            let totalBri = 0, darkPx = 0, brightPx = 0, edgeCount = 0;
            const total = 10000;

            for (let i = 0; i < data.length; i += 4) {
                const bri = (data[i] + data[i+1] + data[i+2]) / 3 / 255;
                totalBri += bri;
                if (bri < 0.3) darkPx++;
                if (bri > 0.7) brightPx++;
            }

            // 가로 에지 검출 (세리프 감지용)
            for (let y = 0; y < 100; y++) {
                for (let x = 1; x < 99; x++) {
                    const idx = (y * 100 + x) * 4;
                    const curr = data[idx];
                    const prev = data[idx - 4];
                    if (Math.abs(curr - prev) > 80) edgeCount++;
                }
            }

            const avgBri = totalBri / total;
            const darkRatio = darkPx / total;
            const edgeRatio = edgeCount / total;

            // 특성 추론
            const isSerif = edgeRatio > 0.08;
            const isBold = darkRatio > 0.4;
            const isLight = darkRatio < 0.15;
            const isHighContrast = edgeRatio > 0.12;

            // 매칭
            let best = FONT_DB[0];
            let bestScore = 0;

            for (const font of FONT_DB) {
                let score = 0;
                if (font.serif === isSerif) score += 30;
                if (font.contrast === 'high' && isHighContrast) score += 20;
                if (font.contrast === 'low' && !isHighContrast) score += 20;
                if (font.weight === 'Bold' && isBold) score += 15;
                if (font.weight === 'Regular' && !isBold && !isLight) score += 10;
                if (font.weight === 'Light' && isLight) score += 15;
                score += Math.random() * 10; // 약간의 다양성

                if (score > bestScore) { bestScore = score; best = font; }
            }

            // 유사 폰트 3개
            const similar = FONT_DB
                .filter(f => f.name !== best.name && f.serif === best.serif)
                .slice(0, 3)
                .map(f => f.name);

            const result = `FONT_NAME:\n${best.name}\nSIMILAR_FONTS:\n${similar.join(', ')}\nCLASSIFICATION:\n${best.classification}\nWEIGHT:\n${best.weight}\nFEATURES:\n${best.features}\nMOOD:\n${best.mood}\nUSE_CASE:\n${best.useCase}\nFREE_ALTERNATIVE:\n${best.free}`;

            resolve(result);
        };
        img.src = dataUrl;
    });
}

function showResults(text, imageSrc) {
    const results = document.getElementById('results');

    const get = (key) => {
        const regex = new RegExp(key + ':\\s*\\n?(.+)', 'i');
        const match = text.match(regex);
        return match ? match[1].trim() : '';
    };

    const fontName = get('FONT_NAME');
    const similar = get('SIMILAR_FONTS');
    const classification = get('CLASSIFICATION');
    const weight = get('WEIGHT');
    const features = get('FEATURES');
    const mood = get('MOOD');
    const useCase = get('USE_CASE');
    const freeAlt = get('FREE_ALTERNATIVE');

    const classColors = {
        '세리프': '#D4A574', '산세리프': '#888', '슬래브세리프': '#D4A574',
        '스크립트': '#C8A2C8', '디스플레이': '#FF69B4', '모노스페이스': '#00FF41'
    };
    const classColor = classColors[classification] || '#3b82f6';

    const similarHtml = similar ? similar.split(',').map(f =>
        `<span class="keyword">${f.trim()}</span>`
    ).join('') : '';

    results.innerHTML = `
        <img src="${imageSrc}" class="result-image">

        <div style="font-size:22px;font-weight:800;color:${classColor}">${fontName}</div>

        ${classification ? `<div style="display:flex;gap:6px;margin:8px 0;">
            <span class="keyword" style="background:${classColor}22;color:${classColor}">${classification}</span>
            ${weight ? `<span class="keyword">${weight}</span>` : ''}
        </div>` : ''}

        ${similar ? `<div class="section-title">유사 폰트</div>
        <div class="keywords">${similarHtml}</div>` : ''}

        ${features ? `<div class="analysis-card">
            <div class="analysis-label" style="color:#38bdf8;">🔤 폰트 특징</div>
            <div class="analysis-text">${features}</div>
        </div>` : ''}

        ${mood ? `<div class="analysis-card">
            <div class="analysis-label" style="color:#a78bfa;">✨ 분위기</div>
            <div class="analysis-text">${mood}</div>
        </div>` : ''}

        ${useCase ? `<div class="analysis-card">
            <div class="analysis-label" style="color:#f472b6;">💡 추천 용도</div>
            <div class="analysis-text">${useCase}</div>
        </div>` : ''}

        ${freeAlt ? `<div class="analysis-card">
            <div class="analysis-label" style="color:#4ade80;">🆓 무료 대안</div>
            <div class="analysis-text">${freeAlt}</div>
        </div>` : ''}

        <button class="retry-btn" id="retryBtn">다른 이미지 분석하기</button>
    `;
    results.classList.add('visible');

    document.getElementById('retryBtn').addEventListener('click', () => {
        results.classList.remove('visible');
        uploadArea.classList.remove('has-image');
        document.getElementById('uploadContent').innerHTML =
            `<div class="upload-icon">🔍</div><div class="upload-text"><strong>이미지를 드래그</strong>하거나 클릭</div>`;
    });
}
