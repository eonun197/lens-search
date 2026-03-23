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
        loading.classList.remove('visible');
        results.innerHTML = `<div style="color:#ef4444;font-size:12px;text-align:center;padding:20px;">분석 실패: ${e.message}<br><br><button class="retry-btn" onclick="location.reload()">다시 시도</button></div>`;
        results.classList.add('visible');
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
