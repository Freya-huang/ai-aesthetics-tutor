import io
import base64
import logging
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image

from app.llm.client import LLMClient, VisionClient
from app.llm.session import session_manager
from app.knowledge_base.retriever import get_retriever, KnowledgeRetriever
from app.art_diagnosis.models import (
    ArtDiagnosisInput,
    ArtDiagnosisOutput,
    SourceCard,
    KnowledgePoint,
    ArtworkType,
)
from app.art_diagnosis.prompts import DiagnosisPrompts
from app.art_diagnosis.output_parser import parse_diagnosis_output

logger = logging.getLogger(__name__)


ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
FORMAT_EXT_MAP = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MIN_IMAGE_DIMENSION = 100


class ImageValidationError(Exception):
    pass


class ImageValidator:
    @staticmethod
    def validate(image_bytes: bytes, max_size: int = MAX_IMAGE_SIZE) -> Tuple[str, str, Tuple[int, int]]:
        if len(image_bytes) == 0:
            raise ImageValidationError("图片为空")
        if len(image_bytes) > max_size:
            raise ImageValidationError(f"图片大小超过限制（最大{max_size // 1024 // 1024}MB）")

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
        except Exception as e:
            raise ImageValidationError(f"无法识别的图片格式: {str(e)}")

        img = Image.open(io.BytesIO(image_bytes))
        fmt = img.format
        if fmt not in ALLOWED_FORMATS:
            raise ImageValidationError(f"不支持的图片格式: {fmt}，仅支持 JPG/PNG/WebP")

        width, height = img.size
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise ImageValidationError(f"图片分辨率过低（最小{MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}）")

        image_type = FORMAT_EXT_MAP[fmt]
        return fmt, image_type, (width, height)

    @staticmethod
    def to_base64(image_bytes: bytes) -> Tuple[str, str]:
        img = Image.open(io.BytesIO(image_bytes))
        fmt = img.format or "JPEG"
        if fmt not in ALLOWED_FORMATS:
            fmt = "JPEG"
        image_type = FORMAT_EXT_MAP[fmt]
        buffered = io.BytesIO()
        if fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buffered, format=fmt)
        b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return image_type, b64


