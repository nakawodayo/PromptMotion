import openai
import subprocess
import os
import random
import time
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
temp_dir = "C:\\Users\\koshi\\Work\\PromptMotion\\temp"
instructions_file = "C:\\Users\\koshi\\Work\\PromptMotion\\instructions.txt"
dancers_file = "C:\\Users\\koshi\\Work\\PromptMotion\\dancers.txt"

# 一時ファイル保存ディレクトリの作成
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

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
    """ 指示の間隔を指定された秒数で調整し、指定がない場合はランダムに設定 """
    processed_instructions = []
    silence_durations = []

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
            processed_instructions.append(f"{dancer} {random_instruction}")
        else:
            processed_instructions.append(action_part)

        # 指定された秒数の無音 or ランダム
        silence_durations.append(int(time_part[:-1]) if time_part and time_part.endswith("s") and time_part[:-1].isdigit() else random.randint(2, 10))

    return processed_instructions, silence_durations

def create_silent_audio(duration):
    """ 指定した秒数の無音mp3を作成（既存の無音ファイルを再利用） """
    silence_file = f"{temp_dir}\\silence_{duration}.mp3"

    # 既にファイルが存在する場合は再作成しない
    if os.path.exists(silence_file):
        print(f"[INFO] 既存の無音ファイルを再利用: {silence_file}")
        return silence_file

    print(f"[INFO] 無音ファイルを作成中: {silence_file} ({duration}s)")
    command = f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t {duration} -q:a 9 -acodec libmp3lame "{silence_file}"'
    subprocess.run(command, shell=True)

    return silence_file

def run_command_with_retry(command, max_retries=3, delay=5):
    """ コマンドを最大 max_retries 回リトライする """
    for attempt in range(max_retries):
        try:
            subprocess.run(command, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] コマンド失敗 ({attempt+1}/{max_retries}): {e}")
            time.sleep(delay)
    return False

def speak_text_with_custom_silence(texts, silence_durations):
    """ 指示ごとに指定された秒数またはランダムな無音を挿入しながら mp3 を作成（進捗表示あり） """
    temp_files = []
    total_steps = len(texts)

    for i, (text, silence_duration) in enumerate(zip(texts, silence_durations)):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            continue

        dancer_name = parts[0]
        instruction = parts[1]

        temp_dancer_file = f"{temp_dir}\\dancer_{i}.mp3"
        temp_instruction_file = f"{temp_dir}\\instruction_{i}.mp3"

        temp_files.append(temp_dancer_file)
        temp_files.append(temp_instruction_file)

        # 進捗表示
        print(f"[INFO] ({i+1}/{total_steps}) {dancer_name}: {instruction}")

        # ダンサー名の音声生成
        command_dancer = f'edge-tts --text "{dancer_name}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_dancer_file}"'
        if not run_command_with_retry(command_dancer):
            print(f"[ERROR] {dancer_name} の音声生成に失敗しました")
            continue  

        # 指示文の音声生成
        command_instruction = f'edge-tts --text "{instruction}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_instruction_file}"'
        if not run_command_with_retry(command_instruction):
            print(f"[ERROR] {instruction} の音声生成に失敗しました")
            continue  

        # 無音ファイルの取得（既存のものがあれば再利用）
        silence_file = create_silent_audio(silence_duration)
        temp_files.append(silence_file)

    # すべての音声ファイルを結合
    concat_list = "|".join(temp_files)
    merge_command = f'ffmpeg -y -i "concat:{concat_list}" -acodec copy "{output_file}"'
    subprocess.run(merge_command, shell=True)

    # Windowsのメディアプレイヤーで再生
    subprocess.Popen(["start", "", output_file], shell=True)

    print("[INFO] すべての音声ファイルを処理完了しました！")

    """ 指示ごとに指定された秒数またはランダムな無音を挿入しながら mp3 を作成 """
    temp_files = []

    for i, (text, silence_duration) in enumerate(zip(texts, silence_durations)):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            continue

        dancer_name = parts[0]
        instruction = parts[1]

        temp_dancer_file = f"{temp_dir}\\dancer_{i}.mp3"
        temp_instruction_file = f"{temp_dir}\\instruction_{i}.mp3"

        temp_files.append(temp_dancer_file)
        temp_files.append(temp_instruction_file)

        # ダンサー名の音声生成
        command_dancer = f'edge-tts --text "{dancer_name}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_dancer_file}"'
        if not run_command_with_retry(command_dancer):
            print(f"[ERROR] {dancer_name} の音声生成に失敗しました")
            continue  

        # 指示文の音声生成
        command_instruction = f'edge-tts --text "{instruction}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_instruction_file}"'
        if not run_command_with_retry(command_instruction):
            print(f"[ERROR] {instruction} の音声生成に失敗しました")
            continue  

        # 無音ファイルの取得（既存のものがあれば再利用）
        silence_file = create_silent_audio(silence_duration)
        temp_files.append(silence_file)

    # すべての音声ファイルを結合
    concat_list = "|".join(temp_files)
    merge_command = f'ffmpeg -y -i "concat:{concat_list}" -acodec copy "{output_file}"'
    subprocess.run(merge_command, shell=True)

    # Windowsのメディアプレイヤーで再生
    subprocess.Popen(["start", "", output_file], shell=True)

if __name__ == "__main__":
    raw_instructions = load_instructions(instructions_file)
    dancers = load_dancers(dancers_file)
    final_instructions, silence_durations = process_instructions_with_timing(raw_instructions, dancers)
    print("\n🎤 スピーカーで指示を読み上げます...")
    speak_text_with_custom_silence(final_instructions, silence_durations)
