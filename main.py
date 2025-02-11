import openai
import subprocess
import os
import random
import re
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# OpenAI APIキーを取得
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("環境変数 'OPENAI_API_KEY' が設定されていません。")

# OpenAIクライアントを初期化
client = openai.OpenAI(api_key=api_key)

# ファイルパス設定
output_file = "C:\\Users\\koshi\\Work\\PromptMotion\\output.mp3"
instructions_file = "C:\\Users\\koshi\\Work\\PromptMotion\\instructions.txt"
dancers_file = "C:\\Users\\koshi\\Work\\PromptMotion\\dancers.txt"

# 無音を表現するタグ（`edge-tts` ではサポートされないので、後で `ffmpeg` で追加）
PAUSE_TAG = "[PAUSE]"

def load_instructions(file_path):
    """ 指示リストをファイルから読み込む """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"指示の設定ファイルが見つかりません: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        instructions = [line.strip() for line in file.readlines() if line.strip()]

    return instructions

def load_dancers(file_path):
    """ ダンサー一覧を読み込む """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ダンサーの設定ファイルが見つかりません: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        dancers = [line.strip() for line in file.readlines() if line.strip()]

    if not dancers:
        raise ValueError("ダンサーのリストが空です。")

    return dancers

def generate_random_instruction():
    """ AIにランダムなダンスの指示を生成させる """
    prompt = """あなたはダンスの指導者です。
    1つのランダムなダンスの指示を生成してください。
    - 具体的で明確なアクション
    - 例: 「右手を上げる」「左足を一歩前に出す」
    1つだけ出力してください。
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    return response.choices[0].message.content.strip()

def process_instructions_with_timing(instructions, dancers):
    """ 指示の間隔を処理し、全体のTTS用テキストを作成 """
    processed_text = []
    pause_durations = []  # 各[PAUSE]の長さを保存

    for instruction in instructions:
        parts = instruction.split(",")  # カンマで分割
        action_part = parts[0].strip()  # 指示部分
        time_part = parts[1].strip() if len(parts) > 1 else None  # 秒数部分

        # **Anyone** をランダムなダンサーに置き換える
        if "**Anyone**" in action_part:
            dancer = random.choice(dancers)
            action_part = action_part.replace("**Anyone**", dancer)

        # **randomize** をAI生成に変更
        if "**randomize**" in action_part:
            dancer = action_part.split(" ")[0]  # ダンサー名を取得
            random_instruction = generate_random_instruction()
            processed_text.append(f"{dancer} {random_instruction}")
        else:
            processed_text.append(action_part)

        # 無音の挿入
        pause_time = int(time_part[:-1]) if time_part and time_part.endswith("s") and time_part[:-1].isdigit() else random.randint(2, 10)
        processed_text.append(PAUSE_TAG)
        pause_durations.append(pause_time)

    return processed_text, pause_durations

def generate_tts_audio(texts):
    """ 全体のTTS音声を一発で生成 """
    combined_text = " ".join(texts).replace(PAUSE_TAG, "")
    temp_audio = "C:\\Users\\koshi\\Work\\PromptMotion\\temp_audio.mp3"
    
    command_tts = f'edge-tts --text "{combined_text}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_audio}"'
    subprocess.run(command_tts, shell=True)

    return temp_audio

def insert_silence(input_audio, pause_durations):
    """ TTS音声に無音を挿入 """
    temp_silence = "C:\\Users\\koshi\\Work\\PromptMotion\\temp_silence.mp3"
    output_audio = "C:\\Users\\koshi\\Work\\PromptMotion\\output.mp3"

    # 無音ファイル作成
    silence_clips = []
    for i, duration in enumerate(pause_durations):
        silence_file = f"C:\\Users\\koshi\\Work\\PromptMotion\\silence_{i}.mp3"
        command_silence = f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t {duration} -q:a 9 -acodec libmp3lame "{silence_file}"'
        subprocess.run(command_silence, shell=True)
        silence_clips.append(silence_file)

    # すべての無音ファイルを連結
    concat_list = "|".join(silence_clips)
    command_concat = f'ffmpeg -y -i "concat:{concat_list}" -acodec copy "{temp_silence}"'
    subprocess.run(command_concat, shell=True)

    # TTS音声と無音を合成
    command_merge = f'ffmpeg -y -i "{input_audio}" -i "{temp_silence}" -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1[out]" -map "[out]" "{output_audio}"'
    subprocess.run(command_merge, shell=True)

    return output_audio

if __name__ == "__main__":
    # 1. 指示リストとダンサーリストを読み込む
    raw_instructions = load_instructions(instructions_file)
    dancers = load_dancers(dancers_file)

    # 2. `randomize` と `Anyone` を処理
    final_text, pause_durations = process_instructions_with_timing(raw_instructions, dancers)

    # 3. TTS音声を一発で生成
    tts_audio = generate_tts_audio(final_text)

    # 4. 無音を適切に挿入
    output_audio = insert_silence(tts_audio, pause_durations)

    # 5. 再生
    subprocess.Popen(["start", "", output_audio], shell=True)
