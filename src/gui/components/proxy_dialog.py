import tkinter as tk
from tkinter import ttk, messagebox
from src.config.proxy import ProxyConfig, ProxyManager

class ProxyDialog:
    def __init__(self, parent, proxy_manager: ProxyManager):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("プロキシ設定")
        self.dialog.geometry("500x300")
        
        self.proxy_manager = proxy_manager
        self.result = None
        
        # モーダルダイアログとして設定
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        self.load_current_config()
    
    def create_widgets(self):
        """ウィジェットの作成"""
        # プロキシ使用の有無
        self.use_proxy_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.dialog,
            text="プロキシを使用",
            variable=self.use_proxy_var,
            command=self.toggle_proxy_fields
        ).pack(padx=10, pady=5, anchor='w')
        
        # 設定フレーム
        settings_frame = ttk.LabelFrame(self.dialog, text="プロキシ設定", padding="10")
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # HTTPプロキシ
        ttk.Label(settings_frame, text="HTTPプロキシ:").grid(row=0, column=0, sticky='w', pady=2)
        self.http_proxy_var = tk.StringVar()
        self.http_proxy_entry = ttk.Entry(settings_frame, textvariable=self.http_proxy_var, width=40)
        self.http_proxy_entry.grid(row=0, column=1, pady=2)
        
        # HTTPSプロキシ
        ttk.Label(settings_frame, text="HTTPSプロキシ:").grid(row=1, column=0, sticky='w', pady=2)
        self.https_proxy_var = tk.StringVar()
        self.https_proxy_entry = ttk.Entry(settings_frame, textvariable=self.https_proxy_var, width=40)
        self.https_proxy_entry.grid(row=1, column=1, pady=2)
        
        # 認証フレーム
        auth_frame = ttk.LabelFrame(self.dialog, text="認証設定", padding="10")
        auth_frame.pack(fill='x', padx=10, pady=5)
        
        # ユーザー名
        ttk.Label(auth_frame, text="ユーザー名:").grid(row=0, column=0, sticky='w', pady=2)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(auth_frame, textvariable=self.username_var)
        self.username_entry.grid(row=0, column=1, pady=2)
        
        # パスワード
        ttk.Label(auth_frame, text="パスワード:").grid(row=1, column=0, sticky='w', pady=2)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(auth_frame, textvariable=self.password_var, show='*')
        self.password_entry.grid(row=1, column=1, pady=2)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="テスト接続",
            command=self.test_connection
        ).pack(side='left', padx=5)
        
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
    
    def toggle_proxy_fields(self):
        """プロキシ設定フィールドの有効/無効を切り替え"""
        state = 'normal' if self.use_proxy_var.get() else 'disabled'
        self.http_proxy_entry.config(state=state)
        self.https_proxy_entry.config(state=state)
        self.username_entry.config(state=state)
        self.password_entry.config(state=state)
    
    def load_current_config(self):
        """現在の設定を読み込む"""
        config = self.proxy_manager.config
        self.use_proxy_var.set(config.enabled)
        self.http_proxy_var.set(config.http or '')
        self.https_proxy_var.set(config.https or '')
        self.username_var.set(config.username or '')
        self.password_var.set(config.password or '')
        self.toggle_proxy_fields()
    
    def test_connection(self):
        """プロキシ接続をテスト"""
        config = self._get_config()
        self.proxy_manager.configure(config)
        
        if self.proxy_manager.test_connection():
            messagebox.showinfo("成功", "プロキシ接続テストが成功しました")
        else:
            messagebox.showerror("エラー", "プロキシ接続テストが失敗しました")
    
    def _get_config(self) -> ProxyConfig:
        """現在の入力値からProxyConfigを生成"""
        return ProxyConfig(
            enabled=self.use_proxy_var.get(),
            http=self.http_proxy_var.get() if self.use_proxy_var.get() else None,
            https=self.https_proxy_var.get() if self.use_proxy_var.get() else None,
            username=self.username_var.get() if self.use_proxy_var.get() else None,
            password=self.password_var.get() if self.use_proxy_var.get() else None
        )
    
    def save_settings(self):
        """設定を保存"""
        try:
            config = self._get_config()
            self.proxy_manager.configure(config)
            self.result = config
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")