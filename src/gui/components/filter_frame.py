import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable
import re

class FilterFrame(ttk.LabelFrame):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, text="フィルター", padding="5", **kwargs)
        self.tree = tree
        self.original_items = []  # 元のデータを保持
        self.filters: Dict[str, Any] = {}
        self.create_widgets()
    
    def create_widgets(self):
        """フィルター用ウィジェットの作成"""
        # 検索フレーム
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=5, pady=2)
        
        # キーワード検索
        ttk.Label(search_frame, text="キーワード:").pack(side='left', padx=2)
        self.keyword_var = tk.StringVar()
        self.keyword_var.trace('w', self.on_filter_change)
        ttk.Entry(
            search_frame,
            textvariable=self.keyword_var,
            width=30
        ).pack(side='left', padx=5)
        
        # 話者フィルター
        speaker_frame = ttk.Frame(self)
        speaker_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(speaker_frame, text="話者:").pack(side='left', padx=2)
        self.speaker_var = tk.StringVar()
        self.speaker_var.trace('w', self.on_filter_change)
        self.speaker_combo = ttk.Combobox(
            speaker_frame,
            textvariable=self.speaker_var,
            width=20
        )
        self.speaker_combo.pack(side='left', padx=5)
        
        # 文字数フィルター
        length_frame = ttk.Frame(self)
        length_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(length_frame, text="文字数:").pack(side='left', padx=2)
        self.min_length_var = tk.StringVar(value="0")
        self.min_length_var.trace('w', self.on_filter_change)
        ttk.Entry(
            length_frame,
            textvariable=self.min_length_var,
            width=5
        ).pack(side='left', padx=2)
        
        ttk.Label(length_frame, text="～").pack(side='left')
        
        self.max_length_var = tk.StringVar()
        self.max_length_var.trace('w', self.on_filter_change)
        ttk.Entry(
            length_frame,
            textvariable=self.max_length_var,
            width=5
        ).pack(side='left', padx=2)
        
        # クリアボタン
        ttk.Button(
            self,
            text="フィルターをクリア",
            command=self.clear_filters
        ).pack(side='right', padx=5, pady=2)
    
    def update_speaker_list(self):
        """話者リストを更新"""
        speakers = set()
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            speakers.add(values[1])  # 話者は2列目
        
        self.speaker_combo['values'] = [''] + sorted(list(speakers))
    
    def store_original_items(self):
        """現在の表示内容を保存"""
        self.original_items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            self.original_items.append((item, values))
    
    def on_filter_change(self, *args):
        """フィルター条件変更時の処理"""
        # フィルター条件の取得
        keyword = self.keyword_var.get().lower()
        speaker = self.speaker_var.get()
        
        try:
            min_length = int(self.min_length_var.get()) if self.min_length_var.get() else 0
            max_length = int(self.max_length_var.get()) if self.max_length_var.get() else float('inf')
        except ValueError:
            return
        
        # 現在の表示をクリア
        self.tree.delete(*self.tree.get_children())
        
        # フィルター適用
        for item_id, values in self.original_items:
            content = values[2].lower()  # 発言内容は3列目
            length = values[3]  # 文字数は4列目
            
            if speaker and values[1] != speaker:  # 話者フィルター
                continue
                
            if keyword and keyword not in content:  # キーワードフィルター
                continue
                
            if not (min_length <= length <= max_length):  # 文字数フィルター
                continue
            
            self.tree.insert('', 'end', values=values)
    
    def clear_filters(self):
        """フィルターをクリア"""
        self.keyword_var.set('')
        self.speaker_var.set('')
        self.min_length_var.set('0')
        self.max_length_var.set('')
        
        # 元のデータを復元
        self.tree.delete(*self.tree.get_children())
        for item_id, values in self.original_items:
            self.tree.insert('', 'end', values=values)