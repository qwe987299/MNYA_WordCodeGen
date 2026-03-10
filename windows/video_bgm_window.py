import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import ffmpeg

def get_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        return float(probe['format']['duration'])
    except:
        return 0.0

def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def open_video_bgm_window(app, parent, config, save_config_func, video_add_bgm_func, on_close):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()
    subwin.title("影片背景音樂工具")
    subwin.resizable(False, False)
    subwin.iconbitmap('icon.ico')
    width, height = 600, 400
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

    # 1. 載入影片
    tk.Label(frame, text='1. 載入影片 (.mp4)', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
    entry_video = tk.Entry(frame, width=38, font=font_entry)
    entry_video.grid(row=row, column=1, padx=5)
    
    video_dur = [0.0]
    music_dur = [0.0]

    def update_dur_display():
        v_str = format_duration(video_dur[0])
        m_str = format_duration(music_dur[0])
        label_info.config(text=f"影片時長：{v_str} / 音樂時長：{m_str}")
        if music_dur[0] < video_dur[0] and video_dur[0] > 0:
            label_warn.config(text="（音樂時長不足）", fg="red")
        else:
            label_warn.config(text="", fg="red")

    def select_video():
        fp = filedialog.askopenfilename(title='選擇影片檔案', filetypes=[('MP4 影片', '*.mp4')])
        if fp:
            entry_video.delete(0, tk.END)
            entry_video.insert(0, fp)
            video_dur[0] = get_duration(fp)
            update_dur_display()

    tk.Button(frame, text='選擇影片', command=select_video, font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    # 2. 用於背景音樂的音樂檔
    tk.Label(frame, text='2. 背景音樂檔 (可多個)', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='nw', pady=5)
    
    # 建立一個 Frame 來包裝 Listbox 與捲軸
    list_frame = tk.Frame(frame, bg='#f4f4f7')
    list_frame.grid(row=row, column=1, padx=5, pady=5, sticky='nsew')
    
    # 水平捲軸
    h_scrollbar = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # 垂直捲軸
    v_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox_audio = tk.Listbox(list_frame, width=38, height=4, font=font_entry, 
                               xscrollcommand=h_scrollbar.set,
                               yscrollcommand=v_scrollbar.set)
    listbox_audio.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    h_scrollbar.config(command=listbox_audio.xview)
    v_scrollbar.config(command=listbox_audio.yview)

    def select_audio():
        fps = filedialog.askopenfilenames(title='選擇音訊檔案', filetypes=[('音訊檔案', '*.mp3;*.wav;*.m4a;*.aac')])
        if fps:
            for fp in fps:
                listbox_audio.insert(tk.END, fp)
            calculate_music_dur()
    
    def clear_audio():
        listbox_audio.delete(0, tk.END)
        calculate_music_dur()

    def calculate_music_dur():
        d = 0.0
        for i in range(listbox_audio.size()):
            d += get_duration(listbox_audio.get(i))
        music_dur[0] = d
        update_dur_display()

    audio_btn_frame = tk.Frame(frame, bg='#f4f4f7')
    audio_btn_frame.grid(row=row, column=2, sticky='n', pady=5)
    tk.Button(audio_btn_frame, text='增加音樂', command=select_audio, font=font_btn).pack(fill='x', pady=2)
    tk.Button(audio_btn_frame, text='清空列表', command=clear_audio, font=font_btn).pack(fill='x', pady=2)
    row += 1

    # 顯示時長
    info_frame = tk.Frame(frame, bg='#f4f4f7')
    info_frame.grid(row=row, column=0, columnspan=3, pady=5)
    label_info = tk.Label(info_frame, text="影片時長：00:00 / 音樂時長：00:00", font=font_info, bg='#f4f4f7')
    label_info.pack(side='left')
    label_warn = tk.Label(info_frame, text="", font=font_info, bg='#f4f4f7')
    label_warn.pack(side='left', padx=5)
    row += 1

    # 3. 片頭淡入
    tk.Label(frame, text='3. 片頭音樂淡入秒數', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
    entry_fade_in = tk.Entry(frame, width=10, font=font_entry, justify='center')
    entry_fade_in.insert(0, config.get("fade_in", "0"))
    entry_fade_in.grid(row=row, column=1, sticky='w', padx=5)
    tk.Label(frame, text='(0~10 秒)', font=font_info, bg='#f4f4f7').grid(row=row, column=1, sticky='e')
    row += 1

    # 4. 片尾淡出
    tk.Label(frame, text='4. 片尾音樂淡出秒數', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
    entry_fade_out = tk.Entry(frame, width=10, font=font_entry, justify='center')
    entry_fade_out.insert(0, config.get("fade_out", "0"))
    entry_fade_out.grid(row=row, column=1, sticky='w', padx=5)
    tk.Label(frame, text='(0~10 秒)', font=font_info, bg='#f4f4f7').grid(row=row, column=1, sticky='e')
    row += 1

    # 5. 輸出位置
    tk.Label(frame, text='5. 輸出位置', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
    entry_output = tk.Entry(frame, width=38, font=font_entry)
    entry_output.grid(row=row, column=1, padx=5)
    if "output_folder" in config:
        entry_output.insert(0, config["output_folder"])

    def select_output():
        folder = filedialog.askdirectory(title='選擇輸出資料夾')
        if folder:
            entry_output.delete(0, tk.END)
            entry_output.insert(0, folder)
    tk.Button(frame, text='選擇資料夾', command=select_output, font=font_btn).grid(row=row, column=2, padx=5)
    row += 1

    # 執行與導引
    btn_run = tk.Button(frame, text='開始執行', width=20, height=2, font=font_btn, bg='#6cb2eb', fg='white', activebackground='#2779bd')
    btn_run.grid(row=row, column=0, columnspan=3, pady=15)
    row += 1

    label_status = tk.Label(frame, text='', font=font_info, fg='blue', bg='#f4f4f7')
    label_status.grid(row=row, column=0, columnspan=3)

    def run():
        video_fp = entry_video.get().strip()
        audio_fps = list(listbox_audio.get(0, tk.END))
        output_dir = entry_output.get().strip()
        
        try:
            fi = float(entry_fade_in.get())
            fo = float(entry_fade_out.get())
            if not (0 <= fi <= 10 and 0 <= fo <= 10):
                raise ValueError
        except:
            messagebox.showerror("錯誤", "淡入淡出秒數請輸入 0 ~ 10 之間的數字", parent=subwin)
            return

        if not video_fp or not os.path.isfile(video_fp):
            messagebox.showerror("錯誤", "請選擇正確的影片檔案", parent=subwin)
            return
        if not audio_fps:
            messagebox.showerror("錯誤", "請至少選擇一個音樂檔案", parent=subwin)
            return
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("錯誤", "請選擇正確的輸出路徑", parent=subwin)
            return

        btn_run.config(state=tk.DISABLED)
        label_status.config(text="處理中，請稍候...")

        # 儲存設定
        save_config_func({
            "fade_in": str(fi),
            "fade_out": str(fo),
            "output_folder": output_dir
        })

        def work():
            try:
                out = video_add_bgm_func(video_fp, audio_fps, output_dir, fi, fo)
                subwin.after(0, lambda: label_status.config(text="完成！"))
                subwin.after(0, lambda: messagebox.showinfo("成功", f"影片處理完成！\n輸出檔案：{out}", parent=subwin))
                subwin.after(0, lambda: os.startfile(output_dir))
            except Exception as e:
                subwin.after(0, lambda: label_status.config(text="發生錯誤"))
                subwin.after(0, lambda: messagebox.showerror("錯誤", f"處理失敗：{e}", parent=subwin))
            finally:
                subwin.after(0, lambda: btn_run.config(state=tk.NORMAL))

        threading.Thread(target=work, daemon=True).start()

    btn_run.config(command=run)
    return subwin
