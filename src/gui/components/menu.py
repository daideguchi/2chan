import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .settings_dialog import SettingsDialog
from .log_window import LogWindow
import logging

class MainMenu:
    def __init__(self, parent, settings_manager):
        self.parent = parent
        self.settings_manager = settings_manager
        self.create_menu()
        self.log_window = None
    
    def create_menu(self):
        """メインメニューの作成"""
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="URLリストを開く", command=self.load_url_list)
        file_menu.add_command(label="結果を保存", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.parent.quit)
        
        # 表示メニュー
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="表示", menu=view_menu)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="表示", menu=view_menu)
        view_menu.add_command(label="ログビューア", command=self.show_log_window)
        view_menu.add_command(label="結果の統計", command=self.show_statistics)
        
        # ツールメニュー
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール", menu=tools_menu)
        tools_menu.add_command(label="設定", command=self.show_settings)
        tools_menu.add_command(label="パターンテスト", command=self.show_pattern_test)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="ヘルプ", command=self.show_help)
        help_menu.add_command(label="バージョン情報", command=self.show_version)
    
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
                # メインウィンドウのURL入力エリアを更新するコールバックを呼び出す
                if hasattr(self.parent, 'update_url_list'):
                    self.parent.update_url_list(urls)
            except Exception as e:
                logging.error(f"URLリストの読み込みに失敗: {e}")
                messagebox.showerror("エラー", f"ファイルの読み込みに失敗しました: {e}")
    
    def save_results(self):
        """結果を保存"""
        if hasattr(self.parent, 'export_manager'):
            self.parent.export_manager.show_export_dialog()
    
    def show_log_window(self):
        """ログウィンドウを表示"""
        if self.log_window is None or not self.log_window.dialog.winfo_exists():
            self.log_window = LogWindow(self.parent)
        else:
            self.log_window.dialog.lift()
    
    def show_statistics(self):
        """結果の統計を表示"""
        if hasattr(self.parent, 'show_statistics_window'):
            self.parent.show_statistics_window()
    
    def show_settings(self):
        """設定ダイアログを表示"""
        SettingsDialog(self.parent, self.settings_manager)
    
    def show_pattern_test(self):
        """パターンテストダイアログを表示"""
        # パターンテストダイアログの実装
        pass
    
    def show_help(self):
        """ヘルプを表示"""
        help_text = """
2ちゃんねるスクレイパー ヘルプ

基本的な使い方:
1. URLを入力欄に貼り付けるか、「ファイル」メニューからURLリストを読み込みます
2. 必要に応じて「ツール」メニューから設定を調整します
3. 「スクレイピング開始」ボタンをクリックします
4. 結果は表形式で表示され、CSVまたはExcelとして保存できます

詳細な設定:
- スクレイピングパターンのカスタマイズ
- プロキシ設定
- 同時実行数の調整
- 待機時間の設定

ログの確認:
「表示」メニューから「ログビューア」を開くと、詳細なログを確認できます。
        """
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("ヘルプ")
        dialog.geometry("600x400")
        
        text = tk.Text(dialog, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert('1.0', help_text)
        text.config(state=tk.DISABLED)
    
    def show_version(self):
        """バージョン情報を表示"""
        version_info = """
2ちゃんねるスクレイパー v1.0.0
Copyright (c) 2024

- マルチスレッド対応
- カスタマイズ可能なスクレイピングパターン
- エクスポート機能
- ログ機能
        """
        
        messagebox.showinfo("バージョン情報", version_info)