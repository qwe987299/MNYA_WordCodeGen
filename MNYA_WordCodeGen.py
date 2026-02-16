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
import threading
import time

# 匯入 batch_tools 各模組
from batch_tools.image_tools import add_watermark, merge_images, split_and_merge_image, center_process_images, compress_images_by_cjpeg
from batch_tools.video_tools import add_video_watermark, video_repeat_fade, video_crop
from batch_tools.audio_tools import merge_audio
from batch_tools.gpx_tools import convert_gpx_files
from batch_tools.subtitle_tools import sub2txt
from batch_tools.webp_tools import webp_to_mp4
from batch_tools.gpx_slope_tool import generate_slope_chart

# 子視窗
from windows.video_repeat_fade_window import open_video_repeat_fade_window
from windows.text_batch_replace_window import open_text_batch_replace_window
from windows.image_compress_window import open_image_compress_window
from windows.video_crop_window import open_video_crop_window
from windows.gpx_slope_window import open_gpx_slope_window

# 測試指令：python MNYA_WordCodeGen.py
# 打包指令：pyinstaller --onefile --icon=icon.ico --noconsole MNYA_WordCodeGen.py

# 應用配置
WINDOW_WIDTH = 435  # 寬度
WINDOW_HEIGHT = 495  # 高度
APP_NAME = "萌芽系列網站圖文原始碼生成器"  # 應用名稱
VERSION = "V1.7.6"  # 版本
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
        self.master.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{self.window_x}+{self.window_y}")
        self.master.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 設置關閉視窗時的回調函數
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

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

        # 限制子視窗只能同時一個
        self.video_repeat_fade_win = None
        self.text_batch_replace_win = None
        self.image_compress_win = None
        self.video_crop_win = None
        self.gpx_slope_win = None

        # 儲存複製按鈕的還原任務 ID
        self._copied_btn_after_id = None

        # 全域鍵功能
        self.master.bind('<Return>', self.on_global_return)
        self.master.bind('<KP_Enter>', self.on_global_return)

    # 全域鍵回調函數
    def on_global_return(self, event=None):
        if self.tabControl.index(self.tabControl.select()) == 0:
            self.generate_and_show_copied()

    # 生成原始碼並顯示已複製的按鈕文字
    def generate_and_show_copied(self):
        self.generate_code()
        old_text = "📑 生成原始碼到剪貼簿"
        # 取消前一個還原任務
        if hasattr(self, '_copied_btn_after_id') and self._copied_btn_after_id:
            self.generate_btn.after_cancel(self._copied_btn_after_id)
        self.generate_btn.config(text="✅ 已複製！")
        self._copied_btn_after_id = self.generate_btn.after(
            1000, lambda: self._restore_generate_btn_text(old_text)
        )

    # 還原生成原始碼按鈕文字
    def _restore_generate_btn_text(self, old_text):
        self.generate_btn.config(text=old_text)
        self._copied_btn_after_id = None

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

        # 初始化邊界值 (使用第一個螢幕的資訊作為基準)
        if monitors:
            info = win32api.GetMonitorInfo(monitors[0][0])["Work"]
            min_x, min_y, max_x, max_y = info[0], info[1], info[2], info[3]
        else:
            min_x, min_y, max_x, max_y = 0, 0, 1920, 1080

        for monitor in monitors:
            monitor_info = win32api.GetMonitorInfo(monitor[0])
            work_area = monitor_info["Work"]
            min_x = min(min_x, work_area[0])
            min_y = min(min_y, work_area[1])
            max_x = max(max_x, work_area[2])
            max_y = max(max_y, work_area[3])

        # 確保視窗位置在所有顯示器範圍內
        if self.window_x < min_x:
            self.window_x = min_x
        elif self.window_x > max_x - WINDOW_WIDTH:
            self.window_x = max_x - WINDOW_WIDTH
        if self.window_y < min_y:
            self.window_y = min_y
        elif self.window_y > max_y - WINDOW_HEIGHT:
            self.window_y = max_y - WINDOW_HEIGHT

    def on_close(self):
        # 保存配置
        self.save_on_close()

        # 關閉視窗
        self.master.destroy()

    def save_on_close(self):
        with open(self.config_path, "r") as f:
            config = json.load(f)
            # 更新需要修改的鍵值
            # 避免在最小化狀態下儲存座標 (會變成 -32000)
            if self.master.state() != 'iconic':
                config["x"] = self.master.winfo_x()
                config["y"] = self.master.winfo_y()

            # 保存到配置檔案
            with open(self.config_path, "w") as f:
                json.dump(config, f)

    def default_config(self):
        # 如果配置檔案不存在，使用預設值
        if not os.path.exists(self.config_path):
            config = {
                "x": self.master.winfo_x(),
                "y": self.master.winfo_y(),
                "is_minimized": False
            }
            # 保存全新配置檔
            with open(self.config_path, "w") as f:
                json.dump(config, f)

    # 通用設定讀取與儲存 helper
    def _load_sub_config(self, key):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                return config.get(key, {})
            except Exception:
                pass
        return {}

    def _save_sub_config(self, key, value):
        config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass
        config[key] = value
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)

    def load_repeat_fade_config(self):
        return self._load_sub_config("video_repeat_fade")

    def save_repeat_fade_config(self, config_dict):
        self._save_sub_config("video_repeat_fade", config_dict)

    def load_text_batch_replace_config(self):
        return self._load_sub_config("text_batch_replace")

    def save_text_batch_replace_config(self, config_dict):
        self._save_sub_config("text_batch_replace", config_dict)

    def load_image_compress_config(self):
        return self._load_sub_config("image_compress")

    def save_image_compress_config(self, config_dict):
        self._save_sub_config("image_compress", config_dict)

    def load_video_crop_config(self):
        return self._load_sub_config("video_crop")

    def save_video_crop_config(self, config_dict):
        self._save_sub_config("video_crop", config_dict)

    def load_gpx_slope_config(self):
        return self._load_sub_config("gpx_slope")

    def save_gpx_slope_config(self, config_dict):
        self._save_sub_config("gpx_slope", config_dict)

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

    def _open_sub_window(self, attr_name, open_func, load_config_func, save_config_func, **kwargs):
        """通用子視窗開啟邏輯"""
        win = getattr(self, attr_name)
        if win is not None:
            try:
                if win.winfo_exists():
                    win.lift()
                    win.focus_force()
                    return
            except:
                setattr(self, attr_name, None)

        cfg = load_config_func()
        # 建立新視窗
        new_win = open_func(
            app=self,
            parent=self.master,
            config=cfg,
            save_config_func=save_config_func,
            on_close=lambda: setattr(self, attr_name, None),
            **kwargs
        )
        setattr(self, attr_name, new_win)

    def open_video_repeat_fade_window(self):
        self._open_sub_window(
            'video_repeat_fade_win',
            open_video_repeat_fade_window,
            self.load_repeat_fade_config,
            self.save_repeat_fade_config,
            video_repeat_fade_func=video_repeat_fade
        )

    def open_text_batch_replace_window(self):
        self._open_sub_window(
            'text_batch_replace_win',
            open_text_batch_replace_window,
            self.load_text_batch_replace_config,
            self.save_text_batch_replace_config
        )

    def open_image_compress_window(self):
        self._open_sub_window(
            'image_compress_win',
            open_image_compress_window,
            self.load_image_compress_config,
            self.save_image_compress_config,
            compress_func=compress_images_by_cjpeg
        )

    def open_video_crop_window(self):
        self._open_sub_window(
            'video_crop_win',
            open_video_crop_window,
            self.load_video_crop_config,
            self.save_video_crop_config,
            video_crop_func=video_crop
        )

    def open_gpx_slope_window(self):
        self._open_sub_window(
            'gpx_slope_win',
            open_gpx_slope_window,
            self.load_gpx_slope_config,
            self.save_gpx_slope_config,
            generate_func=generate_slope_chart
        )

    ###############
    ### 主要功能 ###
    ###############

    def create_widgets(self):

        # 字體設定
        font14 = tkFont.Font(family="微軟正黑體", size=14)
        font = tkFont.Font(family="微軟正黑體", size=13)
        style = ttk.Style()

        # 主內容兩欄
        main_content_frame = tk.Frame(self.tab1)
        main_content_frame.pack(fill=tk.BOTH, pady=(10, 2), expand=True)

        # 萌芽系列網站按鈕組
        self.sites = [("💻 萌芽綜合天地", "cc"),
                      ("⛰ 萌芽爬山網", "k3"),
                      ("🍹 萌芽悠遊網", "yo"),
                      ("🌏 萌芽地科網", "es"),
                      ("🎵 萌芽音樂網", "ms"),
                      ("🖼 萌芽二次元", "2d"),
                      ("🎮 萌芽Game網", "games")]
        self.site_var = tk.StringVar(value=self.sites[0][1])
        site_frame = tk.Frame(main_content_frame)
        site_frame.pack(side=tk.LEFT, padx=10, fill=tk.Y)
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
        input_frame = tk.Frame(main_content_frame)
        input_frame.pack(side=tk.RIGHT, padx=10, anchor='n')
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
                        height=1, padding=(12, 8), background='#008000', borderwidth=1)
        style.map('OK.TButton', foreground=[('pressed', 'black'), ('active', 'white')],
                  background=[('pressed', "#159615"), ('active', "#065E06")])

        self.generate_btn = ttk.Button(
            input_frame,
            text="📑 生成原始碼到剪貼簿",
            style="OK.TButton",
            command=self.generate_and_show_copied
        )
        self.generate_btn.pack(padx=1, pady=(6, 0))

        # 主要功能下方快速批次處理區
        quick_batch_frame = ttk.Labelframe(
            self.tab1, text="🧰 快速批次處理", bootstyle="primary"
        )
        quick_batch_frame.pack(fill=tk.X, side=tk.BOTTOM,
                               pady=(0, 10), padx=10)

        # 內層 frame 置中三顆按鈕
        inner_frame = tk.Frame(quick_batch_frame)
        inner_frame.pack(pady=5)

        quick_batch_buttons = [
            {
                "text": "⚡️ 快速圖片壓縮",
                "cmd": self.batch_image_compress_with_last_config,
                "tip": "批次壓縮 JPG/JPEG 圖片，\n將自動以上次「進階圖片壓縮」設定或預設值進行，\n完成自動開啟目錄\n(支援格式：.jpg、.jpeg)"
            },
            {
                "text": "🌊 圖片萌芽浮水印",
                "cmd": self.watermark_process_images,
                "tip": "為每張圖片上萌芽網頁浮水印，\n位置會在圖片的右下角，\n輸出圖片檔案格式為 .jpg\n(支援格式：.jpg、.jpeg、.png)"
            },
            {
                "text": "💧 影片萌芽浮水印",
                "cmd": self.video_watermark,
                "tip": "為任何 MP4 影片加上萌芽網頁浮水印，\n採直式浮水印，會顯示在影片右上方\n(支援格式：.mp4)"
            },
        ]

        style.configure('QUICKBATCH.TButton',
                        font=('微軟正黑體', 10),
                        padding=(5, 5),
                        borderwidth=1, relief='ridge',
                        foreground="#0759b4", background="#f0f7ff")
        style.map('QUICKBATCH.TButton',
                  background=[('pressed', "#adb8c5"), ('active', "#ccd6e3")],
                  foreground=[('pressed', "#4C9EF0"), ('active', '#004488')]
                  )

        # 讓三顆按鈕水平置中且等高
        for i, btn in enumerate(quick_batch_buttons):
            quick_btn = ttk.Button(
                inner_frame, text=btn["text"], style='QUICKBATCH.TButton',
                command=btn["cmd"], bootstyle="info outline"
            )
            quick_btn.grid(row=0, column=i, padx=5, pady=2, sticky='nsew')
            ToolTip(quick_btn, msg=btn["tip"], delay=0.1,
                    fg="#fff", bg="#1c1c1c", padx=10, pady=6)
            inner_frame.grid_columnconfigure(i, weight=1)

        # 讓按鈕區置中
        inner_frame.grid_columnconfigure((0, 1, 2), weight=1)

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
        try:
            image_num = int(self.image_num_var.get())
        except ValueError:
            messagebox.showerror("輸入錯誤", "文章圖片數必須為整數")
            return
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
            '微軟正黑體', 12), borderwidth=1, padding=5, relief='ridge')
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

        # 分組資訊與詳細 Tooltip
        groups = [
            {
                "label": "🖼 圖片處理",
                "buttons": [
                    ("🌊 圖片萌芽浮水印", self.watermark_process_images,
                     "為每張圖片上萌芽網頁浮水印，\n位置會在圖片的右下角，\n輸出圖片檔案格式為 .jpg\n(支援格式：.jpg、.jpeg、.png)"),
                    ("➗ 圖片倆倆合併", self.load_images,
                     "每兩張圖片水平合併成一張圖片，\n圖片總數為單數則最後一張不合併\n(支援格式：.jpg、.jpeg、.png)"),
                    ("🔀 圖片左右分割後上下合併", self.process_split_and_merge_image,
                     "每張圖左右切半後將右半部從下方合併，\n輸出圖片檔案格式為 .jpg\n(支援格式：.jpg、.jpeg、.png)"),
                    ("🎯 圖片中心處理", self.process_center_images,
                     "為每張圖片建立高斯模糊背景與白色陰影效果，\n並輸出固定尺寸圖片 (1024x768)\n(支援格式：.jpg、.jpeg、.png)"),
                    ("⚡️ 快速圖片壓縮", self.batch_image_compress_with_last_config,
                     "批次壓縮 JPG/JPEG 圖片，\n將自動以上次「進階圖片壓縮」設定或預設值進行，\n完成自動開啟目錄\n(支援格式：.jpg、.jpeg)"),
                    ("⚙️ 進階圖片壓縮", self.open_image_compress_window,
                     "批次壓縮 JPG/JPEG 圖片，\n支援設定品質、漸進式、是否覆蓋原檔\n(支援格式：.jpg、.jpeg)"),
                ]
            },
            {
                "label": "🎬 影片處理",
                "buttons": [
                    ("💧 影片萌芽浮水印", self.video_watermark,
                     "為任何 MP4 影片加上萌芽網頁浮水印，\n採直式浮水印，會顯示在影片右上方\n(支援格式：.mp4)"),
                    ("🌀 WEBP 轉 MP4", self.convert_webp_to_mp4,
                     "批次處理 WEBP 轉 MP4，輸出格式為 .mp4\n(支援格式：.webp)"),
                    ("🔁 影片重複淡化工具", self.open_video_repeat_fade_window,
                     "將影片重複淡入淡出並串接為指定長度，支援自訂淡化秒數與輸出解析度\n(支援格式：.mp4、.mov、.avi、.mkv、.webm、.flv)"),
                    ("✂️ 影片裁切工具", self.open_video_crop_window,
                     "裁切影片至指定寬高，音軌將直接複製\n(支援常見影片格式)")
                ]
            },
            {
                "label": "🧩 其他處理",
                "buttons": [
                    ("🚩 航跡檔轉航點座標", self.convert_gpx_files,
                     "全自動批次 GPX 航跡檔轉換為航點座標\n(支援格式：.gpx)"),
                    ("📈 航跡檔轉坡度分析圖", self.open_gpx_slope_window,
                     "將 GPX 航跡檔轉換為坡度分析圖，\n可自訂寬高、解析度與採樣間距\n(支援格式：.gpx)"),
                    ("📝 字幕檔轉時間軸標記", self.sub2txt,
                     "全自動批次 SRT 字幕檔轉換為 TXT 時間軸標記\n(支援格式：.srt)"),
                    ("🎵 音訊合併", self.merge_audio,
                     "全自動音訊檔合併，輸出規格為 MP3 320kbps\n(支援格式：.mp3、.wav)"),
                    ("🔤 文字批次取代工具", self.open_text_batch_replace_window,
                     "批次執行文字取代規則，\n可自訂多條規則，由上至下依序處理\n每行格式如：\"A\" -> \"B\"")
                ]
            }
        ]

        row_idx = 0
        for group in groups:
            frame = ttk.Labelframe(
                inner_frame, text=group["label"], bootstyle="primary")
            frame.grid(row=row_idx, column=0, padx=10,
                       pady=5, sticky="nsew")
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

        # 使用執行緒執行耗時任務，避免卡住 UI
        def task():
            try:
                self.master.config(cursor="watch")  # 游標變更為等待
                add_watermark(image_paths, "watermark.png", BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(
                    0, lambda: self.master.config(cursor=""))  # 恢復游標

        threading.Thread(target=task, daemon=True).start()

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

        def task():
            try:
                self.master.config(cursor="watch")
                add_video_watermark(
                    video_paths, "watermark-vertical.png", BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

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

        def task():
            try:
                self.master.config(cursor="watch")
                merge_images(image_paths, BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

    ## 批次處理：圖片左右分割後上下合併 ##

    def process_split_and_merge_image(self):
        file_paths = filedialog.askopenfilenames(
            title='選擇圖片', filetypes=[("Image files", "*.jpg *.png *.jpeg")]
        )
        if not file_paths:
            messagebox.showinfo("提示", "未選擇任何圖片，此次處理結束")
            return

        def task():
            try:
                self.master.config(cursor="watch")
                for fp in file_paths:
                    split_and_merge_image(fp, BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

    ## 批次處理：快速圖片壓縮 ##

    def batch_image_compress_with_last_config(self):
        # 讀 config，沒設定用預設值
        cfg = self.load_image_compress_config()
        quality = cfg.get("imgc_quality", 85)
        progressive = cfg.get("imgc_progressive", True)
        overwrite = cfg.get("imgc_overwrite", True)

        # 選檔
        image_paths = filedialog.askopenfilenames(
            title='選擇 JPG/JPEG 圖片',
            filetypes=[("JPG/JPEG 檔案", "*.jpg *.jpeg *.JPG *.JPEG")]
        )
        if not image_paths:
            messagebox.showinfo("提示", "未選擇任何圖片，此次處理結束")
            return

        def task():
            try:
                self.master.config(cursor="watch")
                # 執行壓縮
                output_files, failed = compress_images_by_cjpeg(
                    image_paths,
                    quality=quality,
                    progressive=progressive,
                    overwrite=overwrite
                )

                def on_complete():
                    # 完成後的提示
                    if failed:
                        messagebox.showerror("錯誤", "部分檔案壓縮失敗：\n" +
                                             '\n'.join(f[0] for f in failed))
                    else:
                        # 判斷輸出資料夾，直接開啟
                        if overwrite:
                            # 就是原本路徑
                            if output_files:
                                dir_to_open = os.path.dirname(output_files[0])
                                os.startfile(dir_to_open)
                        else:
                            # 開啟同層 output 資料夾（假設全部都同一層，選第一個）
                            if output_files:
                                out_path = output_files[0]
                                if os.path.sep + "output" + os.path.sep in out_path:
                                    out_dir = os.path.dirname(out_path)
                                else:
                                    # 防呆：萬一不是 output 夾
                                    out_dir = os.path.dirname(out_path)
                                os.startfile(out_dir)

                self.master.after(0, on_complete)
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

    ## 批次處理：字幕檔轉時間軸標記 ##

    def sub2txt(self):
        files = filedialog.askopenfilenames(filetypes=[("SRT 字幕檔", "*.srt")])
        if not files:
            messagebox.showinfo("提示", "未選擇任何字幕檔，此次處理結束")
            return

        def task():
            try:
                self.master.config(cursor="watch")
                sub2txt(files, BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

    ## 批次處理：航跡檔轉航點座標 ##

    def convert_gpx_files(self):
        file_paths = filedialog.askopenfilenames(
            title="選擇 GPX 檔案",
            filetypes=[("GPX files", "*.gpx")]
        )
        if not file_paths:
            messagebox.showinfo("提示", "未選擇任何航跡檔，此次處理結束")
            return

        def task():
            try:
                self.master.config(cursor="watch")
                convert_gpx_files(file_paths, BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

    ## 批次處理：音訊合併 ##

    def merge_audio(self):
        files = filedialog.askopenfilenames(
            filetypes=[("音訊檔案", "*.mp3;*.wav")]
        )
        if len(files) < 2:
            messagebox.showinfo("提示", "未選擇兩個（含）以上的音訊檔，此次處理結束")
            return

        def task():
            try:
                self.master.config(cursor="watch")
                output_file = merge_audio(files, BUILD_DIR)

                def on_complete():
                    if output_file:
                        messagebox.showinfo(
                            "提示", f"音訊檔案已合併，並儲存至 {output_file}")
                        os.startfile(BUILD_DIR)
                self.master.after(0, on_complete)
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

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

        def task():
            try:
                self.master.config(cursor="watch")
                center_process_images(image_paths, BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

    ## 批次處理：WEBP 轉 MP4 ##

    def convert_webp_to_mp4(self):
        webp_files = filedialog.askopenfilenames(
            title="選擇 WEBP 檔案",
            filetypes=[("WEBP 檔案", "*.webp")]
        )
        if not webp_files:
            messagebox.showinfo("提示", "未選擇任何 WEBP 檔案，此次處理結束")
            return

        def task():
            try:
                self.master.config(cursor="watch")
                webp_to_mp4(webp_files, BUILD_DIR)
                self.master.after(0, lambda: os.startfile(BUILD_DIR))
            except Exception as e:
                self.master.after(
                    0, lambda: messagebox.showerror("錯誤", str(e)))
            finally:
                self.master.after(0, lambda: self.master.config(cursor=""))

        threading.Thread(target=task, daemon=True).start()

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
        self.master.clipboard_clear()  # 清除剪貼板內容
        self.master.clipboard_append(text)  # 將指定文字添加到剪貼板
        self.master.update()  # 強制更新 tkinter 的 GUI 介面

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
            "\nCopyright (c) 2026 Feng, Cheng-Chi (萌芽站長) @ 萌芽系列網站 ‧ Mnya Series Website ‧ Mnya.tw\n" \
            "\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n" \
            "\nThe above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n" \
            "\nTHE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n"

        txt.insert("1.0", text)
        txt.config(state="disabled")


if __name__ == "__main__":

    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    root = tk.Tk()

    # --- 啟動畫面 (Splash Screen) ---
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)
    splash_w, splash_h = 450, 260
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x_loc = (screen_w - splash_w) // 2
    y_loc = (screen_h - splash_h) // 2

    # 嘗試讀取設定檔，若有上次位置則計算相對應的中心點，讓 Splash 跟隨主視窗出現的螢幕
    try:
        if os.path.exists(CONFIG_FILENAME):
            with open(CONFIG_FILENAME, "r") as f:
                config = json.load(f)
                last_x = config.get("x")
                last_y = config.get("y")
                if last_x is not None and last_y is not None:
                    # 計算公式：主視窗左上角 + (主視窗寬 - Splash寬)/2
                    x_loc = int(last_x + (WINDOW_WIDTH - splash_w) / 2)
                    y_loc = int(last_y + (WINDOW_HEIGHT - splash_h) / 2)
    except Exception:
        pass

    splash.geometry(f"{splash_w}x{splash_h}+{x_loc}+{y_loc}")

    splash_img = None
    try:
        splash.configure(bg='#2b3e50')
        tk.Label(splash, text=APP_NAME, font=("微軟正黑體", 18, "bold"),
                 fg="white", bg='#2b3e50', wraplength=400).pack(expand=True)
        tk.Label(splash, text=f"{VERSION}\n正在啟動...", font=(
            "微軟正黑體", 10), fg="#cccccc", bg='#2b3e50').pack(side="bottom", pady=20)
    except Exception:
        pass
    splash.update()
    # -------------------------------

    root.withdraw()  # 先隱藏

    # 載入延遲，避免畫面閃爍，提升體驗
    time.sleep(0.1)

    style = ttk.Style("superhero")
    root.title(APP_NAME)
    try:
        root.iconbitmap('icon.ico')
    except Exception:
        pass
    app = App(master=root)
    splash.destroy()  # 關閉啟動畫面

    # 重新設定幾何位置，確保在 deiconify 前生效 (解決 withdraw 後 geometry 失效問題)
    root.geometry(
        f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{app.window_x}+{app.window_y}")
    root.update_idletasks()  # 強制更新狀態，確保 geometry 設定被套用

    if app.is_minimized.get():
        root.iconify()  # 直接最小化，避免視窗閃現
    else:
        root.deiconify()  # 再顯示
    app.mainloop()
