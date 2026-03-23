#!/usr/bin/env python3
"""Style Catcher — 캡처하면 디자인 스타일을 분석하는 도구"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
import subprocess
import os
import time
import base64
import json
import urllib.request
import colorsys
from datetime import datetime
from pathlib import Path
import threading

GEMINI_API_KEY = "AIzaSyCACtyiAu-HIfiG34xpbJd4_FXnBDoyihw"

STYLES = {
    "DREAMCORE": {
        "description": "몽환적이고 초현실적인 감성",
        "color": "#C8A2C8",
        "keywords": ["몽환", "초현실", "파스텔", "안개", "비현실"]
    },
    "BITMAP": {
        "description": "픽셀과 디지털 노스탤지어",
        "color": "#00FF41",
        "keywords": ["픽셀", "도트", "8비트", "디지털", "노이즈"]
    },
    "MODERNISM": {
        "description": "기능적이고 구조적인 모던 디자인",
        "color": "#888888",
        "keywords": ["기하학", "그리드", "무채색", "구조", "타이포"]
    },
    "RETRO": {
        "description": "따뜻한 색감의 빈티지 감성",
        "color": "#D4A574",
        "keywords": ["따뜻한", "머스타드", "빈티지", "필름", "아날로그"]
    }
}


def analyze_with_gemini(image_path):
    """Gemini Vision으로 스타일 분석"""
    try:
        with open(image_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()

        prompt = """이 이미지의 디자인 스타일을 분석해줘.
아래 4가지 스타일 각각에 대한 매칭 점수(0~100)를 반드시 모두 알려줘.

1. DREAMCORE — 몽환적이고 초현실적인 감성 (파스텔, 안개, 비현실, 초현실, liminal space)
2. BITMAP — 픽셀과 디지털 노스탤지어 (픽셀아트, 도트, 8비트, 디지털 노이즈, 저해상도)
3. MODERNISM — 기능적이고 구조적인 모던 디자인 (기하학, 그리드, 무채색, 타이포그래피, 스위스 스타일)
4. RETRO — 따뜻한 색감의 빈티지 감성 (머스타드, 갈색, 필름, 아날로그, 70~80년대)

