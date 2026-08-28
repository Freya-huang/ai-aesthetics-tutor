import sys
import os
import io
from unittest.mock import MagicMock, patch
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.paper_interpreter.models import (
    PaperInterpretInput,
    PaperInterpretOutput,
    SourceCard,
    KnowledgePoint,
    PaperImageRef,
    PageCitation,
)
from app.paper_interpreter.service import PaperInterpreterService
from app.paper_interpreter.output_parser import (
    parse_interpretation_output,
    parse_image_observation,
)


def create_test_pdf_bytes() -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        c.drawString(100, height - 100, "论气韵生动的美学内涵")
        c.drawString(100, height - 130, "作者：测试学者")
        c.drawString(100, height - 170, "摘要：气韵生动是中国美学的核心范畴。")
        c.drawString(100, height - 200, "关键词：气韵生动、美学、中国艺术")
        c.drawString(100, height - 240, "一、引言")
        c.drawString(100, height - 270, "气韵生动作为中国绘画的最高准则，最早由谢赫在《古画品录》中提出。")
        c.drawString(100, height - 300, "本文旨在探讨气韵生动的美学内涵及其当代意义。")
        c.showPage()

        c.drawString(100, height - 100, "二、气韵生动的理论渊源")
        c.drawString(100, height - 130, "气韵生动包含两个层面：一是'气'，指生命的本源与活力；")
        c.drawString(100, height - 160, "二是'韵'，指超越形式的精神韵味。")
        c.drawString(100, height - 200, "三、气韵生动与意境理论")
        c.drawString(100, height - 230, "气韵生动与意境理论有着密切关联，二者都追求超越形似的精神表达。")
        c.showPage()

        c.drawString(100, height - 100, "四、贡献与局限")
        c.drawString(100, height - 130, "本文的贡献在于系统梳理了气韵生动的理论脉络。")
        c.drawString(100, height - 160, "局限在于缺乏对当代艺术实践的具体案例分析。")
        c.drawString(100, height - 200, "参考文献：")
        c.drawString(100, height - 230, "谢赫《古画品录》")
        c.showPage()

        c.save()
        return buffer.getvalue()
    except ImportError:
        return create_minimal_test_pdf_bytes()


def create_minimal_test_pdf_bytes() -> bytes:
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 100 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Paper Content - Page 1) Tj
0 -30 Td
(Qiyun Shengdong is a key concept in Chinese aesthetics) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000416 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
486
%%EOF"""


MOCK_IMAGE_OBSERVATION = """===IMAGE_DESCRIPTION_START===
这是一张示意图，展示了中国绘画中"气韵"的概念框架，包含三个层次的图示说明。
===IMAGE_DESCRIPTION_END===

===IMAGE_OBSERVATION_START===
图片类型：理论框架示意图
主要元素：包含三个同心圆形图示，分别标注"气"、"韵"、"生动"
结构：从内到外层层递进，中心是"气"，中间层是"韵"，外层是"生动"
文字标注：每层都有简短的文字说明，解释各层含义
可能用途：用于可视化展示"气韵生动"的层次结构和内在关系
===IMAGE_OBSERVATION_END==="""


def generate_mock_interpretation_llm_output() -> str:
    return """===LITERATURE_INFO_START===
论文标题：《论气韵生动的美学内涵》
作者：测试学者
论文共3页，本次解读基于完整文本，重点分析核心论点与美学概念
===LITERATURE_INFO_END===

===CORE_THESIS_START===
气韵生动作为中国美学的核心范畴，包含"气"的生命活力与"韵"的精神韵味两个层面，是中国艺术追求超越形似的精神表达的最高准则[第1-2页]
===CORE_THESIS_END===

===RESEARCH_QUESTIONS_START===
- 气韵生动的理论渊源是什么？[第2页]
- 气韵生动与意境理论有何关联？[第2页]
- 气韵生动的当代意义是什么？[第1页]
===RESEARCH_QUESTIONS_END===

===KEY_CONCEPTS_START===
气韵生动|||中国绘画的最高审美准则，指艺术作品展现的生命活力与精神韵律|||第1页|||"气韵生动是中国美学的核心范畴"
气|||生命的本源与活力，是艺术作品生命力的基础|||第2页|||"'气'，指生命的本源与活力"
韵|||超越形式的精神韵味，体现艺术作品的审美格调|||第2页|||"'韵'，指超越形式的精神韵味"
意境|||中国古典美学的重要范畴，追求情景交融的审美境界|||第2页|||"气韵生动与意境理论有着密切关联"
===KEY_CONCEPTS_END===

