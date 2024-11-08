import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import logging

class SettingsDialog:
    def __init__(self, parent, settings_manager):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("一般設定")
        self.dialog.geometry("500x400")
        
        # モーダルダイアログとして設定
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.settings_manager = settings_manager
        self.result = None
        
        self.create_widgets()
        self.load_current_settings()
    
    def create_widgets(self):
        """設定ウィジェットの作成"""
        # スクレイピング設定
        scraping_frame = ttk.LabelFrame(self.dialog, text="スクレイピング設定", padding="10")
        scraping_frame.pack(fill='x', padx=10, pady=5)
        
        # 同時実行数
        ttk.Label(scraping_frame, text="デフォルト同時実行数:").grid(row=0, column=0, padx=5, pady=2)
        self.workers_var = tk.StringVar()
        ttk.Entry(scraping_frame, textvariable=self.workers_var, width=10).grid(row=0, column=1, pady=2)
        
        # 待機時間
        ttk.Label(scraping_frame, text="デフォルト待機時間(秒):").grid(row=1, column=0, padx=5, pady=2)
        self.delay_var = tk.StringVar()
        ttk.Entry(scraping_frame, textvariable=self.delay_var, width=10).grid(row=1, column=1, pady=2)
        
        # 最小文字数
        ttk.Label(scraping_frame, text="デフォルト最小文字数:").grid(row=2, column=0, padx=5, pady=2)
        self.min_length_var = tk.StringVar()
        ttk.Entry(scraping_frame, textvariable=self.min_length_var, width=10).grid(row=2, column=1, pady=2)
        
        # ログ設定
        log_frame = ttk.LabelFrame(self.dialog, text="ログ設定", padding="10")
        log_frame.pack(fill='x', padx=10, pady=5)
        
        # ログレベル
        ttk.Label(log_frame, text="ログレベル:").grid(row=0, column=0, padx=5, pady=2)
        self.log_level_var = tk.StringVar()
        ttk.Combobox(
            log_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly"
        ).grid(row=0, column=1, pady=2)
        
        # エクスポート設定
        export_frame = ttk.LabelFrame(self.dialog, text="エクスポート設定", padding="10")
        export_frame.pack(fill='x', padx=10, pady=5)
        
        # デフォルトフォーマット
        ttk.Label(export_frame, text="デフォルトフォーマット:").grid(row=0, column=0, padx=5, pady=2)
        self.export_format_var = tk.StringVar()
        ttk.Combobox(
            export_frame,
            textvariable=self.export_format_var,
            values=["excel", "csv"],
            state="readonly"
        ).grid(row=0, column=1, pady=2)
        
        # ボタン
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="保存",
            command=self.save_settings
        ).pack(side='right', padx=5)
        
        ttk.Button(
            button_frame,
            text="キャンセル",
            command=self.dialog.destroy
        ).pack(side='right')
    
    def load_current_settings(self):
        """現在の設定を読み込む"""
        settings = self.settings_manager.settings
        
        # スクレイピング設定
        scraping = settings.get('scraping', {})
        self.workers_var.set(str(scraping.get('max_workers', 3)))
        self.delay_var.set(str(scraping.get('default_delay', 1.0)))
        self.min_length_var.set(str(scraping.get('min_length', 0)))
        
        # ログ設定
        logging = settings.get('logging', {})
        self.log_level_var.set(logging.get('level', 'INFO'))
        
        # エクスポート設定
        export = settings.get('export', {})
        self.export_format_var.set(export.get('default_format', 'excel'))
    
    def save_settings(self):
        """設定を保存"""
        try:
            new_settings = {
                'scraping': {
                    'max_workers': int(self.workers_var.get()),
                    'default_delay': float(self.delay_var.get()),
                    'min_length': int(self.min_length_var.get())
                },
                'logging': {
                    'level': self.log_level_var.get(),
                    'file': 'logs/scraper.log'
                },
                'export': {
                    'default_format': self.export_format_var.get(),
                    'default_directory': 'downloads'
                }
            }
            
            self.settings_manager.save_settings(new_settings)
            self.result = True
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("エラー", "入力値が不正です。\n数値項目を確認してください。")
        except Exception as e:
            logging.error(f"設定の保存に失敗: {e}")
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")