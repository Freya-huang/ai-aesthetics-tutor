import sys
import os
import io
from unittest.mock import MagicMock, patch
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.art_diagnosis.models import (
    ArtDiagnosisInput,
    ArtDiagnosisOutput,
    SourceCard,
    KnowledgePoint,
    ArtworkType,
)
from app.art_diagnosis.service import (
    ArtDiagnosisService,
    ImageValidator,
    ImageValidationError,
)
from app.art_diagnosis.output_parser import parse_diagnosis_output


def create_test_image(format: str = "JPEG", size=(800, 600), color=(200, 100, 50)) -> bytes:
    img = Image.new("RGB", size, color)
    buffered = io.BytesIO()
    img.save(buffered, format=format)
    return buffered.getvalue()


class TestImageValidator:
    def test_valid_jpeg(self):
        img_bytes = create_test_image("JPEG")
        fmt, img_type, dims = ImageValidator.validate(img_bytes)
        assert fmt == "JPEG"
        assert img_type == "jpeg"
        assert dims == (800, 600)
        print("  ✓ test_valid_jpeg passed")

    def test_valid_png(self):
        img_bytes = create_test_image("PNG")
        fmt, img_type, dims = ImageValidator.validate(img_bytes)
        assert fmt == "PNG"
        assert img_type == "png"
        print("  ✓ test_valid_png passed")

    def test_empty_image(self):
        try:
            ImageValidator.validate(b"")
            assert False, "Should have raised ImageValidationError"
        except ImageValidationError:
            pass
        print("  ✓ test_empty_image passed")

    def test_unsupported_format(self):
        try:
            ImageValidator.validate(b"not an image")
            assert False, "Should have raised ImageValidationError"
        except ImageValidationError:
            pass
        print("  ✓ test_unsupported_format passed")

    def test_too_small_resolution(self):
        img = Image.new("RGB", (50, 50), (255, 0, 0))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        try:
            ImageValidator.validate(buffered.getvalue())
            assert False, "Should have raised ImageValidationError"
        except ImageValidationError:
            pass
        print("  ✓ test_too_small_resolution passed")

    def test_base64_conversion(self):
        img_bytes = create_test_image("JPEG")
        img_type, b64 = ImageValidator.to_base64(img_bytes)
        assert img_type == "jpeg"
        assert isinstance(b64, str)
        assert len(b64) > 0
        print("  ✓ test_base64_conversion passed")


MOCK_VISUAL_OBSERVATION = """【画面主体】
- 画面中央是一个由暖色调色块构成的主体图形，约占画面60%区域
- 主体位置居中偏上

【构图安排】
- 采用中心构图方式
- 视觉重心位于画面中心
- 前景、中景、背景层次分明

【色彩运用】
- 主要使用橙色、红色系暖色调
- 存在暖色与背景冷灰色的对比
- 整体为暖色调倾向

【明暗关系】
- 整体亮度中等
- 主体区域较亮，背景较暗
- 存在明确的明暗对比

【空间表现】
- 画面有一定深度表现
- 呈现平面化与浅空间结合的特征

【媒介技法】
- 疑似数字绘画作品
- 色块边缘清晰，呈现平涂特征"""


