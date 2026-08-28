import os
import io
import base64
import tempfile
import shutil
import uuid
import logging
from typing import Union, Optional, List, BinaryIO, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    try:
        import pymupdf as fitz
    except ImportError:
        raise ImportError(
            "PyMuPDF is required. Please install it with: pip install pymupdf"
        )

from .models import PDFDocument, PDFPage, PDFImage, PDFSection


SUPPORTED_PDF_VERSION = "文字版PDF"
UNSUPPORTED_NOTE = "一期版本暂不支持扫描版PDF的OCR识别功能，仅支持可提取文本的文字版PDF。"


class PDFParser:
    def __init__(self, temp_dir: Optional[str] = None):
        if temp_dir is None:
            base_dir = Path(__file__).parent.parent.parent / "data" / "temp" / "pdf_images"
            temp_dir = str(base_dir)
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self._session_id = str(uuid.uuid4())
        self._session_dir = os.path.join(self.temp_dir, self._session_id)
        os.makedirs(self._session_dir, exist_ok=True)

    def extract_text(self, doc: fitz.Document) -> List[Tuple[int, str]]:
        pages_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            pages_text.append((page_num + 1, text.strip()))
        return pages_text

    def extract_images(self, doc: fitz.Document) -> List[PDFImage]:
        images = []
        img_index = 0
        seen_xrefs = set()

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_info in image_list:
                xref = img_info[0]
                
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                img_ext = base_image["ext"]
                width = base_image["width"]
                height = base_image["height"]

                if width < 100 or height < 100:
                    continue

                bbox = None
                for rect in page.get_image_rects(xref):
                    bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
                    break

                img_id = f"img_{self._session_id}_{page_num + 1}_{img_index}"
                img_filename = f"{img_id}.png"
                img_path = os.path.join(self._session_dir, img_filename)

                try:
                    if img_ext.lower() != "png":
                        from PIL import Image
                        img_pil = Image.open(io.BytesIO(image_bytes))
                        img_pil.save(img_path, "PNG")
                    else:
                        with open(img_path, "wb") as f:
                            f.write(image_bytes)
                except Exception:
                    with open(img_path, "wb") as f:
                        f.write(image_bytes)

                with open(img_path, "rb") as f:
                    img_data_base64 = base64.b64encode(f.read()).decode("utf-8")

                pdf_image = PDFImage(
                    image_id=img_id,
                    page_number=page_num + 1,
                    position=bbox if bbox else (0, 0, width, height),
                    image_data=img_data_base64,
                    width=width,
                    height=height,
                    file_path=img_path
                )
                images.append(pdf_image)
                img_index += 1
                
                if len(images) >= 9:
                    logger.info(f"Reached max image limit (9), stopping extraction")
                    return images

        return images

    def detect_sections(self, doc: fitz.Document) -> List[PDFSection]:
        sections = []
        font_sizes = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip():
                            font_sizes.append(span["size"])

        if not font_sizes:
            return sections

        avg_size = sum(font_sizes) / len(font_sizes)
        title_threshold = avg_size * 1.2

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    line_text = ""
                    max_size = 0
                    for span in line["spans"]:
                        line_text += span["text"]
                        if span["size"] > max_size:
                            max_size = span["size"]
                    line_text = line_text.strip()
                    if line_text and max_size >= title_threshold and len(line_text) < 100:
                        level = 1 if max_size >= title_threshold * 1.3 else 2
                        sections.append(PDFSection(
                            title=line_text,
                            level=level,
                            page_number=page_num + 1,
                            start_pos=line["bbox"][1]
                        ))

        return sections

    def parse_pdf(
        self,
        file_input: Union[str, bytes, BinaryIO, io.BytesIO],
        filename: Optional[str] = None
    ) -> PDFDocument:
        if isinstance(file_input, str):
            doc = fitz.open(file_input)
            if filename is None:
                filename = os.path.basename(file_input)
        else:
            if isinstance(file_input, bytes):
                file_input = io.BytesIO(file_input)
            file_input.seek(0)
            doc = fitz.open(stream=file_input.read(), filetype="pdf")
            if filename is None:
                filename = f"uploaded_{self._session_id}.pdf"

        metadata = {}
        if doc.metadata:
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
            }

        pages_text = self.extract_text(doc)
        all_images = self.extract_images(doc)
        sections = self.detect_sections(doc)

        pages = []
        for page_num, text in pages_text:
            page_images = [img for img in all_images if img.page_number == page_num]
            pages.append(PDFPage(
                page_number=page_num,
                text=text,
                images=page_images
            ))

        document = PDFDocument(
            filename=filename,
            total_pages=len(doc),
            pages=pages,
            metadata=metadata,
            sections=sections
        )

        doc.close()
        return document

    def cleanup(self):
        if os.path.exists(self._session_dir):
            shutil.rmtree(self._session_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def parse_pdf(
    file_input: Union[str, bytes, BinaryIO, io.BytesIO],
    filename: Optional[str] = None,
    temp_dir: Optional[str] = None,
    cleanup_temp: bool = False
) -> PDFDocument:
    parser = PDFParser(temp_dir=temp_dir)
    document = parser.parse_pdf(file_input, filename=filename)
    if cleanup_temp:
        parser.cleanup()
    return document


def get_supported_info() -> dict:
    return {
        "supported_version": SUPPORTED_PDF_VERSION,
        "note": UNSUPPORTED_NOTE
    }
