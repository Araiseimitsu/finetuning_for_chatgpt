# 新井精密アシスタント - 管理システム

OpenAI ファインチューニング管理のための統合Webアプリケーションです。
FastAPI, HTMX, Jinja2, TailwindCSS を使用して構築されています。

## 機能概要

このアプリケーションは、以下の機能を一つのインターフェースで提供します：

* **ダッシュボード**: ファインチューニング用ファイル、ジョブ、モデルの統計情報を一目で確認できます。
* **ファイル管理**: JSONL形式のトレーニングデータのアップロード、一覧表示、削除、内容のバリデーションが可能です。
* **ジョブ管理**: ファインチューニングジョブの作成（モデル選択、エポック数設定）、ステータス確認、キャンセルが可能です。
* **チャット**: 作成したファインチューニング済みモデルを選択し、チャット形式で対話テストを行うことができます。

## 技術スタック

* **Backend**: Python 3.x, FastAPI
* **Frontend**: HTML5, TailwindCSS (CDN), HTMX
* **Template Engine**: Jinja2
* **API**: OpenAI API

## セットアップ手順

1. **リポジトリのクローン**

    ```bash
    git clone <repository_url>
    cd finetuning_for_chatgpt
    ```

2. **仮想環境の作成と有効化**

    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3. **依存関係のインストール**

    ```bash
    pip install -r requirements.txt
    ```

4. **環境変数の設定**
    コマンドラインまたは `.env` ファイルなどで `OPENAI_API_KEY` を設定してください。

    ```powershell
    $env:OPENAI_API_KEY="sk-..."
    ```

## 起動方法

以下のコマンドでアプリケーションを起動します。

```bash
python src/app.py
```

または `uvicorn` を直接使用する場合:

```bash
uvicorn src.app:app --reload
```

ブラウザで `http://127.0.0.1:8000` にアクセスしてください。

## ディレクトリ構成

```
.
├── .docs/              # ドキュメント関連
├── src/
│   ├── static/         # 静的ファイル (CSS, JS)
│   ├── templates/      # Jinja2 テンプレート
│   ├── app.py          # アプリケーションエントリーポイント
│   └── ...
├── requirements.txt    # 依存パッケージ一覧
└── README.md           # 本ファイル
```
