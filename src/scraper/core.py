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
import textwrap
from bs4.element import Tag  # これを追加


@dataclass
class ScrapingResult:
    """スクレイピング結果を格納するデータクラス"""
    url: str
    speaker: str
    content: str
    char_count: int
    timestamp: str

class TextProcessor:
    """テキスト処理を担当するクラス"""
    def __init__(self, use_line_break: bool = False):
        self.use_line_break = use_line_break

    def process_content(self, content: str) -> str:
        """テキストを処理して整形する"""
        # >>数字 形式の引用を削除
        content = re.sub(r'>>+\d+\s*', '', content)
        
        # >で始まる引用行を削除
        content = '\n'.join(line.strip() for line in content.split('\n') 
                          if not line.strip().startswith('>'))
        
        # 改行オプションが有効な場合のみ23文字改行を適用
        if self.use_line_break:
            content = '\n'.join(textwrap.wrap(content, width=23, replace_whitespace=False))

        return content.strip()

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
                    'div.thread'
                ]
            }
        }

class Scraper:
    """スクレイピングの実行を担当するクラス"""
    def __init__(self, pattern_config: Optional[Path] = None, proxy_manager=None):
        self.pattern_manager = ScrapingPattern(pattern_config)
        self.text_processor = TextProcessor()
        if proxy_manager:
            self.session = proxy_manager.get_session()
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

    def set_line_break_option(self, use_line_break: bool):
        """改行オプションを設定"""
        self.text_processor.use_line_break = use_line_break

    def process_post(self, text: str) -> Optional[ScrapingResult]:
        """投稿テキストを処理"""
        try:
            logging.debug(f"処理中のテキスト: {text[:200]}")
            
            patterns = [
                r'^\s*(\d+).*?\n*(.*?)(?=\d+[^\d]|$)',
                r'^\s*(\d+)[^\d]+(.*?)(?=\n\d+[^\d]|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                if match:
                    number = match.group(1)
                    content = match.group(2).strip()
                    
                    # テキスト処理を適用
                    content = self.text_processor.process_content(content)
                    
                    if content:
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

                # アルセウス速報のパターン
                if 'arceus-sokuho.com' in url:
                    # 1. スレッドのレスを抽出
                    entry_content = soup.find('div', class_='entry-content')
                    if entry_content:
                        current_header = None
                        for element in entry_content.children:
                            if isinstance(element, Tag):
                                # ヘッダー(投稿者情報)の処理
                                if 't_h' in element.get('class', []):
                                    current_header = element
                                
                                # レス本文の処理
                                elif 't_poke' in element.get('class', []):
                                    if current_header:
                                        try:
                                            # 投稿者名を取得
                                            author = current_header.find('span', style=lambda x: x and 'font-weight: bold' in x)
                                            if author:
                                                author = author.text.strip()
                                            
                                            # 本文を取得
                                            content = element.get_text().strip()
                                            
                                            # テキスト処理を適用
                                            content = self.text_processor.process_content(content)
                                            
                                            if content and len(content) >= min_length:
                                                result = ScrapingResult(
                                                    url=url,
                                                    speaker=author if author else 'Unknown',
                                                    content=content,
                                                    char_count=len(content),
                                                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                )
                                                results.append(result)
                                                logging.debug(f"スレッドレスを抽出: {author} | {content[:100]}...")
                                        
                                        except Exception as e:
                                            logging.error(f"スレッドレスの処理中にエラー: {e}")
                                            continue
                    
                    # 2. コメント欄のレスを抽出
                    comments = soup.find_all('li', {'class': 'comment'})
                    for comment in comments:
                        try:
                            # コメントIDを取得
                            comment_id = comment.get('id', '').replace('comment-', '')
                            
                            # 投稿者名を取得
                            author = comment.find('cite', class_='comment-author')
                            if author:
                                author = author.text.strip()
                            
                            # コメント本文を取得
                            content_div = comment.find('div', class_='st-comment-content')
                            if content_div:
                                # 不要な要素を除去
                                [p.decompose() for p in content_div.find_all('p', class_='wpulike')]
                                [div.decompose() for div in content_div.find_all('div', class_='wpulike')]
                                
                                content = content_div.get_text().strip()
                                
                                # テキスト処理を適用
                                content = self.text_processor.process_content(content)
                                
                                if content and len(content) >= min_length:
                                    result = ScrapingResult(
                                        url=url,
                                        speaker=f"{author}#{comment_id}" if author else comment_id,
                                        content=content,
                                        char_count=len(content),
                                        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    )
                                    results.append(result)
                                    logging.debug(f"コメントを抽出: {comment_id} | {content[:100]}...")
                        
                        except Exception as e:
                            logging.error(f"コメントの処理中にエラー: {e}")
                            continue
                            
                    logging.info(f"アルセウス速報の抽出完了 - {len(results)} 件の結果")

                # あにまんch掲示板のパターン
                elif 'bbs.animanch.com' in url:
                    article = soup.find('article', id='reslist')
                    if article:
                        posts = article.find_all('li', class_='list-group-item')
                        
                        for post in posts:
                            if post.find('div', class_='disabled'):
                                continue
                            
                            header = post.find('div', class_='resheader')
                            if not header:
                                continue
                                
                            number = header.find('span', class_='resnumber')
                            if not number:
                                continue
                            number = number.text.strip()
                            
                            body = post.find('div', class_='resbody')
                            if not body:
                                continue
                                
                            content_parts = []
                            for p in body.find_all('p'):
                                text = p.get_text().strip()
                                content_parts.append(text)
                            
                            content = '\n'.join(content_parts).strip()
                            # テキスト処理を適用
                            content = self.text_processor.process_content(content)
                            
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

                # あにまんchのブログ記事パターン
                elif 'animanch.com' in url:
                    intro_section = soup.find('section', id='introtext')
                    main_section = soup.find('section', id='maintext')
                    
                    posts = []
                    if intro_section:
                        posts.extend(intro_section.find_all('div', class_='res'))
                    if main_section:
                        posts.extend(main_section.find_all('div', class_='res'))
                        
                    for post in posts:
                        header = post.find('div', class_='t_h')
                        if header:
                            number = header.find('span', class_='resnum')
                            if not number:
                                continue
                            number = number.text.strip()
                            
                            body = post.find('div', class_='t_b')
                            if body:
                                content = body.get_text().strip()
                                # テキスト処理を適用
                                content = self.text_processor.process_content(content)
                                
                                if content and len(content) >= min_length:
                                    result = ScrapingResult(
                                        url=url,
                                        speaker=number,
                                        content=content,
                                        char_count=len(content),
                                        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    )
                                    results.append(result)
                    
                    # コメント欄のレス抽出
                    comment_area = soup.find('div', id='commentarea')
                    if comment_area:
                        comments = comment_area.find_all('div', class_='commentwrap')
                        for comment in comments:
                            number = comment.find('span', class_='commentnumber')
                            if not number:
                                continue
                            number = number.text.strip()
                            
                            body = comment.find('div', class_='commentbody')
                            if body:
                                content_parts = []
                                for text in body.stripped_strings:
                                    if not text.startswith('>>'):
                                        content_parts.append(text)
                                
                                content = ' '.join(content_parts).strip()
                                # テキスト処理を適用
                                content = self.text_processor.process_content(content)
                                
                                if content and len(content) >= min_length:
                                    result = ScrapingResult(
                                        url=url,
                                        speaker=number,
                                        content=content,
                                        char_count=len(content),
                                        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    )
                                    results.append(result)

                # doorblog.jpのパターン (新規追加)
                elif 'doorblog.jp' in url:
                    comments = soup.find_all('li', class_='comment-set')
                    for comment in comments:
                        try:
                            # コメント番号と著者名の取得
                            comment_info = comment.find('li', class_='comment-author')
                            if not comment_info:
                                continue
                                
                            number = comment_info.text.strip().split('.')[0]
                            
                            # コメント本文の取得
                            body = comment.find('li', class_='comment-body')
                            if not body:
                                continue
                                
                            # 引用部分を除去
                            quotes = body.find_all('a', href=lambda x: x and x.startswith('#comment-'))
                            for quote in quotes:
                                quote.decompose()
                                
                            content = body.get_text().strip()
                            
                            # テキスト処理を適用
                            content = self.text_processor.process_content(content)
                            
                            if content and len(content) >= min_length:
                                result = ScrapingResult(
                                    url=url,
                                    speaker=number,
                                    content=content,
                                    char_count=len(content),
                                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                )
                                results.append(result)
                                logging.debug(f"コメントを抽出: {number} | {content[:100]}...")
                        
                        except Exception as e:
                            logging.error(f"コメントの処理中にエラー: {e}")
                            continue

                # パカパカ情報局のパターン
                else:
                    content_area = soup.find('div', class_='content')
                    if content_area:
                        # すべての t_h と t_b のペアを探す（再帰的に検索）
                        all_headers = content_area.find_all('div', class_='t_h', recursive=True)
                        
                        for header in all_headers:
                            try:
                                # 次の兄弟要素を探して本文を見つける
                                body = None
                                next_elem = header.next_sibling
                                
                                # 本文を探す（次の数要素を確認）
                                for _ in range(3):  # 最大3要素先まで確認
                                    if isinstance(next_elem, Tag) and 't_b' in next_elem.get('class', []):
                                        body = next_elem
                                        break
                                    next_elem = next_elem.next_sibling if next_elem else None
                                
                                if not body:
                                    continue
                                
                                # 不要な要素を削除
                                [ad.decompose() for ad in body.find_all(class_='diver_widget_adarea')]
                                [ad.decompose() for ad in body.find_all(id=lambda x: x and 'widget-in-article' in x)]
                                
                                # 本文を抽出
                                content = body.get_text().strip()
                                
                                # 無視すべきキーワードのチェック
                                ignore_keywords = ['スポンサーリンク', 'Facebook', 'post', 'はてブ']
                                if any(keyword in content for keyword in ignore_keywords):
                                    continue
                                
                                # テキスト処理を適用
                                content = self.text_processor.process_content(content)
                                
                                # 投稿者情報の抽出
                                speaker = ''
                                # 投稿者情報の抽出を修正
                                if header:
                                    # 投稿番号のみを抽出（冒頭の数字だけ）
                                    number_match = re.search(r'^\s*(\d+):', header.get_text())
                                    if number_match:
                                        speaker = number_match.group(1)  # 番号だけを取得
                                    else:
                                        speaker = ''  # 番号が見つからない場合は空文字

                                    # 有効な投稿のみ追加
                                    if content and len(content) >= min_length:
                                        result = ScrapingResult(
                                            url=url,
                                            speaker=speaker,  # 番号だけを設定
                                            content=content,
                                            char_count=len(content),
                                            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        )
                                        results.append(result)
                                        logging.debug(f"投稿を抽出: #{speaker} | {content[:100]}...")
                                    
                            except Exception as e:
                                logging.error(f"投稿の処理中にエラー: {e}")
                                continue

                        logging.info(f"スクレイピング完了 - {len(results)} 件の結果")
                    
                    # 既存の掲示板パターン（結果が得られなかった場合のフォールバック）
                    if not results:
                        posts = soup.find_all('div', class_='res')
                        for post in posts:
                            header = post.find('div', class_='t_h')
                            if header:
                                number = header.find('span', class_='resnum')
                                if number:
                                    number = number.text.strip()
                                    body = post.find('div', class_='t_b')
                                    if body:
                                        content = body.get_text().strip()
                                        # テキスト処理を適用
                                        content = self.text_processor.process_content(content)
                                        
                                        if content and len(content) >= min_length:
                                            result = ScrapingResult(
                                                url=url,
                                                speaker=number,
                                                content=content,
                                                char_count=len(content),
                                                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            )
                                            results.append(result)

                logging.info(f"スクレイピング完了 - {len(results)} 件の結果")
                return results

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

if __name__ == "__main__":
    # ロガーの設定
    setup_logger()
    
    # スクレイパーの使用例
    scraper = Scraper()
    scraper.set_line_break_option(True)  # 23文字改行を有効化
    
    try:
        results = scraper.scrape_url("https://example.com", min_length=10)
        for result in results:
            print(f"発言番号: {result.speaker}")
            print(f"内容: {result.content}")
            print(f"文字数: {result.char_count}")
            print("---")
    except Exception as e:
        logging.error(f"スクレイピング実行エラー: {e}")