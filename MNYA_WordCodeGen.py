import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import tkinter.font as tkFont
import ttkbootstrap as ttk
from tktooltip import ToolTip
from ttkbootstrap.constants import *
import pyperclip
from PIL import Image
import os
import threading
import json
import win32api
import re
import webbrowser
import gpxpy
import pyproj
import pydub

# 測試指令：python MNYA_WordCodeGen.py
# 打包指令：pyinstaller --onefile --icon=icon.ico --noconsole MNYA_WordCodeGen.py

# 應用配置
WINDOW_WIDTH = 435  # 寬度
WINDOW_HEIGHT = 430  # 高度
APP_NAME = "萌芽系列網站圖文原始碼生成器"  # 應用名稱
VERSION = "V1.3.5"  # 版本
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
        self.batch_widgets()
        self.copy_widgets()
        self.links_widgets()
        self.setting_widgets()
        self.about_widgets()

        # 設定視窗的最小化狀態
        self.master.after(1, self.minimized)

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

    ###############
    ### 主要功能 ###
    ###############

    def create_widgets(self):

        # 字體設定
        font14 = tkFont.Font(family="微軟正黑體", size=14)
        font = tkFont.Font(family="微軟正黑體", size=13)
        style = ttk.Style()
        style.configure('OK.TButton', font=('微軟正黑體', 13), background='green',
                        borderwidth=1)
        style.map('OK.TButton', foreground=[('pressed', 'black'), ('active', 'white')],
                  background=[('pressed', 'green'), ('active', 'dark green')])

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
            tk.Radiobutton(site_frame, text=site,
                           variable=self.site_var, value=code, font=font14, indicatoron=False, width=15, height=1).pack(anchor=tk.W)

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
        tk.Label(input_frame, text="年份：", font=font).pack()
        tk.Entry(input_frame, textvariable=self.year_var, font=font).pack()
        tk.Label(input_frame, text="文章編號：", font=font).pack()
        tk.Entry(input_frame, textvariable=self.article_var, font=font).pack()
        tk.Label(input_frame, text="文章圖片數：", font=font).pack()
        tk.Entry(input_frame, textvariable=self.image_num_var, font=font).pack()
        tk.Label(input_frame, text="圖片寬度：", font=font).pack()
        tk.Entry(input_frame, textvariable=self.image_width_var, font=font).pack()
        tk.Label(input_frame, text="圖片高度：", font=font).pack()
        tk.Entry(input_frame, textvariable=self.image_height_var,
                 font=font).pack()

        space_frame = tk.Frame(input_frame)
        space_frame.pack(pady=2)

        def set_image_size(width, height):
            self.image_width_var.set(width)
            self.image_height_var.set(height)

        button_frame = tk.Frame(input_frame)
        button_frame.pack()

        tk.Button(button_frame, text="1024 x 768",
                  command=lambda: set_image_size(1024, 768)).pack(side=tk.LEFT, padx=1, pady=1)
        tk.Button(button_frame, text="1024 x 473",
                  command=lambda: set_image_size(1024, 473)).pack(side=tk.LEFT, padx=1, pady=1)
        tk.Button(button_frame, text="1024 x 576",
                  command=lambda: set_image_size(1024, 576)).pack(side=tk.LEFT, padx=1, pady=1)

        button_frame2 = tk.Frame(input_frame)
        button_frame2.pack()

        tk.Button(button_frame2, text="710 x 768",
                  command=lambda: set_image_size(710, 768)).pack(side=tk.LEFT, padx=1, pady=1)
        tk.Button(button_frame2, text="1280 x 768",
                  command=lambda: set_image_size(1280, 768)).pack(side=tk.LEFT, padx=1, pady=1)
        tk.Button(button_frame2, text="1920 x 1080",
                  command=lambda: set_image_size(1920, 1080)).pack(side=tk.LEFT, padx=1, pady=1)

        # 生成圖文原始碼按鈕
        ttk.Button(input_frame, text="📑 生成原始碼到剪貼簿", style="OK.TButton",
                   command=self.generate_code).pack(padx=5, pady=5)

    # 確保只能選擇其中一個按鈕的功能
    def update_checkbutton_state(self, selected_var):
        if selected_var.get():
            if selected_var is self.include_symbol_up:
                self.include_symbol_down.set(False)
            else:
                self.include_symbol_up.set(False)

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

    ###############
    ### 批次處理 ###
    ###############

    def batch_widgets(self):

        # 字體設定
        style.configure('HANDLE.TButton', font=('微軟正黑體', 13), background='#A0522D',
                        borderwidth=1)
        style.map('HANDLE.TButton', foreground=[('pressed', 'black'), ('active', 'white')],
                  background=[('pressed', '#A0522D'), ('active', '#8B4513')])

        self.image_per2_merge_button = ttk.Button(
            self.tab2, text="【圖片倆倆合併】點我載入圖片並處理", style="HANDLE.TButton", command=self.load_images)
        self.image_per2_merge_button.pack(fill='both', padx=2, pady=2)
        ToolTip(self.image_per2_merge_button, msg="每兩張圖片水平合併成一張圖片，\n圖片總數為單數則最後一張不合併\n(支援格式：.jpg、.jpeg、.png)",
                delay=0.2, fg="#ffffff", bg="#1c1c1c", padx=8, pady=5)

        self.sub2txt_button = ttk.Button(
            self.tab2, text="【字幕檔轉時間軸標記】點我載入字幕檔並處理", style="HANDLE.TButton", command=self.sub2txt)
        self.sub2txt_button.pack(fill='both', padx=2, pady=2)
        ToolTip(self.sub2txt_button, msg="全自動批次 SRT 字幕檔轉換為 TXT 時間軸標記\n(支援格式：.srt)", delay=0.2,
                fg="#ffffff", bg="#1c1c1c", padx=8, pady=5)

        self.convert_gpx_button = ttk.Button(
            self.tab2, text="【航跡檔轉航點座標 】點我載入航跡檔並處理", style="HANDLE.TButton", command=self.convert_gpx_files)
        self.convert_gpx_button.pack(fill='both', padx=2, pady=2)
        ToolTip(self.convert_gpx_button, msg="全自動批次 GPX 航跡檔轉換為航點座標\n(支援格式：.gpx)", delay=0.2,
                fg="#ffffff", bg="#1c1c1c", padx=8, pady=5)

        self.merge_audio_button = ttk.Button(
            self.tab2, text="【音訊合併】點我載入音訊檔並處理", style="HANDLE.TButton", command=self.merge_audio)
        self.merge_audio_button.pack(fill='both', padx=2, pady=2)
        ToolTip(self.merge_audio_button, msg="全自動音訊檔合併，輸出規格為 MP3 320kbps\n(支援格式：.mp3、.wav)", delay=0.2,
                fg="#ffffff", bg="#1c1c1c", padx=8, pady=5)

    ## 批次處理：圖片倆倆合併 ##

    def load_images(self):
        self.images = filedialog.askopenfilenames(initialdir=os.getcwd(
        ), title="選擇圖片", filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if len(self.images) == 0:
            messagebox.showinfo("提示", "未選擇任何圖片，此次處理結束")
            return
        self.merge_images()

    def merge_images(self):
        self.image_per2_merge_button.configure(state='disabled')
        threading.Thread(target=self.merge_thread).start()

    def merge_thread(self):
        # 如果圖片總數為單數，最後一張不合併
        if len(self.images) % 2 == 1:
            self.images = self.images[:-1]

        # 每兩張圖片合併
        for i in range(0, len(self.images), 2):
            image1 = Image.open(self.images[i])
            image2 = Image.open(self.images[i+1])
            width = image1.width + image2.width
            height = image1.height
            new_image = Image.new('RGB', (width, height))
            new_image.paste(image1, (0, 0))
            new_image.paste(image2, (image1.width, 0))
            output_path = os.path.join(BUILD_DIR, f'merge_{i//2}.jpg')
            new_image.save(output_path)

        # 使用檔案總管打開 build 目錄
        os.startfile(BUILD_DIR)

        self.image_per2_merge_button.configure(state='normal')

    ## 批次處理：字幕檔轉時間軸標記 ##

    def sub2txt(self):
        self.files = filedialog.askopenfilenames()
        if len(self.files) == 0:
            messagebox.showinfo("提示", "未選擇任何字幕檔，此次處理結束")
            return

        for file_path in self.files:
            filename = os.path.basename(file_path)

            # 讀取檔案
            with open(file_path, 'r', encoding='utf-16 le') as f:
                text = f.read()

            # 使用正規表達式進行批次尋找取代的動作
            text = re.sub(r'\s\n[0-9][0-9][0-9]', '', text)
            text = re.sub(r'\s\n[0-9][0-9]', '', text)
            text = re.sub(r'\s\n[0-9]', '', text)
            text = re.sub(r',[0-9][0-9][0-9] --> .*\n', ' ', text)
            text = re.sub(r',[0-9][0-9] --> .*\n', ' ', text)
            text = re.sub(r',[0-9] --> .*\n', ' ', text)

            # 刪除第一行
            text = text.split('\n', 1)[1]

            # 新增第一行
            text = '00:00:00 片頭\n' + text

            # 將結果寫入新檔案
            output_filename = os.path.splitext(filename)[0] + '.txt'
            output_path = os.path.join(BUILD_DIR, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            # 將結果輸出到終端機
            with open(output_path, 'r', encoding='utf-8') as f:
                output_text = f.read()
                print(f'======== {output_filename} ========')
                print(output_text)

        # 直接開啟輸出目錄
        os.startfile(BUILD_DIR)

    ## 批次處理：航跡檔轉航點座標 ##

    def convert_coordinate(self, org, to, lon, lat, is_int):
        # 座標轉換
        transformer = pyproj.Transformer.from_crs(org, to, always_xy=True)
        lon, lat = transformer.transform(lon, lat)
        if is_int:
            return int(lon), int(lat)
        else:
            return lon, lat

    def convert_gpx_files(self):
        # 定義投影坐標系
        twd67_longlat = pyproj.CRS(
            "+proj=longlat +ellps=aust_SA +towgs84=-752,-358,-179,-.0000011698,.0000018398,.0000009822,.00002329 +no_defs"
        )  # TWD67 經緯度
        twd67_tm2 = pyproj.CRS(
            "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 "
            "+ellps=aust_SA +towgs84=-752,-358,-179,-0.0000011698,0.0000018398,0.0000009822,0.00002329 +units=m +no_defs"
        )  # TWD67 二度分帶
        twd97_longlat = pyproj.CRS(
            "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
        )  # TWD97(WGS84) 經緯度
        twd97_tm2 = pyproj.CRS(
            "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +units=m +no_defs"
        )  # TWD97 二度分帶

        # 開啟檔案選擇對話框，讓使用者選擇要載入的檔案
        file_paths = tk.filedialog.askopenfilenames(
            title="選擇 GPX 檔案",
            filetypes=[("GPX files", "*.gpx")])

        # 如果沒有選擇任何檔案，顯示提示訊息
        if not file_paths:
            messagebox.showinfo("提示", "未選擇任何航跡檔，此次處理結束")
            return

        # 讀取每個檔案，提取所需資訊，並輸出到 .txt 檔案
        for file_path in file_paths:
            # 讀取 .gpx 檔案
            with open(file_path, "r", encoding="utf-8") as gpx_file:
                gpx = gpxpy.parse(gpx_file)

            # 提取所需資訊
            wpt_info = []
            for wpt in gpx.waypoints:
                name = wpt.name
                lon = wpt.longitude
                lat = wpt.latitude
                lon_twd67_longlat, lat_twd67_longlat = self.convert_coordinate(
                    twd97_longlat, twd67_longlat, lon, lat, False)
                lon_twd67_tm2_T, lat_twd67_tm2_T = self.convert_coordinate(
                    twd97_longlat, twd67_tm2, lon, lat, True)
                lon_twd67_tm2_F, lat_twd67_tm2_F = self.convert_coordinate(
                    twd97_longlat, twd67_tm2, lon, lat, False)
                lon_twd97_tm2_T, lat_twd97_tm2_T = self.convert_coordinate(
                    twd97_longlat, twd97_tm2, lon, lat, True)
                lon_twd97_tm2_F, lat_twd97_tm2_F = self.convert_coordinate(
                    twd97_longlat, twd97_tm2, lon, lat, False)
                wpt_info.append(
                    f"{name}\n▶️ TWD67 經緯度座標值: {lon_twd67_longlat}, {lat_twd67_longlat} \
                    \n▶️ TWD67 二度分帶座標值: {lon_twd67_tm2_T}, {lat_twd67_tm2_T} ({lon_twd67_tm2_F}, {lat_twd67_tm2_F}) \
                    \n▶️ TWD97(WGS84) 經緯度座標值: {wpt.longitude}, {wpt.latitude} \
                    \n▶️ TWD97 二度分帶座標值: {lon_twd97_tm2_T}, {lat_twd97_tm2_T} ({lon_twd97_tm2_F}, {lat_twd97_tm2_F}) \
                    \n\n")

            # 將結果輸出到 .txt 檔案
            output_file_path = os.path.join("build", os.path.splitext(
                os.path.basename(file_path))[0] + ".txt")
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                output_file.writelines(wpt_info)

        # 直接開啟輸出目錄
        os.startfile(BUILD_DIR)

    ## 批次處理：音訊合併 ##

    def merge_audio(self):
        # 選擇多個音訊檔案
        files = filedialog.askopenfilenames(
            filetypes=[("音訊檔案", "*.mp3;*.wav")])
        if len(files) < 2:
            messagebox.showinfo("提示", "未選擇兩個（含）以上的音訊檔，此次處理結束")
            return
        # 載入音訊檔案
        audio_files = [pydub.AudioSegment.from_file(
            file) for file in files]
        # 合併音訊檔案
        combined_audio = pydub.AudioSegment.empty()
        for audio in audio_files:
            combined_audio += audio
        # 輸出合併後的音訊檔案
        output_file = os.path.join(BUILD_DIR, os.path.splitext(
            os.path.basename(files[0]))[0] + "_merge.mp3")
        combined_audio.export(output_file, format="mp3", bitrate="320k")
        # 顯示訊息視窗
        tk.messagebox.showinfo("提示", f"音訊檔案已合併，並儲存至 {output_file}")

        # 直接開啟輸出目錄
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

        for i, button in enumerate(buttons):
            new_button = tk.Button(button_frame, text=button[0], font=font,
                                   width=6, height=1,
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

        for i, button in enumerate(buttons):
            new_button = tk.Button(button_frame, text=button[0], font=font,
                                   width=18, height=1,
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
        # 建立可捲動的文字方塊
        txt = scrolledtext.ScrolledText(
            self.tab0, width=50, height=20, font=('微軟正黑體', 13))
        txt.pack(fill='both', expand=True)
        # 將文字放入文字方塊中
        text = "版本：" + VERSION + "\n軟體開發及維護者：萌芽站長\n" \
            "萌芽系列網站 ‧ Mnya Series Website ‧ Mnya.tw\n" \
            "\n ■ 更新日誌 ■ \n" \
            "2023/03/23：V1.3.5 複製取用、快速連結內容更新\n" \
            "2023/03/20：V1.3.4 批次處理頁籤內新增音訊合併功能，需依賴 ffmpeg.exe 及 ffprobe.exe\n" \
            "2023/03/20：V1.3.3 批次處理頁籤內新增航跡檔轉航點座標功能\n" \
            "2023/03/19：V1.3.2 新增快速連結頁籤\n" \
            "2023/03/18：V1.3.1 新增複製取用頁籤\n" \
            "2023/03/18：V1.3 新增設定頁籤，新增啟動時最小化功能\n" \
            "2023/03/18：V1.2.3 主要功能新增勾選選項「包含\"▼\"」，與「包含\"▲\"」只能擇一\n" \
            "2023/03/17：V1.2.2 批次處理頁籤內新增字幕檔轉時間軸標記功能\n" \
            "2023/03/17：V1.2.1 自動記憶上次關閉前的視窗位置\n" \
            "2023/03/16：V1.2 新增批次處理頁籤，新增圖片倆倆合併功能\n" \
            "2023/03/15：V1.1 樣式美化，新增頁籤，預設採用暗黑模式\n" \
            "2023/03/15：V1.0 初始版釋出\n" \
            "\n ■ MIT License ■ \n" \
            "\nCopyright (c) 2023 Feng, Cheng-Chi (萌芽站長) @ 萌芽系列網站 ‧ Mnya Series Website ‧ Mnya.tw\n" \
            "\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n" \
            "\nThe above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n" \
            "\nTHE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n"

        txt.insert("1.0", text)


if __name__ == "__main__":
    import datetime

    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    root = tk.Tk()
    style = ttk.Style("superhero")
    root.title(APP_NAME)
    root.geometry("{}x{}".format(WINDOW_WIDTH, WINDOW_HEIGHT))
    root.iconbitmap('icon.ico')
    app = App(master=root)
    app.mainloop()
