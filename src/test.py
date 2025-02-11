import openai
import subprocess
import os
from dotenv import load_dotenv  # .envファイルから環境変数を読み込む

# 環境変数をロード（.envファイルを使う場合）
load_dotenv()

# OpenAI APIキーの設定（環境変数を使用）
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("環境変数 'OPENAI_API_KEY' が設定されていません。")

# OpenAIクライアントを初期化
client = openai.OpenAI(api_key=api_key)

def generate_instruction():
    """ OpenAI APIを使ってダンスの指示を生成 """
    prompt = "ダンスの動作を1つ指示してください。例: 右手を上げる"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "あなたはダンスの指導者です。"},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def speak_text(text):
    """ Edge TTS を使って音声合成し、Windowsのメディアプレイヤーで再生 """
    output_file = "C:\\Users\\koshi\\Work\\PromptMotion\\output.mp3"  # Windowsパスに変更

    # Edge TTSで音声合成
    command = f'edge-tts --text "{text}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{output_file}"'
    subprocess.run(command, shell=True)

    # Windowsのメディアプレイヤーで音声を再生
    subprocess.Popen(["start", "", output_file], shell=True)

if __name__ == "__main__":
    print("AIにダンスの指示をリクエスト中...")
    instruction = generate_instruction()
    print("生成された指示:", instruction)

    print("スピーカーで指示を読み上げます...")
    speak_text(instruction)
