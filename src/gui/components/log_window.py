import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
from queue import Queue
from datetime import datetime

class QueueHandler(logging.Handler):
    """ログメッセージをキューに送るハンドラ"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        self.log_queue.put(record)

class LogWindow:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ログビューア")
        self.dialog.geometry("800x400")
        
        # ログメッセージのキュー
        self.log_queue = Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        self.queue_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger = logging.getLogger()
        logger.addHandler(self.queue_handler)
        
        self.create_widgets()
        self.update_log()
    
    def create_widgets(self):
        """ウィジェットの作成"""
        # ツールバー
        toolbar = ttk.Frame(self.dialog)
        toolbar.pack(fill='x', padx=5, pady=2)
        
        # フィルターコントロール
        ttk.Label(toolbar, text="ログレベル:").pack(side='left', padx=5)
        self.level_var = tk.StringVar(value="INFO")
        level_combo = ttk.Combobox(toolbar, textvariable=self.level_var,
                                 values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        level_combo.pack(side='left', padx=5)
        
        # クリアボタン
        ttk.Button(toolbar, text="クリア", 
                  command=self.clear_log).pack(side='right', padx=5)
        
        # 検索フレーム
        search_frame = ttk.Frame(self.dialog)
        search_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(search_frame, text="検索:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_log)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # ログテキストエリア
        self.log_text = scrolledtext.ScrolledText(self.dialog, height=20)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ステータスバー
        self.status_bar = ttk.Label(self.dialog, text="0 件のログ")
        self.status_bar.pack(fill='x', padx=5, pady=2)
    
    def update_log(self):
        """ログの更新"""
        while True:
            try:
                record = self.log_queue.get_nowait()
                msg = self.queue_handler.format(record)
                self.log_text.insert('end', msg + '\n')
                self.log_text.see('end')
                self.update_status()
            except:
                break
        
        self.dialog.after(100, self.update_log)
    
    def clear_log(self):
        """ログをクリア"""
        self.log_text.delete('1.0', tk.END)
        self.update_status()
    
    def filter_log(self, *args):
        """ログのフィルタリング"""
        search_text = self.search_var.get().lower()
        min_level = getattr(logging, self.level_var.get())
        
        self.log_text.tag_remove('highlight', '1.0', tk.END)
        
        if search_text:
            pos = '1.0'
            while True:
                pos = self.log_text.search(search_text, pos, tk.END, nocase=True)
                if not pos:
                    break
                end_pos = f"{pos}+{len(search_text)}c"
                self.log_text.tag_add('highlight', pos, end_pos)
                pos = end_pos
            
            self.log_text.tag_config('highlight', background='yellow')
        
        self.update_status()
    
    def update_status(self):
        """ステータスバーの更新"""
        log_count = len(self.log_text.get('1.0', tk.END).splitlines()) - 1
        self.status_bar['text'] = f"{log_count} 件のログ"