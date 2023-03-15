import tkinter as tk
import tkinter.font as tkFont
import pyperclip


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("萌芽系列網站圖文原始碼生成器")
        self.pack()
        self.create_widgets()

    def create_widgets(self):

        # 字體設定
        font = tkFont.Font(family="微軟正黑體", size=13)

        # 萌芽系列網站按鈕組
        self.sites = [("💻 萌芽綜合天地", "cc"),
                      ("⛰ 萌芽爬山網", "k3"),
                      ("🍹 萌芽悠遊網", "yo"),
                      ("🌏 萌芽地科網", "es"),
                      ("🎵 萌芽音樂網", "ms"),
                      ("🖼 萌芽二次元", "2d"),
                      ("🎮 萌芽Game網", "games")]
        self.site_var = tk.StringVar(value=self.sites[0][1])
        site_frame = tk.Frame(self)
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
        input_frame = tk.Frame(self)
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

        button_frame = tk.Frame(input_frame)
        button_frame.pack()

        def set_image_size(width, height):
            self.image_width_var.set(width)
            self.image_height_var.set(height)

        tk.Button(button_frame, text="1024x768",
                  command=lambda: set_image_size(1024, 768)).pack(side=tk.LEFT, padx=1, pady=5)
        tk.Button(button_frame, text="1024x473",
                  command=lambda: set_image_size(1024, 473)).pack(side=tk.LEFT, padx=1, pady=5)
        tk.Button(button_frame, text="1024x576",
                  command=lambda: set_image_size(1024, 576)).pack(side=tk.LEFT, padx=1, pady=5)

        # 生成圖文原始碼按鈕
        tk.Button(input_frame, text="📑 生成圖文原始碼到剪貼簿",
                  command=self.generate_code, font=font).pack(padx=5, pady=5)

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


if __name__ == "__main__":
    import datetime
    root = tk.Tk()
    root.title("萌芽系列網站圖文原始碼生成器")
    root.geometry("400x400")
    root.iconbitmap('icon.ico')
    app = App(master=root)
    app.mainloop()
