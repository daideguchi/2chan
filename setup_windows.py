import PyInstaller.__main__
from pathlib import Path

# プロジェクトのルートディレクトリを取得
project_root = Path(__file__).parent

PyInstaller.__main__.run([
    'src/main.py',
    '--name=2chスクレイパー',
    '--windowed',
    '--onefile',
    '--clean',
    '--noconfirm',
    '--add-data=src/config;config',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.ttk',
    '--hidden-import=requests',
    '--hidden-import=pandas',
    '--hidden-import=openpyxl',
    '--hidden-import=yaml',
    '--hidden-import=beautifulsoup4',
    '--hidden-import=lxml',
])