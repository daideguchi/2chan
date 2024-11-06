from src.gui.components.proxy_dialog import ProxyDialog
from src.gui.components.filter_frame import FilterFrame
from src.config.proxy import ProxyManager
# ... 他のインポート
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import threading
import queue
from datetime import datetime
import logging
from typing import List, Optional
from tkinter import ttk, scrolledtext, messagebox, filedialog  # filedialogを追加
from .components.settings_dialog import SettingsDialog  # 追加
import time

from .components.menu import MainMenu
from .components.export import ExportManager
from .components.statistics import StatisticsWindow
from .components.log_window import LogWindow
from ..scraper.core import Scraper, ScrapingResult
from ..config.settings import SettingsManager

class ThreadScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("2ちゃんねるスクレイパー Pro")
        self.root.geometry("1200x800")
        
        # マネージャーの初期化
        self.settings_manager = SettingsManager()
        self.proxy_manager = ProxyManager()
        
        # スクレイパーの初期化
        self.scraper = Scraper(proxy_manager=self.proxy_manager)
        
        # キューの初期化
        self.result_queue = queue.Queue()
        
        # UI状態の初期化
        self.is_scraping = False
        self.current_thread = None
        
        # メインフレームの作成
        self.create_main_frame()
        self.create_menu()
        self.create_url_input()
        self.create_options()
        self.create_progress_area()
        self.create_results_area()  # Treeviewの作成
        
        # コンテキストメニューの作成
        self.create_context_menu()
        
        # 設定の読み込み
        self.load_settings()
    
    def create_main_frame(self):
        """メインフレームの作成"""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(3, weight=1)
    
    def create_url_input(self):
        """URL入力エリアの作成"""
        url_frame = ttk.LabelFrame(self.main_frame, text="URL入力", padding="5")
        url_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # URLテキストエリア
        self.url_text = scrolledtext.ScrolledText(url_frame, height=5)
        self.url_text.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # ボタンフレーム
        button_frame = ttk.Frame(url_frame)
        button_frame.grid(row=0, column=1, padx=5, pady=5)
        
        self.start_button = ttk.Button(
            button_frame,
            text="スクレイピング開始",
            command=self.start_scraping
        )
        self.start_button.grid(row=0, column=0, pady=2)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="停止",
            command=self.stop_scraping,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=1, column=0, pady=2)
    
    def create_options(self):
        """オプションエリアの作成"""
        options_frame = ttk.LabelFrame(self.main_frame, text="オプション設定", padding="5")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 同時実行数
        ttk.Label(options_frame, text="同時実行数:").grid(row=0, column=0, padx=5)
        self.workers_var = tk.StringVar(value="3")
        ttk.Spinbox(
            options_frame,
            from_=1,
            to=10,
            width=5,
            textvariable=self.workers_var
        ).grid(row=0, column=1, padx=5)
        
        # 待機時間
        ttk.Label(options_frame, text="待機時間(秒):").grid(row=0, column=2, padx=5)
        self.delay_var = tk.StringVar(value="1.0")
        ttk.Spinbox(
            options_frame,
            from_=0.0,
            to=10.0,
            increment=0.1,
            width=5,
            textvariable=self.delay_var
        ).grid(row=0, column=3, padx=5)
        
        # 最小文字数
        ttk.Label(options_frame, text="最小文字数:").grid(row=0, column=4, padx=5)
        self.min_length_var = tk.StringVar(value="0")
        ttk.Spinbox(
            options_frame,
            from_=0,
            to=1000,
            width=5,
            textvariable=self.min_length_var
        ).grid(row=0, column=5, padx=5)
    
    def create_progress_area(self):
        """進捗表示エリアの作成"""
        progress_frame = ttk.LabelFrame(self.main_frame, text="進捗状況", padding="5")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="待機中")
        self.status_label.grid(row=1, column=0, sticky=tk.W, padx=5)
   
    def create_results_area(self):
        """結果表示エリアの作成"""
        self.results_frame = ttk.LabelFrame(self.main_frame, text="スクレイピング結果", padding="5")
        self.results_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # スクロール可能なフレームを作成
        self.tree_frame = ttk.Frame(self.results_frame)
        self.tree_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        columns = ('num', 'content', 'chars')
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=columns,
            show='headings',
            selectmode='extended'
        )
        
        # スクロールバーの設定
        self.vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self.results_frame, orient="horizontal", command=self.tree.xview)
        
        # Treeviewとスクロールバーの関連付け
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        
        # グリッドの設定
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.hsb.grid(row=2, column=0, sticky=(tk.E, tk.W))
        
        # 列の設定
        self.tree.heading('num', text='番号')
        self.tree.heading('content', text='発言内容')
        self.tree.heading('chars', text='文字数')
        
        self.tree.column('num', width=50, minwidth=50, anchor=tk.W)
        self.tree.column('content', width=800, minwidth=200, anchor=tk.W)
        self.tree.column('chars', width=70, minwidth=70, anchor=tk.E)
        
        # スクロールバーの設定
        vsb = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # コンポーネントの配置
        self.tree.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=1, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=2, column=0, sticky=(tk.E, tk.W))
        
        # グリッドの設定
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(1, weight=1)
        
        # フィルターフレームの作成と配置
        self.filter_frame = FilterFrame(self.results_frame, self.tree)
        self.filter_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 列の重みを設定
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(1, weight=1)
        
        # テスト用のデータを追加（デバッグ時のみ）
        self.tree.insert('', tk.END, values=('テスト', 'これはテストデータです', '10'))

    # メニューの作成メソッドを追加
    def create_menu(self):
        """メニューバーの作成"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="URLリストを開く", command=self.load_url_list)
        file_menu.add_command(label="結果を保存", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit)
        
        # ツールメニュー
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ツール", menu=tools_menu)
        tools_menu.add_command(label="プロキシ設定", command=self.show_proxy_settings)
        tools_menu.add_command(label="一般設定", command=self.show_settings)
    
    # プロキシ設定を表示するメソッドを追加
    def show_proxy_settings(self):
        """プロキシ設定ダイアログを表示"""
        dialog = ProxyDialog(self.root, self.proxy_manager)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # スクレイパーのセッションを更新
            self.scraper.update_session(self.proxy_manager.get_session())

    
    def create_context_menu(self):
        """コンテキストメニューの作成"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="コピー", command=self.copy_selected)
        self.context_menu.add_command(label="選択行を削除", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="すべて選択", command=self.select_all)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """コンテキストメニューを表示"""
        self.context_menu.post(event.x_root, event.y_root)
    
    def copy_selected(self):
        """選択された行をクリップボードにコピー"""
        selected = self.tree.selection()
        if not selected:
            return
        
        text = "\n".join(
            "\t".join(str(x) for x in self.tree.item(item)['values'])
            for item in selected
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
    
    def delete_selected(self):
        """選択された行を削除"""
        selected = self.tree.selection()
        if not selected:
            return
        
        if messagebox.askyesno("確認", "選択された行を削除しますか？"):
            for item in selected:
                self.tree.delete(item)
    
    def select_all(self):
        """すべての行を選択"""
        self.tree.selection_set(self.tree.get_children())
    
    def show_statistics_window(self):
        """統計ウィンドウを表示"""
        StatisticsWindow(self.root, self.tree)
    
    def update_url_list(self, urls: List[str]):
        """URLリストを更新"""
        self.url_text.delete('1.0', tk.END)
        self.url_text.insert('1.0', ''.join(urls))
    
    def start_scraping(self):
        """スクレイピングを開始"""
        # 既存のデータをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)
        logging.info("Treeview をクリアしました")

        urls = [url.strip() for url in self.url_text.get('1.0', tk.END).splitlines() if url.strip()]
        if not urls:
            messagebox.showerror("エラー", "URLを入力してください。")
            return

        try:
            max_workers = int(self.workers_var.get())
            delay = float(self.delay_var.get())
            min_length = int(self.min_length_var.get())
        except ValueError:
            messagebox.showerror("エラー", "オプションの値が不正です。")
            return

        # UI状態の更新
        self.is_scraping = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.url_text.config(state=tk.DISABLED)

        # プログレスバーの初期化
        self.progress_var.set(0)
        self.progress_bar['maximum'] = len(urls)
        self.status_label.config(text="スクレイピング中...")

        # スクレイピングスレッドの開始
        self.current_thread = threading.Thread(
            target=self.scraping_thread,
            args=(urls, max_workers, delay, min_length),
            daemon=True
        )
        self.current_thread.start()

        # 結果の更新を開始
        self.update_results()
        
    
    def scraping_thread(self, urls: List[str], max_workers: int, delay: float, min_length: int):
        """スクレイピングを実行するスレッド"""
        try:
            logging.info(f"スクレイピングを開始: {len(urls)} URLs")
            results = self.scraper.scrape_urls(
                urls=urls,
                max_workers=max_workers,
                delay=delay,
                min_length=min_length
            )
            
            logging.info(f"スクレイピング結果数: {len(results) if results else 0}")  # デバッグログ追加
            
            if results:
                for result in results:
                    if not self.is_scraping:
                        break
                    item_data = {
                        'num': result.speaker,
                        'content': result.content.strip(),
                        'chars': len(result.content.strip())
                    }
                    logging.info(f"キューに追加するデータ: {item_data}")  # デバッグログ追加
                    self.result_queue.put(('result', item_data))
                    time.sleep(0.1)
            else:
                logging.warning("スクレイピング結果が0件でした")
            
            self.result_queue.put(('finished', None))
            
        except Exception as e:
            logging.error(f"スクレイピング中にエラー: {e}")
            self.result_queue.put(('error', str(e)))
    
    def update_results(self):
        """結果を更新"""
        try:
            items_processed = False
            
            while True:
                try:
                    msg_type, data = self.result_queue.get_nowait()
                    
                    if msg_type == 'result':
                        # データの形式をログ出力
                        logging.info(f"結果をツリーに追加: {data}")
                        
                        # Treeview に結果を追加
                        values = (
                            str(data['num']),
                            str(data['content']),
                            len(str(data['content']))
                        )
                        
                        try:
                            self.tree.insert('', tk.END, values=values)
                            items_processed = True
                            logging.info(f"Treeview に追加完了: {values}")
                        except Exception as e:
                            logging.error(f"Treeview 追加エラー: {e}, データ: {values}")
                        
                        # プログレスバーを更新
                        self.progress_var.set(self.progress_var.get() + 1)
                        
                    elif msg_type == 'error':
                        logging.error(f"エラーメッセージを受信: {data}")
                        messagebox.showerror("エラー", f"スクレイピング中にエラー: {data}")
                        self.stop_scraping()
                        return
                        
                    elif msg_type == 'finished':
                        if items_processed:
                            logging.info("スクレイピング完了")
                        else:
                            messagebox.showwarning("警告", "結果が0件でした")
                        self.finish_scraping()
                        return
                        
                except queue.Empty:
                    break
                
            # 表示を更新
            if items_processed:
                self.tree.update_idletasks()
                if self.tree.get_children():
                    last_item = self.tree.get_children()[-1]
                    self.tree.see(last_item)
                
            # 処理を継続
            if self.is_scraping:
                self.root.after(100, self.update_results)
                
        except Exception as e:
            logging.error(f"結果更新中にエラー: {e}", exc_info=True)
            messagebox.showerror("エラー", f"結果更新中にエラー: {e}")
            self.stop_scraping()

    def add_test_data(self):
        """テスト用データを追加（デバッグ用）"""
        test_data = [
            ("1", "テストデータ1", "10"),
            ("2", "テストデータ2", "15"),
            ("3", "テストデータ3", "20"),
        ]
        for values in test_data:
            self.tree.insert('', tk.END, values=values)
        logging.info("テストデータを追加しました")

    def stop_scraping(self):
        """スクレイピングを停止"""
        self.is_scraping = False
        self.status_label.config(text="停止中...")
        self.finish_scraping()
    
    def finish_scraping(self):
            """スクレイピングの終了処理"""
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.url_text.config(state=tk.NORMAL)
            
            total_results = len(self.tree.get_children())
            self.status_label.config(text=f"完了 - {total_results}件の結果")
            
            if total_results > 0:
                logging.info(f"スクレイピング完了: {total_results}件の結果を取得")
                self.show_completion_dialog(total_results)
    
    def show_completion_dialog(self, total_results: int):
        """完了ダイアログを表示"""
        response = messagebox.askquestion(
            "完了",
            f"{total_results}件の結果を取得しました。\n統計情報を表示しますか？"
        )
        if response == 'yes':
            self.show_statistics_window()
    
    def load_settings(self):
        """設定を読み込んで適用"""
        try:
            scraper_settings = self.settings_manager.get_scraper_settings()
            
            # オプション値の設定
            self.workers_var.set(str(scraper_settings.max_workers))
            self.delay_var.set(str(scraper_settings.delay))
            self.min_length_var.set(str(scraper_settings.min_length))
            
            # スクレイパーの設定を更新（この部分を修正）
            self.scraper = Scraper(proxy_manager=self.proxy_manager)
            
            logging.info("設定を読み込みました")
            
        except Exception as e:
            logging.error(f"設定の読み込みに失敗: {e}")
            messagebox.showwarning("警告", "設定の読み込みに失敗しました。デフォルト値を使用します。")
    
    def save_settings(self):
        """現在の設定を保存"""
        try:
            current_settings = {
                'scraper': {
                    'max_workers': int(self.workers_var.get()),
                    'delay': float(self.delay_var.get()),
                    'min_length': int(self.min_length_var.get())
                }
            }
            
            self.settings_manager.save_settings(current_settings)
            logging.info("設定を保存しました")
            
        except Exception as e:
            logging.error(f"設定の保存に失敗: {e}")
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")
    
    def clear_results(self):
        """結果をクリア"""
        if not self.tree.get_children():
            return
            
        if messagebox.askyesno("確認", "すべての結果をクリアしますか？"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            logging.info("結果をクリアしました")
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        if self.is_scraping:
            if not messagebox.askyesno("確認", 
                "スクレイピングが実行中です。終了しますか？"):
                return
                
        try:
            self.save_settings()
        except:
            pass
        
        self.root.destroy()
    
    def show_error_log(self):
        """エラーログを表示"""
        if self.log_window is None or not self.log_window.dialog.winfo_exists():
            self.log_window = LogWindow(self.root)
        self.log_window.dialog.lift()
    
    def run(self):
        """アプリケーションを実行"""
        # 終了処理の設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # メインループの開始
        try:
            self.root.mainloop()
        except Exception as e:
            logging.error(f"予期せぬエラーが発生: {e}")
            messagebox.showerror("エラー", f"予期せぬエラーが発生: {e}")
        finally:
            try:
                self.save_settings()
            except:
                pass
    def load_url_list(self):
        """URLリストファイルを読み込む"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("テキストファイル", "*.txt"),
                ("CSVファイル", "*.csv"),
                ("すべてのファイル", "*.*")
            ],
            title="URLリストを開く"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = f.readlines()
                    self.url_text.delete('1.0', tk.END)
                    self.url_text.insert('1.0', ''.join(urls))
            except Exception as e:
                logging.error(f"URLリストの読み込みに失敗: {e}")
                messagebox.showerror("エラー", f"ファイルの読み込みに失敗しました: {e}")

    def save_results(self):
        """結果を保存"""
        if not self.tree.get_children():
            messagebox.showerror("エラー", "保存する結果がありません。")
            return
            
        if hasattr(self, 'export_manager'):
            self.export_manager.show_export_dialog()

    def show_settings(self):
        """一般設定ダイアログを表示"""
        try:
            dialog = SettingsDialog(self.root, self.settings_manager)
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                # 設定を再読み込み
                self.load_settings()
                logging.info("設定を更新しました")
        except Exception as e:
            logging.error(f"設定ダイアログの表示に失敗: {e}")
            messagebox.showerror("エラー", f"設定ダイアログの表示に失敗しました: {e}")

if __name__ == "__main__":
    app = ThreadScraperGUI()
    app.run()