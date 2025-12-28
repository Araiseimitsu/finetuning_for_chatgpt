"""
新井精密アシスタント - 対話型チャットボット

ファインチューニング済みモデルを使用して、
新井精密に関する質問に回答します。
"""

import os
from openai import OpenAI


# ファインチューニング済みモデルID
MODEL_ID = "ft:gpt-4o-mini-2024-07-18:araiseimitsu:araiseimitsu:CrPCK1Rg"


def chat():
    """対話型チャット"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません")
        return

    client = OpenAI(api_key=api_key)

    print("=" * 60)
    print("新井精密アシスタント")
    print("=" * 60)
    print("新井精密について質問してください。(終了: quit または exit)")
    print()

    while True:
        try:
            user_input = input("あなた: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "終了"]:
                print("終了します。")
                break

            print()

            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは埼玉県秩父市にある株式会社新井精密についての情報を提供するアシスタントです。"
                    },
                    {"role": "user", "content": user_input}
                ],
                max_tokens=500
            )

            answer = response.choices[0].message.content
            print(f"アシスタント: {answer}")
            print()

        except KeyboardInterrupt:
            print("\n終了します。")
            break
        except Exception as e:
            print(f"エラー: {e}")
            print()


if __name__ == "__main__":
    chat()
