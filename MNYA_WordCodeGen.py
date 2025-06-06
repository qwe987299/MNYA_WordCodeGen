import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import tkinter.font as tkFont
import ttkbootstrap as ttk
from TkToolTip import ToolTip
from ttkbootstrap.constants import *
import pyperclip
import os
import json
import win32api
import webbrowser
import datetime
import subprocess
import sys

# 匯入 batch_tools 各模組
from batch_tools.image_tools import add_watermark, merge_images, split_and_merge_image, center_process_images
from batch_tools.video_tools import add_video_watermark, video_repeat_fade
from batch_tools.audio_tools import merge_audio
from batch_tools.gpx_tools import convert_gpx_files
from batch_tools.subtitle_tools import sub2txt
from batch_tools.webp_tools import webp_to_mp4

# 子視窗
from video_repeat_fade_window import open_video_repeat_fade_window
from text_batch_replace_window import open_text_batch_replace_window

# 測試指令：python MNYA_WordCodeGen.py
# 打包指令：pyinstaller --onefile --icon=icon.ico --noconsole MNYA_WordCodeGen.py

# 應用配置
WINDOW_WIDTH = 435  # 寬度
WINDOW_HEIGHT = 430  # 高度
APP_NAME = "萌芽系列網站圖文原始碼生成器"  # 應用名稱
VERSION = "V1.6.0"  # 版本
BUILD_DIR = "build"  # 輸出目錄

