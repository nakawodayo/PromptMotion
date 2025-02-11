import openai
import subprocess
import os
import random
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# OpenAI APIキーを取得
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("環境変数 'OPENAI_API_KEY' が設定されていません。")

# OpenAIクライアントを初期化
client = openai.OpenAI(api_key=api_key)

# 音声ファイルの出力先
output_file = "C:\\Users\\koshi\\Work\\PromptMotion\\output.mp3"
temp_dir = "C:\\Users\\koshi\\Work\\PromptMotion\\temp"

# 一時ファイル保存ディレクトリの作成
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

def generate_instructions():
    """ 1回のAPIリクエストで10個のダンスの指示を生成 """
    prompt = """
    あなたはダンスの指導者です。
    以下の条件に従い、10個の異なるダンス動作を生成してください。

    条件:
    - 各動作は短く、簡潔に
    - 具体的で明確なアクション
    - 例: 「右手を上げる」「左足を一歩前に出す」

    10個の動作を改行で区切って出力してください。
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    # 改行で分割してリスト化
    instructions = response.choices[0].message.content.strip().split("\n")
    
    # 指示が10個未満の場合の補正
    if len(instructions) < 10:
        raise ValueError("OpenAI APIのレスポンスが不完全です。")

    print("生成されたダンスの指示:")
    for i, instruction in enumerate(instructions, start=1):
        print(f"{i}. {instruction}")

    return instructions

def create_silent_audio(duration, output_file):
    """ 指定した秒数の無音mp3を作成 """
    command = f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t {duration} -q:a 9 -acodec libmp3lame "{output_file}"'
    subprocess.run(command, shell=True)

def speak_text_with_silence(texts):
    """ 指示ごとに無音を挿入しながら mp3 を作成 """
    temp_files = []
    
    for i, text in enumerate(texts):
        temp_text_file = f"{temp_dir}\\temp_{i}.mp3"
        temp_silence_file = f"{temp_dir}\\silence_{i}.mp3"
        temp_files.append(temp_text_file)
        temp_files.append(temp_silence_file)

        # Edge TTS で音声合成
        command = f'edge-tts --text "{text}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_text_file}"'
        subprocess.run(command, shell=True)

        # 2秒~10秒の無音を生成
        silence_duration = random.randint(2, 10)
        create_silent_audio(silence_duration, temp_silence_file)
    
    # すべての音声ファイルを結合
    concat_list = "|".join(temp_files)
    merge_command = f'ffmpeg -y -i "concat:{concat_list}" -acodec copy "{output_file}"'
    subprocess.run(merge_command, shell=True)

    # 一時ファイル削除
    for file in temp_files:
        os.remove(file)

    # Windowsのメディアプレイヤーで再生
    subprocess.Popen(["start", "", output_file], shell=True)

if __name__ == "__main__":
    instructions = generate_instructions()
    print("スピーカーで指示を読み上げます...")
    speak_text_with_silence(instructions)
