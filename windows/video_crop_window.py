import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading

def open_video_crop_window(app, parent, config, save_config_func, video_crop_func, on_close):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()  # 先隱藏
    subwin.title("影片裁切工具")
    subwin.resizable(False, False)
    try:
        subwin.iconbitmap('icon.ico')
    except tk.TclError:
        pass  # icon.ico not found
    width, height = 480, 220
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

    # 影片來源
    tk.Label(frame, text='影片來源', font=font_label).grid(row=row, column=0, sticky='w', pady=5)
    entry_video_path = tk.Entry(frame, width=30, font=font_entry)
    entry_video_path.grid(row=row, column=1, padx=5, sticky='ew')

    def select_video_file():
        filepath = filedialog.askopenfilename(
            title='選擇影片檔案',
            filetypes=[('影片檔案', '*.mp4;*.mov;*.avi;*.mkv;*.webm;*.flv'), ('全部檔案', '*.*')]
        )
        if filepath:
            entry_video_path.delete(0, tk.END)
            entry_video_path.insert(0, filepath)

    tk.Button(frame, text='載入影片', command=select_video_file, font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    # 裁切寬度
    tk.Label(frame, text='寬度', font=font_label).grid(row=row, column=0, sticky='w', pady=5)
    entry_width = tk.Entry(frame, width=10, font=font_entry, justify='center')
    entry_width.grid(row=row, column=1, padx=5, sticky='w')
    entry_width.insert(0, config.get("width", "1920"))
    row += 1

    # 裁切高度
    tk.Label(frame, text='高度', font=font_label).grid(row=row, column=0, sticky='w', pady=5)
    entry_height = tk.Entry(frame, width=10, font=font_entry, justify='center')
    entry_height.grid(row=row, column=1, padx=5, sticky='w')
    entry_height.insert(0, config.get("height", "1080"))
    row += 1


    # 開始執行按鈕與狀態
    btn_run = tk.Button(frame, text='開始執行', width=18, height=2, font=font_btn)
    btn_run.grid(row=row, column=0, columnspan=3, pady=20)
    row += 1

    label_status = tk.Label(frame, text='', font=font_label, fg='blue', wraplength=420)
    label_status.grid(row=row, column=0, columnspan=3, pady=(5, 0))

    def run():
        video_path = entry_video_path.get().strip()
        width_str = entry_width.get().strip()
        height_str = entry_height.get().strip()

        if not video_path or not os.path.isfile(video_path):
            messagebox.showerror("錯誤", "請選擇有效的影片檔案", parent=subwin)
            return

        try:
            width = int(width_str)
            height = int(height_str)
            if width <= 0 or height <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的寬度和高度", parent=subwin)
            return
        
        # 儲存設定
        current_config = {"width": width, "height": height}
        save_config_func(current_config)

        btn_run.config(state=tk.DISABLED)
        label_status.config(text="處理中，請稍候...")

        def work():
            try:
                output_path = video_crop_func(video_path, width, height, "build")
                label_status.config(text="處理完成！")
                messagebox.showinfo("成功", f"影片裁切完成！\n檔案儲存於：\n{output_path}", parent=subwin)
                os.startfile(os.path.dirname(output_path))
            except Exception as e:
                label_status.config(text="處理失敗！")
                messagebox.showerror("錯誤", f"處理失敗：\n{e}", parent=subwin)
            finally:
                btn_run.config(state=tk.NORMAL)

        threading.Thread(target=work, daemon=True).start()

    btn_run.config(command=run)

    return subwin
