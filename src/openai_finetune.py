"""
OpenAI ファインチューニング実行スクリプト

アップロードした学習データを使用してモデルをファインチューニングします。
"""

import os
import time
from datetime import datetime
from openai import OpenAI


def create_finetuning_job(
    training_file_id: str,
    model: str = "gpt-4o-mini-2024-07-18",
    suffix: str = None,
    epochs: int = 3
):
    """
    ファインチューニングジョブを作成

    Args:
        training_file_id: 学習データのファイルID
        model: ベースモデル (gpt-4o-mini, gpt-3.5-turbo など)
        suffix: モデル名のサフィックス（英数字とハイフンのみ）
        epochs: 学習エポック数
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return None

    client = OpenAI(api_key=api_key)

    print("=" * 80)
    print("ファインチューニングジョブ作成")
    print("=" * 80)
    print(f"学習ファイルID: {training_file_id}")
    print(f"ベースモデル: {model}")
    print(f"エポック数: {epochs}")
    if suffix:
        print(f"モデル名サフィックス: {suffix}")
    print()

    try:
        # ファインチューニングジョブ作成
        response = client.fine_tuning.jobs.create(
            training_file=training_file_id,
            model=model,
            hyperparameters={
                "n_epochs": epochs
            },
            suffix=suffix
        )

        print("○ ファインチューニングジョブを作成しました!")
        print()
        print("ジョブ情報:")
        print(f"  ジョブID: {response.id}")
        print(f"  ステータス: {response.status}")
        print(f"  モデル: {response.model}")
        print(f"  作成日時: {datetime.fromtimestamp(response.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("完了まで数分〜数十分かかる場合があります。")
        print(f"ジョブID: {response.id}")
        print()

        return response.id

    except Exception as e:
        print(f"✗ エラー: {e}")
        return None


def list_finetuning_jobs(limit: int = 10):
    """ファインチューニングジョブの一覧を表示"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return

    client = OpenAI(api_key=api_key)

    print("=" * 80)
    print("ファインチューニングジョブ一覧")
    print("=" * 80)

    try:
        jobs = client.fine_tuning.jobs.list(limit=limit)

        if not jobs.data:
            print("ジョブはありません")
            return

        for i, job in enumerate(jobs.data, 1):
            print(f"[{i}] ジョブID: {job.id}")
            print(f"    モデル: {job.model}")
            print(f"    ファインチューンモデル: {job.fine_tuned_model}")
            print(f"    ステータス: {job.status}")
            print(f"    作成日時: {datetime.fromtimestamp(job.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
            if job.finished_at:
                print(f"    完了日時: {datetime.fromtimestamp(job.finished_at).strftime('%Y-%m-%d %H:%M:%S')}")
            print()

    except Exception as e:
        print(f"エラー: {e}")


def check_job_status(job_id: str):
    """ジョブのステータスを確認"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return

    client = OpenAI(api_key=api_key)

    try:
        job = client.fine_tuning.jobs.retrieve(job_id)

        print("=" * 80)
        print(f"ジョブステータス: {job.id}")
        print("=" * 80)
        print(f"ステータス: {job.status}")
        print(f"ベースモデル: {job.model}")
        print(f"ファインチューンモデル: {job.fine_tuned_model}")
        print(f"作成日時: {datetime.fromtimestamp(job.created_at).strftime('%Y-%m-%d %H:%M:%S')}")

        if job.finished_at:
            print(f"完了日時: {datetime.fromtimestamp(job.finished_at).strftime('%Y-%m-%d %H:%M:%S')}")

        # 結果ファイルがあれば表示
        if hasattr(job, 'result_files') and job.result_files:
            print(f"結果ファイル: {job.result_files}")

        # エラーがあれば表示
        if hasattr(job, 'error') and job.error:
            print(f"エラー: {job.error}")

        # イベントを取得
        events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=5)
        if events.data:
            print()
            print("最近のイベント:")
            for event in reversed(events.data):
                timestamp = datetime.fromtimestamp(event.created_at).strftime('%H:%M:%S')
                print(f"  [{timestamp}] {event.message}")

        return job

    except Exception as e:
        print(f"エラー: {e}")
        return None


def wait_for_completion(job_id: str, check_interval: int = 30):
    """ジョブが完了するまで待機"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return

    client = OpenAI(api_key=api_key)

    print("=" * 80)
    print("ファインチューニング完了待機中...")
    print("=" * 80)

    while True:
        try:
            job = client.fine_tuning.jobs.retrieve(job_id)
            status = job.status

            if status == "succeeded":
                print()
                print("○ ファインチューニング完了!")
                print(f"ファインチューンモデル: {job.fine_tuned_model}")
                break
            elif status == "failed":
                print()
                print(f"✗ ファインチューニング失敗")
                if hasattr(job, 'error') and job.error:
                    print(f"エラー: {job.error}")
                break
            elif status == "cancelled":
                print()
                print("キャンセルされました")
                break
            else:
                now = datetime.now().strftime('%H:%M:%S')
                print(f"[{now}] ステータス: {status}... 待機中")

            time.sleep(check_interval)

        except Exception as e:
            print(f"エラー: {e}")
            break


def test_model(model_id: str, prompt: str):
    """ファインチューニング後のモデルをテスト"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return

    client = OpenAI(api_key=api_key)

    print("=" * 80)
    print("モデルテスト")
    print("=" * 80)
    print(f"モデル: {model_id}")
    print(f"プロンプト: {prompt}")
    print()

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        answer = response.choices[0].message.content
        print("回答:")
        print(answer)

        return answer

    except Exception as e:
        print(f"エラー: {e}")
        return None


def delete_model(model_id: str):
    """ファインチューニングモデルを削除"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return False

    client = OpenAI(api_key=api_key)

    print("=" * 80)
    print("モデル削除")
    print("=" * 80)
    print(f"削除対象: {model_id}")
    print()
    print("⚠️  このモデルを削除しますか?")
    print("この操作は取り消せません。")
    print()
    confirmation = input("続行しますか? (yes/no): ").strip().lower()
    if confirmation not in ["yes", "y"]:
        print("キャンセルしました")
        return False

    try:
        client.models.delete(model_id)
        print()
        print("○ モデルを削除しました")
        print(f"削除済みモデル: {model_id}")
        return True

    except Exception as e:
        print(f"✗ エラー: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OpenAI ファインチューニング管理")
    parser.add_argument("--create", "-c", help="学習ファイルIDを指定してジョブ作成")
    parser.add_argument("--model", "-m", default="gpt-4o-mini-2024-07-18",
                        help="ベースモデル (デフォルト: gpt-4o-mini-2024-07-18)")
    parser.add_argument("--suffix", "-s", help="モデル名のサフィックス")
    parser.add_argument("--epochs", "-e", type=int, default=3,
                        help="エポック数 (デフォルト: 3)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="ジョブ一覧表示")
    parser.add_argument("--status", help="ジョブIDを指定してステータス確認")
    parser.add_argument("--wait", "-w", help="ジョブIDを指定して完了まで待機")
    parser.add_argument("--test", "-t", nargs=2, metavar=("MODEL", "PROMPT"),
                        help="モデルをテスト: --test model_id 'prompt'")
    parser.add_argument("--delete", "-d", help="削除するモデルID")

    args = parser.parse_args()

    if args.list:
        list_finetuning_jobs()
    elif args.status:
        check_job_status(args.status)
    elif args.wait:
        wait_for_completion(args.wait)
    elif args.test:
        test_model(args.test[0], args.test[1])
    elif args.delete:
        delete_model(args.delete)
    elif args.create:
        create_finetuning_job(
            training_file_id=args.create,
            model=args.model,
            suffix=args.suffix,
            epochs=args.epochs
        )
    else:
        print("使用方法:")
        print("  ジョブ作成:")
        print("    py -3.xx src/openai_finetune.py --create <file_id> [--model gpt-4o-mini] [--suffix xxx] [--epochs 3]")
        print()
        print("  ジョブ一覧:")
        print("    py -3.xx src/openai_finetune.py --list")
        print()
        print("  ステータス確認:")
        print("    py -3.xx src/openai_finetune.py --status <job_id>")
        print()
        print("  完了まで待機:")
        print("    py -3.xx src/openai_finetune.py --wait <job_id>")
        print()
        print("  モデルテスト:")
        print('    py -3.xx src/openai_finetune.py --test <model_id> "プロンプト"')
        print()
        print("  モデル削除:")
        print('    py -3.xx src/openai_finetune.py --delete <model_id>')
