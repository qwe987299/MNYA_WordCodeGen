import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import re
import urllib.request

def open_youtube_thumbnail_window(
    app, parent, config, save_config_func, on_close
):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()
    subwin.title("YouTube 縮圖下載器")
    subwin.resizable(False, False)
    try:
        subwin.iconbitmap('icon.ico')
    except:
        pass
    
    width, height = 500, 320
    subwin.transient(parent)
    
    # 置中視窗
    parent.update_idletasks()
    x = parent.winfo_x()
    y = parent.winfo_y()
    w = parent.winfo_width()
    h = parent.winfo_height()
    new_x = x + (w - width) // 2
    new_y = y + (h - height) // 2
    subwin.geometry(f"{width}x{height}+{new_x}+{new_y}")
    subwin.deiconify()

    def handle_close():
        if callable(on_close):
            on_close()
        subwin.destroy()
    subwin.protocol("WM_DELETE_WINDOW", handle_close)

    frame = tk.Frame(subwin, bg='#f4f4f7')
    frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    font_label = ('微軟正黑體', 12)
    font_entry = ('微軟正黑體', 11)
    font_btn = ('微軟正黑體', 11, 'bold')

    tk.Label(frame, text='請輸入 YouTube 網址或影片 ID：', font=font_label, bg='#f4f4f7').pack(anchor='w', pady=(0, 5))
    
    url_var = tk.StringVar()
    url_entry = tk.Entry(frame, textvariable=url_var, font=font_entry, width=50)
    url_entry.pack(fill='x', pady=5)
    url_entry.focus_set()

    tk.Label(frame, text='下載目錄：', font=font_label, bg='#f4f4f7').pack(anchor='w', pady=(10, 5))
    
    path_frame = tk.Frame(frame, bg='#f4f4f7')
    path_frame.pack(fill='x')
    
    # 預設路徑
    default_path = config.get("yt_download_path", os.path.abspath("build"))
    if not os.path.exists(default_path):
        os.makedirs(default_path, exist_ok=True)
        
    path_var = tk.StringVar(value=default_path)
    path_entry = tk.Entry(path_frame, textvariable=path_var, font=font_entry)
    path_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
    
    def select_folder():
        folder = filedialog.askdirectory(initialdir=path_var.get())
        if folder:
            path_var.set(folder)
            save_config_func({"yt_download_path": folder})
            
    btn_browse = tk.Button(path_frame, text='瀏覽...', command=select_folder, font=('微軟正黑體', 10))
    btn_browse.pack(side='right')

    status_label = tk.Label(frame, text='', font=('微軟正黑體', 10), fg='blue', bg='#f4f4f7')
    status_label.pack(pady=10)

    def extract_video_id(url_or_id):
        # 匹配常見的 YouTube URL 格式
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:shorts\/)([0-9A-Za-z_-]{11}).*',
            r'(?:be\/)([0-9A-Za-z_-]{11}).*',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        return None

    def download_thumbnail():
        input_val = url_var.get().strip()
        video_id = extract_video_id(input_val)
        
        if not video_id:
            messagebox.showerror("錯誤", "無法辨識 YouTube 影片 ID，請檢查網址格式。")
            return
        
        save_dir = path_var.get()
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except:
                messagebox.showerror("錯誤", "無法建立下載目錄。")
                return

        btn_download.config(state=tk.DISABLED)
        status_label.config(text="正在嘗試下載最高畫質...", fg="blue")

        def task():
            qualities = [
                ("maxresdefault", "1080p/720p"),
                ("sddefault", "480p"),
                ("hqdefault", "360p")
            ]
            
            success = False
            for slug, label in qualities:
                img_url = f"https://img.youtube.com/vi/{video_id}/{slug}.jpg"
                try:
                    # 使用 urllib 下載
                    request = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(request) as response:
                        if response.status == 200:
                            # 檢查內容是否為有效的 JPG (YouTube 會回傳一個幾百 bytes 的無效圖片代表不存在)
                            content = response.read()
                            if len(content) > 5000: # 正常縮圖通常大於 5KB
                                file_path = os.path.join(save_dir, f"{video_id}_{slug}.jpg")
                                with open(file_path, "wb") as f:
                                    f.write(content)
                                success = True
                                self_msg = f"下載成功！畫質：{label}"
                                subwin.after(0, lambda m=self_msg: status_label.config(text=m, fg="green"))
                                subwin.after(0, lambda: os.startfile(save_dir))
                                break
                except:
                    continue
            
            if not success:
                subwin.after(0, lambda: status_label.config(text="下載失敗，找不到可用的縮圖。", fg="red"))
            
            subwin.after(0, lambda: btn_download.config(state=tk.NORMAL))

        threading.Thread(target=task, daemon=True).start()

    btn_download = tk.Button(frame, text='🚀 開始下載', command=download_thumbnail,
                            font=font_btn, bg='#008000', fg='white', padx=20, pady=5)
    btn_download.pack(pady=10)

    return subwin
