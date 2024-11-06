from bs4 import BeautifulSoup
import requests
import logging
import yaml
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

@dataclass
class ScrapingResult:
    """スクレイピング結果を格納するデータクラス"""
    url: str
    speaker: str
    content: str
    char_count: int
    timestamp: str

class ScrapingPattern:
    """スクレイピングパターンを管理するクラス"""
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path("config/default_patterns.yml")
        
        self.patterns = self.load_patterns(config_path)
    
    def load_patterns(self, config_path: Path) -> dict:
        """設定ファイルからパターンを読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"パターン設定の読み込みに失敗: {e}")
            return self.get_default_patterns()
    
    def get_default_patterns(self) -> dict:
        """デフォルトのパターンを返す"""
        return {
            'default': {
                'post_patterns': [
                    # 番号、投稿内容を取得するパターン
                    r'^(\d+).*?\n(.+?)(?:\n|$)',
                    # >>による引用を除外するパターン
                    r'(?!^>>)'
                ],
                'post_selectors': [
                    'div.post',
                    'div.comment',
                    'p.message',
                    'div.comentbox',
                    'div.message',
                    'div.thread'  # スレッド全体を取得する場合
                ]
            }
        }

class Scraper:
    """スクレイピングの実行を担当するクラス"""
    def __init__(self, pattern_config: Optional[Path] = None, proxy_manager=None):
        self.pattern_manager = ScrapingPattern(pattern_config)
        if proxy_manager:
            self.session = proxy_manager.get_session()
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

    def process_post(self, text: str) -> Optional[ScrapingResult]:
        """投稿テキストを処理"""
        try:
            # デバッグ用にテキストの内容を出力
            logging.debug(f"処理中のテキスト: {text[:200]}")
            
            # 番号と内容を抽出するパターンを修正
            patterns = [
                r'^\s*(\d+).*?\n*(.*?)(?=\d+[^\d]|$)',  # 基本パターン
                r'^\s*(\d+)[^\d]+(.*?)(?=\n\d+[^\d]|$)',  # 別のパターン
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                if match:
                    number = match.group(1)
                    content = match.group(2).strip()
                    
                    # >>で始まる行や日付のみの行は除外
                    if content.startswith('>>') or re.match(r'^\d{2}/\d{2}/\d{2}', content):
                        continue
                    
                    logging.debug(f"マッチ: 番号={number}, 内容={content}")
                    
                    return ScrapingResult(
                        url='',
                        speaker=number,
                        content=content,
                        char_count=len(content),
                        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
            
            return None
            
        except Exception as e:
            logging.error(f"投稿処理エラー: {e}")
            return None


    def scrape_url(self, url: str, min_length: int = 0) -> List[ScrapingResult]:
        """単一URLをスクレイピング"""
        try:
            logging.info(f"URLにアクセス中: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            logging.info(f"ステータスコード: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # 投稿を探す（div class="res"）
            posts = soup.find_all('div', class_='res')
            
            for post in posts:
                # ヘッダー部分から投稿番号を取得
                header = post.find('div', class_='t_h')
                if header:
                    number = header.find('span', class_='resnum')
                    if number:
                        number = number.text.strip()
                        
                        # 本文を取得
                        body = post.find('div', class_='t_b')
                        if body:
                            content = body.get_text().strip()
                            
                            # >>形式の引用を除去
                            content = re.sub(r'>>+\d+\s*', '', content).strip()
                            
                            if content and len(content) >= min_length:
                                result = ScrapingResult(
                                    url=url,
                                    speaker=number,
                                    content=content,
                                    char_count=len(content),
                                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                )
                                results.append(result)
                                logging.info(f"投稿を抽出: {number} | {content[:50]}...")
            
            logging.info(f"スクレイピング完了 - {len(results)} 件の結果")
            return results
                
        except Exception as e:
            logging.error(f"スクレイピングエラー ({url}): {e}")
            raise
                
        except Exception as e:
            logging.error(f"スクレイピングエラー ({url}): {e}")
            raise

    def scrape_urls(self, urls: List[str], max_workers: int = 3, delay: float = 1.0, 
                   min_length: int = 0) -> List[ScrapingResult]:
        """複数URLを並行してスクレイピング"""
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.scrape_url, url, min_length): url 
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    page_results = future.result()
                    results.extend(page_results)
                    time.sleep(delay)
                except Exception as e:
                    logging.error(f"URL {url} のスクレイピングに失敗: {e}")
        
        return results
    
    def update_session(self, session):
        """セッションを更新"""
        self.session = session

def setup_logger(log_path: Optional[Path] = None):
    """ロガーの設定"""
    if log_path is None:
        log_path = Path('logs/scraper.log')
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