def generate_mock_diagnosis_llm_output(sources: list) -> str:
    return f"""===CREATIVE_GOAL_START===
探索色彩对比在视觉表达中的运用，通过暖色调主体营造情感氛围
===CREATIVE_GOAL_END===

===VISUAL_OBSERVATIONS_START===
{MOCK_VISUAL_OBSERVATION}
===VISUAL_OBSERVATIONS_END===

===STRENGTHS_START===
- 明确的色彩对比运用，暖色调主体有效建立了视觉焦点
- 中心构图稳定，视觉重心清晰
- 明暗关系处理明确，主体与背景区分度良好
===STRENGTHS_END===

===KEY_LEARNING_START===
本次重点学习「色彩关系」中的对比色原理。理解如何通过色相对比建立视觉层级，是提升作品表现力的关键
===KEY_LEARNING_END===

===AESTHETICS_KNOWLEDGE_START===
色彩对比是视觉美学中的核心概念之一。根据色彩理论，色相对比是指不同色相并置时产生的视觉效果。暖色（红、橙、黄）具有前进感，冷色具有后退感，合理运用可以建立画面的空间层次和视觉焦点。在你的作品中，暖橙色主体与冷灰色背景形成了有效的色相对比和冷暖对比，这是建立视觉重心的常用手法。
===AESTHETICS_KNOWLEDGE_END===

===MULTIPLE_PERSPECTIVES_START===
- 从色彩心理学角度：暖色调传递温暖、活力的情感联想
- 从构图形式角度：中心对称构图带来稳定、庄重的视觉感受
- 从媒介表达角度：数字平涂技法强调色块本身的形状与色彩关系
===MULTIPLE_PERSPECTIVES_END===

===REVISION_TASKS_START===
- 尝试调整主体色彩面积，观察不同比例的冷暖对比效果
- 在主体中加入少量邻近色变化，增加色彩层次而不破坏整体色调
- 思考是否可以通过调整明暗交界线的虚实来丰富空间感
===REVISION_TASKS_END===

===REFLECTION_QUESTIONS_START===
- 你选择暖色调作为主体是想传达什么样的情感？
- 如果将主体位置移到三分法交点，视觉效果会有什么不同？
- 你认为当前的色彩对比强度是否符合你的表达意图？
===REFLECTION_QUESTIONS_END===

===USAGE_BOUNDARIES_START===
本反馈基于当前视觉观察和检索到的美学知识提供教学参考。美学理解具有多元性，不存在唯一"正确"的创作方式。建议结合个人创作意图综合判断，选择性地尝试建议。
===USAGE_BOUNDARIES_END===

===RECOMMENDED_KNOWLEDGE_START===
色彩关系|||VIS-005|||与作品中色彩对比的运用直接相关
构图|||VIS-002|||中心构图是作品的重要形式特征
明暗|||VIS-006|||明暗对比建立了画面的基本层级
===RECOMMENDED_KNOWLEDGE_END==="""


class TestOutputParser:
    def test_parse_complete_output(self):
        sources = [
            SourceCard(source_id="VIS-005", title="色彩关系", category="VIS", snippet="...", relevance=0.9),
            SourceCard(source_id="VIS-002", title="构图", category="VIS", snippet="...", relevance=0.8),
            SourceCard(source_id="VIS-006", title="明暗", category="VIS", snippet="...", relevance=0.7),
        ]
        llm_out = generate_mock_diagnosis_llm_output(sources)
        result = parse_diagnosis_output(llm_out, "art_test123", sources)

        assert isinstance(result, ArtDiagnosisOutput)
        assert result.session_id == "art_test123"
        assert "色彩对比" in result.creative_goal
        assert "中心构图" in result.visual_observations
        assert len(result.strengths) >= 1
        assert "色彩关系" in result.key_learning
        assert len(result.aesthetics_knowledge) > 0
        assert len(result.multiple_perspectives) >= 1
        assert len(result.revision_tasks) >= 1
        assert len(result.reflection_questions) >= 1
        assert len(result.usage_boundaries) > 0
        assert len(result.sources) == 3
        assert len(result.recommended_knowledge) == 3
        print("  ✓ test_parse_complete_output passed")

    def test_parse_partial_output(self):
        sources = []
        partial_output = "Some invalid content without sections"
        result = parse_diagnosis_output(partial_output, "art_test456", sources)

        assert result.session_id == "art_test456"
        assert len(result.creative_goal) > 0
        assert len(result.strengths) >= 1
        assert len(result.revision_tasks) >= 1
        print("  ✓ test_parse_partial_output passed")


