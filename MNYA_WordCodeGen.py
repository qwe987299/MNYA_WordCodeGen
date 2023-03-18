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

# 測試指令：python MNYA_WordCodeGen.py
# 打包指令：pyinstaller --onefile --icon=icon.ico --noconsole MNYA_WordCodeGen.py

# 應用配置
WINDOW_WIDTH = 410  # 寬度
WINDOW_HEIGHT = 430  # 高度
APP_NAME = "萌芽系列網站圖文原始碼生成器"  # 應用名稱
VERSION = "V1.3"  # 版本
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
        site_frame.pack(side=tk.LEFT, padx=5, pady=5)
        for site, code in self.sites:
            tk.Radiobutton(site_frame, text=site,
                           variable=self.site_var, value=code, font=font, indicatoron=False, width=13, height=1).pack(anchor=tk.W)

        include_frame = tk.Frame(site_frame)
        include_frame.pack(padx=1, pady=10)

        self.include_previous_var = tk.BooleanVar(value=True)
        tk.Checkbutton(include_frame, text="包含前文",
                       variable=self.include_previous_var, font=font).pack()

        self.include_symbol_up = tk.BooleanVar(value=True)
        tk.Checkbutton(include_frame, text="包含\"▲\"",
                       variable=self.include_symbol_up, font=font,
                       command=lambda: self.update_checkbutton_state(self.include_symbol_up)).pack()

        self.include_symbol_down = tk.BooleanVar(value=False)
        tk.Checkbutton(include_frame, text="包含\"▼\"",
                       variable=self.include_symbol_down, font=font,
                       command=lambda: self.update_checkbutton_state(self.include_symbol_down)).pack()

        # 年份、文章編號、文章圖片數、圖片寬度、圖片高度輸入框
        input_frame = tk.Frame(self.tab1)
        input_frame.pack(side=tk.RIGHT, padx=5, pady=5)
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
        ttk.Button(input_frame, text="📑 生成圖文原始碼到剪貼簿", style="OK.TButton",
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
            "2023/03/18：V1.3 新增設定頁籤，新增啟動時最小化功能\n" \
            "2023/03/18：V1.2.3 主要功能新增勾選選項「包含\"▼\"」，與「包含\"▲\"」只能擇一\n" \
            "2023/03/17：V1.2.2 批次處理頁籤內新增字幕檔轉時間軸標記功能\n" \
            "2023/03/17：V1.2.1 自動記憶上次關閉前的視窗位置\n" \
            "2023/03/16：V1.2 新增批次處理頁籤，新增圖片倆倆合併功能\n" \
            "2023/03/15：V1.1 樣式美化，新增頁籤，預設採用暗黑模式\n" \
            "2023/03/15：V1.0 初始版釋出\n"
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
