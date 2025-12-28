"""
OpenAI アップロード済みファイル確認スクリプト

ファインチューニング用にアップロードされたファイルの一覧を表示します。
"""

import os
from datetime import datetime
from openai import OpenAI


def format_bytes(size_bytes: int) -> str:
    """バイト単位を人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_timestamp(timestamp: int) -> str:
    """Unixタイムスタンプを読みやすい日時形式に変換"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def list_uploaded_files(purpose: str = None):
    """
    アップロード済みファイルの一覧を表示

    Args:
        purpose: フィルタする目的 (例: 'fine-tune', 'assistants')
    """
    # APIキーの設定
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        print("実行前に以下のように設定してください:")
        print("  set OPENAI_API_KEY=your_api_key_here")
        return

    client = OpenAI(api_key=api_key)

    print("=" * 80)
    print("OpenAI アップロード済みファイル一覧")
    print("=" * 80)

    try:
        # ファイル一覧を取得
        files = client.files.list()

        # 目的でフィルタ（指定されている場合）
        if purpose:
            files.data = [f for f in files.data if f.purpose == purpose]
            print(f"目的: {purpose}")
        print()

        if not files.data:
            print("アップロード済みファイルはありません")
            return

        # ファイル情報を表示
        for i, file in enumerate(files.data, 1):
            print(f"[{i}] ファイルID: {file.id}")
            print(f"    ファイル名: {file.filename}")
            print(f"    目的: {file.purpose}")
            print(f"    サイズ: {format_bytes(file.bytes)}")
            print(f"    作成日時: {format_timestamp(file.created_at)}")
            print(f"    ステータス: {file.status}")
            if hasattr(file, 'status_details') and file.status_details:
                print(f"    詳細: {file.status_details}")
            print()

        print(f"合計: {len(files.data)} 件")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


def delete_file(file_id: str):
    """
    指定したファイルを削除

    Args:
        file_id: 削除するファイルのID
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return

    client = OpenAI(api_key=api_key)

    try:
        # ファイル情報を取得して確認
        file = client.files.retrieve(file_id)
        print(f"削除対象ファイル: {file.filename} ({file.id})")

        # 確認なしで削除する場合は注意
        confirm = input("このファイルを削除しますか？ (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            client.files.delete(file_id)
            print("ファイルを削除しました")
        else:
            print("キャンセルしました")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OpenAI アップロード済みファイル管理")
    parser.add_argument("--purpose", "-p", default="fine-tune",
                        help="フィルタする目的 (デフォルト: fine-tune)")
    parser.add_argument("--delete", "-d", help="削除するファイルID")
    parser.add_argument("--all", "-a", action="store_true",
                        help="全ての目的のファイルを表示")

    args = parser.parse_args()

    if args.delete:
        delete_file(args.delete)
    else:
        if args.all:
            list_uploaded_files(purpose=None)
        else:
            list_uploaded_files(purpose=args.purpose)
