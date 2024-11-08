import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import json
import pandas as pd
import logging

class ExportManager:
    def __init__(self, parent, tree):
        self.parent = parent
        self.tree = tree
        
    def show_export_dialog(self):
        """エクスポートダイアログを表示"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("結果を保存")
        dialog.geometry("300x150")
        
        # フォーマット選択
        format_frame = ttk.LabelFrame(dialog, text="出力形式", padding="5")
        format_frame.pack(fill='x', padx=5, pady=5)
        
        format_var = tk.StringVar(value="csv")
        ttk.Radiobutton(format_frame, text="CSV", variable=format_var, value="csv").pack(side='left', padx=5)
        ttk.Radiobutton(format_frame, text="JSON", variable=format_var, value="json").pack(side='left', padx=5)
        ttk.Radiobutton(format_frame, text="Excel", variable=format_var, value="excel").pack(side='left', padx=5)
        
        # ボタン
        button_frame = ttk.Frame(dialog, padding="5")
        button_frame.pack(fill='x', side='bottom')
        
        ttk.Button(
            button_frame,
            text="保存",
            command=lambda: self.export_data(format_var.get(), dialog)
        ).pack(side='right', padx=5)
        
        ttk.Button(
            button_frame,
            text="キャンセル",
            command=dialog.destroy
        ).pack(side='right', padx=5)
    
    def get_tree_data(self):
        """Treeviewのデータを取得"""
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            data.append({
                '番号': values[0],
                '発言内容': values[1],
                '文字数': values[2]
            })
        return data
    
    def export_data(self, format_type: str, dialog: tk.Toplevel):
        """データをエクスポート"""
        try:
            data = self.get_tree_data()
            
            if format_type == "csv":
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSVファイル", "*.csv")],
                    title="CSVとして保存"
                )
                if file_path:
                    with open(file_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=['番号', '発言内容', '文字数'])
                        writer.writeheader()
                        writer.writerows(data)
            
            elif format_type == "json":
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSONファイル", "*.json")],
                    title="JSONとして保存"
                )
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            
            elif format_type == "excel":
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excelファイル", "*.xlsx")],
                    title="Excelとして保存"
                )
                if file_path:
                    df = pd.DataFrame(data)
                    df.to_excel(file_path, index=False)
            
            if file_path:
                logging.info(f"データを保存しました: {file_path}")
                messagebox.showinfo("完了", "データを保存しました")
                dialog.destroy()
                
        except Exception as e:
            logging.error(f"データの保存に失敗: {e}")
            messagebox.showerror("エラー", f"データの保存に失敗しました: {e}")