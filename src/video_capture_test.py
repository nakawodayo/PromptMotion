import cv2
import pytesseract

def capture_text():
    """ 書画カメラで画像を撮影し、OCRでテキストを取得 """
    ret, frame = cap.read()
    if not ret:
        print("カメラから映像を取得できませんでした")
        return None

    # 画像を保存して確認
    image_path = "C:\\Users\\koshi\\Work\\PromptMotion\\capture_test.png"
    cv2.imwrite(image_path, frame)
    print(f"画像をキャプチャしました: {image_path}")

    # 画像をグレースケールに変換
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 画像の解像度を2倍に拡大
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # コントラストを強調
    gray = cv2.equalizeHist(gray)

    # 二値化（背景を白、文字を黒にする）
    _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR（画像からテキスト抽出）
    text = pytesseract.image_to_string(gray, lang="jpn")
    text = text.strip()

    if text:
        print(f"OCR認識結果: {text}")
    else:
        print("OCRでテキストを検出できませんでした。")

    return text if text else None
