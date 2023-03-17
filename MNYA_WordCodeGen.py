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

# 應用配置
WINDOW_WIDTH = 410  # 寬度
WINDOW_HEIGHT = 430  # 高度
APP_NAME = "萌芽系列網站圖文原始碼生成器"  # 應用名稱
VERSION = "V1.2.1"  # 版本

# 配置檔案名稱
CONFIG_FILENAME = "config.json"


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # 讀取配置檔案
        self.config_path = CONFIG_FILENAME
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
        self.about()

    def load_window_position(self):
        # 如果配置檔案存在，讀取視窗位置
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                self.window_x = config.get("x", 0)
                self.window_y = config.get("y", 0)
        else:
            # 如果配置檔案不存在，使用預設位置
            self.window_x = 0
            self.window_y = 0

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

    def save_window_position(self):
        # 保存視窗位置到配置檔案
        with open(self.config_path, "w") as f:
            config = {
                "x": root.winfo_x(),
                "y": root.winfo_y(),
            }
            json.dump(config, f)

    def on_close(self):
        # 保存視窗位置
        self.save_window_position()

        # 關閉視窗
        root.destroy()

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

        self.include_symbol_var = tk.BooleanVar(value=True)
        tk.Checkbutton(include_frame, text="包含\"▲\"",
                       variable=self.include_symbol_var, font=font).pack()

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
            code += f'<img src="{img_url}" width="{image_width}" height="{image_height}" />'
            if self.include_symbol_var.get():
                code += "\n▲\n"
            else:
                code += "\n"
            pyperclip.copy(code)

    def batch_widgets(self):

        # 字體設定
        style.configure('HANDLE.TButton', font=('微軟正黑體', 13), background='#A0522D',
                        borderwidth=1)
        style.map('HANDLE.TButton', foreground=[('pressed', 'black'), ('active', 'white')],
                  background=[('pressed', '#A0522D'), ('active', '#8B4513')])

        self.image_per2_merge_button = ttk.Button(
            self.tab2, text="【圖片倆倆合併】點我載入多張圖片並處理", style="HANDLE.TButton", command=self.load_images)
        self.image_per2_merge_button.pack(fill='both', padx=2, pady=2)
        ToolTip(self.image_per2_merge_button, msg="每兩張圖片水平合併成一張圖片，\n圖片總數為單數則最後一張不合併", delay=0.2,
                fg="#ffffff", bg="#1c1c1c", padx=8, pady=5)

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
            output_path = os.path.join(build_dir, f'merge_{i//2}.jpg')
            new_image.save(output_path)

        # 使用檔案總管打開 build 目錄
        os.startfile(build_dir)

        self.image_per2_merge_button.configure(state='normal')

    def about(self):
        # 建立可捲動的文字方塊
        txt = scrolledtext.ScrolledText(
            self.tab0, width=50, height=20, font=('微軟正黑體', 13))
        txt.pack(fill='both', expand=True)
        # 將文字放入文字方塊中
        text = "版本：" + VERSION + "\n軟體開發及維護者：萌芽站長\n" \
            "萌芽系列網站 ‧ Mnya Series Website ‧ Mnya.tw\n" \
            "\n ■ 更新日誌 ■ \n" \
            "2023/03/17：V1.2.1 自動記憶上次關閉前的視窗位置\n" \
            "2023/03/16：V1.2 新增批次處理頁籤，新增圖片倆倆合併功能\n" \
            "2023/03/15：V1.1 樣式美化，新增頁籤，預設採用暗黑模式\n" \
            "2023/03/15：V1.0 初始版釋出\n"
        txt.insert("1.0", text)


if __name__ == "__main__":
    import datetime

    # 設定要處理的目錄
    build_dir = "build"
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    root = tk.Tk()
    style = ttk.Style("superhero")
    root.title(APP_NAME)
    root.geometry("{}x{}".format(WINDOW_WIDTH, WINDOW_HEIGHT))
    root.iconbitmap('icon.ico')
    app = App(master=root)
    app.mainloop()
