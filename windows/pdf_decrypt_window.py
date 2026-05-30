import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import threading

def open_pdf_decrypt_window(app, parent, config, save_config_func, decrypt_pdf_func, on_close):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()
    subwin.title("解密 PDF 工具")
    subwin.resizable(False, False)
    try:
        subwin.iconbitmap('icon.ico')
    except Exception:
        pass
    
    width, height = 680, 370
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

    # 1. 載入 PDF 檔案
    tk.Label(frame, text='1. 待解密的 PDF 檔案 (可多個)', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='nw', pady=5)
    
    list_frame = tk.Frame(frame, bg='#f4f4f7')
    list_frame.grid(row=row, column=1, padx=5, pady=5, sticky='nsew')
    
    h_scrollbar = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    v_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox_pdf = tk.Listbox(list_frame, width=38, height=6, font=font_entry, 
                              xscrollcommand=h_scrollbar.set,
                              yscrollcommand=v_scrollbar.set)
    listbox_pdf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    h_scrollbar.config(command=listbox_pdf.xview)
    v_scrollbar.config(command=listbox_pdf.yview)

    def select_pdf():
        fps = filedialog.askopenfilenames(title='選擇 PDF 檔案', filetypes=[('PDF 檔案', '*.pdf')])
        if fps:
            for fp in fps:
                existing = listbox_pdf.get(0, tk.END)
                if fp not in existing:
                    listbox_pdf.insert(tk.END, fp)
    
    def clear_pdf():
        listbox_pdf.delete(0, tk.END)

    def remove_selected_pdf():
        selected_indices = listbox_pdf.curselection()
        if selected_indices:
            for index in sorted(selected_indices, reverse=True):
                listbox_pdf.delete(index)

    pdf_btn_frame = tk.Frame(frame, bg='#f4f4f7')
    pdf_btn_frame.grid(row=row, column=2, sticky='n', pady=5)
    tk.Button(pdf_btn_frame, text='增加 PDF', command=select_pdf, font=font_btn).pack(fill='x', pady=2)
    tk.Button(pdf_btn_frame, text='移除選取', command=remove_selected_pdf, font=font_btn).pack(fill='x', pady=2)
    tk.Button(pdf_btn_frame, text='清空列表', command=clear_pdf, font=font_btn).pack(fill='x', pady=2)
    row += 1

    # 2. 輸入密碼 (多行，每行一個)
    tk.Label(frame, text='2. 可能的密碼 (每行一個)', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='nw', pady=5)
    
    password_text = scrolledtext.ScrolledText(frame, width=36, height=5, font=font_entry)
    password_text.grid(row=row, column=1, padx=5, pady=5, sticky='w')
    
    cached_passwords = config.get("passwords_cache", [])
    if cached_passwords:
        password_text.insert(tk.END, "\n".join(cached_passwords))
    
    tk.Label(frame, text='(優先試用上一次\n成功解密的密碼)', font=font_info, fg='#666666', bg='#f4f4f7', justify='left').grid(row=row, column=2, sticky='w', padx=5)
    row += 1

    # 3. 輸出位置
    tk.Label(frame, text='3. 輸出位置', font=font_label, bg='#f4f4f7').grid(row=row, column=0, sticky='w', pady=5)
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
    btn_run = tk.Button(frame, text='開始解密', width=20, height=2, font=font_btn, bg='#6cb2eb', fg='white', activebackground='#2779bd')
    btn_run.grid(row=row, column=0, columnspan=3, pady=15)
    row += 1

    label_status = tk.Label(frame, text='', font=font_info, fg='blue', bg='#f4f4f7')
    label_status.grid(row=row, column=0, columnspan=3)

    def run():
        pdf_fps = list(listbox_pdf.get(0, tk.END))
        output_dir = entry_output.get().strip()
        
        raw_pw_text = password_text.get("1.0", tk.END)
        passwords = [line.strip() for line in raw_pw_text.split('\n') if line.strip()]

        if not pdf_fps:
            messagebox.showerror("錯誤", "請至少選擇一個 PDF 檔案", parent=subwin)
            return
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("錯誤", "請選擇正確的輸出路徑", parent=subwin)
            return

        btn_run.config(state=tk.DISABLED)
        label_status.config(text="準備開始解密...", fg="blue")

        def work():
            try:
                def progress_cb(completed, total, res):
                    status_text = f"處理中... ({completed}/{total}) - {os.path.basename(res['path'])}"
                    if res['status'] == 'success':
                        subwin.after(0, lambda: label_status.config(text=f"{status_text} (成功解密)", fg="green"))
                    elif res['status'] == 'skipped':
                        subwin.after(0, lambda: label_status.config(text=f"{status_text} (無需解密已導出)", fg="green"))
                    else:
                        subwin.after(0, lambda: label_status.config(text=f"{status_text} (失敗: {res['error_msg']})", fg="red"))

                # 呼叫解密工具
                results, new_passwords_cache = decrypt_pdf_func(pdf_fps, passwords, output_dir, progress_callback=progress_cb)
                
                success_count = sum(1 for r in results if r['status'] in ('success', 'skipped'))
                failed_count = len(results) - success_count
                
                failed_details = []
                for r in results:
                    if r['status'] == 'failed':
                        failed_details.append(f"- {os.path.basename(r['path'])}: {r['error_msg']}")
                
                # 儲存最新的密碼快取與輸出路徑至設定檔
                save_config_func({
                    "passwords_cache": new_passwords_cache,
                    "output_folder": output_dir
                })

                # 更新 UI 中的密碼欄位
                def update_ui_passwords():
                    password_text.delete("1.0", tk.END)
                    password_text.insert(tk.END, "\n".join(new_passwords_cache))
                subwin.after(0, update_ui_passwords)

                msg = f"解密完成！\n成功：{success_count} 個\n失敗：{failed_count} 個"
                if failed_details:
                    msg += "\n\n失敗詳情：\n" + "\n".join(failed_details)
                
                subwin.after(0, lambda: label_status.config(text=f"完成！成功 {success_count}，失敗 {failed_count}", fg="green"))
                subwin.after(0, lambda: messagebox.showinfo("處理結果", msg, parent=subwin))
                
                if success_count > 0:
                    subwin.after(0, lambda: os.startfile(output_dir))
                    
            except Exception as e:
                subwin.after(0, lambda: label_status.config(text="處理時發生錯誤", fg="red"))
                subwin.after(0, lambda: messagebox.showerror("錯誤", f"解密失敗：{e}", parent=subwin))
            finally:
                subwin.after(0, lambda: btn_run.config(state=tk.NORMAL))

        threading.Thread(target=work, daemon=True).start()

    btn_run.config(command=run)
    return subwin
