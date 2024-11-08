# 2chan

2ちゃんねるまとめサイトスクレイパー

## インストール方法

```bash
# 仮想環境のアクティベート
# Windows:
.\activate.bat

# Unix/Mac:
source ./activate.sh

# 依存関係のインストール
pip install -r requirements.txt

# 開発用依存関係のインストール（オプション）
pip install -e ".[dev]"
```

## 使用方法

```bash
python src/main.py
```

## 開発者向け

### テスト実行
```bash
pytest tests/
```

### コードフォーマット
```bash
black src/ tests/
```

### リンター実行
```bash
flake8 src/ tests/
```

### 実行
```bash
PYTHONPATH=$PWD python src/main.py
```