===ARGUMENT_STRUCTURE_START===
引言|||提出研究问题与论文主旨|||第1页|||通过介绍气韵生动的重要性，引出本文的研究目的
理论渊源|||梳理气韵生动的历史发展与概念内涵|||第2页|||从"气"与"韵"两个层面解析气韵生动的含义
与意境的关联|||探讨气韵生动与其他美学范畴的关系|||第2页|||分析气韵生动与意境理论的内在联系
贡献与局限|||总结论文贡献与不足|||第3页|||客观评价论文的学术价值与未来研究方向
===ARGUMENT_STRUCTURE_END===

===CLASSICAL_CONNECTIONS_START===
气韵生动|||论文系统讨论了谢赫"六法"中的气韵生动，追溯了其从六朝到当代的理论发展|||第1-2页|||论文直接引用谢赫《古画品录》作为理论源头，证据充分
===CLASSICAL_CONNECTIONS_END===

===CONTRIBUTIONS_LIMITATIONS_START===
主要贡献[第3页]：1.系统梳理了气韵生动的理论脉络，明确了"气"与"韵"的两层内涵；2.建立了气韵生动与意境理论的关联。
局限[第3页]：1.缺乏对当代艺术实践的具体案例分析；2.对中西美学比较涉及较少。
待讨论问题：气韵生动在数字艺术时代是否仍然适用？[第3页]
===CONTRIBUTIONS_LIMITATIONS_END===

===RECOMMENDED_READING_START===
气韵生动|||THE-002|||直接对应论文核心概念，可深入理解气韵生动的美学内涵
意境|||THE-001|||论文讨论了气韵生动与意境的关联，可拓展阅读意境理论
===RECOMMENDED_READING_END===

