#!/usr/bin/env python3
"""Keyword Catcher — 캡처하면 관련 키워드를 뽑아주는 도구"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
import subprocess
import os
import time
import base64
import json
import urllib.request
from datetime import datetime
from pathlib import Path
import threading

GEMINI_API_KEY = "AIzaSyCACtyiAu-HIfiG34xpbJd4_FXnBDoyihw"


def extract_keywords(image_path):
    """Gemini Vision으로 이미지에서 키워드 추출"""
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()

    prompt = """이 이미지를 분석해서 디자인/시각적 관점에서 핵심 키워드를 뽑아줘.

다음 카테고리별로 키워드를 추출해:
색감: (이미지의 주요 색상과 색감 느낌, 3~5개)
분위기: (이미지가 주는 감정/무드, 3~5개)
스타일: (디자인 스타일이나 트렌드, 2~3개)
소재: (이미지에 보이는 주요 요소/오브젝트, 3~5개)

반드시 아래 형식으로만 답변해:
색감: 키워드1, 키워드2, 키워드3
분위기: 키워드1, 키워드2, 키워드3
스타일: 키워드1, 키워드2, 키워드3
소재: 키워드1, 키워드2, 키워드3"""

    body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": b64}}
            ]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 500
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    req = urllib.request.Request(url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"]

    # 파싱
    result = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            if key in ["색감", "분위기", "스타일", "소재"]:
                keywords = [k.strip() for k in val.split(",") if k.strip()]
                result[key] = keywords

    return result


CATEGORIES = {
    "색감": {"color": "#f472b6", "emoji": "🎨"},
    "분위기": {"color": "#a78bfa", "emoji": "✨"},
    "스타일": {"color": "#38bdf8", "emoji": "💎"},
    "소재": {"color": "#4ade80", "emoji": "📦"},
}


class KeywordCatcherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Keyword Catcher")
        self.root.geometry("340x580+50+50")
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#0f0f0f')
        self.root.resizable(True, True)
        self.root.minsize(300, 450)

        self.history_dir = Path.home() / "keyword-catcher" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        self.build_ui()

    def build_ui(self):
        # 헤더
        header = tk.Frame(self.root, bg='#0f0f0f', pady=14)
        header.pack(fill='x')

        tk.Label(header, text="Keyword Catcher",
                font=("Helvetica Neue", 20, "bold"),
                fg='white', bg='#0f0f0f').pack()

        tk.Label(header, text="캡처하면 키워드를 뽑아드려요",
                font=("Helvetica Neue", 11),
                fg='#666', bg='#0f0f0f').pack(pady=(2, 0))

        # 캡처 버튼
        btn_frame = tk.Frame(self.root, bg='#0f0f0f', pady=8)
        btn_frame.pack(fill='x', padx=20)

        self.capture_btn = tk.Button(btn_frame, text="캡처해서 키워드 추출",
                                     font=("Helvetica Neue", 14, "bold"),
                                     fg='white', bg='#3b82f6',
                                     activebackground='#2563eb',
                                     activeforeground='white',
                                     relief='flat', cursor='hand2',
                                     pady=10,
                                     command=self.do_capture)
        self.capture_btn.pack(fill='x')

        # 로딩
        self.loading_frame = tk.Frame(self.root, bg='#0f0f0f')
        self.loading_label = tk.Label(self.loading_frame, text="",
                                      font=("Helvetica Neue", 12),
                                      fg='#3b82f6', bg='#0f0f0f')
        self.loading_label.pack(pady=(10, 4))
        self.progress_canvas = Canvas(self.loading_frame, width=280, height=4,
                                       bg='#1a1a1a', highlightthickness=0)
        self.progress_canvas.pack(pady=(0, 6))

        # 결과 스크롤
        container = tk.Frame(self.root, bg='#0f0f0f')
        container.pack(fill='both', expand=True, padx=8, pady=4)

        self.result_canvas = Canvas(container, bg='#0f0f0f', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient='vertical',
                                      command=self.result_canvas.yview)
        self.result_frame = tk.Frame(self.result_canvas, bg='#0f0f0f')

        self.result_frame.bind('<Configure>',
            lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox('all')))

        self.result_canvas.create_window((0, 0), window=self.result_frame, anchor='nw')
        self.result_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.result_canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        self.result_canvas.bind('<MouseWheel>',
            lambda e: self.result_canvas.yview_scroll(-1 * int(e.delta / 120), 'units'))

    def do_capture(self):
        self.root.withdraw()
        time.sleep(0.3)

        capture_file = "/tmp/kw_capture.png"
        try:
            os.remove(capture_file)
        except FileNotFoundError:
            pass

        subprocess.run(["/usr/sbin/screencapture", "-i", capture_file])
        self.root.deiconify()

        if not os.path.exists(capture_file) or os.path.getsize(capture_file) == 0:
            try:
                os.remove(capture_file)
            except:
                pass
            return

        self.start_loading()
        threading.Thread(target=self.process, args=(capture_file,), daemon=True).start()

    def start_loading(self):
        self.loading_frame.pack(fill='x', padx=20, after=self.capture_btn.master)
        self.loading_active = True
        self.loading_step = 0
        self.animate_loading()

    def animate_loading(self):
        if not self.loading_active:
            return
        self.loading_step += 1
        dots = "." * (self.loading_step % 4)
        self.loading_label.config(text=f"키워드를 뽑는 중{dots}")

        # 프로그레스 바
        self.progress_canvas.delete("all")
        w = 280
        pos = (self.loading_step % 35) / 35
        bx = int(pos * w)
        bw = 70
        self.progress_canvas.create_rectangle(bx, 0, min(bx + bw, w), 4,
                                               fill='#3b82f6', outline='')
        if bx + bw > w:
            self.progress_canvas.create_rectangle(0, 0, (bx + bw) - w, 4,
                                                   fill='#3b82f6', outline='')
        self.root.after(100, self.animate_loading)

    def stop_loading(self):
        self.loading_active = False
        self.loading_frame.pack_forget()

    def process(self, capture_file):
        try:
            result = extract_keywords(capture_file)
            # 썸네일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            thumb_path = self.history_dir / f"{timestamp}.png"
            img = Image.open(capture_file)
            img.thumbnail((280, 140))
            img.save(str(thumb_path))

            self.root.after(0, lambda: self.show_results(result, str(thumb_path)))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
        finally:
            try:
                os.remove(capture_file)
            except:
                pass

    def show_error(self, msg):
        self.stop_loading()
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        tk.Label(self.result_frame, text=f"오류: {msg}",
                font=("Helvetica Neue", 11), fg='#ef4444',
                bg='#0f0f0f', wraplength=280).pack(pady=20)

    def show_results(self, result, thumb_path):
        self.stop_loading()

        # 기존 결과 위에 새 결과 추가 (기록 쌓기)
        # 구분선
        if self.result_frame.winfo_children():
            tk.Frame(self.result_frame, bg='#333', height=1).pack(fill='x', padx=8, pady=8)

        # 썸네일
        try:
            img = Image.open(thumb_path)
            img.thumbnail((280, 130))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(self.result_frame, image=photo, bg='#0f0f0f')
            img_label.image = photo
            img_label.pack(padx=8, pady=(8, 6))
        except:
            pass

        # 시간
        tk.Label(self.result_frame,
                text=datetime.now().strftime("%m/%d %H:%M"),
                font=("Helvetica Neue", 9), fg='#555',
                bg='#0f0f0f').pack(pady=(0, 6))

        # 카테고리별 키워드
        for cat_name in ["색감", "분위기", "스타일", "소재"]:
            keywords = result.get(cat_name, [])
            if not keywords:
                continue

            cat_info = CATEGORIES[cat_name]

            cat_frame = tk.Frame(self.result_frame, bg='#151515',
                               highlightbackground='#222', highlightthickness=1)
            cat_frame.pack(fill='x', padx=8, pady=3)

            # 카테고리 헤더
            tk.Label(cat_frame,
                    text=f"{cat_info['emoji']}  {cat_name}",
                    font=("Helvetica Neue", 12, "bold"),
                    fg=cat_info['color'], bg='#151515').pack(anchor='w', padx=10, pady=(8, 4))

            # 키워드 태그들
            tag_frame = tk.Frame(cat_frame, bg='#151515')
            tag_frame.pack(fill='x', padx=10, pady=(0, 8))

            for kw in keywords:
                tag = tk.Label(tag_frame, text=f" {kw} ",
                              font=("Helvetica Neue", 11),
                              fg=cat_info['color'], bg='#1e1e1e',
                              relief='flat', padx=8, pady=3)
                tag.pack(side='left', padx=(0, 4), pady=2)

                # 클릭하면 복사
                def make_copy(keyword=kw, label=tag, color=cat_info['color']):
                    def copy(e):
                        self.root.clipboard_clear()
                        self.root.clipboard_append(keyword)
                        label.config(fg='#4ade80', text=f" ✓ {keyword} ")
                        self.root.after(1000, lambda: label.config(fg=color, text=f" {keyword} "))
                    return copy
                tag.bind('<Button-1>', make_copy())
                tag.config(cursor='hand2')

        # 전체 복사 버튼
        all_keywords = []
        for cat in ["색감", "분위기", "스타일", "소재"]:
            all_keywords.extend(result.get(cat, []))

        if all_keywords:
            def copy_all():
                self.root.clipboard_clear()
                self.root.clipboard_append(", ".join(all_keywords))
                copy_all_btn.config(text="전체 복사됨!", fg='#4ade80')
                self.root.after(1500, lambda: copy_all_btn.config(text="전체 키워드 복사", fg='#888'))

            copy_all_btn = tk.Button(self.result_frame, text="전체 키워드 복사",
                                    font=("Helvetica Neue", 11),
                                    fg='#888', bg='#1a1a1a',
                                    activebackground='#222',
                                    activeforeground='#fff',
                                    relief='flat', cursor='hand2',
                                    command=copy_all)
            copy_all_btn.pack(pady=(6, 10))

        self.result_canvas.update_idletasks()
        self.result_canvas.yview_moveto(1.0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = KeywordCatcherApp()
    app.run()
