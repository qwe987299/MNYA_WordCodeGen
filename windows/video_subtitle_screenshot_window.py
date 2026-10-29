import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import ffmpeg
from batch_tools.video_tools import extract_subtitles_start_times


def get_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        return float(probe['format']['duration'])
    except Exception:
        return 0.0


def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def open_video_subtitle_screenshot_window(app, parent, config, save_config_func, video_sub_screenshot_func, on_close):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()
    subwin.title("影片依字幕截圖")
    subwin.resizable(False, False)
    try:
        subwin.iconbitmap('icon.ico')
    except tk.TclError:
        pass
    width, height = 600, 320
    subwin.transient(parent)
    subwin.lift()
    subwin.focus_force()

    # 置中邏輯
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
    frame.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
    row = 0

    font_label = ('微軟正黑體', 11)
    font_entry = ('微軟正黑體', 10)
    font_btn = ('微軟正黑體', 10, 'bold')
    font_info = ('微軟正黑體', 10)

    # 1. 選取影片檔案 (單檔)
    tk.Label(frame, text='1. 選取影片檔案', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
    entry_video = tk.Entry(frame, width=38, font=font_entry)
    entry_video.grid(row=row, column=1, padx=5)

    label_video_info = tk.Label(frame, text="影片時長：尚未載入", font=font_info, bg='#f4f4f7', fg='#666')

    def select_video():
        fp = filedialog.askopenfilename(
            title='選擇影片檔案',
            filetypes=[
                ('影片檔案', '*.mp4;*.mov;*.avi;*.mkv;*.webm;*.flv;*.ts;*.wmv'),
                ('MP4 影片', '*.mp4'),
                ('MKV 影片', '*.mkv'),
                ('全部檔案', '*.*')
            ]
        )
        if fp:
            entry_video.delete(0, tk.END)
            entry_video.insert(0, fp)
            dur = get_duration(fp)
            if dur > 0:
                label_video_info.config(text=f"影片時長：{format_duration(dur)}", fg='#00FF00')
            else:
                label_video_info.config(text="影片時長：未知", fg='#666')

    tk.Button(frame, text='選擇影片', command=select_video, font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    # 影片資訊標籤
    label_video_info.grid(row=row, column=1, sticky='w', padx=5, pady=(0, 4))
    row += 1

    # 2. 選取字幕檔案 (單檔)
    tk.Label(frame, text='2. 選取字幕檔案', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
    entry_sub = tk.Entry(frame, width=38, font=font_entry)
    entry_sub.grid(row=row, column=1, padx=5)

    label_sub_info = tk.Label(frame, text="字幕資訊：尚未載入", font=font_info, bg='#f4f4f7', fg='#666')

    def select_sub():
        fp = filedialog.askopenfilename(
            title='選擇字幕檔案',
            filetypes=[
                ('字幕檔案', '*.srt;*.vtt;*.ass;*.ssa'),
                ('SRT 字幕', '*.srt'),
                ('VTT 字幕', '*.vtt'),
                ('ASS/SSA 字幕', '*.ass;*.ssa'),
                ('全部檔案', '*.*')
            ]
        )
        if fp:
            entry_sub.delete(0, tk.END)
            entry_sub.insert(0, fp)
            try:
                times = extract_subtitles_start_times(fp)
                label_sub_info.config(text=f"偵測到字幕數量：{len(times)} 條", fg='#00FF00')
            except Exception as e:
                label_sub_info.config(text=f"讀取字幕失敗：{e}", fg='red')

    tk.Button(frame, text='選擇字幕', command=select_sub, font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    # 字幕資訊標籤
    label_sub_info.grid(row=row, column=1, sticky='w', padx=5, pady=(0, 4))
    row += 1

    # 3. 時間軸偏移 (ms)
    tk.Label(frame, text='3. 時間軸偏移', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)

    offset_frame = tk.Frame(frame, bg='#f4f4f7')
    offset_frame.grid(row=row, column=1, sticky='w', padx=5)

    entry_offset = tk.Entry(offset_frame, width=10, font=font_entry, justify='center')
    saved_offset = config.get("offset_ms", "-100")
    entry_offset.insert(0, str(saved_offset))
    entry_offset.pack(side='left')

    def adjust_offset(delta):
        try:
            curr = int(float(entry_offset.get().strip()))
            entry_offset.delete(0, tk.END)
            entry_offset.insert(0, str(curr + delta))
        except Exception:
            pass

    entry_offset.bind('<Up>', lambda e: adjust_offset(10))
    entry_offset.bind('<Down>', lambda e: adjust_offset(-10))

    tk.Label(offset_frame, text='(毫秒)', font=font_info, bg='#f4f4f7', fg='#666').pack(side='left', padx=5)
    row += 1

    # 4. 截圖輸出路徑
    tk.Label(frame, text='4. 截圖輸出路徑', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
    entry_output = tk.Entry(frame, width=38, font=font_entry)
    entry_output.grid(row=row, column=1, padx=5)
    if "output_folder" in config:
        entry_output.insert(0, config["output_folder"])

    def select_output():
        folder = filedialog.askdirectory(title='選擇截圖輸出資料夾')
        if folder:
            entry_output.delete(0, tk.END)
            entry_output.insert(0, folder)

    tk.Button(frame, text='選擇資料夾', command=select_output, font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    # 開始執行按鈕
    btn_run = tk.Button(frame, text='開始執行', width=20, height=2, font=font_btn, bg='#6cb2eb', fg='white', activebackground='#2779bd')
    btn_run.grid(row=row, column=0, columnspan=3, pady=15)
    row += 1

    # 狀態標籤
    label_status = tk.Label(frame, text='', font=font_info, fg='blue', bg='#f4f4f7')
    label_status.grid(row=row, column=0, columnspan=3)

    def run():
        video_fp = entry_video.get().strip()
        sub_fp = entry_sub.get().strip()
        offset_val_str = entry_offset.get().strip()
        output_dir = entry_output.get().strip()

        if not video_fp or not os.path.isfile(video_fp):
            messagebox.showerror("錯誤", "請選擇正確的影片檔案", parent=subwin)
            return

        if not sub_fp or not os.path.isfile(sub_fp):
            messagebox.showerror("錯誤", "請選擇正確的字幕檔案", parent=subwin)
            return

        try:
            offset_ms = float(offset_val_str)
        except ValueError:
            messagebox.showerror("錯誤", "時間軸偏移請輸入有效數字 (毫秒，可正可負)", parent=subwin)
            return

        if not output_dir:
            messagebox.showerror("錯誤", "請設定截圖輸出路徑", parent=subwin)
            return

        btn_run.config(state=tk.DISABLED)
        label_status.config(text="準備處理截圖中...", fg="blue")

        # 儲存 3 與 4 設定至 config.json
        save_config_func({
            "offset_ms": str(offset_val_str),
            "output_folder": output_dir
        })

        def work():
            try:
                def progress(curr, tot):
                    subwin.after(0, lambda: label_status.config(text=f"截圖進度：{curr} / {tot}"))

                count = video_sub_screenshot_func(
                    video_fp, sub_fp, offset_ms, output_dir, progress_callback=progress
                )
                subwin.after(0, lambda: label_status.config(text="完成！", fg="green"))
                subwin.after(0, lambda: messagebox.showinfo(
                    "成功", f"影片截圖完成！\n共輸出 {count} 張 JPG 圖片\n輸出路徑：{output_dir}", parent=subwin))
                subwin.after(0, lambda: os.startfile(output_dir))
            except Exception as e:
                subwin.after(0, lambda: label_status.config(text="發生錯誤", fg="red"))
                subwin.after(0, lambda: messagebox.showerror("錯誤", f"處理失敗：{e}", parent=subwin))
            finally:
                subwin.after(0, lambda: btn_run.config(state=tk.NORMAL))

        threading.Thread(target=work, daemon=True).start()

    btn_run.config(command=run)
    return subwin