반드시 아래 형식으로만 답변해. 다른 텍스트 없이:
DREAMCORE:점수
BITMAP:점수
MODERNISM:점수
RETRO:점수"""

        body = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": b64}}
                ]
            }],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"]

        results = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                parts = line.split(":")
                name = parts[0].strip().upper()
                try:
                    score = int(parts[1].strip().replace("%", ""))
                except ValueError:
                    continue
                if name in STYLES:
                    results.append((name, min(100, max(0, score))))

        if len(results) >= 3:
            results.sort(key=lambda x: x[1], reverse=True)
            return results
        return None
    except:
        return None


def analyze_local(image_path):
    """로컬 색상 분석으로 스타일 판별 (API 없이)"""
    img = Image.open(image_path).convert('RGB').resize((150, 150))
    pixels = list(img.getdata())
    total = len(pixels)

    hsv_pixels = []
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        hsv_pixels.append((h * 360, s, v))

    avg_sat = sum(p[1] for p in hsv_pixels) / total
    avg_bri = sum(p[2] for p in hsv_pixels) / total
    bri_std = (sum((p[2] - avg_bri) ** 2 for p in hsv_pixels) / total) ** 0.5

    low_sat = sum(1 for p in hsv_pixels if p[1] < 0.15) / total
    high_sat = sum(1 for p in hsv_pixels if p[1] > 0.5) / total
    dark_pixels = sum(1 for p in hsv_pixels if p[2] < 0.3) / total
    bright_pixels = sum(1 for p in hsv_pixels if p[2] > 0.7) / total

    hue_counts = {}
    for h, s, v in hsv_pixels:
        if s > 0.1:
            bucket = int(h // 30) * 30
            hue_counts[bucket] = hue_counts.get(bucket, 0) + 1

    warm = sum(1 for h, s, v in hsv_pixels if s > 0.1 and (h < 60 or h > 330)) / max(1, sum(1 for p in hsv_pixels if p[1] > 0.1))
    cool = sum(1 for h, s, v in hsv_pixels if s > 0.1 and 180 < h < 300) / max(1, sum(1 for p in hsv_pixels if p[1] > 0.1))
    pink_purple = sum(1 for h, s, v in hsv_pixels if s > 0.2 and (280 < h < 360 or h < 10)) / total
    contrast = bri_std

    scores = {}

    # DREAMCORE: 파스텔 + 밝음 + 저대비 + 차가운톤
    pastel = sum(1 for h, s, v in hsv_pixels if 0.1 < s < 0.45 and v > 0.7) / total
    scores["DREAMCORE"] = pastel * 100 + cool * 30 + bright_pixels * 25 + (1 - contrast) * 20

    # BITMAP: 고채도 원색 + 높은 대비 + 적은 색상 수
    primary = sum(1 for h, s, v in hsv_pixels if s > 0.7 and v > 0.5) / total
    scores["BITMAP"] = primary * 60 + high_sat * 40 + contrast * 30 + (1 - len(hue_counts) / 12) * 30

    # MODERNISM: 무채색 + 저채도 + 높은 대비
    scores["MODERNISM"] = low_sat * 80 + (1 - avg_sat) * 40 + contrast * 20 + (1 - len(hue_counts) / 12) * 20

    # RETRO: 따뜻한 톤 + 중간 채도/밝기
    orange_brown = sum(1 for h, s, v in hsv_pixels if s > 0.15 and 15 < h < 50) / total
    scores["RETRO"] = warm * 50 + orange_brown * 100 + (1 - abs(avg_sat - 0.4)) * 20 + (1 - abs(avg_bri - 0.5)) * 20

    max_score = max(scores.values()) if max(scores.values()) > 0 else 1
    normalized = {k: min(100, int(v / max_score * 100)) for k, v in scores.items()}
    ranked = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    return ranked


class StyleCatcherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Style Catcher")
        self.root.geometry("320x550+50+50")
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#111111')
        self.root.resizable(True, True)
        self.root.minsize(300, 450)

        self.history_dir = Path.home() / "style-catcher" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        self.history = []
        self.build_ui()
        self.load_history()

    def build_ui(self):
        header = tk.Frame(self.root, bg='#111111', pady=14)
        header.pack(fill='x')

        tk.Label(header, text="Style Catcher",
                font=("Helvetica Neue", 20, "bold"),
                fg='white', bg='#111111').pack()
        tk.Label(header, text="캡처하면 디자인 스타일을 분석해요",
                font=("Helvetica Neue", 11),
                fg='#666', bg='#111111').pack(pady=(2, 0))

        btn_frame = tk.Frame(self.root, bg='#111111', pady=8)
        btn_frame.pack(fill='x', padx=16)

        self.search_btn = tk.Button(btn_frame, text="캡처해서 스타일 분석",
                                    font=("Helvetica Neue", 14, "bold"),
                                    fg='white', bg='#3b82f6',
                                    activebackground='#2563eb',
                                    activeforeground='white',
                                    relief='flat', cursor='hand2',
                                    pady=10, command=self.do_analyze)
        self.search_btn.pack(fill='x')

        self.status_label = tk.Label(self.root, text="",
                                     font=("Helvetica Neue", 12),
                                     fg='#3b82f6', bg='#111111')
        self.status_label.pack(pady=(4, 0))

        self.progress_canvas = Canvas(self.root, width=280, height=4,
                                       bg='#111111', highlightthickness=0)

        tk.Frame(self.root, bg='#222', height=1).pack(fill='x', padx=16, pady=(12, 8))

        tk.Label(self.root, text="분석 기록",
                font=("Helvetica Neue", 12, "bold"),
                fg='#555', bg='#111111', anchor='w').pack(fill='x', padx=16)

        container = tk.Frame(self.root, bg='#111111')
        container.pack(fill='both', expand=True, padx=8, pady=8)

        self.canvas = Canvas(container, bg='#111111', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient='vertical', command=self.canvas.yview)
        self.history_frame = tk.Frame(self.canvas, bg='#111111')

        self.history_frame.bind('<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0, 0), window=self.history_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        self.canvas.bind('<MouseWheel>',
            lambda e: self.canvas.yview_scroll(-1 * int(e.delta / 120), 'units'))

        tk.Button(self.root, text="기록 지우기",
                 font=("Helvetica Neue", 11), fg='#555', bg='#111111',
                 activebackground='#111111', activeforeground='#888',
                 relief='flat', cursor='hand2',
                 command=self.clear_history).pack(pady=(0, 8))

    def do_analyze(self):
        self.root.withdraw()
        time.sleep(0.3)

        capture_file = "/tmp/style_capture.png"
        try: os.remove(capture_file)
        except: pass

        subprocess.run(["/usr/sbin/screencapture", "-i", capture_file])
        self.root.deiconify()

        if not os.path.exists(capture_file): return
        if os.path.getsize(capture_file) == 0:
            try: os.remove(capture_file)
            except: pass
            return

        self.start_loading()
        threading.Thread(target=self.process, args=(capture_file,), daemon=True).start()

    def start_loading(self):
        self.loading_active = True
        self.loading_step = 0
        self.status_label.config(text="")
        self.progress_canvas.pack(pady=(2, 0))
        self.animate_loading()

    def animate_loading(self):
        if not self.loading_active: return
        self.loading_step += 1
        dots = "." * (self.loading_step % 4)
        self.status_label.config(text=f"스타일 분석 중{dots}", fg='#3b82f6')

        self.progress_canvas.delete("all")
        w = 280
        pos = (self.loading_step % 35) / 35
        bx = int(pos * w)
        bw = 70
        self.progress_canvas.create_rectangle(bx, 0, min(bx + bw, w), 4, fill='#3b82f6', outline='')
        if bx + bw > w:
            self.progress_canvas.create_rectangle(0, 0, (bx + bw) - w, 4, fill='#3b82f6', outline='')
        self.root.after(100, self.animate_loading)

    def stop_loading(self):
        self.loading_active = False
        self.progress_canvas.pack_forget()
        self.status_label.config(text="분석 완료!", fg='#4ade80')
        self.root.after(2000, lambda: self.status_label.config(text=""))

    def process(self, capture_file):
        try:
            # Gemini 우선, 실패 시 로컬
            results = analyze_with_gemini(capture_file)
            if results is None:
                results = analyze_local(capture_file)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            thumb_path = self.history_dir / f"{timestamp}.png"
            img = Image.open(capture_file)
            img.thumbnail((260, 160))
            img.save(str(thumb_path))

            result_text = "\n".join([f"{n}: {s}%" for n, s in results])
            (self.history_dir / f"{timestamp}.txt").write_text(result_text)

            self.root.after(0, lambda: self.show_result(str(thumb_path), timestamp, results))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"오류: {e}", fg='#ef4444'))
        finally:
            try: os.remove(capture_file)
            except: pass

    def show_result(self, thumb_path, timestamp, results):
        self.stop_loading()
        self.add_history_item(thumb_path, timestamp, results)

    def add_history_item(self, thumb_path, timestamp, results=None):
        card = tk.Frame(self.history_frame, bg='#1a1a1a',
                       highlightbackground='#2a2a2a', highlightthickness=1)
        card.pack(fill='x', pady=5, padx=4)

        try:
            img = Image.open(thumb_path)
            img.thumbnail((260, 120))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(card, image=photo, bg='#1a1a1a')
            img_label.image = photo
            img_label.pack(padx=8, pady=(8, 4))
        except: pass

        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        tk.Label(card, text=dt.strftime("%m/%d %H:%M"),
                font=("Helvetica Neue", 9), fg='#555', bg='#1a1a1a').pack(pady=(0, 4))

        if results:
            top_name, top_score = results[0]
            style_info = STYLES.get(top_name, {})

            tk.Label(card, text=top_name,
                    font=("Helvetica Neue", 22, "bold"),
                    fg=style_info.get("color", "#fff"), bg='#1a1a1a').pack(pady=(4, 0))
            tk.Label(card, text=style_info.get("description", ""),
                    font=("Helvetica Neue", 10),
                    fg='#888', bg='#1a1a1a').pack(pady=(0, 6))

            for name, score in results:
                s_info = STYLES.get(name, {})
                s_color = s_info.get("color", "#666")

                bar_frame = tk.Frame(card, bg='#1a1a1a')
                bar_frame.pack(fill='x', padx=12, pady=1)

                tk.Label(bar_frame, text=name, font=("Helvetica Neue", 9, "bold"),
                        fg='#aaa', bg='#1a1a1a', width=8, anchor='w').pack(side='left')

                bar_bg = tk.Canvas(bar_frame, bg='#222', height=8, highlightthickness=0)
                bar_bg.pack(side='left', fill='x', expand=True, padx=(4, 4))

                bar_width = max(2, int(150 * score / 100))
                bar_bg.create_rectangle(0, 0, bar_width, 8, fill=s_color, outline='')

                tk.Label(bar_frame, text=f"{score}%", font=("Helvetica Neue", 9),
                        fg='#666', bg='#1a1a1a', width=4, anchor='e').pack(side='right')

            keywords = style_info.get("keywords", [])
            if keywords:
                kw_text = "  ".join([f"#{k}" for k in keywords])
                tk.Label(card, text=kw_text, font=("Helvetica Neue", 9),
                        fg='#555', bg='#1a1a1a').pack(pady=(6, 8))

        self.history.append({'path': thumb_path, 'timestamp': timestamp, 'frame': card})
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def load_history(self):
        thumbs = sorted(self.history_dir.glob("*.png"))
        for thumb in thumbs[-10:]:
            timestamp = thumb.stem
            result_file = self.history_dir / f"{timestamp}.txt"
            results = None
            if result_file.exists():
                results = []
                for line in result_file.read_text().strip().split("\n"):
                    parts = line.split(": ")
                    if len(parts) == 2:
                        results.append((parts[0], int(parts[1].replace("%", ""))))
            self.add_history_item(str(thumb), timestamp, results)

    def clear_history(self):
        for item in self.history:
            item['frame'].destroy()
            try:
                os.remove(item['path'])
                txt = item['path'].replace('.png', '.txt')
                if os.path.exists(txt): os.remove(txt)
            except: pass
        self.history = []

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = StyleCatcherApp()
    app.run()