class TestArtDiagnosisService:
    def setup_method(self):
        self.mock_llm = MagicMock()
        self.mock_vision = MagicMock()
        self.mock_retriever = MagicMock()

        self.service = ArtDiagnosisService(
            llm_client=self.mock_llm,
            vision_client=self.mock_vision,
            retriever=self.mock_retriever,
        )

    def _create_test_input(self, **kwargs):
        img_bytes = create_test_image("JPEG")
        defaults = {
            "image": img_bytes,
            "artwork_type": ArtworkType.DIGITAL_ART,
            "scene": "个人创作练习",
            "intent": "练习色彩对比",
            "focus_points": ["色彩", "构图"],
            "session_id": None,
        }
        defaults.update(kwargs)
        return ArtDiagnosisInput(**defaults)

    def test_diagnose_flow(self):
        self.mock_vision.analyze_image.return_value = MOCK_VISUAL_OBSERVATION

        mock_search_results = {
            "results": [
                {
                    "id": "VIS-005",
                    "title": "色彩关系",
                    "category": "VIS",
                    "content": "色彩对比包括色相对比、明度对比、饱和度对比、冷暖对比等。对比色并置可以增强视觉冲击力，建立视觉焦点。",
                    "score": 0.92,
                },
                {
                    "id": "VIS-002",
                    "title": "构图",
                    "category": "VIS",
                    "content": "构图是画面元素的组织安排方式。中心构图具有稳定感，三分法构图更具动感，对称构图体现秩序感。",
                    "score": 0.85,
                },
                {
                    "id": "VIS-006",
                    "title": "明暗",
                    "category": "VIS",
                    "content": "明暗关系塑造体积感和空间感。明暗交界线是形体转折的关键位置。",
                    "score": 0.78,
                },
            ]
        }
        self.mock_retriever.search.return_value = mock_search_results

        sources_list = [
            SourceCard(source_id=r["id"], title=r["title"], category=r["category"],
                       snippet=r["content"], relevance=r["score"])
            for r in mock_search_results["results"]
        ]
        self.mock_llm.chat.return_value = generate_mock_diagnosis_llm_output(sources_list)

        input_data = self._create_test_input()
        result = self.service.diagnose(input_data)

        assert isinstance(result, ArtDiagnosisOutput)
        assert result.session_id.startswith("art_")
        assert self.mock_vision.analyze_image.called
        assert self.mock_retriever.search.called
        assert self.mock_llm.chat.called
        assert len(result.sources) == 3
        assert len(result.recommended_knowledge) <= 3
        assert len(result.strengths) > 0
        assert len(result.revision_tasks) > 0
        assert len(result.reflection_questions) > 0
        print("  ✓ test_diagnose_flow passed")

    def test_followup_flow(self):
        from app.llm.session import session_manager
        sid = session_manager.create_session("art")
        session_manager.add_message(sid, "assistant", "[诊断反馈]\n这是之前的诊断内容")

        self.mock_retriever.search.return_value = {"results": []}
        self.mock_llm.chat.return_value = "这是对您追问的回答：关于色彩对比的问题..."

        answer = self.service.followup(
            session_id=sid,
            question="能再讲讲色彩对比吗？",
            knowledge_point_name="色彩关系",
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


def test_integration_mock_mode():
    print("\n=== Running Integration Test (Mock Mode) ===")
    img_bytes = create_test_image("JPEG", (1024, 768))
    input_data = ArtDiagnosisInput(
        image=img_bytes,
        artwork_type=ArtworkType.PAINTING,
        scene="课堂练习",
        intent="学习构图",
        focus_points=["构图", "空间"],
    )

    service = ArtDiagnosisService()
    result = service.diagnose(input_data)

    assert isinstance(result, ArtDiagnosisOutput)
    assert result.session_id.startswith("art_")
    assert len(result.creative_goal) > 0
    assert len(result.visual_observations) > 0
    assert isinstance(result.strengths, list)
    assert len(result.key_learning) > 0
    assert len(result.aesthetics_knowledge) > 0
    assert isinstance(result.multiple_perspectives, list)
    assert isinstance(result.revision_tasks, list)
    assert isinstance(result.reflection_questions, list)
    assert len(result.usage_boundaries) > 0
    assert isinstance(result.sources, list)
    assert isinstance(result.recommended_knowledge, list)
    assert len(result.recommended_knowledge) <= 3

    print(f"  ✓ Session ID: {result.session_id}")
    print(f"  ✓ Creative goal present: {len(result.creative_goal) > 0}")
    print(f"  ✓ Visual observations present: {len(result.visual_observations) > 0}")
    print(f"  ✓ Strengths: {len(result.strengths)} items")
    print(f"  ✓ Sources found: {len(result.sources)}")
    print(f"  ✓ Recommended knowledge: {len(result.recommended_knowledge)} (max 3 enforced)")
    print(f"  ✓ Revision tasks: {len(result.revision_tasks)} items")
    print(f"  ✓ Reflection questions: {len(result.reflection_questions)} items")
    print("  ✓ Integration mock test PASSED!")


def run_all_tests():
    print("=" * 60)
    print("Running Art Diagnosis Unit Tests")
    print("=" * 60)

    print("\n--- TestImageValidator ---")
    tv = TestImageValidator()
    tv.test_valid_jpeg()
    tv.test_valid_png()
    tv.test_empty_image()
    tv.test_unsupported_format()
    tv.test_too_small_resolution()
    tv.test_base64_conversion()

    print("\n--- TestOutputParser ---")
    tp = TestOutputParser()
    tp.test_parse_complete_output()
    tp.test_parse_partial_output()

    print("\n--- TestArtDiagnosisService ---")
    ts = TestArtDiagnosisService()
    ts.setup_method()
    ts.test_diagnose_flow()
    ts.setup_method()
    ts.test_followup_flow()
    ts.setup_method()
    ts.test_followup_invalid_session()

    print("\n--- Integration Test ---")
    test_integration_mock_mode()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
