import openai
import subprocess
import os
import random
import time
import shutil
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv(dotenv_path='config/.env')

# OpenAI APIキーを取得
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("環境変数 'OPENAI_API_KEY' が設定されていません。")

# OpenAIクライアントを初期化
client = openai.OpenAI(api_key=api_key)

# ファイルパス設定
output_file = r"C:\Users\koshi\Work\PromptMotion\output.mp3"
temp_dir = r"C:\Users\koshi\Work\PromptMotion\temp"
instructions_file = r"C:\Users\koshi\Work\PromptMotion\docs\instructions.txt"
dancers_file = r"C:\Users\koshi\Work\PromptMotion\docs\dancers.txt"
title_file = r"C:\Users\koshi\Work\PromptMotion\docs\title.txt"  # ★ ここがタイトル用のファイルです

temp_output_file = os.path.join(temp_dir, "temp_output.mp3")

# 一時ファイル保存ディレクトリの作成
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)


def ensure_output_file_is_writable(file_path):
    """
    出力先のMP3を事前に削除して、PermissionErrorを防ぐ。
    他プロセスが握っている場合は削除に失敗するので警告を出す。
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] 既存の {file_path} を削除しました。")
        except PermissionError:
            print(f"[ERROR] {file_path} の削除に失敗しました。他のプロセスが使用中の可能性があります。")
            return False
    return True


def load_instructions(file_path):
    """ 指示リストをファイルから読み込む """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"指示の設定ファイルが見つかりません: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        instructions = [line.strip() for line in file if line.strip()]

    return instructions


def load_dancers(file_path):
    """ ダンサー一覧を読み込む """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ダンサーの設定ファイルが見つかりません: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        dancers = [line.strip() for line in file if line.strip()]

    if not dancers:
        raise ValueError("ダンサーのリストが空です。")

    return dancers


def load_title(file_path):
    """タイトル用のテキストファイルを読み込む"""
    if not os.path.exists(file_path):
        print(f"[WARNING] タイトルファイルが見つかりません: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        title_text = file.read().strip()
        return title_text if title_text else None


def generate_random_instruction():
    """
    AIにランダムなダンスの指示を生成させる
    """
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
    """
    指示の間隔を指定された秒数で調整し、指定がない場合はランダムに設定
    例:
        Billy,10s
        **Anyone**,5s
        Gan
    などの場合に対応
    """
    processed_instructions = []
    silence_durations = []

    for instruction in instructions:
        parts = instruction.split(",", maxsplit=1)
        action_part = parts[0].strip()  # 指示部分
        time_part = parts[1].strip() if len(parts) > 1 else None  # 秒数部分

        # **Anyone** をランダムなダンサーに置き換える
        if "**Anyone**" in action_part:
            dancer = random.choice(dancers)
            action_part = action_part.replace("**Anyone**", dancer)

        # **randomize** があれば、AI生成の指示文に置き換え
        if "**randomize**" in action_part:
            dancer = action_part.split(" ")[0]  # ダンサー名 (例: Billy)
            random_instruction = generate_random_instruction()
            processed_instructions.append(f"{dancer} {random_instruction}")
        else:
            processed_instructions.append(action_part)

        # 指定された秒数の無音 or ランダム秒数
        if time_part and time_part.endswith("s") and time_part[:-1].isdigit():
            silence_durations.append(int(time_part[:-1]))
        else:
            silence_durations.append(random.randint(2, 10))

    return processed_instructions, silence_durations


def create_silent_audio(duration):
    """
    指定秒数の無音MP3を作成、再利用できるようにキャッシュ
    """
    silence_file = os.path.join(temp_dir, f"silence_{duration}.mp3")
    if os.path.exists(silence_file):
        return silence_file  # すでに存在する場合は再利用

    print(f"[INFO] 無音ファイルを作成中: {silence_file} ({duration}s)")
    command = (
        f'ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono '
        f'-t {duration} -q:a 9 -acodec libmp3lame "{silence_file}"'
    )
    subprocess.run(command, shell=True)
    return silence_file


def run_command_with_retry(command, max_retries=3, delay=5):
    """
    コマンド失敗時にリトライする簡易関数
    """
    for attempt in range(max_retries):
        try:
            subprocess.run(command, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] コマンド失敗 ({attempt+1}/{max_retries}): {e}")
            time.sleep(delay)
    return False


def rename_output_file(temp_file, final_file):
    """
    ffmpeg 結合後の一時ファイルを output.mp3 にリネームする
    """
    try:
        if os.path.exists(final_file):
            os.remove(final_file)
        shutil.move(temp_file, final_file)
        print(f"[INFO] {temp_file} を {final_file} にリネームしました。")
    except PermissionError:
        print(f"[ERROR] {final_file} へのリネームに失敗しました。他のプロセスが使用中の可能性があります。")


def speak_text_with_custom_silence(title_text, texts, silence_durations):
    """
    1. タイトルを読み上げ
    2. 5秒の無音
    3. 指示ごとに音声ファイルを作り、指定秒数の無音を挟んで concat.txt で一気に結合する。
    最後に temp_output.mp3 を output.mp3 にリネームする。
    """
    temp_files = []
    concat_file_path = os.path.join(temp_dir, "concat.txt")

    # タイトル読み上げ
    if title_text:
        temp_title_file = os.path.join(temp_dir, "title.mp3")
        cmd_title = (
            f'edge-tts --text "{title_text}" '
            f'--voice ja-JP-NanamiNeural --write-media "{temp_title_file}"'
        )
        print(f"[INFO] タイトルを読み上げます: {title_text}")
        run_command_with_retry(cmd_title)
        temp_files.append(temp_title_file)

        # 5秒の無音
        silence_5s = create_silent_audio(5)
        temp_files.append(silence_5s)

    total_steps = len(texts)
    silence_cache = {}

    # 各指示を音声化 + 無音
    for i, (text, silence_duration) in enumerate(zip(texts, silence_durations)):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            continue

        dancer_name, instruction = parts[0], parts[1]

        temp_dancer_file = os.path.join(temp_dir, f"dancer_{i}.mp3")
        temp_instruction_file = os.path.join(temp_dir, f"instruction_{i}.mp3")

        # ログ出力
        print(f"[INFO] ({i+1}/{total_steps}) {dancer_name}: {instruction}")

        # ダンサー名の音声生成
        cmd_dancer = (
            f'edge-tts --text "{dancer_name}" '
            f'--voice ja-JP-NanamiNeural --write-media "{temp_dancer_file}"'
        )
        run_command_with_retry(cmd_dancer)

        # 指示文の音声生成
        cmd_instruction = (
            f'edge-tts --text "{instruction}" '
            f'--voice ja-JP-NanamiNeural --write-media "{temp_instruction_file}"'
        )
        run_command_with_retry(cmd_instruction)

        temp_files.append(temp_dancer_file)
        temp_files.append(temp_instruction_file)

        # 指定秒数の無音を追加
        if silence_duration not in silence_cache:
            silence_cache[silence_duration] = create_silent_audio(silence_duration)
        temp_files.append(silence_cache[silence_duration])

    # すべてのファイルパスを concat.txt に書き出し
    with open(concat_file_path, "w", encoding="utf-8") as concat_file:
        for tf in temp_files:
            concat_file.write(f"file '{tf}'\n")

    # ffmpeg で結合
    if ensure_output_file_is_writable(output_file):
        merge_command = (
            f'ffmpeg -y -f concat -safe 0 '
            f'-i "{concat_file_path}" -acodec copy "{temp_output_file}"'
        )
        subprocess.run(merge_command, shell=True)

        # temp_output.mp3 を output.mp3 にリネーム
        rename_output_file(temp_output_file, output_file)

        # Windowsメディアプレイヤーで再生（必要に応じて）
        subprocess.Popen(["start", "", output_file], shell=True)

    print("[INFO] すべての音声ファイルを処理完了しました！")


if __name__ == "__main__":
    # 1. 指示ファイル & ダンサーファイル & タイトルファイルの読み込み
    raw_instructions = load_instructions(instructions_file)
    dancers = load_dancers(dancers_file)
    title_text = load_title(title_file)

    # 2. インストラクションとサイレンス秒数を整形
    final_instructions, silence_durations = process_instructions_with_timing(
        raw_instructions, dancers
    )

    # 3. 実行
    print("\n🎤 スピーカーで指示を読み上げます...")
    speak_text_with_custom_silence(title_text, final_instructions, silence_durations)
