import tkinter as tk
from tkinter import messagebox
import pyperclip


def open_text_batch_replace_window(app, parent, config, save_config_func, on_close):
    subwin = tk.Toplevel(parent)
    subwin.withdraw()  # 先隱藏
    subwin.title("文字批次取代工具")
    subwin.resizable(False, False)
    subwin.iconbitmap('icon.ico')
    width, height = 540, 450
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

    font_label = ('微軟正黑體', 12)
    font_text = ('微軟正黑體', 12)
    font_btn = ('微軟正黑體', 12, 'bold')

    frame = tk.Frame(subwin)
    frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

    # 取代規則
    tk.Label(frame, text="取代規則（每行一組，例如 \" \" -> \", \"）",
             font=font_label).pack(anchor='w')
    rules_text = tk.Text(frame, height=6, width=62, font=font_text)
    rules_text.pack(fill=tk.X, pady=(0, 10))
    default_rules = '" " -> ", "\n"_" -> " "'
    rules_text.insert('1.0', config.get(
        "text_batch_replace_rules", default_rules))

    # 處理文字
    tk.Label(frame, text="處理文字（輸入欲批次取代之文字）", font=font_label).pack(anchor='w')
    input_text = tk.Text(frame, height=6, width=62, font=font_text)
    input_text.pack(fill=tk.BOTH, pady=(0, 10), expand=True)

    # 狀態顯示
    status_label = tk.Label(frame, text="", font=font_label, fg='blue')
    status_label.pack(anchor='w', pady=(0, 8))

    # 執行批次取代
    def do_batch_replace():
        try:
            from batch_tools.text_tools import parse_rules, batch_replace
        except ImportError:
            messagebox.showerror("錯誤", "找不到 text_tools.py！", parent=subwin)
            return

        rule_str = rules_text.get("1.0", tk.END)
        text = input_text.get("1.0", tk.END)
        try:
            rules = parse_rules(rule_str)
            if not rules:
                raise Exception("請輸入至少一組規則！")
            result = batch_replace(rules, text)
            pyperclip.copy(result)
            status_label.config(text="處理完成，結果已複製到剪貼簿！")
        except Exception as e:
            messagebox.showerror("錯誤", f"批次取代失敗：{e}", parent=subwin)
            status_label.config(text="處理失敗！")
            return

        # 儲存規則到 config
        save_config_func({
            "text_batch_replace_rules": rule_str.strip()
        })

    btn = tk.Button(frame, text="開始執行", font=font_btn, bg="#6cb2eb",
                    fg='white', width=20, height=2, command=do_batch_replace)
    btn.pack(pady=(2, 0))

    # 正確的關閉事件，通知主程式釋放視窗實例
    def handle_close():
        if callable(on_close):
            on_close()
        subwin.destroy()
    subwin.protocol("WM_DELETE_WINDOW", handle_close)

    return subwin
