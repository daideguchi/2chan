import os
import sys
import shutil
from pathlib import Path

def create_mac_app():
    # 現在のディレクトリのパスを取得
    current_dir = Path.cwd()
    src_dir = current_dir / 'src'
    config_dir = src_dir / 'config'
    
    # configディレクトリの存在確認
    if not config_dir.exists():
        print(f"Error: 設定ディレクトリが見つかりません: {config_dir}")
        return
    
    # ビルドディレクトリをクリーン
    os.system('rm -rf build dist')
    
    # 基本的なスクリプト名と出力ディレクトリを設定
    script_path = str(src_dir / 'main.py')
    output_name = '2chスクレイパー'
    
    # .specファイルを作成
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{script_path}'],
    pathex=['{str(src_dir)}'],
    binaries=[],
    datas=[
        ('{str(config_dir)}', 'config'),
        ('/opt/homebrew/opt/python@3.9/Frameworks/Python.framework/Versions/3.9/Python', 'Python'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        '_tkinter',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{output_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{output_name}'
)
'''
    
    # .specファイルを書き出し
    with open('build.spec', 'w') as f:
        f.write(spec_content)
    
    print("ビルドを開始します...")
    print(f"スクリプトパス: {script_path}")
    print(f"設定ファイルパス: {config_dir}")
    
    # PyInstallerを実行
    os.system('pyinstaller --clean --noconfirm build.spec')
    
    # ビルド結果の確認
    dist_dir = Path('dist')
    source_dir = dist_dir / output_name
    target_dir = dist_dir / f"{output_name}.app"
    
    if not source_dir.exists():
        print(f"Error: ビルドされたディレクトリが見つかりません: {source_dir}")
        return
    
    print("アプリケーションバンドルを作成中...")
    
    # .app構造を作成
    macos_dir = target_dir / 'Contents' / 'MacOS'
    frameworks_dir = target_dir / 'Contents' / 'Frameworks'
    resources_dir = target_dir / 'Contents' / 'Resources'
    
    # 既存のディレクトリを削除
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    # ディレクトリ構造を作成
    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(frameworks_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)
    
    # Info.plistを作成
    info_plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>2chスクレイパー</string>
    <key>CFBundleExecutable</key>
    <string>2chスクレイパー</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.2chscraper</string>
    <key>CFBundleName</key>
    <string>2chスクレイパー</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>'''
    
    with open(target_dir / 'Contents' / 'Info.plist', 'w', encoding='utf-8') as f:
        f.write(info_plist)
    
    print("ファイルをコピー中...")
    try:
        # 実行ファイルとその他のファイルをコピー
        for item in source_dir.iterdir():
            dst = macos_dir / item.name
            try:
                if item.is_dir():
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)
                print(f"コピー完了: {item} -> {dst}")
            except Exception as e:
                print(f"Warning: {item}のコピー中にエラー: {e}")
        
        # Python Frameworkをコピー
        python_framework = '/opt/homebrew/opt/python@3.9/Frameworks/Python.framework/Versions/3.9/Python'
        if os.path.exists(python_framework):
            shutil.copy2(python_framework, frameworks_dir / 'Python')
            print(f"Pythonフレームワークをコピーしました: {python_framework} -> {frameworks_dir / 'Python'}")
        
        # 実行権限を設定
        os.chmod(macos_dir / output_name, 0o755)
        
        print("\nビルドが完了しました！")
        print(f"アプリケーションは '{target_dir}' にあります。")
        print("\nデバッグ情報:")
        print(f"- 実行ファイル: {macos_dir / output_name}")
        print(f"- Info.plist: {target_dir / 'Contents' / 'Info.plist'}")
        print(f"- Python Framework: {frameworks_dir / 'Python'}")
        
        print("\nアプリケーションをテストするには:")
        print(f"open '{target_dir}'")
        print("または")
        print(f"'{macos_dir / output_name}'")
        
    except Exception as e:
        print(f"Error: ファイルのコピー中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if sys.platform != 'darwin':
        print("このスクリプトはmacOS専用です。")
        sys.exit(1)
    
    create_mac_app()