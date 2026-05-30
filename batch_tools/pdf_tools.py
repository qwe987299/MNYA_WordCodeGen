import os
import multiprocessing
import traceback

def decrypt_single_pdf(args):
    """
    處理單一 PDF 的 Worker 任務
    Args:
        args: tuple of (pdf_path, passwords, output_dir, shared_passwords)
    Returns:
        dict: {
            "path": pdf_path,
            "status": "success" | "failed" | "skipped",
            "matched_password": str | None,
            "error_msg": str | None
        }
    """
    pdf_path, passwords, output_dir, shared_passwords = args
    try:
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                return {
                    "path": pdf_path,
                    "status": "failed",
                    "matched_password": None,
                    "error_msg": "未安裝 pypdf 或 PyPDF2 模組，請先執行 pip install pypdf"
                }

        # 檢查檔案是否存在
        if not os.path.exists(pdf_path):
            return {
                "path": pdf_path,
                "status": "failed",
                "matched_password": None,
                "error_msg": "檔案不存在"
            }

        reader = PdfReader(pdf_path)
        
        # 1. 檢查是否加密
        if not reader.is_encrypted:
            # 未加密，直接重新輸出到目標資料夾
            filename = os.path.basename(pdf_path)
            out_path = os.path.join(output_dir, filename)
            
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            with open(out_path, "wb") as f:
                writer.write(f)
                
            return {
                "path": pdf_path,
                "status": "skipped",
                "matched_password": None,
                "error_msg": None
            }

        # 2. 嘗試密碼 (優先使用 shared_passwords，再使用 UI 輸入的 passwords)
        # 這裡 shared_passwords 是一個 multiprocessing.Manager().list()
        local_shared = list(shared_passwords)
        
        try_passwords = []
        for p in local_shared:
            if p not in try_passwords:
                try_passwords.append(p)
        for p in passwords:
            if p not in try_passwords:
                try_passwords.append(p)

        matched_password = None
        decrypted = False
        unsupported_algorithm = False
        error_detail = None
        
        for p in try_passwords:
            try:
                # 只用 reader.decrypt() 驗證，不提前讀取頁面內容
                result = reader.decrypt(p)
                if result:
                    decrypted = True
                    matched_password = p
                    break
            except NotImplementedError as ne:
                unsupported_algorithm = True
                error_detail = f"不支援的加密演算法 (可能需要安裝 pycryptodome): {str(ne)}"
                break
            except Exception as e:
                error_str = str(e).lower()
                if "crypt" in error_str or "implement" in error_str or "algorithm" in error_str:
                    unsupported_algorithm = True
                    error_detail = f"解密模組出錯 (可能需要安裝 pycryptodome): {str(e)}"
                    break
                error_detail = str(e)
                continue

        if unsupported_algorithm:
            return {
                "path": pdf_path,
                "status": "failed",
                "matched_password": None,
                "error_msg": error_detail
            }

        if not decrypted:
            return {
                "path": pdf_path,
                "status": "failed",
                "matched_password": None,
                "error_msg": "密碼不正確"
            }

        # 更新 shared_passwords (LRU 概念)
        if matched_password is not None:
            try:
                current_shared = list(shared_passwords)
                if matched_password in current_shared:
                    current_shared.remove(matched_password)
                current_shared.insert(0, matched_password)
                shared_passwords[:] = current_shared[:100]  # 快取上限 100 筆
            except Exception:
                pass

        # 3. 寫出解密後的 PDF
        filename = os.path.basename(pdf_path)
        out_path = os.path.join(output_dir, filename)
        
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
            
        with open(out_path, "wb") as f:
            writer.write(f)

        return {
            "path": pdf_path,
            "status": "success",
            "matched_password": matched_password,
            "error_msg": None
        }

    except Exception as e:
        error_msg = str(e)
        if "decrypted" in error_msg.lower() or "cipher" in error_msg.lower() or "crypt" in error_msg.lower():
            error_msg = f"解密失敗 (密碼可能無效或檔案損壞): {error_msg}"
        else:
            error_msg = f"發生錯誤: {error_msg}"
        return {
            "path": pdf_path,
            "status": "failed",
            "matched_password": None,
            "error_msg": error_msg
        }

def decrypt_pdf_files(pdf_paths, passwords, output_dir, progress_callback=None):
    """
    平行解密多個 PDF 檔案 (以 CPU 核心數為準)
    """
    manager = multiprocessing.Manager()
    shared_passwords = manager.list()
    
    # 預先將當前有的密碼加入 shared_passwords 確保啟動時就照這個順序
    for p in passwords:
        if p not in shared_passwords:
            shared_passwords.append(p)
            
    tasks = [(path, passwords, output_dir, shared_passwords) for path in pdf_paths]
    
    # 平行運算以 CPU 核心數為準
    num_workers = os.cpu_count() or 2
    
    results = []
    
    with multiprocessing.Pool(processes=num_workers) as pool:
        total = len(tasks)
        completed = 0
        for res in pool.imap_unordered(decrypt_single_pdf, tasks):
            completed += 1
            results.append(res)
            if progress_callback:
                progress_callback(completed, total, res)
                
    final_shared_passwords = list(shared_passwords)
    return results, final_shared_passwords
