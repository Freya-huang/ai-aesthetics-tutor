import sys
import os
import io
import tempfile
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.pdf_parser import (
    PDFDocument,
    PDFPage,
    PDFImage,
    PDFSection,
    PDFParser,
    parse_pdf,
    get_supported_info
)


class TestPDFModels(unittest.TestCase):
    def test_pdf_image_creation(self):
        img = PDFImage(
            image_id="test_img_001",
            page_number=1,
            position=(100, 200, 300, 400),
            image_data="base64data",
            width=200,
            height=200,
            file_path="/tmp/test.png"
        )
        self.assertEqual(img.image_id, "test_img_001")
        self.assertEqual(img.page_number, 1)
        self.assertEqual(img.width, 200)
        d = img.to_dict()
        self.assertIn("image_id", d)
        self.assertIn("position", d)

    def test_pdf_page_creation(self):
        img1 = PDFImage("img1", 1, (0, 0, 100, 100))
        page = PDFPage(
            page_number=1,
            text="测试文本内容",
            images=[img1]
        )
        self.assertEqual(page.page_number, 1)
        self.assertEqual(page.text, "测试文本内容")
        self.assertEqual(len(page.images), 1)
        d = page.to_dict()
        self.assertIn("images", d)

    def test_pdf_section_creation(self):
        section = PDFSection(
            title="第一章 引言",
            level=1,
            page_number=1,
            start_pos=100.0
        )
        self.assertEqual(section.title, "第一章 引言")
        self.assertEqual(section.level, 1)
        d = section.to_dict()
        self.assertEqual(d["page_number"], 1)

    def test_pdf_document_creation(self):
        page1 = PDFPage(1, "页面1内容")
        page2 = PDFPage(2, "页面2内容")
        sec1 = PDFSection("标题1", 1, 1)
        doc = PDFDocument(
            filename="test.pdf",
            total_pages=2,
            pages=[page1, page2],
            metadata={"title": "测试文档", "author": "测试作者"},
            sections=[sec1]
        )
        self.assertEqual(doc.filename, "test.pdf")
        self.assertEqual(doc.total_pages, 2)
        self.assertEqual(len(doc.pages), 2)
        full_text = doc.get_full_text()
        self.assertIn("[第1页]", full_text)
        self.assertIn("[第2页]", full_text)
        d = doc.to_dict()
        self.assertIn("metadata", d)
        self.assertIn("sections", d)


class TestPDFParserMock(unittest.TestCase):
    def test_get_supported_info(self):
        info = get_supported_info()
        self.assertIn("supported_version", info)
        self.assertIn("note", info)
        self.assertIn("不支持扫描版PDF", info["note"])

    @patch("app.pdf_parser.parser.fitz")
    def test_parser_initialization(self, mock_fitz):
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = PDFParser(temp_dir=tmpdir)
            self.assertTrue(os.path.exists(parser._session_dir))
            parser.cleanup()

    @patch("app.pdf_parser.parser.fitz")
    def test_parse_pdf_with_mock(self, mock_fitz):
        mock_page1 = MagicMock()
        mock_page1.get_text.side_effect = lambda arg="text": {
            "text": "第一页文本内容\n这是测试",
            "dict": {"blocks": []}
        }[arg]
        mock_page1.get_images.return_value = []
        mock_page1.get_image_rects.return_value = []

        mock_page2 = MagicMock()
        mock_page2.get_text.side_effect = lambda arg="text": {
            "text": "第二页内容",
            "dict": {"blocks": []}
        }[arg]
        mock_page2.get_images.return_value = []
        mock_page2.get_image_rects.return_value = []

        def get_page_by_index(idx):
            if idx == 0:
                return mock_page1
            elif idx == 1:
                return mock_page2

        mock_fitz_doc = MagicMock()
        mock_fitz_doc.__len__ = MagicMock(return_value=2)
        mock_fitz_doc.__getitem__ = MagicMock(side_effect=get_page_by_index)
        mock_fitz_doc.metadata = {"title": "测试PDF", "author": "测试"}
        mock_fitz_doc.close = MagicMock()

        def open_doc(filename=None, stream=None, filetype=None, *args, **kwargs):
            return mock_fitz_doc

        mock_fitz.open.side_effect = open_doc

        parser = PDFParser(temp_dir=tempfile.mkdtemp())
        pdf_bytes = b"%PDF-1.4 mock pdf content"
        doc = parser.parse_pdf(pdf_bytes, filename="mock.pdf")
        self.assertEqual(doc.filename, "mock.pdf")
        self.assertEqual(doc.total_pages, 2)
        self.assertEqual(len(doc.pages), 2)
        self.assertEqual(doc.pages[0].text, "第一页文本内容\n这是测试")
        self.assertEqual(doc.pages[1].text, "第二页内容")
        parser.cleanup()

    def test_context_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = None
            with PDFParser(temp_dir=tmpdir) as parser:
                session_dir = parser._session_dir
                self.assertTrue(os.path.exists(session_dir))
            self.assertFalse(os.path.exists(session_dir))


class TestImportCheck(unittest.TestCase):
    def test_imports(self):
        import app.pdf_parser
        self.assertTrue(hasattr(app.pdf_parser, "PDFParser"))
        self.assertTrue(hasattr(app.pdf_parser, "parse_pdf"))
        self.assertTrue(hasattr(app.pdf_parser, "get_supported_info"))


if __name__ == "__main__":
    print("=" * 60)
    print("PDF解析模块测试")
    print("=" * 60)
    print()

    print("支持信息:")
    info = get_supported_info()
    for k, v in info.items():
        print(f"  {k}: {v}")
    print()

    unittest.main(verbosity=2)
