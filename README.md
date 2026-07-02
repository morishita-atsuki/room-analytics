# ROOM Analytics for Sakura Market Rakuten Store

この静的サイトは、楽天ROOMの分析ダッシュボードを「さくらマーケット楽天市場店」向けに差し替えたサンプルです。

## 使い方

1. このフォルダでローカルサーバーを起動します。
   - `python3 -m http.server 8000`
2. ブラウザで `http://localhost:8000` を開きます。

## API連携について

現在はサンプルデータを表示しています。実データに差し替える場合は、`script.js` 内の `shopData` を実APIから取得するように変更してください。

## ROOMデータ取得のための調査スクリプト

`room_scrape.py` を追加しました。本スクリプトはPlaywrightを使い、Rakuten ROOMの検索ページにアクセスして検索リクエストの挙動を調査します。

使用例:

```bash
python3 room_scrape.py --keyword "ハーバニエンス" --headful --screenshot room_search.png
```

出力には検索ページの最終URL、HTTPステータス、リダイレクト情報、検索リクエストの詳細が含まれます。

### 依存関係

`playwright` が必要です。

```bash
python3 -m pip install playwright
python3 -m playwright install
```
