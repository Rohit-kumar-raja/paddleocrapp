from paddleocr import PaddleOCR
ocr = PaddleOCR(lang="en", use_textline_orientation=True)
print(dir(ocr))
