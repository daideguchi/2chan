import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict

class ExportManager:
    """エクスポート機能を管理するクラス"""
    
    def __init__(self, parent, tree):
        self.parent = parent
        self.tree = tree
        self.create_export_buttons()
    
    def create_export_buttons(self):
        """エクスポートボタンの作成"""
        export_frame = ttk.Frame(self.parent)
        export_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(
            export_frame,
            text="Excelとして保存",
            command=lambda: self.export_data("excel")
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            export_frame,
            text="CSVとして保存",
            command=lambda: self.export_data("csv")
        ).grid(row=0, column=1, padx=5)
    
    def get_tree_data(self) -> List[Dict]:
        """Treeviewのデータを取得"""
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            data.append({
                'URL': values[0],
                '話者': values[1],
                '発言内容': values[2],
                '文字数': values[3],
                '取得時刻': values[4]
            })
        return data
    
    def export_data(self, format_type: str):
        """データをエクスポート"""
        if not self.tree.get_children():
            messagebox.showerror("エラー", "エクスポートするデータがありません。")
            return
        
        try:
            data = self.get_tree_data()
            df = pd.DataFrame(data)
            
            if format_type == "excel":
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")],
                    title="Excelファイルとして保存"
                )
                if file_path:
                    df.to_excel(file_path, index=False)
                    
            elif format_type == "csv":
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    title="CSVファイルとして保存"
                )
                if file_path:
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            if file_path:
                messagebox.showinfo("成功", "ファイルを保存しました。")
                logging.info(f"データを {file_path} にエクスポートしました")
                
        except Exception as e:
            error_msg = f"エクスポート中にエラーが発生: {e}"
            logging.error(error_msg)
            messagebox.showerror("エラー", error_msg)