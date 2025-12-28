"""
OpenAI ファインチューニング用ファイルアップロードスクリプト

JSONL形式の学習データをOpenAIにアップロードします。
"""

import os
import json
from openai import OpenAI


def validate_jsonl(file_path: str) -> tuple[bool, str]:
    """
    JSONLファイルのバリデーション

    OpenAIファインチューニング対応フォーマット:
    - 古い形式: { "prompt": "...", "completion": "..." }
    - 新しい形式（チャット）: { "messages": [ {"role": "...", "content": "..."} ] }

    Args:
        file_path: JSONLファイルのパス

    Returns:
        (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"ファイルが存在しません: {file_path}"

    try:
        line_count = 0
        format_type = None

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                line_count += 1
                try:
                    data = json.loads(line)

                    # フォーマット形式の自動判定（最初の行で決定）
                    if format_type is None:
                        if 'messages' in data:
                            format_type = 'chat'
                        elif 'prompt' in data and 'completion' in data:
                            format_type = 'legacy'

                    # チャット形式のバリデーション
                    if format_type == 'chat':
                        if 'messages' not in data:
                            return False, f"行{line_num}: 'messages'キーがありません"
                        messages = data['messages']
                        if not isinstance(messages, list):
                            return False, f"行{line_num}: 'messages'は配列である必要があります"
                        if len(messages) == 0:
                            return False, f"行{line_num}: 'messages'が空です"
                        for msg in messages:
                            if 'role' not in msg or 'content' not in msg:
                                return False, f"行{line_num}: メッセージに'role'または'content'がありません"

                    # 古い形式のバリデーション
                    elif format_type == 'legacy':
                        if 'prompt' not in data or 'completion' not in data:
                            return False, f"行{line_num}: 'prompt'または'completion'キーがありません"

                except json.JSONDecodeError as e:
                    return False, f"行{line_num}: JSON形式が正しくありません - {e}"

        format_label = "チャット形式" if format_type == 'chat' else "古い形式"
        return True, f"バリデーション成功 ({format_label}): {line_count}行"

    except Exception as e:
        return False, f"バリデーションエラー: {e}"


def upload_file(file_path: str, purpose: str = 'fine-tune'):
    """
    ファイルをOpenAIにアップロード

    Args:
        file_path: アップロードするファイルのパス
        purpose: アップロード目的 (デフォルト: fine-tune)
    """
    # APIキーの確認
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        print("実行前に以下のように設定してください:")
        print("  set OPENAI_API_KEY=your_api_key_here")
        return None

    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが存在しません: {file_path}")
        return None

    print("=" * 80)
    print("OpenAI ファイルアップロード")
    print("=" * 80)
    print(f"ファイル: {file_path}")
    print(f"目的: {purpose}")
    print()

    # バリデーション実行
    print("バリデーション中...")
    is_valid, message = validate_jsonl(file_path)
    if not is_valid:
        print(f"✗ {message}")
        return None
    print(f"○ {message}")
    print()

    # ファイルサイズ表示
    file_size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB']:
        if file_size < 1024.0:
            size_str = f"{file_size:.2f} {unit}"
            break
        file_size /= 1024.0
    else:
        size_str = f"{file_size:.2f} GB"
    print(f"ファイルサイズ: {size_str}")
    print()

    # アップロード実行
    print("アップロード中...")
    try:
        client = OpenAI(api_key=api_key)

        with open(file_path, 'rb') as f:
            uploaded_file = client.files.create(
                file=f,
                purpose=purpose
            )

        print("○ アップロード成功!")
        print()
        print("アップロードファイル情報:")
        print(f"  ファイルID: {uploaded_file.id}")
        print(f"  ファイル名: {uploaded_file.filename}")
        print(f"  目的: {uploaded_file.purpose}")
        print(f"  サイズ: {uploaded_file.bytes} bytes")
        print(f"  ステータス: {uploaded_file.status}")
        print()
        print("このファイルIDをファインチューニング時に使用します:")
        print(f"  {uploaded_file.id}")

        return uploaded_file

    except Exception as e:
        print(f"✗ アップロードエラー: {e}")
        return None


def list_uploaded_files(purpose: str = 'fine-tune'):
    """アップロード済みファイルの一覧を表示"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return

    client = OpenAI(api_key=api_key)
    files = client.files.list()

    if purpose:
        files.data = [f for f in files.data if f.purpose == purpose]

    print()
    print("=" * 80)
    print("アップロード済みファイル一覧")
    print("=" * 80)

    if not files.data:
        print("ファイルはありません")
        return

    for i, file in enumerate(files.data, 1):
        print(f"[{i}] {file.filename}")
        print(f"    ID: {file.id}")
        print(f"    ステータス: {file.status}")
        print(f"    作成日時: {file.created_at}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OpenAI ファインチューニング用ファイルアップロード")
    parser.add_argument("file", nargs="?", help="アップロードするJSONLファイルのパス")
    parser.add_argument("--list", "-l", action="store_true", help="アップロード済みファイル一覧表示")

    args = parser.parse_args()

    if args.list:
        list_uploaded_files()
    elif args.file:
        upload_file(args.file)
    else:
        # デフォルトファイルを指定
        default_file = "src/araiseimitsu_data.jsonl"
        if os.path.exists(default_file):
            upload_file(default_file)
        else:
            print("使用方法:")
            print(f"  py -3.xx src/openai_upload_file.py <ファイルパス>")
            print(f"  py -3.xx src/openai_upload_file.py --list")
            print()
            print(f"例:")
            print(f"  py -3.xx src/openai_upload_file.py src/araiseimitsu_data.jsonl")