===PAGE_CITATIONS_START===
第1页|||气韵生动的定义、引言部分，提出研究问题
第2页|||气韵生动的理论渊源，气与韵的两层内涵，与意境理论的关联
第3页|||贡献与局限分析，参考文献
===PAGE_CITATIONS_END==="""


class TestModels:
    def test_paper_interpret_input(self):
        input_data = PaperInterpretInput(
            pdf_file=b"test pdf content",
            reading_purpose="学习美学理论",
            focus_questions=["什么是气韵生动？"],
            session_id="paper_test123",
        )
        assert input_data.reading_purpose == "学习美学理论"
        assert len(input_data.focus_questions) == 1
        assert input_data.session_id == "paper_test123"
        print("  ✓ test_paper_interpret_input passed")

    def test_page_citation(self):
        citation = PageCitation(page_number=1, quote_snippet="test quote")
        assert citation.page_number == 1
        assert citation.quote_snippet == "test quote"
        print("  ✓ test_page_citation passed")

    def test_paper_image_ref(self):
        img_ref = PaperImageRef(
            image_id="img_001",
            page_number=2,
            description="test image",
            observation="test observation",
        )
        assert img_ref.image_id == "img_001"
        assert img_ref.page_number == 2
        print("  ✓ test_paper_image_ref passed")

    def test_source_card(self):
        source = SourceCard(
            source_id="THE-002",
            title="气韵生动",
            category="THE",
            snippet="test snippet",
            relevance=0.9,
        )
        assert source.source_id == "THE-002"
        assert 0 <= source.relevance <= 1
        print("  ✓ test_source_card passed")

    def test_knowledge_point(self):
        kp = KnowledgePoint(
            name="气韵生动",
            source_id="THE-002",
            description="test description",
        )
        assert kp.name == "气韵生动"
        print("  ✓ test_knowledge_point passed")

    def test_paper_interpret_output(self):
        output = PaperInterpretOutput(
            literature_info="test info",
            core_thesis="test thesis",
            research_questions=["q1", "q2"],
            key_concepts=[{"name": "test"}],
            argument_structure=[{"title": "intro"}],
            classical_connections=[],
            paper_images=[],
            contributions_limitations="test",
            recommended_reading=[],
            sources={"page_citations": [], "rag_sources": []},
            session_id="paper_test",
        )
        assert output.session_id == "paper_test"
        assert isinstance(output.research_questions, list)
        print("  ✓ test_paper_interpret_output passed")


class TestOutputParser:
    def test_parse_complete_output(self):
        sources = [
            SourceCard(source_id="THE-002", title="气韵生动", category="THE", snippet="...", relevance=0.95),
            SourceCard(source_id="THE-001", title="意境", category="THE", snippet="...", relevance=0.88),
        ]
        paper_images = [
            PaperImageRef(
                image_id="img_001",
                page_number=2,
                description="概念框架图",
                observation="展示三层结构",
            )
        ]
        llm_out = generate_mock_interpretation_llm_output()
        result = parse_interpretation_output(
            llm_output=llm_out,
            session_id="paper_test123",
            sources=sources,
            paper_images=paper_images,
            total_pages=3,
        )

        assert isinstance(result, PaperInterpretOutput)
        assert result.session_id == "paper_test123"
        assert "气韵生动" in result.literature_info
        assert "气韵生动" in result.core_thesis
        assert len(result.research_questions) >= 1
        assert len(result.key_concepts) >= 1
        assert len(result.argument_structure) >= 1
        assert len(result.contributions_limitations) > 0
        assert len(result.recommended_reading) <= 3
        assert "page_citations" in result.sources
        assert "rag_sources" in result.sources
        assert len(result.paper_images) == 1
        print("  ✓ test_parse_complete_output passed")

    def test_parse_partial_output(self):
        sources = []
        paper_images = []
        partial_output = "Some invalid content without proper sections"
        result = parse_interpretation_output(
            llm_output=partial_output,
            session_id="paper_test456",
            sources=sources,
            paper_images=paper_images,
            total_pages=10,
        )

        assert result.session_id == "paper_test456"
        assert len(result.literature_info) > 0
        assert len(result.core_thesis) > 0
        assert len(result.contributions_limitations) > 0
        assert isinstance(result.research_questions, list)
        assert isinstance(result.key_concepts, list)
        assert isinstance(result.argument_structure, list)
        assert isinstance(result.classical_connections, list)
        print("  ✓ test_parse_partial_output passed")

    def test_parse_image_observation(self):
        desc, obs = parse_image_observation(MOCK_IMAGE_OBSERVATION)
        assert "示意图" in desc
        assert "图片类型" in obs
        assert "气韵" in obs
        print("  ✓ test_parse_image_observation passed")

    def test_parse_image_observation_invalid(self):
        desc, obs = parse_image_observation("invalid content")
        assert len(desc) > 0
        assert len(obs) > 0
        print("  ✓ test_parse_image_observation_invalid passed")


class TestPaperInterpreterService:
    def setup_method(self):
        self.mock_llm = MagicMock()
        self.mock_vision = MagicMock()
        self.mock_retriever = MagicMock()
        self.mock_pdf_parser = MagicMock()

        self.service = PaperInterpreterService(
            llm_client=self.mock_llm,
            vision_client=self.mock_vision,
            retriever=self.mock_retriever,
            pdf_parser=self.mock_pdf_parser,
        )

    def _create_mock_pdf_document(self):
        from app.pdf_parser.models import PDFDocument, PDFPage, PDFImage
        pages = []
        for i in range(1, 4):
            pages.append(PDFPage(
                page_number=i,
                text=f"第{i}页内容：气韵生动是中国美学的核心概念。" * 10,
                images=[],
            ))
        return PDFDocument(
            filename="test_paper.pdf",
            total_pages=3,
            pages=pages,
            metadata={"title": "论气韵生动", "author": "测试"},
            sections=[],
        )

    def _create_test_input(self, **kwargs):
        pdf_bytes = create_minimal_test_pdf_bytes()
        defaults = {
            "pdf_file": pdf_bytes,
            "reading_purpose": "学习中国美学",
            "focus_questions": ["气韵生动的内涵是什么？"],
            "session_id": None,
        }
        defaults.update(kwargs)
        return PaperInterpretInput(**defaults)

    def test_parse_pdf(self):
        mock_doc = self._create_mock_pdf_document()
        self.mock_pdf_parser.parse_pdf.return_value = mock_doc

        result = self.service.parse_pdf(b"test pdf bytes", "test.pdf")
        assert result.total_pages == 3
        assert self.mock_pdf_parser.parse_pdf.called
        print("  ✓ test_parse_pdf passed")

    def test_extract_key_concepts(self):
        mock_doc = self._create_mock_pdf_document()
        concepts = self.service.extract_key_concepts(mock_doc)
        assert isinstance(concepts, list)
        assert "美学" in concepts or "艺术" in concepts or len(concepts) > 0
        print("  ✓ test_extract_key_concepts passed")

    def test_retrieve_knowledge(self):
        mock_search_results = {
            "results": [
                {
                    "id": "THE-002",
                    "title": "气韵生动",
                    "category": "THE",
                    "content": "气韵生动是中国绘画六法之首，指艺术作品中展现的生命活力...",
                    "score": 0.95,
                },
                {
                    "id": "THE-001",
                    "title": "意境",
                    "category": "THE",
                    "content": "意境是中国古典美学的核心范畴...",
                    "score": 0.88,
                },
            ]
        }
        self.mock_retriever.search.return_value = mock_search_results

        sources = self.service.retrieve_knowledge(["气韵生动", "意境"])
        assert len(sources) <= 3
        assert all(isinstance(s, SourceCard) for s in sources)
        assert self.mock_retriever.search.called
        print("  ✓ test_retrieve_knowledge passed")

    def test_retrieve_knowledge_failure(self):
        self.mock_retriever.search.side_effect = Exception("Retrieval failed")
        sources = self.service.retrieve_knowledge(["test"])
        assert sources == []
        print("  ✓ test_retrieve_knowledge_failure passed")

    def test_interpret_flow(self):
        mock_doc = self._create_mock_pdf_document()
        self.mock_pdf_parser.parse_pdf.return_value = mock_doc
        self.mock_vision.analyze_image.return_value = MOCK_IMAGE_OBSERVATION

        mock_search_results = {
            "results": [
                {
                    "id": "THE-002",
                    "title": "气韵生动",
                    "category": "THE",
                    "content": "气韵生动是中国绘画六法之首...",
                    "score": 0.95,
                },
                {
                    "id": "THE-001",
                    "title": "意境",
                    "category": "THE",
                    "content": "意境是中国古典美学的核心范畴...",
                    "score": 0.88,
                },
            ]
        }
        self.mock_retriever.search.return_value = mock_search_results
        self.mock_llm.chat.return_value = generate_mock_interpretation_llm_output()

        input_data = self._create_test_input()
        result = self.service.interpret(input_data)

        assert isinstance(result, PaperInterpretOutput)
        assert result.session_id.startswith("paper_")
        assert self.mock_pdf_parser.parse_pdf.called
        assert self.mock_retriever.search.called
        assert self.mock_llm.chat.called
        assert len(result.recommended_reading) <= 3
        assert "page_citations" in result.sources
        assert "rag_sources" in result.sources
        print("  ✓ test_interpret_flow passed")

    def test_followup_flow(self):
        from app.llm.session import session_manager
        sid = session_manager.create_session("paper")
        session_manager.add_message(sid, "system", "[论文上下文]\n总页数: 3\n论文内容...")
        session_manager.add_message(sid, "assistant", "[论文解读结果]\n这是之前的解读内容")

        self.mock_retriever.search.return_value = {"results": []}
        self.mock_llm.chat.return_value = "这是对您追问的回答：关于气韵生动的问题，气韵是指..."

        answer = self.service.followup(
            session_id=sid,
            question="能再解释一下'气'和'韵'的区别吗？",
        )

        assert isinstance(answer, str)
        assert len(answer) > 0
        assert self.mock_llm.chat.called
        print("  ✓ test_followup_flow passed")

    def test_followup_invalid_session(self):
        try:
            self.service.followup("nonexistent_session", "test question")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        print("  ✓ test_followup_invalid_session passed")

    def test_analyze_pdf_images_no_images(self):
        mock_doc = self._create_mock_pdf_document()
        images = self.service.analyze_pdf_images(mock_doc)
        assert images == []
        print("  ✓ test_analyze_pdf_images_no_images passed")


def test_integration_mock_mode():
    print("\n=== Running Paper Interpreter Integration Test (Mock Mode) ===")
    pdf_bytes = create_minimal_test_pdf_bytes()
    input_data = PaperInterpretInput(
        pdf_file=pdf_bytes,
        reading_purpose="系统学习中国美学经典概念",
        focus_questions=["气韵生动的定义是什么？", "与意境有什么关系？"],
    )

    service = PaperInterpreterService()
    result = service.interpret(input_data)

    assert isinstance(result, PaperInterpretOutput)
    assert result.session_id.startswith("paper_")
    assert len(result.literature_info) > 0
    assert len(result.core_thesis) > 0
    assert isinstance(result.research_questions, list)
    assert isinstance(result.key_concepts, list)
    assert isinstance(result.argument_structure, list)
    assert isinstance(result.classical_connections, list)
    assert isinstance(result.paper_images, list)
    assert len(result.contributions_limitations) > 0
    assert isinstance(result.recommended_reading, list)
    assert len(result.recommended_reading) <= 3
    assert "page_citations" in result.sources
    assert "rag_sources" in result.sources
    assert "usage_boundary" in result.sources
    assert len(result.sources["usage_boundary"]) > 0

    print(f"  ✓ Session ID: {result.session_id}")
    print(f"  ✓ Literature info present: {len(result.literature_info) > 0}")
    print(f"  ✓ Core thesis present: {len(result.core_thesis) > 0}")
    print(f"  ✓ Research questions: {len(result.research_questions)} items")
    print(f"  ✓ Key concepts: {len(result.key_concepts)} items")
    print(f"  ✓ Argument structure: {len(result.argument_structure)} sections")
    print(f"  ✓ Classical connections: {len(result.classical_connections)} (empty if no evidence)")
    print(f"  ✓ Paper images: {len(result.paper_images)}")
    print(f"  ✓ Contributions & limitations present: {len(result.contributions_limitations) > 0}")
    print(f"  ✓ Recommended reading: {len(result.recommended_reading)} (max 3 enforced)")
    print(f"  ✓ Page citations: {len(result.sources.get('page_citations', []))}")
    print(f"  ✓ RAG sources: {len(result.sources.get('rag_sources', []))}")
    print(f"  ✓ Usage boundary stated: {len(result.sources.get('usage_boundary', '')) > 0}")
    print("  ✓ Integration mock test PASSED!")


def test_followup_integration_mock():
    print("\n=== Running Followup Integration Test (Mock Mode) ===")
    from app.llm.session import session_manager

    pdf_bytes = create_minimal_test_pdf_bytes()
    input_data = PaperInterpretInput(
        pdf_file=pdf_bytes,
        reading_purpose="测试",
    )
    service = PaperInterpreterService()
    result = service.interpret(input_data)

    answer = service.followup(
        session_id=result.session_id,
        question="这篇论文的核心观点是什么？",
    )

    assert isinstance(answer, str)
    assert len(answer) > 0
    print(f"  ✓ Followup answer received, length: {len(answer)}")
    print("  ✓ Followup integration test PASSED!")


def run_all_tests():
    print("=" * 60)
    print("Running Paper Interpreter Unit Tests")
    print("=" * 60)

    print("\n--- TestModels ---")
    tm = TestModels()
    tm.test_paper_interpret_input()
    tm.test_page_citation()
    tm.test_paper_image_ref()
    tm.test_source_card()
    tm.test_knowledge_point()
    tm.test_paper_interpret_output()

    print("\n--- TestOutputParser ---")
    tp = TestOutputParser()
    tp.test_parse_complete_output()
    tp.test_parse_partial_output()
    tp.test_parse_image_observation()
    tp.test_parse_image_observation_invalid()

    print("\n--- TestPaperInterpreterService ---")
    ts = TestPaperInterpreterService()
    ts.setup_method()
    ts.test_parse_pdf()
    ts.setup_method()
    ts.test_extract_key_concepts()
    ts.setup_method()
    ts.test_retrieve_knowledge()
    ts.setup_method()
    ts.test_retrieve_knowledge_failure()
    ts.setup_method()
    ts.test_interpret_flow()
    ts.setup_method()
    ts.test_followup_flow()
    ts.setup_method()
    ts.test_followup_invalid_session()
    ts.setup_method()
    ts.test_analyze_pdf_images_no_images()

    print("\n--- Integration Tests ---")
    test_integration_mock_mode()
    test_followup_integration_mock()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
