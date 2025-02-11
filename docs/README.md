# ダンス指示生成プロジェクト

このプロジェクトは、OpenAI の API を使用してダンスの指示を生成し、音声ファイルを作成するものです。

## 実行環境

このプロジェクトは Windows 環境に対応しています。以下の手順でセットアップを行ってください：

1. [Python](https://www.python.org/downloads/) をインストールします。
2. コマンドプロンプトを開き、プロジェクトのディレクトリに移動します。
3. `config/requirements.txt`に記載されている依存関係をインストールします：
   ```
   pip install -r config/requirements.txt
   ```
4. `.env`ファイルに OpenAI API キーを設定します。
5. `src/main.py`を実行して、音声ファイルを生成します。

## 動きの例

`docs/instructions.txt`に以下のように記載すると、ランダムな動きが生成されます：

```
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
**Anyone** **randomize**
```

この指示をもとに、`src/main.py`を実行すると、以下のような出力が得られます：

```
PS C:\Users\koshi\Work\PromptMotion> python src/main.py

🎤 スピーカーで指示を読み上げます...
[INFO] タイトルを読み上げます: にくをこねるのじょうえんを始めます
[INFO] (1/10) Suzu: 左足で地面を蹴る。
[INFO] (2/10) Yuka: 左足で地面を蹴る。
[INFO] (3/10) Yuka: 「両手を軽く振る」
[INFO] (4/10) Gan: 両手を広げて円を描くように回転する。
[INFO] (5/10) Billy: 「両手を広げて大きく振る」
[INFO] (6/10) Yuno: 両手を広げて大きく円を描く。
[INFO] (7/10) Gan: 両手を広げて、ゆっくりと踊りながら360度回転する。
[INFO] (8/10) Suzu: 背中を丸めて膝を曲げる
[INFO] (9/10) Yuno: 「両手を広げて円を描く」
[INFO] (10/10) Gan: 「両手を振りながら右足で一回転する」
```

## ファイル構成

- `src/main.py`: プロジェクトのメインスクリプト。指示を読み込み、音声ファイルを生成します。
- `docs/instructions.txt`: ダンサーの名前と指示がリストされたファイル。各指示には実行時間が秒単位で指定されています。
- `docs/dancers.txt`: ダンサーの名前がリストされたファイル。
- `docs/title.txt`: タイトル用のテキストファイル。
- `config/requirements.txt`: プロジェクトの依存関係をリストしたファイル。
- `assets/`: プロジェクトで使用するアセットを格納するディレクトリ。
- `.env`: 環境変数を設定するファイル。OpenAI API キーを設定します。

## ファイルの詳細

- `docs/title.txt`: プロジェクトのタイトルを記載するファイルです。音声ファイルの初めに読み上げられます。例: "ダンスパフォーマンス 2025"
- `docs/dancers.txt`: ダンサーの名前をリストするファイルです。各行に一人のダンサーの名前を記載します。例:
  ```
  Alice
  Bob
  Charlie
  ```
- `docs/instructions.txt`: ダンサーごとの指示を記載するファイルです。各行に「ダンサー名 指示内容,次の指示を読み上げるまでの秒数」の形式で記載します。秒数の指定がない場合、2~10s のランダムな間隔が設けられます。\*\*Anyone\*\*を指定すると、dancers.txt に記載されている任意のダンサーがピックアップされます。\*\*randomize\*\*を指定すると、任意の指示内容が AI によって生成されます。例:
  ```
  Alice ステップを踏む, 5s
  Bob 回転する, 1s
  Charlie 手を上げる
  **Anyone** 拍手する,1s
  Alice **randomize**,1s
  ```

1. `.env`ファイルに OpenAI API キーを設定します。
2. `docs/instructions.txt`と`docs/dancers.txt`を必要に応じて編集します。
3. `src/main.py`を実行します。音声ファイルが`output.mp3`として生成されます。

## 注意事項

- `output.mp3`ファイルが他のプロセスによって使用されていないことを確認してください。
- 必要に応じて、`title.txt`にタイトルを設定してください。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
