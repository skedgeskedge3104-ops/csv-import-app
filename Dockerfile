# 軽量で安定したPython公式イメージを使用 (データサイエンス系ライブラリには-slimが推奨)
FROM python:3.11-slim

# OSに必要なパッケージのアップデート
# RUN apt-get update && apt-get install -y \
#     # 依存パッケージが必要な場合に追加 \
#     # && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /app

# RUN mkdir -p config

# requirements.txt をコンテナにコピーし、ライブラリをインストール
# アプリケーションコードをコピーする前に依存関係をインストールすることで、
# コード変更時のビルド高速化 (Dockerキャッシュの活用) を図ります。
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードとデータをコンテナにコピー
# data/base_file_a.csv も含まれます
COPY . .

# Flaskアプリケーションがリッスンするポートを公開 (Docker内部のポート)
EXPOSE 5000

# コンテナ起動時にGunicornを使ってアプリケーションを実行
# Gunicornは本番環境で推奨されるWSGIサーバーです
# `app:app` は 'app.py' ファイル内の 'app' という名前のFlaskインスタンスを指します
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "csv_import_app:app"]