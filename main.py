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
dancers_file = "C:\\Users\\koshi\\Work\\PromptMotion\\dancers.txt"

# 一時ファイル保存ディレクトリの作成
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

def load_dancers():
    """ 設定ファイルからダンサー一覧を読み込む """
    if not os.path.exists(dancers_file):
        raise FileNotFoundError(f"ダンサーの設定ファイルが見つかりません: {dancers_file}")

    with open(dancers_file, "r", encoding="utf-8") as file:
        dancers = [line.strip() for line in file.readlines() if line.strip()]
    
    if not dancers:
        raise ValueError("ダンサーのリストが空です。")

    return dancers

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
    
    if len(instructions) < 10:
        raise ValueError("OpenAI APIのレスポンスが不完全です。")

    return instructions

def assign_instructions_to_dancers(instructions, dancers):
    """ ダンサーごとにランダムな動作を割り当て、数字を削除する """
    assignments = []
    for instruction in instructions:
        dancer = random.choice(dancers)  # ランダムにダンサーを選ぶ
        # 先頭の数字（1. など）を削除
        cleaned_instruction = " ".join(instruction.split()[1:]) if instruction[0].isdigit() else instruction
        assignments.append(f"{dancer} {cleaned_instruction}")

    print("\n📢 **ダンサーごとの指示:**")
    for assignment in assignments:
        print(assignment)

    return assignments


def create_silent_audio(duration, output_file):
    """ 指定した秒数の無音mp3を作成 """
    command = f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t {duration} -q:a 9 -acodec libmp3lame "{output_file}"'
    subprocess.run(command, shell=True)

def speak_text_with_silence(texts):
    """ 指示ごとにダンサー名の後に1.5秒の無音を挿入し、指示間の無音を2〜10秒ランダムに挿入しながら mp3 を作成 """
    temp_files = []

    for i, text in enumerate(texts):
        parts = text.split(" ", 1)  # 最初のスペースで分割
        if len(parts) < 2:
            continue  # 念のため、指示が分割できない場合はスキップ

        dancer_name = parts[0]
        instruction = parts[1]

        temp_dancer_file = f"{temp_dir}\\dancer_{i}.mp3"
        temp_silence_file = f"{temp_dir}\\silence_{i}.mp3"
        temp_instruction_file = f"{temp_dir}\\instruction_{i}.mp3"
        temp_pause_file = f"{temp_dir}\\pause_{i}.mp3"  # 指示間のランダムな無音

        temp_files.append(temp_dancer_file)
        temp_files.append(temp_silence_file)
        temp_files.append(temp_instruction_file)
        temp_files.append(temp_pause_file)

        # ダンサー名の音声生成
        command_dancer = f'edge-tts --text "{dancer_name}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_dancer_file}"'
        subprocess.run(command_dancer, shell=True)

        # 1.5秒の無音を生成（ダンサー名と指示の間）
        create_silent_audio(1.5, temp_silence_file)

        # 指示文の音声生成
        command_instruction = f'edge-tts --text "{instruction}" --voice ja-JP-NanamiNeural --rate=+5% --volume=+0% --write-media "{temp_instruction_file}"'
        subprocess.run(command_instruction, shell=True)

        # 2〜10秒のランダムな無音を生成（指示と指示の間）
        silence_duration = random.randint(2, 10)
        create_silent_audio(silence_duration, temp_pause_file)

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
    # 1. ダンサー一覧を読み込む
    dancers = load_dancers()

    # 2. AIがダンスの指示を10個生成
    instructions = generate_instructions()

    # 3. ダンサーにランダムに割り当て
    assigned_instructions = assign_instructions_to_dancers(instructions, dancers)

    # 4. 音声を生成し、スピーカーで指示を読み上げる
    print("\n🎤 スピーカーで指示を読み上げます...")
    speak_text_with_silence(assigned_instructions)
