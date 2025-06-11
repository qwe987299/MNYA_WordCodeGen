import tkinter as tk
from tkinter import filedialog, messagebox
import threading


def open_image_compress_window(
    app, parent, config, save_config_func, compress_func, on_close
):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()  # 先隱藏
    subwin.title("進階圖片壓縮")
    subwin.resizable(False, False)
    subwin.iconbitmap('icon.ico')
    width, height = 480, 380
    subwin.transient(parent)
    subwin.lift()
    subwin.focus_force()
    parent.update_idletasks()
    x = parent.winfo_x()
    y = parent.winfo_y()
    w = parent.winfo_width()
    h = parent.winfo_height()
    new_x = x + (w - width) // 2
    new_y = y + (h - height) // 2
    subwin.geometry(f"{width}x{height}+{new_x}+{new_y}")
    subwin.deiconify()  # 再顯示

    # 關閉處理
    def handle_close():
        if callable(on_close):
            on_close()
        subwin.destroy()
    subwin.protocol("WM_DELETE_WINDOW", handle_close)

    frame = tk.Frame(subwin, bg='#f4f4f7')
    frame.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
    row = 0

    font_label = ('微軟正黑體', 12)
    font_entry = ('微軟正黑體', 11)
    font_btn = ('微軟正黑體', 11, 'bold')

    tk.Label(frame, text='點擊下方方塊選擇圖片進行壓縮', font=font_label, bg='#f4f4f7').grid(
        row=row, column=0, columnspan=3, sticky='w')
    row += 1
    drop_area = tk.Label(frame, text="（點擊選取檔案並處理）", font=(
        '微軟正黑體', 15), bg="#eef", width=36, height=3, relief="ridge", borderwidth=2)
    drop_area.grid(row=row, column=0, columnspan=3, pady=5, sticky='nsew')
    row += 1

    files_set = set()
    file_listbox = tk.Listbox(frame, font=font_entry, height=4, width=38)
    file_listbox.grid(row=row, column=0, columnspan=3, sticky='we', padx=1)
    row += 1

    def drop(event):
        filepaths = filedialog.askopenfilenames(
            title='選擇圖片',
            filetypes=[("JPG/JPEG 檔案", "*.jpg *.jpeg *.JPG *.JPEG")]
        )
        if filepaths:
            for fp in filepaths:
                if fp not in files_set:
                    files_set.add(fp)
                    file_listbox.insert(tk.END, fp)
            # 拖曳完自動壓縮
            do_compress()
    drop_area.bind("<Button-1>", drop)

    # 參數設定
    var_quality = tk.IntVar(value=config.get("imgc_quality", 85))
    var_progressive = tk.BooleanVar(value=config.get("imgc_progressive", True))
    var_overwrite = tk.BooleanVar(value=config.get("imgc_overwrite", True))

    # 第一排：品質
    quality_frame = tk.Frame(frame, bg='#f4f4f7')
    quality_frame.grid(row=row, column=0, columnspan=3,
                       pady=(12, 0), sticky='ew')
    quality_frame.grid_columnconfigure(0, weight=1)
    quality_frame.grid_columnconfigure(1, weight=0)
    quality_frame.grid_columnconfigure(2, weight=1)
    tk.Label(quality_frame, text="品質（0 ~ 100）：", font=font_label, bg='#f4f4f7')\
        .grid(row=0, column=1, sticky='e')
    entry_quality = tk.Entry(
        quality_frame, width=6, textvariable=var_quality, font=font_entry, justify='center')
    entry_quality.grid(row=0, column=2, sticky='w', padx=(8, 0))
    row += 1

    # 第二排：兩個勾選方塊
    checkbox_frame = tk.Frame(frame, bg='#f4f4f7')
    checkbox_frame.grid(row=row, column=0, columnspan=3, pady=(2, 10))
    cb_progressive = tk.Checkbutton(
        checkbox_frame, text="漸進式(Progressive)", variable=var_progressive, font=font_label, bg='#f4f4f7')
    cb_progressive.pack(side=tk.LEFT, padx=16)
    cb_overwrite = tk.Checkbutton(
        checkbox_frame, text="覆蓋原檔", variable=var_overwrite, font=font_label, bg='#f4f4f7')
    cb_overwrite.pack(side=tk.LEFT, padx=16)
    row += 1

    # 儲存設定按鈕

    def save_setting(show_info=False):
        setting = {
            "imgc_quality": var_quality.get(),
            "imgc_progressive": var_progressive.get(),
            "imgc_overwrite": var_overwrite.get(),
        }
        save_config_func(setting)
        if show_info:
            messagebox.showinfo("提示", "設定已儲存且立即生效", parent=subwin)

    btn_save = tk.Button(frame, text='儲存設定', command=lambda: save_setting(True),
                         font=font_btn, bg='#6cb2eb', fg='white')
    btn_save.grid(row=row, column=0, columnspan=3, pady=8)
    row += 1

    # 狀態
    label_status = tk.Label(
        frame, text='', font=font_label, fg='blue', bg='#f4f4f7')
    label_status.grid(row=row, column=0, columnspan=3, pady=2)

    # 壓縮執行
    def do_compress():
        imgs = list(files_set)
        if not imgs:
            label_status.config(text="請先拖曳圖片進來")
            return
        quality = var_quality.get()
        progressive = var_progressive.get()
        overwrite = var_overwrite.get()
        # 寫入 config.json
        save_setting()
        label_status.config(text="壓縮中...")
        btn_save.config(state=tk.DISABLED)

        def worker():
            try:
                out_files, failed = compress_func(
                    imgs,
                    quality=quality,
                    progressive=progressive,
                    overwrite=overwrite
                )
                if out_files:
                    label_status.config(text=f"完成！處理 {len(out_files)} 張圖片。")
                if failed:
                    messagebox.showerror(
                        "錯誤", f"部分檔案壓縮失敗：\n" + '\n'.join(f[0] for f in failed), parent=subwin)
                else:
                    messagebox.showinfo("成功", "圖片壓縮完成！", parent=subwin)
            except Exception as e:
                messagebox.showerror("錯誤", str(e), parent=subwin)
            btn_save.config(state=tk.NORMAL)
        threading.Thread(target=worker, daemon=True).start()

    return subwin
