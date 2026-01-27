import fitz  # PyMuPDF
import io
from PIL import Image

def get_pdf_first_page_image(pdf_path: str) -> bytes:
    """
    Extracts the first page of a PDF and returns it as image bytes (JPEG).
    """
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        raise ValueError("PDF is empty")
    
    page = doc.load_page(0)  # first page
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # increase resolution
    
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    
    doc.close()
    return img_byte_arr.getvalue()
