import PyInstaller.__main__
import sys
import os
import shutil
from pathlib import Path

def build():
    """アプリケーションをビルド"""
    if sys.platform == 'darwin':  # Mac
        # 古いビルドを削除
        os.system('rm -rf build dist *.spec')
        
        # PyInstallerでビルド
        PyInstaller.__main__.run([
            'src/main.py',
            '--name=2chスクレイパー',
            '--windowed',
            '--onedir',  # onefileではなくonedirを使用
            '--clean',
            '--noconfirm',
            '--noupx',
            '--debug=all',  # デバッグ情報を有効化
            '--hidden-import=bs4',
            '--hidden-import=tkinter',
            '--hidden-import=requests',
            '--hidden-import=pandas',
            '--hidden-import=lxml',
            '--hidden-import=yaml',
            '--hidden-import=PIL',
            '--hidden-import=_tkinter',
            '--hidden-import=tkinter.filedialog',
            '--add-data=src/config:config',
            '--add-binary=/opt/homebrew/opt/python-tk@3.9/libexec:tk',
            '--add-binary=/System/Library/Frameworks/Tk.framework/Tk:tk',
            '--add-binary=/System/Library/Frameworks/Tcl.framework/Tcl:tcl',
            '--collect-all=tkinter',
            '--collect-all=_tkinter',
        ])

        try:
            # 実行権限を付与
            os.system('chmod +x dist/2chスクレイパー/2chスクレイパー')
            
            # シンボリックリンクを作成（オプション）
            app_path = Path.home() / 'Desktop' / '2chスクレイパー.app'
            if app_path.exists():
                os.remove(app_path)
            os.symlink(
                Path.cwd() / 'dist' / '2chスクレイパー',
                app_path
            )
            
            print("\nビルドが完了しました。")
            print("アプリケーションは以下の場所にあります：")
            print(f"1. dist/2chスクレイパー/")
            print(f"2. デスクトップ上のショートカット（2chスクレイパー.app）")

        except Exception as e:
            print(f"警告: 後処理中にエラーが発生しました: {e}")
            print("アプリケーションは 'dist/2chスクレイパー' にあります。")
    
    else:  # Windows
        PyInstaller.__main__.run([
            'src/main.py',
            '--name=2chスクレイパー',
            '--windowed',
            '--onefile',
            '--clean',
            '--noconfirm',
            '--hidden-import=bs4',
            '--hidden-import=tkinter',
            '--hidden-import=requests',
            '--hidden-import=pandas',
            '--hidden-import=lxml',
            '--hidden-import=yaml',
            '--hidden-import=PIL',
            '--add-data=src/config;config',
        ])

def debug_build():
    """ビルドが失敗した場合のデバッグ用"""
    executable_path = 'dist/2chスクレイパー/2chスクレイパー'
    
    if os.path.exists(executable_path):
        # 実行権限を確認
        print(f"実行権限の確認: {os.access(executable_path, os.X_OK)}")
        
        # ファイルの詳細情報を表示
        os.system(f'ls -la {executable_path}')
        
        # 依存関係を確認
        os.system(f'otool -L {executable_path}')
        
        # 実行してエラーを確認
        print("\n実行テスト:")
        os.system(f'{executable_path}')
    else:
        print("ビルドされた実行ファイルが見つかりません。")

if __name__ == '__main__':
    build()
    
    # デバッグ情報を表示（必要に応じてコメントを解除）
    # debug_build()

    # アプリケーションを直接実行してテスト（必要に応じてコメントを解除）
    # os.system('dist/2chスクレイパー/2chスクレイパー')