class ArtDiagnosisService:
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        vision_client: Optional[VisionClient] = None,
        retriever: Optional[KnowledgeRetriever] = None,
    ):
        self.llm = llm_client or LLMClient()
        self.vision = vision_client or VisionClient()
        self.retriever = retriever or get_retriever()
        self.validator = ImageValidator()

    def validate_image(self, image_bytes: bytes) -> Tuple[str, str, Tuple[int, int]]:
        return self.validator.validate(image_bytes)

    def generate_visual_observation(
        self,
        image_bytes: bytes,
        user_context: str = "",
    ) -> str:
        image_type, img_b64 = self.validator.to_base64(image_bytes)
        prompt = DiagnosisPrompts.VISUAL_OBSERVATION.format(user_context=user_context or "无")
        return self.vision.analyze_image(
            prompt=prompt,
            image_base64=img_b64,
            image_type=image_type,
            temperature=0.2,
            max_tokens=1500,
        )

    def _build_user_context(
        self,
        artwork_type: Optional[ArtworkType],
        scene: Optional[str],
        intent: Optional[str],
        focus_points: Optional[List[str]],
    ) -> str:
        parts = []
        if artwork_type:
            type_map = {
                ArtworkType.PAINTING: "绘画",
                ArtworkType.DIGITAL_ART: "数字艺术",
                ArtworkType.PHOTOGRAPHY: "摄影",
                ArtworkType.SKETCH: "素描",
                ArtworkType.POSTER: "海报",
                ArtworkType.PPT: "PPT演示",
                ArtworkType.OTHER: "其他",
            }
            parts.append(f"作品类型：{type_map.get(artwork_type, '其他')}")
        if scene:
            parts.append(f"创作场景：{scene}")
        if intent:
            parts.append(f"创作意图：{intent}")
        if focus_points:
            parts.append(f"关注重点：{'、'.join(focus_points)}")
        return "\n".join(parts) if parts else ""

    def _build_retrieval_query(self, observations: str, intent: Optional[str]) -> str:
        query_parts = []
        if intent:
            query_parts.append(intent)
        key_terms = ["构图", "色彩", "明暗", "空间", "对比", "视觉"]
        for term in key_terms:
            if term in observations:
                query_parts.append(term)
                break
        obs_excerpt = observations[:200].replace("\n", " ")
        query_parts.append(obs_excerpt)
        return " ".join(query_parts) if query_parts else observations[:300]

    def retrieve_knowledge(
        self,
        observations: str,
        intent: Optional[str],
        top_k: int = 3,
    ) -> List[SourceCard]:
        query = self._build_retrieval_query(observations, intent)
        logger.info(f"Retrieving knowledge with query: {query[:100]}...")
        try:
            results = self.retriever.search(query=query, top_k=top_k)
            sources = []
            for item in results.get("results", []):
                sources.append(SourceCard(
                    source_id=item.get("id", ""),
                    title=item.get("title", ""),
                    category=item.get("category", ""),
                    snippet=item.get("content", "")[:500],
                    relevance=float(item.get("score", 0.0)),
                ))
            return sources[:3]
        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")
            return []

    def _format_knowledge_sources(self, sources: List[SourceCard]) -> str:
        if not sources:
            return "无相关知识检索结果。"
        parts = []
        for idx, s in enumerate(sources, 1):
            parts.append(
                f"[来源{idx}] ID: {s.source_id}\n"
                f"标题: {s.title}\n"
                f"分类: {s.category}\n"
                f"内容: {s.snippet}\n"
            )
        return "\n".join(parts)

    def generate_feedback(
        self,
        observations: str,
        sources: List[SourceCard],
        artwork_type: Optional[ArtworkType],
        scene: Optional[str],
        intent: Optional[str],
        focus_points: Optional[List[str]],
    ) -> str:
        artwork_type_str = artwork_type.value if artwork_type else "未指定"
        scene_str = scene or "未提供"
        intent_str = intent or "探索视觉美学表达"
        focus_str = "、".join(focus_points) if focus_points else "未指定"
        knowledge_str = self._format_knowledge_sources(sources)

        prompt = DiagnosisPrompts.DIAGNOSIS_FEEDBACK.format(
            observations=observations,
            artwork_type=artwork_type_str,
            scene=scene_str,
            intent=intent_str,
            focus_points=focus_str,
            knowledge_sources=knowledge_str,
        )

        messages = [{"role": "user", "content": prompt}]
        return self.llm.chat(messages=messages, temperature=0.4, max_tokens=3000)

    def extract_recommended_knowledge(
        self,
        sources: List[SourceCard],
    ) -> List[KnowledgePoint]:
        points = []
        for s in sources[:3]:
            points.append(KnowledgePoint(
                name=s.title,
                source_id=s.source_id,
                description=s.snippet[:100],
            ))
        return points[:3]

    def diagnose(self, input_data: ArtDiagnosisInput) -> ArtDiagnosisOutput:
        fmt, image_type, dimensions = self.validate_image(input_data.image)
        logger.info(f"Image validated: format={fmt}, dimensions={dimensions}")

        if input_data.session_id and session_manager.session_exists(input_data.session_id):
            session_id = input_data.session_id
        else:
            session_id = session_manager.create_session(agent_type="art")

        user_context = self._build_user_context(
            input_data.artwork_type,
            input_data.scene,
            input_data.intent,
            input_data.focus_points,
        )

        observations = self.generate_visual_observation(input_data.image, user_context)
        logger.info(f"Generated visual observations ({len(observations)} chars)")

        session_manager.add_message(session_id, "user", f"[作品诊断]\n{user_context}")
        session_manager.add_message(session_id, "assistant", f"[视觉观察]\n{observations}")

        sources = self.retrieve_knowledge(observations, input_data.intent)
        logger.info(f"Retrieved {len(sources)} knowledge sources")

        llm_output = self.generate_feedback(
            observations=observations,
            sources=sources,
            artwork_type=input_data.artwork_type,
            scene=input_data.scene,
            intent=input_data.intent,
            focus_points=input_data.focus_points,
        )
        logger.info(f"Generated feedback ({len(llm_output)} chars)")

        output = parse_diagnosis_output(llm_output, session_id, sources)

        if not output.recommended_knowledge:
            output.recommended_knowledge = self.extract_recommended_knowledge(sources)

        session_manager.add_message(session_id, "assistant", f"[诊断反馈]\n{llm_output}")

        return output

    def followup(
        self,
        session_id: str,
        question: str,
        knowledge_point_name: Optional[str] = None,
    ) -> str:
        if not session_manager.session_exists(session_id):
            raise ValueError(f"Session not found: {session_id}")

        history_msgs = session_manager.get_messages_for_llm(session_id, limit=10)
        history_str = "\n\n".join([f"[{m['role']}]: {m['content'][:500]}" for m in history_msgs])

        prev_diagnosis = ""
        for m in reversed(history_msgs):
            if "[诊断反馈]" in m["content"]:
                prev_diagnosis = m["content"]
                break

        context = ""
        if knowledge_point_name:
            try:
                results = self.retriever.search(query=knowledge_point_name, top_k=2)
                if results.get("results"):
                    item = results["results"][0]
                    context = f"[相关知识] {item.get('title', '')}\n{item.get('content', '')[:800]}"
            except Exception:
                pass

        prompt = DiagnosisPrompts.FOLLOWUP_FEEDBACK.format(
            previous_diagnosis=prev_diagnosis[:2000],
            conversation_history=history_str,
            question=question,
            knowledge_context=context,
        )

        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages=messages, temperature=0.5, max_tokens=2000)

        session_manager.add_message(session_id, "user", question)
        session_manager.add_message(session_id, "assistant", response)

        return response


_service_instance: Optional[ArtDiagnosisService] = None


def get_diagnosis_service() -> ArtDiagnosisService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ArtDiagnosisService()
    return _service_instance
