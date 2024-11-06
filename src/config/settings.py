# アプリケーション設定
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ScraperSettings:
    """スクレイパーの設定を保持するデータクラス"""
    max_workers: int = 3
    delay: float = 1.0
    min_length: int = 0
    timeout: int = 30
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

class SettingsManager:
    """設定を管理するクラス"""
    
    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path("config/settings.yml")
        self.config_path = config_path
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                return self.get_default_settings()
        except Exception as e:
            logging.error(f"設定ファイルの読み込みに失敗: {e}")
            return self.get_default_settings()
    
    def get_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            'scraper': {
                'max_workers': 3,
                'delay': 1.0,
                'min_length': 0,
                'timeout': 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'gui': {
                'window_size': '1000x800',
                'theme': 'default'
            },
            'export': {
                'default_directory': str(Path.home() / "Downloads"),
                'default_format': 'excel'
            }
        }
    
    def save_settings(self, new_settings: Dict[str, Any]):
        """設定を保存"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(new_settings, f, allow_unicode=True)
            self.settings = new_settings
            logging.info("設定を保存しました")
        except Exception as e:
            logging.error(f"設定の保存に失敗: {e}")
            raise
    
    def get_scraper_settings(self) -> ScraperSettings:
        """スクレイパーの設定を取得"""
        scraper_config = self.settings.get('scraper', {})
        return ScraperSettings(
            max_workers=scraper_config.get('max_workers', 3),
            delay=scraper_config.get('delay', 1.0),
            min_length=scraper_config.get('min_length', 0),
            timeout=scraper_config.get('timeout', 30),
            user_agent=scraper_config.get('user_agent', 'Mozilla/5.0')
        )