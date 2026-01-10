import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading


def open_gpx_slope_window(app, parent, config, save_config_func, on_close, generate_func):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()  # 先隱藏
    subwin.title("航跡檔轉坡度分析圖")
    subwin.resizable(False, False)
    try:
        subwin.iconbitmap('icon.ico')
    except tk.TclError:
        pass  # icon.ico not found
    width, height = 500, 320
    subwin.transient(parent)
    subwin.lift()
    subwin.focus_force()
    app.center_child_window(subwin, width, height)
    subwin.deiconify()  # 再顯示

    # 關閉處理
    def handle_close():
        if callable(on_close):
            on_close()
        subwin.destroy()

    subwin.protocol("WM_DELETE_WINDOW", handle_close)

    frame = tk.Frame(subwin)
    frame.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
    row = 0

    font_label = ('微軟正黑體', 12)
    font_entry = ('微軟正黑體', 11)
    font_btn = ('微軟正黑體', 11, 'bold')

    # GPX 來源
    tk.Label(frame, text='GPX 來源', font=font_label).grid(
        row=row, column=0, sticky='w', pady=5)
    entry_gpx_path = tk.Entry(frame, width=30, font=font_entry)
    entry_gpx_path.grid(row=row, column=1, padx=5, sticky='ew')

    def select_gpx_file():
        filepath = filedialog.askopenfilename(
            title='選擇 GPX 檔案',
            filetypes=[('GPX files', '*.gpx'), ('全部檔案', '*.*')]
        )
        if filepath:
            entry_gpx_path.delete(0, tk.END)
            entry_gpx_path.insert(0, filepath)

    tk.Button(frame, text='載入檔案', command=select_gpx_file,
              font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    # 參數設定 Helper
    def add_param_row(label_text, config_key, default_val):
        nonlocal row
        tk.Label(frame, text=label_text, font=font_label).grid(
            row=row, column=0, sticky='w', pady=5)
        entry = tk.Entry(frame, width=10, font=font_entry, justify='center')
        entry.grid(row=row, column=1, padx=5, sticky='w')
        entry.insert(0, config.get(config_key, default_val))
        row += 1
        return entry

    entry_width = add_param_row('圖片寬度', "WIDTH_PX", "1024")
    entry_height = add_param_row('圖片高度', "HEIGHT_PX", "768")
    entry_dpi = add_param_row('解析度 (DPI)', "DPI", "100")
    entry_interval = add_param_row('採樣間距 (m)', "INTERVAL_M", "200")
    entry_bg_color = add_param_row('背景顏色', "BG_COLOR", "#F5F5F5")

    # 開始執行按鈕與狀態
    btn_run = tk.Button(frame, text='開始執行', width=18, height=2, font=font_btn)
    btn_run.grid(row=row, column=0, columnspan=3, pady=20)
    row += 1

    label_status = tk.Label(
        frame, text='', font=font_label, fg='blue', wraplength=420)
    label_status.grid(row=row, column=0, columnspan=3, pady=(5, 0))

    def run():
        gpx_path = entry_gpx_path.get().strip()

        if not gpx_path or not os.path.isfile(gpx_path):
            messagebox.showerror("錯誤", "請選擇有效的 GPX 檔案", parent=subwin)
            return

        # 儲存設定
        new_config = {
            "WIDTH_PX": entry_width.get().strip(),
            "HEIGHT_PX": entry_height.get().strip(),
            "DPI": entry_dpi.get().strip(),
            "INTERVAL_M": entry_interval.get().strip(),
            "BG_COLOR": entry_bg_color.get().strip()
        }
        save_config_func(new_config)

        btn_run.config(state=tk.DISABLED)
        label_status.config(text="處理中，請稍候...")

        def task():
            try:
                output_dir = "build"
                save_path = generate_func(gpx_path, output_dir, new_config)
                label_status.config(text="處理完成！")
                messagebox.showinfo(
                    "成功", f"已生成圖片：\n{save_path}", parent=subwin)
                os.startfile(os.path.dirname(save_path))
            except Exception as e:
                label_status.config(text="處理失敗！")
                messagebox.showerror("錯誤", f"處理失敗：\n{e}", parent=subwin)
            finally:
                btn_run.config(state=tk.NORMAL)

        threading.Thread(target=task, daemon=True).start()

    btn_run.config(command=run)

    return subwin
