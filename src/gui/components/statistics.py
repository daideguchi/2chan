import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import List, Dict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class StatisticsWindow:
    def __init__(self, parent, tree):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("スクレイピング結果の統計")
        self.dialog.geometry("800x600")
        self.tree = tree
        
        self.create_widgets()
        self.calculate_statistics()
    
    def create_widgets(self):
        """ウィジェットの作成"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # サマリータブ
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="サマリー")
        self.create_summary_tab(summary_frame)
        
        # グラフタブ
        graph_frame = ttk.Frame(notebook)
        notebook.add(graph_frame, text="グラフ")
        self.create_graph_tab(graph_frame)
        
        # 詳細タブ
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="詳細")
        self.create_details_tab(details_frame)
    
    def create_summary_tab(self, parent):
        """サマリータブの作成"""
        self.summary_text = tk.Text(parent, wrap=tk.WORD, padx=10, pady=10)
        self.summary_text.pack(fill='both', expand=True)
    
    def create_graph_tab(self, parent):
        """グラフタブの作成"""
        self.figure, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 5))
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_details_tab(self, parent):
        """詳細タブの作成"""
        self.details_tree = ttk.Treeview(parent, columns=('項目', '値'), show='headings')
        self.details_tree.heading('項目', text='項目')
        self.details_tree.heading('値', text='値')
        self.details_tree.pack(fill='both', expand=True)
    
    def get_tree_data(self) -> List[Dict]:
        """Treeviewのデータを取得"""
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            data.append({
                '番号': values[0],
                '発言内容': values[1],
                '文字数': int(values[2])  # 文字列から整数に変換
            })
        return data
    
    def calculate_statistics(self):
        """統計情報を計算"""
        data = self.get_tree_data()
        df = pd.DataFrame(data)
        
        # サマリー統計
        total_posts = len(df)
        total_chars = df['文字数'].sum()
        avg_chars = df['文字数'].mean()
        unique_speakers = df['番号'].nunique()
        
        summary = f"""スクレイピング結果の統計情報

総投稿数: {total_posts}
総文字数: {total_chars:,}
平均文字数: {avg_chars:.1f}
ユニーク投稿者数: {unique_speakers}
"""
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary)
        
        # グラフの作成
        # 投稿者別投稿数
        speaker_counts = df['番号'].value_counts()
        self.ax1.clear()
        speaker_counts.head(10).plot(kind='bar', ax=self.ax1)
        self.ax1.set_title('投稿者別投稿数 (Top 10)')
        self.ax1.tick_params(axis='x', rotation=45)
        
        # 文字数の分布
        self.ax2.clear()
        df['文字数'].hist(bins=30, ax=self.ax2)
        self.ax2.set_title('文字数の分布')
        self.ax2.set_xlabel('文字数')
        self.ax2.set_ylabel('頻度')
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        # 詳細統計
        details = [
            ('総投稿数', total_posts),
            ('総文字数', f"{total_chars:,}"),
            ('平均文字数', f"{avg_chars:.1f}"),
            ('最大文字数', df['文字数'].max()),
            ('最小文字数', df['文字数'].min()),
            ('標準偏差 (文字数)', f"{df['文字数'].std():.1f}"),
            ('ユニーク投稿者数', unique_speakers)
        ]
        
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        
        for item, value in details:
            self.details_tree.insert('', tk.END, values=(item, value))