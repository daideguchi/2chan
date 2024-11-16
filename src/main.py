from pathlib import Path
import logging
from src.gui.app import ThreadScraperGUI
from src.scraper.core import setup_logger

def main():
    # ログ設定
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    setup_logger(log_dir / "scraper.log")
    
    logging.info("アプリケーションを開始します")
    
    try:
        app = ThreadScraperGUI()
        app.run()
    except Exception as e:
        logging.error(f"アプリケーション実行中にエラーが発生: {e}", exc_info=True)
    finally:
        logging.info("アプリケーションを終了します")

if __name__ == "__main__":
    main()