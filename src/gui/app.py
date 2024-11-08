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
import csv
import pandas as pd

from .components.menu import MainMenu
from .components.export import ExportManager
from .components.statistics import StatisticsWindow
from .components.log_window import LogWindow
from ..scraper.core import Scraper, ScrapingResult
from ..config.settings import SettingsManager
from typing import List, Optional, Dict 

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
        self.create_results_area()
        self.create_context_menu()  # コンテキストメニューの作成
        
        # 設定の読み込み
        self.load_settings()

    def start_scraping(self):
        """スクレイピングを開始"""
        # 既存のデータをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.total_chars_label.config(text="合計文字数: 0")
        logging.info("結果をクリアしました")

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
    
    def create_main_frame(self):
        """メインフレームの作成"""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # 各行の重みを設定
        # self.main_frame.rowconfigure(0, weight=1)  # URL入力
        # self.main_frame.rowconfigure(1, weight=1)  # オプション設定
        self.main_frame.rowconfigure(2, weight=1)  # 進捗状況
        self.main_frame.rowconfigure(3, weight=8)  # 結果表示エリア - ここを大きく
    
    def create_url_input(self):
        """URL入力エリアの作成"""
        url_frame = ttk.LabelFrame(self.main_frame, text="URL入力", padding="2")
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
        
        # 基本設定用のフレーム
        basic_frame = ttk.Frame(options_frame)
        basic_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 同時実行数
        ttk.Label(basic_frame, text="同時実行数:").grid(row=0, column=0, padx=5)
        self.workers_var = tk.StringVar(value="3")
        ttk.Spinbox(
            basic_frame,
            from_=1,
            to=10,
            width=5,
            textvariable=self.workers_var
        ).grid(row=0, column=1, padx=5)
        
        # 待機時間
        ttk.Label(basic_frame, text="待機時間(秒):").grid(row=0, column=2, padx=5)
        self.delay_var = tk.StringVar(value="1.0")
        ttk.Spinbox(
            basic_frame,
            from_=0.0,
            to=10.0,
            increment=0.1,
            width=5,
            textvariable=self.delay_var
        ).grid(row=0, column=3, padx=5)
        
        # 最小文字数
        ttk.Label(basic_frame, text="最小文字数:").grid(row=0, column=4, padx=5)
        self.min_length_var = tk.StringVar(value="0")
        ttk.Spinbox(
            basic_frame,
            from_=0,
            to=1000,
            width=5,
            textvariable=self.min_length_var
        ).grid(row=0, column=5, padx=5)

        # テキスト処理オプション用のフレーム
        text_options_frame = ttk.LabelFrame(options_frame, text="テキスト処理オプション", padding="5")
        text_options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # 23文字改行オプション
        self.line_break_var = tk.BooleanVar(value=False)
        self.line_break_check = ttk.Checkbutton(
            text_options_frame,
            text="23文字で改行する",
            variable=self.line_break_var
        )
        self.line_break_check.grid(row=0, column=0, padx=5, sticky=tk.W)

        # スクレイピング開始時に改行オプションを反映させるための設定
        def update_line_break(*args):
            if hasattr(self, 'scraper'):
                self.scraper.set_line_break_option(self.line_break_var.get())

        self.line_break_var.trace_add('write', update_line_break)
    
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
        
        # Treeviewの作成（最初に作成）
        columns = ('num', 'content', 'chars')
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=columns,
            show='headings',
            selectmode='extended',
            height=100
        )

        # スタイル設定
        style = ttk.Style()
        style.configure('Treeview', rowheight=50)

        # 列のヘッダー設定
        self.tree.heading('num', text='番号')
        self.tree.heading('content', text='発言内容')
        self.tree.heading('chars', text='文字数')

        # 列の幅と配置
        self.tree.column('num', width=50, minwidth=50, anchor=tk.W)
        self.tree.column('content', width=800, minwidth=200, anchor=tk.W, stretch=True)
        self.tree.column('chars', width=70, minwidth=70, anchor=tk.E)

        # 上部フレーム（FilterFrameより後に作成）
        top_frame = ttk.Frame(self.results_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.filter_frame = FilterFrame(top_frame, self.tree)  # treeが作成された後に初期化
        self.filter_frame.pack(side='left', fill='x', expand=True)

        self.total_chars_label = ttk.Label(top_frame, text="合計文字数: 0")
        self.total_chars_label.pack(side='right', padx=5)

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

        # ボタンフレーム
        button_frame = ttk.Frame(self.results_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(
            button_frame,
            text="CSVとして出力",
            command=lambda: self.export_results("csv")
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Excelとして出力",
            command=lambda: self.export_results("excel")
        ).pack(side='left', padx=5)

        # グリッド設定
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(1, weight=3)

        # テキスト折り返しの設定
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option) if elm[:2] != ('!disabled', '!selected')]
        style.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))

        def wrap_text(text, width=50):
            """テキストを指定幅で折り返し"""
            lines = text.split('\n')
            wrapped_lines = []
            for line in lines:
                while len(line) > width:
                    idx = line.rfind(' ', 0, width)
                    if idx == -1:
                        idx = width
                    wrapped_lines.append(line[:idx])
                    line = line[idx:].lstrip()
                wrapped_lines.append(line)
            return '\n'.join(wrapped_lines)

        # カスタムinsertの設定
        original_insert = self.tree.insert
        def custom_insert(parent='', index='end', **kw):
            if 'values' in kw:
                values = list(kw['values'])
                if len(values) > 1:
                    values[1] = wrap_text(str(values[1]))
                    kw['values'] = tuple(values)
            return original_insert(parent, index, **kw)

        self.tree.insert = custom_insert

        # コンテキストメニューのバインド
        self.tree.bind("<Button-3>", self.show_context_menu)

        # キーボードショートカットによるコピー機能を追加
        self.tree.bind('<Control-c>', self.copy_selected)
        self.tree.bind('<Command-c>', self.copy_selected)  # Mac用

        # 選択してコピーできるようにする
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # 右クリックメニューを有効にする
        self.tree.bind("<Button-3>", self.show_context_menu)

        # コンテキストメニューの作成
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="コピー", command=lambda: self.copy_selected(None))
        self.context_menu.add_command(label="選択行を削除", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="すべて選択", command=self.select_all)

    def update_results(self):
        """結果を更新"""
        try:
            while True:
                try:
                    msg_type, data = self.result_queue.get_nowait()
                    
                    if msg_type == 'result':
                        logging.info(f"結果をツリーに追加: {data}")
                        
                        content = str(data['content'])
                        values = (
                            str(data['num']),
                            content,
                            len(content)
                        )
                        
                        try:
                            self.tree.insert('', tk.END, values=values)
                            self.update_total_chars()  # 確実に呼び出し
                            logging.info(f"Treeview に追加完了: {values}")
                        except Exception as e:
                            logging.error(f"Treeview 追加エラー: {e}, データ: {values}")
                        
                        self.progress_var.set(self.progress_var.get() + 1)
                        self.tree.see(self.tree.get_children()[-1])
                        
                    elif msg_type == 'error':
                        logging.error(f"エラーメッセージを受信: {data}")
                        messagebox.showerror("エラー", f"スクレイピング中にエラー: {data}")
                        self.stop_scraping()
                        return
                        
                    elif msg_type == 'finished':
                        logging.info("スクレイピング完了")
                        self.finish_scraping()
                        return
                        
                except queue.Empty:
                    break
            
            # 次の更新をスケジュール
            if self.is_scraping:
                self.root.after(100, self.update_results)
                
        except Exception as e:
            logging.error(f"結果更新中にエラー: {e}", exc_info=True)
            messagebox.showerror("エラー", f"結果更新中にエラー: {e}")
            self.stop_scraping()

    def copy_selected(self, event=None):
        """選択された項目をコピー"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # 選択された行のデータを取得
        rows = []
        for item in selected_items:
            values = self.tree.item(item)['values']
            rows.append('\t'.join(str(v) for v in values))
        
        # クリップボードにコピー
        text = '\n'.join(rows)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def update_total_chars(self):
        """合計文字数を更新"""
        total = 0
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if values and len(values) > 2:  # 文字数は3番目の列
                try:
                    total += int(values[2])
                except (ValueError, TypeError):
                    continue
        
        # 合計を表示（3桁区切りで）
        self.total_chars_label.config(text=f"合計文字数: {total:,}")

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
    
    def export_results(self, format_type: str):
        """結果をエクスポート"""
        if not self.tree.get_children():
            messagebox.showerror("エラー", "エクスポートする結果がありません。")
            return

        if format_type == "csv":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv")],
                title="CSVとして保存"
            )
            if file_path:
                try:
                    data = []
                    for item in self.tree.get_children():
                        values = self.tree.item(item)['values']
                        data.append({
                            '番号': values[0],
                            '発言内容': values[1],
                            '文字数': values[2]
                        })
                    
                    with open(file_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=['番号', '発言内容', '文字数'])
                        writer.writeheader()
                        writer.writerows(data)
                    
                    messagebox.showinfo("完了", "CSVファイルを保存しました")
                    
                except Exception as e:
                    logging.error(f"CSVファイルの保存に失敗: {e}")
                    messagebox.showerror("エラー", f"ファイルの保存に失敗しました: {e}")

        elif format_type == "excel":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excelファイル", "*.xlsx")],
                title="Excelとして保存"
            )
            if file_path:
                try:
                    data = []
                    for item in self.tree.get_children():
                        values = self.tree.item(item)['values']
                        data.append({
                            '番号': values[0],
                            '発言内容': values[1],
                            '文字数': values[2]
                        })
                    
                    df = pd.DataFrame(data)
                    df.to_excel(file_path, index=False)
                    
                    messagebox.showinfo("完了", "Excelファイルを保存しました")
                    
                except Exception as e:
                    logging.error(f"Excelファイルの保存に失敗: {e}")
                    messagebox.showerror("エラー", f"ファイルの保存に失敗しました: {e}")

    def _export_to_csv(self, file_path: str):
        """CSVとしてエクスポート"""
        try:
            text_content = self.results_text.get('1.0', tk.END)
            results = self._parse_results(text_content)
            
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['番号', '内容', '文字数'])
                for result in results:
                    writer.writerow([result['number'], result['content'], result['chars']])
            
            messagebox.showinfo("完了", "CSVファイルを保存しました")
        except Exception as e:
            messagebox.showerror("エラー", f"保存中にエラーが発生しました: {e}")

    def _parse_results(self, text_content: str) -> List[Dict]:
        """テキスト内容をパースして結果のリストを返す"""
        results = []
        lines = text_content.split('\n')
        current_result = {}
        content_lines = []
        
        for line in lines:
            if line.startswith('【'):
                # 新しい結果の開始
                if current_result and content_lines:
                    current_result['content'] = '\n'.join(content_lines)
                    results.append(current_result)
                    content_lines = []
                
                # 番号と文字数を抽出
                number = line[line.find('【')+1:line.find('】')]
                chars = int(line[line.find('(')+1:line.find('文字')])
                current_result = {'number': number, 'chars': chars}
            elif line.startswith('-' * 80):
                # 区切り線は無視
                continue
            else:
                # 内容行
                content_lines.append(line.strip())
        
        # 最後の結果を追加
        if current_result and content_lines:
            current_result['content'] = '\n'.join(content_lines)
            results.append(current_result)
        
        return results
    
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
        self.context_menu.add_command(label="コピー", command=lambda: self.copy_selected(None))
        self.context_menu.add_command(label="選択行を削除", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="すべて選択", command=self.select_all)
        
        self.tree.bind("<Button-3>", self.show_context_menu)

    def copy_selection(self, event=None):
        """選択された項目をコピー"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        copy_text = []
        for item in selected_items:
            values = self.tree.item(item)['values']
            # タブ区切りでテキストを作成
            copy_text.append('\t'.join(str(x) for x in values))
        
        # クリップボードにコピー
        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(copy_text))
        
    def copy_cell_content(self):
        # 現在選択されているセルの内容をコピー
        selected = self.tree.selection()
        if not selected:
            return
        
        column = self.tree.identify_column(self.last_clicked_x)  # 最後にクリックした列を特定
        col_num = int(column.replace('#', '')) - 1
        cell_value = self.tree.item(selected[0])['values'][col_num]
        
        self.root.clipboard_clear()
        self.root.clipboard_append(str(cell_value))

    def copy_selected_rows(self):
        # 選択された行全体をコピー
        selected = self.tree.selection()
        if not selected:
            return
        
        text = []
        for item in selected:
            values = self.tree.item(item)['values']
            text.append('\t'.join(str(x) for x in values))
        
        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(text))

    # マウスクリック位置を記録
    def on_tree_click(self, event):
        self.last_clicked_x = event.x
        self.last_clicked_y = event.y
        
    def show_context_menu(self, event):
        """コンテキストメニューを表示"""
        self.context_menu.post(event.x_root, event.y_root)

    
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
    


    def finish_scraping(self):
        """スクレイピングの終了処理"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.url_text.config(state=tk.NORMAL)
        
        total_results = len(self.tree.get_children())
        self.status_label.config(text=f"完了 - {total_results}件の結果")
        
        if total_results > 0:
            logging.info(f"スクレイピング完了: {total_results}件の結果を取得")

    def stop_scraping(self):
        """スクレイピングを停止"""
        self.is_scraping = False
        self.status_label.config(text="停止中...")
        self.finish_scraping()

    
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
        self.results_text.configure(state='normal')
        self.results_text.delete('1.0', tk.END)
        self.results_text.configure(state='disabled')
        self.total_chars_label.config(text="合計文字数: 0")
        
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
        
        self.export_results("excel")  # または "csv"

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




