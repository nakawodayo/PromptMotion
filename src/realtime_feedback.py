import os
import cv2
import pytesseract
import subprocess
import time

# Tesseract OCR のパスを設定
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# カメラを起動
cap = cv2.VideoCapture(0)

def capture_text():
    """ 書画カメラで画像を撮影し、OCRでテキストを取得 """
    ret, frame = cap.read()
    if not ret:
        print("カメラから映像を取得できませんでした")
        return None

    # 画像をグレースケールに変換
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # OCR（画像からテキスト抽出）
    text = pytesseract.image_to_string(gray, lang="jpn")
    text = text.strip()

    return text if text else None

if __name__ == "__main__":
    print("リアルタイムで指示を取得します。Ctrl + C で終了。")
    
    prev_text = None
    try:
        while True:
            text = capture_text()
            if text and text != prev_text:
                print(f"認識結果: {text}")
                prev_text = text
            
            time.sleep(3)
    except KeyboardInterrupt:
        print("終了します...")
        cap.release()
        cv2.destroyAllWindows()