# 配置檔案名稱
CONFIG_FILENAME = "config.json"


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # 讀取配置檔案
        self.config_path = CONFIG_FILENAME
        self.is_minimized = tk.BooleanVar(value=False)
        self.default_config()  # 首次啟動建立配置檔案
        self.load_window_position()

        # 設置視窗大小和位置
        root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{self.window_x}+{self.window_y}")

        # 設置關閉視窗時的回調函數
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tabControl = ttk.Notebook(self)
        # 頁籤 1
        self.tab1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab1, text='主要功能')
        # 頁籤 2
        self.tab2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab2, text='批次處理')
        # 頁籤 3
        self.tab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab3, text='複製取用')
        # 頁籤 4
        self.tab4 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab4, text='快速連結')
        # 設定頁籤
        self.tabSet = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tabSet, text='設定')
        # 頁籤 0
        self.tab0 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab0, text='關於程式')
        # 設定預設進入頁籤 1
        self.tabControl.pack(expand=1, fill="both")
        self.master = master
        self.master.title(APP_NAME + " " + VERSION)
        self.pack()
        self.create_widgets()
        self.load_last_article()
        self.batch_widgets()
        self.copy_widgets()
        self.links_widgets()
        self.setting_widgets()
        self.about_widgets()

        # 設定視窗的最小化狀態
        self.master.after(1, self.minimized)

        # 限制子視窗只能同時一個
        self.video_repeat_fade_win = None
        self.text_batch_replace_win = None

    # 視窗最小化功能
    def minimized(self):
        if self.is_minimized.get():
            self.master.iconify()

    def load_window_position(self):
        # 如果配置檔案存在，讀取視窗位置
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                self.window_x = config.get("x", 0)
                self.window_y = config.get("y", 0)
                self.is_minimized.set(config.get("is_minimized", False))
        else:
            # 如果配置檔案不存在，使用預設位置
            self.window_x = 0
            self.window_y = 0
            self.is_minimized = False

        # 獲取所有顯示器的資訊
        monitors = win32api.EnumDisplayMonitors()
        max_x = 0
        max_y = 0
        for monitor in monitors:
            monitor_info = win32api.GetMonitorInfo(monitor[0])
            work_area = monitor_info["Work"]
            if work_area[2] > max_x:
                max_x = work_area[2]
            if work_area[3] > max_y:
                max_y = work_area[3]

        # 確保視窗位置在所有顯示器範圍內
        if self.window_x < 0:
            self.window_x = 0
        elif self.window_x > max_x - WINDOW_WIDTH:
            self.window_x = max_x - WINDOW_WIDTH
        if self.window_y < 0:
            self.window_y = 0
        elif self.window_y > max_y - WINDOW_HEIGHT:
            self.window_y = max_y - WINDOW_HEIGHT

    def on_close(self):
        # 保存配置
        self.save_on_close()

        # 關閉視窗
        root.destroy()

    def save_on_close(self):
        with open(self.config_path, "r") as f:
            config = json.load(f)
            # 更新需要修改的鍵值
            config["x"] = root.winfo_x()
            config["y"] = root.winfo_y()

            # 保存到配置檔案
            with open(self.config_path, "w") as f:
                json.dump(config, f)

    def default_config(self):
        # 如果配置檔案不存在，使用預設值
        if not os.path.exists(self.config_path):
            config = {
                "x": root.winfo_x(),
                "y": root.winfo_y(),
                "is_minimized": False
            }
            # 保存全新配置檔
            with open(self.config_path, "w") as f:
                json.dump(config, f)

    def load_repeat_fade_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("video_repeat_fade", {})
        return {}

    def save_repeat_fade_config(self, config_dict):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        config["video_repeat_fade"] = config_dict
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)

    def load_text_batch_replace_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("text_batch_replace", {})
        return {}

    def save_text_batch_replace_config(self, config_dict):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        config["text_batch_replace"] = config_dict
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)

    def center_child_window(self, child_win, width, height):
        # 取得主視窗座標與大小
        self.master.update_idletasks()
        x = self.master.winfo_x()
        y = self.master.winfo_y()
        w = self.master.winfo_width()
        h = self.master.winfo_height()
        # 計算新視窗的左上座標（讓它在主視窗中央）
        new_x = x + (w - width) // 2
        new_y = y + (h - height) // 2
        child_win.geometry(f"{width}x{height}+{new_x}+{new_y}")

    def open_video_repeat_fade_window(self):
        # 檢查視窗有沒有被開啟過
        if self.video_repeat_fade_win is not None:
            try:
                if self.video_repeat_fade_win.winfo_exists():
                    self.video_repeat_fade_win.lift()
                    self.video_repeat_fade_win.focus_force()
                    return
            except:
                self.video_repeat_fade_win = None
        # 建立新視窗
        cfg = self.load_repeat_fade_config()
        self.video_repeat_fade_win = open_video_repeat_fade_window(
            app=self,
            parent=self.master,
            config=cfg,
            save_config_func=self.save_repeat_fade_config,
            video_repeat_fade_func=video_repeat_fade,
            on_close=lambda: setattr(self, 'video_repeat_fade_win', None)
        )

    def open_text_batch_replace_window(self):
        # 檢查視窗是否已開啟
        if self.text_batch_replace_win is not None:
            try:
                if self.text_batch_replace_win.winfo_exists():
                    self.text_batch_replace_win.lift()
                    self.text_batch_replace_win.focus_force()
                    return
            except:
                self.text_batch_replace_win = None
        cfg = self.load_text_batch_replace_config()
        self.text_batch_replace_win = open_text_batch_replace_window(
            app=self,
            parent=self.master,
            config=cfg,
            save_config_func=self.save_text_batch_replace_config,
            on_close=lambda: setattr(self, 'text_batch_replace_win', None)
        )

    ###############
    ### 主要功能 ###
    ###############

    def create_widgets(self):

        # 字體設定
        font14 = tkFont.Font(family="微軟正黑體", size=14)
        font = tkFont.Font(family="微軟正黑體", size=13)
        style = ttk.Style()

        # 萌芽系列網站按鈕組
        self.sites = [("💻 萌芽綜合天地", "cc"),
                      ("⛰ 萌芽爬山網", "k3"),
                      ("🍹 萌芽悠遊網", "yo"),
                      ("🌏 萌芽地科網", "es"),
                      ("🎵 萌芽音樂網", "ms"),
                      ("🖼 萌芽二次元", "2d"),
                      ("🎮 萌芽Game網", "games")]
        self.site_var = tk.StringVar(value=self.sites[0][1])
        site_frame = tk.Frame(self.tab1)
        site_frame.pack(side=tk.LEFT, padx=10, pady=5)
        for site, code in self.sites:
            tk.Radiobutton(site_frame, text=site, variable=self.site_var, value=code, font=font14,
                           indicatoron=False, width=15, height=1, command=self.load_last_article).pack(anchor=tk.W)

        include_frame = tk.Frame(site_frame)
        include_frame.pack(padx=1, pady=10)

        self.include_previous_var = tk.BooleanVar(value=True)
        tk.Checkbutton(include_frame, text="包含前文",
                       variable=self.include_previous_var, font=font14).pack()

        self.include_symbol_up = tk.BooleanVar(value=True)
        tk.Checkbutton(include_frame, text="包含\"▲\"",
                       variable=self.include_symbol_up, font=font14,
                       command=lambda: self.update_checkbutton_state(self.include_symbol_up)).pack()

        self.include_symbol_down = tk.BooleanVar(value=False)
        tk.Checkbutton(include_frame, text="包含\"▼\"",
                       variable=self.include_symbol_down, font=font14,
                       command=lambda: self.update_checkbutton_state(self.include_symbol_down)).pack()

        # 年份、文章編號、文章圖片數、圖片寬度、圖片高度輸入框
        input_frame = tk.Frame(self.tab1)
        input_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        self.year_var = tk.StringVar(value=str(datetime.datetime.now().year))
        self.article_var = tk.StringVar(value="1")
        self.image_num_var = tk.StringVar(value="10")
        self.image_width_var = tk.StringVar(value="1024")
        self.image_height_var = tk.StringVar(value="768")

        tk.Label(input_frame, text="年份：", font=font).pack(pady=2)
        entry_year = tk.Entry(
            input_frame, textvariable=self.year_var, font=font)
        entry_year.pack()
        self.bind_numeric_entry(entry_year, self.year_var)

        tk.Label(input_frame, text="文章編號：", font=font).pack(pady=2)
        entry_article = tk.Entry(
            input_frame, textvariable=self.article_var, font=font)
        entry_article.pack()
        self.bind_numeric_entry(entry_article, self.article_var)

        tk.Label(input_frame, text="文章圖片數：", font=font).pack(pady=2)
        entry_image_num = tk.Entry(
            input_frame, textvariable=self.image_num_var, font=font)
        entry_image_num.pack()
        self.bind_numeric_entry(entry_image_num, self.image_num_var)

        tk.Label(input_frame, text="圖片寬高：", font=font).pack(pady=2)

        image_size_entry_frame = tk.Frame(input_frame)
        image_size_entry_frame.pack()

        entry_image_width = tk.Entry(
            image_size_entry_frame, textvariable=self.image_width_var, width=7, font=font)
        entry_image_width.pack(side=tk.LEFT)
        self.bind_numeric_entry(entry_image_width, self.image_width_var)

        tk.Label(image_size_entry_frame, text=" x ",
                 font=font).pack(side=tk.LEFT)

        entry_image_height = tk.Entry(
            image_size_entry_frame, textvariable=self.image_height_var, width=7, font=font)
        entry_image_height.pack(side=tk.LEFT)
        self.bind_numeric_entry(entry_image_height, self.image_height_var)

        tk.Label(image_size_entry_frame, text=" px",
                 font=font).pack(side=tk.LEFT)

        space_frame = tk.Frame(input_frame)
        space_frame.pack(pady=5)

        def set_image_size(width, height):
            self.image_width_var.set(width)
            self.image_height_var.set(height)

        button_groups = [
            [(1024, 768), (1024, 473), (1024, 576)],
            [(1024, 640), (1030, 730), (1280, 768)],
            [(690, 768), (710, 768), (1920, 1080)]
        ]

        style.configure('SIZE.TButton',
                        font=('微軟正黑體', 8),
                        width=10, height=1,
                        padding=2, relief='ridge')
        style.map('SIZE.TButton',
                  background=[('pressed', '#1C83E8'), ('active', '#71A9E0')]
                  )

        for group in button_groups:
            button_frame = tk.Frame(input_frame)
            button_frame.pack()
            for w, h in group:
                text = f"{w} x {h}"
                ttk.Button(
                    button_frame,
                    text=text,
                    style='SIZE.TButton',
                    command=lambda w=w, h=h: set_image_size(w, h)
                ).pack(side=tk.LEFT, padx=1, pady=1)

        # 生成圖文原始碼按鈕
        style.configure('OK.TButton', font=('微軟正黑體', 13), width=18,
                        height=1, padding=(12, 8), background='green', borderwidth=1)
        style.map('OK.TButton', foreground=[('pressed', 'black'), ('active', 'white')],
                  background=[('pressed', 'green'), ('active', 'dark green')])
        ttk.Button(input_frame, text="📑 生成原始碼到剪貼簿", style="OK.TButton",
                   command=self.generate_code).pack(padx=1, pady=6)

    # 確保只能選擇其中一個按鈕的功能
    def update_checkbutton_state(self, selected_var):
        if selected_var.get():
            if selected_var is self.include_symbol_up:
                self.include_symbol_down.set(False)
            else:
                self.include_symbol_up.set(False)

    # 數字增減輔助功能
    def increment_value(self, var, delta):
        try:
            current = int(var.get())
            var.set(str(current + delta))
        except ValueError:
            pass

    def bind_numeric_entry(self, entry, var):
        entry.bind("<Up>", lambda event: self.increment_value(var, 1))
        entry.bind("<Down>", lambda event: self.increment_value(var, -1))

    def generate_code(self):
        site_code = self.site_var.get()
        year = self.year_var.get()
        article = self.article_var.get()
        image_num = int(self.image_num_var.get())
        image_width = self.image_width_var.get()
        image_height = self.image_height_var.get()

        if self.include_previous_var.get():
            code = "文\n\n"
        else:
            code = ""

        for i in range(1, image_num+1):
            img_url = f"https://mnya.tw/{site_code}/wp-content/uploads/{year}/{article}-{i}.jpg"
            if self.include_symbol_down.get():
                code += "▼\n"
            code += f'<img src="{img_url}" width="{image_width}" height="{image_height}" />'
            if self.include_symbol_up.get():
                code += "\n▲\n"
            else:
                code += "\n"
        pyperclip.copy(code)

        # 儲存當前網站的文章編號到配置檔案
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
        except Exception:
            config = {}
        config["article_" + site_code] = article
        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def load_last_article(self):
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
        except Exception:
            config = {}
        site_code = self.site_var.get()
        last_article = config.get("article_" + site_code, "1")
        self.article_var.set(last_article)

    ###############
    ### 批次處理 ###
    ###############

    def batch_widgets(self):
        style = ttk.Style()
        style.configure('HANDLE.TButton', font=(
            '微軟正黑體', 12), borderwidth=1, padding=6, relief='ridge')
        style.map('HANDLE.TButton', background=[
                  ('pressed', '#1C83E8'), ('active', '#71A9E0')])

        # 清空 widget
        for widget in self.tab2.winfo_children():
            widget.destroy()

        # Canvas 移除外框避免白邊
        canvas = tk.Canvas(self.tab2, borderwidth=0, highlightthickness=0)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar = tk.Scrollbar(
            self.tab2, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame,
                             anchor='nw', tags='inner_frame')

        # 讓 inner_frame 寬度隨 canvas 寬度自動同步
        def resize_inner_frame(event):
            canvas_width = event.width
            canvas.itemconfig('inner_frame', width=canvas_width)
        canvas.bind("<Configure>", resize_inner_frame)

        def on_canvas_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta / 120), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all(
            '<MouseWheel>', on_canvas_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))
        inner_frame.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox('all')))

        # ====== 分組資訊與詳細 Tooltip ======
        groups = [
            {
                "label": "🖼 圖片處理",
                "buttons": [
                    ("圖片萌芽浮水印", self.watermark_process_images,
                     "為每張圖片上萌芽網頁浮水印，\n位置會在圖片的右下角，\n輸出圖片檔案格式為 .jpg\n(支援格式：.jpg、.jpeg、.png)"),
                    ("圖片倆倆合併", self.load_images,
                     "每兩張圖片水平合併成一張圖片，\n圖片總數為單數則最後一張不合併\n(支援格式：.jpg、.jpeg、.png)"),
                    ("圖片左右分割後上下合併", self.process_split_and_merge_image,
                     "每張圖左右切半後將右半部從下方合併，\n輸出圖片檔案格式為 .jpg\n(支援格式：.jpg、.jpeg、.png)"),
                    ("圖片中心處理", self.process_center_images,
                     "為每張圖片建立高斯模糊背景與白色陰影效果，\n並輸出固定尺寸圖片 (1024x768)\n(支援格式：.jpg、.jpeg、.png)")
                ]
            },
            {
                "label": "🎬 影片處理",
                "buttons": [
                    ("影片萌芽浮水印", self.video_watermark,
                     "為任何 MP4 影片加上萌芽網頁浮水印，\n採直式浮水印，會顯示在影片右上方\n(支援格式：.mp4)"),
                    ("WEBP 轉 MP4", self.convert_webp_to_mp4,
                     "批次處理 WEBP 轉 MP4，輸出格式為 .mp4\n(支援格式：.webp)"),
                    ("影片重複淡化工具", self.open_video_repeat_fade_window,
                     "將影片重複淡入淡出並串接為指定長度，支援自訂淡化秒數與輸出解析度\n(支援格式：.mp4、.mov、.avi、.mkv、.webm、.flv)")
                ]
            },
            {
                "label": "🧩 其他處理",
                "buttons": [
                    ("字幕檔轉時間軸標記", self.sub2txt,
                     "全自動批次 SRT 字幕檔轉換為 TXT 時間軸標記\n(支援格式：.srt)"),
                    ("航跡檔轉航點座標", self.convert_gpx_files,
                     "全自動批次 GPX 航跡檔轉換為航點座標\n(支援格式：.gpx)"),
                    ("音訊合併", self.merge_audio,
                     "全自動音訊檔合併，輸出規格為 MP3 320kbps\n(支援格式：.mp3、.wav)"),
                    ("文字批次取代工具", self.open_text_batch_replace_window,
                     "批次執行文字取代規則，\n可自訂多條規則，由上至下依序處理\n每行格式如：\"A\" -> \"B\"")
                ]
            }
        ]

        row_idx = 0
        for group in groups:
            frame = ttk.Labelframe(
                inner_frame, text=group["label"], bootstyle="primary")
            frame.grid(row=row_idx, column=0, padx=10,
                       pady=8, sticky="nsew")
            row_idx += 1

            btns = group["buttons"]
            for i, (btn_text, btn_cmd, btn_tip) in enumerate(btns):
                btn = ttk.Button(
                    frame,
                    text=f"{btn_text}",
                    style="HANDLE.TButton",
                    command=btn_cmd,
                    bootstyle="secondary outline",
                )
                btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="ew")
                ToolTip(btn, msg=btn_tip, delay=0.2, fg="#fff",
                        bg="#1c1c1c", padx=8, pady=5)
            for col in range(2):
                frame.grid_columnconfigure(col, weight=1)
        inner_frame.grid_columnconfigure(0, weight=1)

    ## 批次處理：圖片萌芽浮水印 ##

    def watermark_process_images(self):
        image_paths = filedialog.askopenfilenames(
            initialdir=os.getcwd(),
            title="選擇圖片",
            filetypes=[("Image files", "*.jpg *.png *.jpeg")]
        )
        if not image_paths:
            messagebox.showinfo("提示", "未選擇任何圖片，此次處理結束")
            return
        add_watermark(image_paths, "watermark.png",
                      BUILD_DIR)
        os.startfile(BUILD_DIR)

    ## 批次處理：影片萌芽浮水印 ##

    def video_watermark(self):
        video_paths = filedialog.askopenfilenames(
            initialdir=os.getcwd(),
            title="選擇影片",
            filetypes=[("MP4 影片", "*.mp4")]
        )
        if not video_paths:
            messagebox.showinfo("提示", "未選擇任何影片，此次處理結束")
            return
        add_video_watermark(video_paths, "watermark-vertical.png", BUILD_DIR)
        os.startfile(BUILD_DIR)

    ## 批次處理：圖片倆倆合併 ##

    def load_images(self):
        image_paths = filedialog.askopenfilenames(
            initialdir=os.getcwd(),
            title="選擇圖片",
            filetypes=[("Image files", "*.jpg *.png *.jpeg")]
        )
        if not image_paths:
            messagebox.showinfo("提示", "未選擇任何圖片，此次處理結束")
            return
        merge_images(image_paths, BUILD_DIR)
        os.startfile(BUILD_DIR)

    ## 批次處理：圖片左右分割後上下合併 ##

    def process_split_and_merge_image(self):
        file_paths = filedialog.askopenfilenames(
            title='選擇圖片', filetypes=[("Image files", "*.jpg *.png *.jpeg")]
        )
        if not file_paths:
            messagebox.showinfo("提示", "未選擇任何圖片，此次處理結束")
            return
        for fp in file_paths:
            split_and_merge_image(fp, BUILD_DIR)
        os.startfile(BUILD_DIR)

    ## 批次處理：字幕檔轉時間軸標記 ##

    def sub2txt(self):
        files = filedialog.askopenfilenames(filetypes=[("SRT 字幕檔", "*.srt")])
        if not files:
            messagebox.showinfo("提示", "未選擇任何字幕檔，此次處理結束")
            return
        sub2txt(files, BUILD_DIR)
        os.startfile(BUILD_DIR)

    ## 批次處理：航跡檔轉航點座標 ##

    def convert_gpx_files(self):
        file_paths = filedialog.askopenfilenames(
            title="選擇 GPX 檔案",
            filetypes=[("GPX files", "*.gpx")]
        )
        if not file_paths:
            messagebox.showinfo("提示", "未選擇任何航跡檔，此次處理結束")
            return
        convert_gpx_files(file_paths, BUILD_DIR)
        os.startfile(BUILD_DIR)

    ## 批次處理：音訊合併 ##

    def merge_audio(self):
        files = filedialog.askopenfilenames(
            filetypes=[("音訊檔案", "*.mp3;*.wav")]
        )
        if len(files) < 2:
            messagebox.showinfo("提示", "未選擇兩個（含）以上的音訊檔，此次處理結束")
            return
        output_file = merge_audio(files, BUILD_DIR)
        if output_file:
            messagebox.showinfo("提示", f"音訊檔案已合併，並儲存至 {output_file}")
            os.startfile(BUILD_DIR)

    ## 批次處理：圖片中心處理 ##

    def process_center_images(self):
        image_paths = filedialog.askopenfilenames(
            initialdir=os.getcwd(),
            title="選擇圖片",
            filetypes=[("Image files", "*.jpg *.png *.jpeg")]
        )
        if not image_paths:
            messagebox.showinfo("提示", "未選擇任何圖片，此次處理結束")
            return
        center_process_images(image_paths, BUILD_DIR)
        os.startfile(BUILD_DIR)

    ## 批次處理：WEBP 轉 MP4 ##

    def convert_webp_to_mp4(self):
        webp_files = filedialog.askopenfilenames(
            title="選擇 WEBP 檔案",
            filetypes=[("WEBP 檔案", "*.webp")]
        )
        if not webp_files:
            messagebox.showinfo("提示", "未選擇任何 WEBP 檔案，此次處理結束")
            return
        webp_to_mp4(webp_files, BUILD_DIR)
        os.startfile(BUILD_DIR)

    ###############
    ### 複製取用 ###
    ###############

    def copy_widgets(self):
        font = tkFont.Font(family="微軟正黑體", size=13)

        # 建立一個 Canvas，設定為可捲動的
        canvas = tk.Canvas(self.tab3)
        canvas.pack(side='left', fill='both', expand=True)

        # 在 Canvas 上建立一個 Frame，用來放置按鈕
        button_frame = tk.Frame(canvas)

        # 把 Frame 放進 Scrollbar 裡面
        scrollbar = tk.Scrollbar(
            self.tab3, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=button_frame, anchor='nw')

        # 設定 Canvas 的捲動範圍
        button_frame.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox('all')))

        # 設定捲動事件
        def on_canvas_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta/120), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all(
            '<MouseWheel>', on_canvas_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))

        buttons = [["發圖文", "🆕"], ["發公告", "ℹ️"], ["發影片", "🎬"], ["發討論", "💬"], ["發連結", "🔗"], ["發警訊", "⚠️"], ["給按讚", "👍"], ["給倒讚", "👎"], ["比中指", "🖕"],
                   ["YT嵌入", "<iframe src=\"https://www.youtube.com/embed/\" width=\"1024\" height=\"576\" frameborder=\"0\" allowfullscreen=\"allowfullscreen\"></iframe>\n▲ 影片欣賞<strong>《》</strong>"], ["航跡圖", "<iframe src='XXX' width='1024' height='768'></iframe>\n▲ 航跡圖（<a href='XXX' target='_blank' rel='noopener noreferrer'>GPX 下載</a>）。"], ["NSFW", "🔞"], ["沒問題", "👌"], ["方綠勾", "✅"], ["方綠叉", "❎"], ["一張紙", "📄"], ["筆跟紙", "📝"], ["方塊零", "0️⃣"], ["方塊一", "1️⃣"], ["方塊二", "2️⃣"], ["方塊三", "3️⃣"], ["方塊四", "4️⃣"], ["方塊五", "5️⃣"], ["方塊六", "6️⃣"], ["方塊七", "7️⃣"], ["方塊八", "8️⃣"], ["方塊九", "9️⃣"], ["方塊十", "🔟"], ["一座山", "⛰"], ["調色板", "🎨"]]

        style.configure('COPY.TButton', font=('微軟正黑體', 12),
                        width=6, height=1, padding=(4, 6), relief='ridge')
        style.map('COPY.TButton',
                  background=[('pressed', '#1C83E8'), ('active', '#71A9E0')]
                  )

        for i, button in enumerate(buttons):
            new_button = ttk.Button(button_frame, text=button[0], style='COPY.TButton',
                                    command=lambda text=button[1]: self.copy_text(text))
            new_button.grid(row=i//6, column=i % 6, padx=1, pady=1)

    def copy_text(self, text):
        root.clipboard_clear()  # 清除剪貼板內容
        root.clipboard_append(text)  # 將指定文字添加到剪貼板
        root.update()  # 強制更新 tkinter 的 GUI 介面

    ###############
    ### 快速連結 ###
    ###############

    def links_widgets(self):
        font = tkFont.Font(family="微軟正黑體", size=14)

        # 建立一個 Canvas，設定為可捲動的
        canvas = tk.Canvas(self.tab4)
        canvas.pack(side='left', fill='both', expand=True)

        # 在 Canvas 上建立一個 Frame，用來放置按鈕
        button_frame = tk.Frame(canvas)

        # 把 Frame 放進 Scrollbar 裡面
        scrollbar = tk.Scrollbar(
            self.tab4, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=button_frame, anchor='nw')

        # 設定 Canvas 的捲動範圍
        button_frame.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox('all')))

        # 設定捲動事件
        def on_canvas_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta/120), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all(
            '<MouseWheel>', on_canvas_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))

        buttons = [
            ["🌳 萌芽網頁", "https://mnya.tw/"],
            ["💬 萌芽論壇", "https://bbs.mnya.tw"],
            ["💻 萌芽綜合天地", "https://mnya.tw/cc/"],
            ["⛰ 萌芽爬山網", "https://mnya.tw/k3/"],
            ["🍹 萌芽悠遊網", "https://mnya.tw/yo/"],
            ["🌏 萌芽地科網", "https://mnya.tw/es/"],
            ["🎵 萌芽音樂網", "https://mnya.tw/ms/"],
            ["🖼 萌芽二次元", "https://mnya.tw/2d/"],
            ["🎮 萌芽Game網", "https://mnya.tw/games/"],
            ["萌芽大數據", "https://mnya.tw/bigdata/"],
            ["萌芽開發", "https://mnya.tw/dv/"],
            ["萌芽下載站", "https://mnya.tw/dl/"],
            ["萌芽攝影網", "https://mnya.tw/pt/"],
            ["方塊鴨之家", "https://mnya.tw/blockduck"],
            ["關於本站", "https://mnya.tw/about"],
            ["萌芽網站導覽", "https://mnya.tw/map.html"],
            ["萌芽搜尋中心", "https://mnya.tw/search"]
        ]

        style.configure('LINK.TButton', font=('微軟正黑體', 13), width=19,
                        height=1, padding=5, relief='ridge')
        style.map('LINK.TButton',
                  background=[('pressed', '#1C83E8'), ('active', '#71A9E0')]
                  )

        for i, button in enumerate(buttons):
            new_button = ttk.Button(button_frame, text=button[0], style='LINK.TButton',
                                    command=lambda text=button[1]: self.open_browser(text))
            new_button.grid(row=i//2, column=i % 2, padx=1, pady=1)

    def open_browser(self, url):
        webbrowser.open_new_tab(url)

    ###############
    ##### 設定 ####
    ###############

    def setting_widgets(self):
        font = tkFont.Font(family="微軟正黑體", size=13)
        # 勾選是否啟動時最小化
        is_minimized_button = tk.Checkbutton(self.tabSet, text="啟動時最小化", font=font,
                                             variable=self.is_minimized,
                                             command=self.save_config)
        is_minimized_button.pack(padx=1, pady=10)

    def save_config(self):
        with open(self.config_path, "r") as f:
            config = json.load(f)
            # 更新需要修改的鍵值
            config["is_minimized"] = self.is_minimized.get()

            # 保存到配置檔案
            with open(self.config_path, "w") as f:
                json.dump(config, f)

    ###############
    ### 關於程式 ###
    ###############

    def about_widgets(self):

        # 建立 Frame 放版本號與更新按鈕
        version_frame = tk.Frame(self.tab0)
        version_frame.pack(anchor='nw', padx=5, pady=5)

        # 版本號 Label
        tk.Label(version_frame, text=APP_NAME + " " + VERSION,
                 font=('微軟正黑體', 12)).pack(side='left')

        # 執行更新按鈕
        def run_auto_update():
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            batch_path = os.path.join(app_dir, "auto_update.bat")
            if os.path.exists(batch_path):
                subprocess.Popen(['cmd', '/c', batch_path], cwd=app_dir)
                self.master.destroy()
            else:
                messagebox.showerror("找不到檔案", "auto_update.bat 不存在！")

        style.configure('UPDATE.TButton', font=(
            '微軟正黑體', 11), padding=(5, 3), relief='ridge')
        style.map('UPDATE.TButton',
                  background=[('pressed', '#1C83E8'), ('active', '#71A9E0')]
                  )

        update_btn = ttk.Button(
            version_frame,
            text="執行更新",
            style='UPDATE.TButton',
            command=run_auto_update
        )
        update_btn.pack(side='left', padx=10)

        # 捲動文字區
        txt = scrolledtext.ScrolledText(
            self.tab0, width=50, height=20, font=('微軟正黑體', 12))
        txt.pack(fill='both', expand=True)
        # 讀取 changelog.txt
        try:
            with open("changelog.txt", "r", encoding="utf-8") as f:
                changelog = f.read()
        except Exception as e:
            changelog = "（找不到 changelog.txt 或讀取失敗）"
        # 組合文字內容
        text = "軟體開發及維護者：萌芽站長\n" \
            "萌芽系列網站 ‧ Mnya Series Website ‧ Mnya.tw\n" \
            "\n ■ 更新日誌 ■ \n" \
            "\n" + changelog + "\n" \
            "\n ■ MIT License ■ \n" \
            "\nCopyright (c) 2025 Feng, Cheng-Chi (萌芽站長) @ 萌芽系列網站 ‧ Mnya Series Website ‧ Mnya.tw\n" \
            "\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n" \
            "\nThe above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n" \
            "\nTHE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n"

        txt.insert("1.0", text)
        txt.config(state="disabled")


if __name__ == "__main__":

    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    root = tk.Tk()
    style = ttk.Style("superhero")
    root.title(APP_NAME)
    root.geometry("{}x{}".format(WINDOW_WIDTH, WINDOW_HEIGHT))
    root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
    root.iconbitmap('icon.ico')
    app = App(master=root)
    app.mainloop()
