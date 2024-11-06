import unittest
from unittest.mock import Mock, patch
import tkinter as tk
from pathlib import Path
import yaml
# tests/test_gui.py の先頭に追加
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = ['Noto Sans CJK JP', 'Sans-serif']  # IPAexGothic から変更

from src.gui.app import ThreadScraperGUI
from src.scraper.core import ScrapingResult

class TestGUI(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        self.root = tk.Tk()
        
        # テスト用の設定ファイルを作成
        self.test_config = Path("config/test_settings.yml")
        with open(self.test_config, "w", encoding="utf-8") as f:
            yaml.dump({
                "app": {"name": "Test App", "version": "1.0.0"},
                "scraping": {
                    "default_delay": 1.0,
                    "max_workers": 3,
                    "min_length": 0
                },
                "logging": {
                    "level": "INFO",
                    "file": "logs/test.log"
                },
                "export": {
                    "default_directory": "test_downloads",
                    "default_format": "excel"
                }
            }, f)
        
        self.app = ThreadScraperGUI()

    def tearDown(self):
        """テストの後処理"""
        self.root.destroy()
        if self.test_config.exists():
            self.test_config.unlink()

    def test_initial_state(self):
        """初期状態のテスト"""
        # 初期値の確認
        self.assertEqual(self.app.workers_var.get(), "3")
        self.assertEqual(self.app.delay_var.get(), "1.0")
        self.assertEqual(self.app.min_length_var.get(), "0")
        self.assertFalse(self.app.is_scraping)
        
        # ボタンの状態確認
        self.assertEqual(str(self.app.start_button['state']), 'normal')
        self.assertEqual(str(self.app.stop_button['state']), 'disabled')

    def test_url_input(self):
        """URL入力のテスト"""
        test_urls = "https://example.com/test1\nhttps://example.com/test2"
        self.app.url_text.insert('1.0', test_urls)
        
        # URLリストの取得をテスト
        urls = [url.strip() for url in self.app.url_text.get('1.0', tk.END).splitlines() if url.strip()]
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://example.com/test1")
        self.assertEqual(urls[1], "https://example.com/test2")

    @patch('src.scraper.core.Scraper')
    def test_start_scraping(self, mock_scraper):
        """スクレイピング開始のテスト"""
        # モックの設定
        mock_result = ScrapingResult(
            url="https://example.com/test",
            speaker="テスト太郎",
            content="テスト投稿",
            char_count=10,
            timestamp="2024-01-01 00:00:00"
        )
        self.app.scraper = mock_scraper
        mock_scraper.scrape_urls.return_value = [mock_result]
        
        # URLを設定してスクレイピングを開始
        self.app.url_text.insert('1.0', "https://example.com/test")
        
        def check_state():
            self.app.start_scraping()
            self.root.update()  # GUIの更新を待つ
            
            # スクレイピング状態の確認
            self.assertTrue(self.app.is_scraping)
            self.assertEqual(str(self.app.start_button['state']), 'disabled')
            self.assertEqual(str(self.app.stop_button['state']), 'normal')
            self.assertEqual(str(self.app.url_text['state']), 'disabled')
        
        # メインスレッドでテストを実行
        self.app.root.after(0, check_state)
        self.app.root.update()

    def test_input_validation(self):
        """入力値の検証テスト"""
        # 不正な値を設定
        self.app.workers_var.set("invalid")
        self.app.delay_var.set("invalid")
        self.app.min_length_var.set("invalid")
        
        # URLを設定
        self.app.url_text.insert('1.0', "https://example.com/test")
        
        # スクレイピングを開始（エラーが発生することを期待）
        with patch('tkinter.messagebox.showerror') as mock_error:
            self.app.start_scraping()
            mock_error.assert_called_once()

    def test_tree_operations(self):
        """Treeviewの操作テスト"""
        # テストデータの追加
        test_values = ('url', 'speaker', 'content', 10, 'time')
        self.app.tree.insert('', 'end', values=test_values)
        
        # データが正しく追加されたことを確認
        items = self.app.tree.get_children()
        self.assertEqual(len(items), 1)
        
        # アイテムの値を確認
        item_values = self.app.tree.item(items[0])['values']
        self.assertEqual(item_values, list(test_values))
        
        # 選択と削除のテスト
        self.app.tree.selection_set(items)
        self.app.delete_selected()
        self.assertEqual(len(self.app.tree.get_children()), 0)

    def test_menu_operations(self):
        """メニュー操作のテスト"""
        # メニューの存在確認
        self.assertTrue(hasattr(self.app, 'menubar'))
        
        # 各メニュー項目の確認
        menu_items = self.app.menubar.children
        self.assertGreater(len(menu_items), 0)

if __name__ == '__main__':
    unittest.main()