import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading


def open_video_repeat_fade_window(app, parent, config, save_config_func, video_repeat_fade_func, on_close):
    """
    開啟「影片重複淡化工具」子視窗，並進行參數設定、執行與結果回傳。

    參數說明:
        app                  : 主程式 App 實例，若需與主程式互動可使用（可選）。
        parent               : 主視窗 (通常為 root 或 app.master)，用於建立子視窗的父物件。
        config               : 初始化視窗時帶入的設定參數 (dict)，例如過去儲存的使用值。
        save_config_func     : 呼叫此函式時儲存參數設定，通常為主程式提供的函式。
        video_repeat_fade_func: 處理影片重複淡化的實際運算函式（如 batch_tools.video_tools 內函式）。
        on_close             : 子視窗關閉時呼叫的 callback，通常用於將主程式的視窗狀態變數設為 None。

    回傳:
        傳回建立的 Toplevel 視窗 (tk.Toplevel 實例)，可供主程式做單例視窗管理。
    """
    subwin = tk.Toplevel(parent)
    subwin.title("影片重複淡化工具")
    subwin.resizable(False, False)
    subwin.iconbitmap('icon.ico')
    width, height = 480, 300
    subwin.transient(parent)
    subwin.lift()
    subwin.focus_force()

    # 關閉視窗時
    def handle_close():
        if callable(on_close):
            on_close()
        subwin.destroy()

    subwin.protocol("WM_DELETE_WINDOW", handle_close)

    # 視窗置中
    parent.update_idletasks()
    x = parent.winfo_x()
    y = parent.winfo_y()
    w = parent.winfo_width()
    h = parent.winfo_height()
    new_x = x + (w - width) // 2
    new_y = y + (h - height) // 2
    subwin.geometry(f"{width}x{height}+{new_x}+{new_y}")

    frame = tk.Frame(subwin, bg='#f4f4f7')
    frame.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
    row = 0

    font_label = ('微軟正黑體', 12)
    font_entry = ('微軟正黑體', 11)
    font_btn = ('微軟正黑體', 11, 'bold')

    tk.Label(frame, text='載入影片', font=font_label, bg='#f4f4f7').grid(
        row=row, column=0, sticky='w')
    entry_file = tk.Entry(frame, width=30, font=font_entry)
    entry_file.grid(row=row, column=1, padx=5)

    def select_file():
        filepath = filedialog.askopenfilename(
            title='選擇影片檔案',
            filetypes=[
                ('影片檔案', '*.mp4;*.mov;*.avi;*.mkv;*.webm;*.flv'), ('全部檔案', '*.*')]
        )
        if filepath:
            entry_file.delete(0, tk.END)
            entry_file.insert(0, filepath)
    tk.Button(frame, text='選擇檔案', command=select_file,
              font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    tk.Label(frame, text='目標長度', font=font_label, bg='#f4f4f7').grid(
        row=row, column=0, sticky='w')
    frame_time = tk.Frame(frame, bg='#f4f4f7')
    frame_time.grid(row=row, column=1, padx=5, sticky='w')
    entry_minute = tk.Entry(frame_time, width=4,
                            font=font_entry, justify='center')
    entry_minute.grid(row=0, column=0)
    tk.Label(frame_time, text='分', font=font_label,
             bg='#f4f4f7').grid(row=0, column=1, padx=5)
    entry_second = tk.Entry(frame_time, width=4,
                            font=font_entry, justify='center')
    entry_second.grid(row=0, column=2, padx=5)
    tk.Label(frame_time, text='秒', font=font_label,
             bg='#f4f4f7').grid(row=0, column=3, padx=5)
    row += 1

    tk.Label(frame, text='淡化秒數', font=font_label, bg='#f4f4f7').grid(
        row=row, column=0, sticky='w')
    frame_fade = tk.Frame(frame, bg='#f4f4f7')
    frame_fade.grid(row=row, column=1, padx=5, sticky='w')
    entry_fade = tk.Entry(frame_fade, width=4,
                          font=font_entry, justify='center')
    entry_fade.insert(0, config.get("fade_sec", "0.5"))
    entry_fade.grid(row=0, column=0)
    tk.Label(frame_fade, text='秒 (0.1~5)', font=font_label,
             bg='#f4f4f7').grid(row=0, column=1, padx=5)
    row += 1

    tk.Label(frame, text='輸出寬度', font=font_label, bg='#f4f4f7').grid(
        row=row, column=0, sticky='w')
    frame_width = tk.Frame(frame, bg='#f4f4f7')
    frame_width.grid(row=row, column=1, padx=5, sticky='w')
    entry_width = tk.Entry(frame_width, width=8,
                           font=font_entry, justify='center')
    entry_width.grid(row=0, column=0)
    tk.Label(frame_width, text='px', font=font_label,
             bg='#f4f4f7').grid(row=0, column=1, padx=5)
    row += 1

    tk.Label(frame, text='輸出高度', font=font_label, bg='#f4f4f7').grid(
        row=row, column=0, sticky='w')
    frame_height = tk.Frame(frame, bg='#f4f4f7')
    frame_height.grid(row=row, column=1, padx=5, sticky='w')
    entry_height = tk.Entry(frame_height, width=8,
                            font=font_entry, justify='center')
    entry_height.grid(row=0, column=0)
    tk.Label(frame_height, text='px', font=font_label,
             bg='#f4f4f7').grid(row=0, column=1, padx=5)
    row += 1

    tk.Label(frame, text='輸出位置', font=font_label, bg='#f4f4f7').grid(
        row=row, column=0, sticky='w')
    entry_output = tk.Entry(frame, width=30, font=font_entry)
    entry_output.grid(row=row, column=1, padx=5)

    def select_output_folder():
        folderpath = filedialog.askdirectory(title='選擇輸出資料夾')
        if folderpath:
            entry_output.delete(0, tk.END)
            entry_output.insert(0, folderpath)
    tk.Button(frame, text='選擇資料夾', command=select_output_folder,
              font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    btn_run = tk.Button(frame, text='開始執行', width=18, height=2, font=font_btn,
                        bg='#6cb2eb', fg='white', activebackground='#2779bd')
    btn_run.grid(row=row, column=0, columnspan=3, pady=20)
    row += 1

    label_status = tk.Label(
        frame, text='', font=font_label, fg='blue', bg='#f4f4f7')
    label_status.grid(row=row, column=0, columnspan=3, pady=(5, 0))

    # 預設帶入上次參數
    if "target_length" in config and ':' in str(config["target_length"]):
        min_str, sec_str = str(config["target_length"]).split(':')
        entry_minute.insert(0, min_str)
        entry_second.insert(0, sec_str)
    if "output_folder" in config:
        entry_output.insert(0, config["output_folder"])
    if "out_width" in config:
        entry_width.insert(0, str(config["out_width"]))
    if "out_height" in config:
        entry_height.insert(0, str(config["out_height"]))
    if "fade_sec" in config:
        entry_fade.delete(0, tk.END)
        entry_fade.insert(0, str(config["fade_sec"]))

    def run():
        input_file = entry_file.get().strip()
        output_dir = entry_output.get().strip()
        min_text = entry_minute.get().strip()
        sec_text = entry_second.get().strip()
        fade_text = entry_fade.get().strip()
        width_text = entry_width.get().strip()
        height_text = entry_height.get().strip()
        # 檢查
        try:
            fade_time = float(fade_text) if fade_text else 0.5
            if not (0.1 <= fade_time <= 5):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "錯誤", "淡化秒數請輸入 0.1 ~ 5.0 之間的數值", parent=subwin)
            return
        try:
            minute = int(min_text) if min_text else 0
            second = int(sec_text) if sec_text else 0
            if minute < 0 or second < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入正確的長度（分鐘與秒）", parent=subwin)
            return
        total_length = minute * 60 + second
        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("錯誤", "請選擇正確的輸入影片檔案", parent=subwin)
            return
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("錯誤", "請選擇正確的輸出資料夾", parent=subwin)
            return
        if total_length <= 0:
            messagebox.showerror("錯誤", "請輸入正確的目標長度", parent=subwin)
            return
        try:
            out_width = int(width_text)
            out_height = int(height_text)
            if out_width <= 0 or out_height <= 0:
                raise ValueError
        except:
            messagebox.showerror("錯誤", "請輸入正確的輸出寬度與高度", parent=subwin)
            return
        btn_run.config(state=tk.DISABLED)
        label_status.config(text="處理中，請稍候...")

        # 儲存參數到 config.json
        config_dict = {
            "target_length": f"{minute}:{second}",
            "output_folder": output_dir,
            "out_width": out_width,
            "out_height": out_height,
            "fade_sec": fade_time
        }
        save_config_func(config_dict)

        def work():
            try:
                output_file = video_repeat_fade_func(
                    input_file, output_dir, minute, second, fade_time, out_width, out_height
                )
                label_status.config(text=f"完成！輸出檔案：{output_file}")
                messagebox.showinfo(
                    "成功", f"處理完成！\n輸出檔案位置：\n{output_file}", parent=subwin)
            except Exception as e:
                label_status.config(text="錯誤：" + str(e))
                messagebox.showerror("錯誤", f"處理失敗：{e}", parent=subwin)
            finally:
                btn_run.config(state=tk.NORMAL)
        threading.Thread(target=work, daemon=True).start()

    btn_run.config(command=run)
    return subwin
