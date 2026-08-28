import logging
from typing import List, Optional
from io import BytesIO

from app.llm.client import LLMClient, VisionClient
from app.llm.session import session_manager
from app.knowledge_base.retriever import get_retriever, KnowledgeRetriever
from app.pdf_parser.parser import PDFParser
from app.pdf_parser.models import PDFDocument
from app.paper_interpreter.models import (
    PaperInterpretInput,
    PaperInterpretOutput,
    SourceCard,
    KnowledgePoint,
    PaperImageRef,
)
from app.paper_interpreter.prompts import PaperInterpreterPrompts
from app.paper_interpreter.output_parser import (
    parse_interpretation_output,
    parse_image_observation,
)

logger = logging.getLogger(__name__)


class PaperInterpreterService:
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        vision_client: Optional[VisionClient] = None,
        retriever: Optional[KnowledgeRetriever] = None,
        pdf_parser: Optional[PDFParser] = None,
    ):
        self.llm = llm_client or LLMClient()
        self.vision = vision_client or VisionClient()
        self.retriever = retriever or get_retriever()
        self.pdf_parser = pdf_parser or PDFParser()

    def parse_pdf(self, pdf_bytes: bytes, filename: Optional[str] = None) -> PDFDocument:
        logger.info(f"Parsing PDF, filename: {filename or 'unnamed'}")
        pdf_stream = BytesIO(pdf_bytes)
        document = self.pdf_parser.parse_pdf(pdf_stream, filename=filename)
        logger.info(f"PDF parsed: {document.total_pages} pages, {len(document.sections)} sections")
        return document

    def analyze_pdf_images(self, document: PDFDocument) -> List[PaperImageRef]:
        images_refs = []
        all_images = []
        for page in document.pages:
            all_images.extend(page.images)

        if not all_images:
            logger.info("No images found in PDF")
            return images_refs

        logger.info(f"Analyzing {len(all_images)} images from PDF")
        for img in all_images:
            try:
                prompt = PaperInterpreterPrompts.IMAGE_OBSERVATION.format(
                    page_number=img.page_number,
                    image_id=img.image_id,
                )
                if img.image_data:
                    llm_output = self.vision.analyze_image(
                        prompt=prompt,
                        image_base64=img.image_data,
                        image_type="png",
                        temperature=0.2,
                        max_tokens=1000,
                    )
                    description, observation = parse_image_observation(llm_output)
                else:
                    description = f"第{img.page_number}页图片"
                    observation = "图片数据不可用，无法进行视觉分析"

                images_refs.append(PaperImageRef(
                    image_id=img.image_id,
                    page_number=img.page_number,
                    description=description,
                    observation=observation,
                ))
            except Exception as e:
                logger.warning(f"Failed to analyze image {img.image_id}: {e}")
                images_refs.append(PaperImageRef(
                    image_id=img.image_id,
                    page_number=img.page_number,
                    description=f"第{img.page_number}页图片",
                    observation=f"图片分析失败: {str(e)}",
                ))

        return images_refs

    def extract_key_concepts(self, document: PDFDocument) -> List[str]:
        full_text = document.get_full_text()
        text_excerpt = full_text[:3000]

        concept_keywords = [
            "美学", "艺术", "审美", "意境", "气韵", "摹仿", "模仿", "崇高",
            "机械复制", "媒介", "视觉", "构图", "色彩", "空间", "形式",
            "内容", "再现", "表现", "主体性", "创造力", "原创", "版权",
        ]

        concepts = []
        for keyword in concept_keywords:
            if keyword in text_excerpt:
                concepts.append(keyword)

        if not concepts:
            concepts = ["美学理论", "艺术研究"]

        logger.info(f"Extracted key concepts: {concepts}")
        return concepts[:8]

    def retrieve_knowledge(self, key_concepts: List[str], top_k: int = 3) -> List[SourceCard]:
        query = " ".join(key_concepts)
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

    def _format_pdf_content(self, document: PDFDocument) -> str:
        parts = []
        for page in document.pages:
            parts.append(f"[第{page.page_number}页]\n{page.text}")
        return "\n\n".join(parts)

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

    def generate_interpretation(
        self,
        document: PDFDocument,
        sources: List[SourceCard],
        reading_purpose: Optional[str],
        focus_questions: Optional[List[str]],
    ) -> str:
        pdf_content = self._format_pdf_content(document)
        knowledge_str = self._format_knowledge_sources(sources)
        purpose_str = reading_purpose or "全面了解论文的核心观点和论证结构"
        focus_str = "\n".join([f"- {q}" for q in focus_questions]) if focus_questions else "无特别指定的关注问题"

        prompt = PaperInterpreterPrompts.PDF_ANALYSIS.format(
            pdf_content=pdf_content[:15000],
            reading_purpose=purpose_str,
            focus_questions=focus_str,
            knowledge_sources=knowledge_str,
        )

        messages = [{"role": "user", "content": prompt}]
        return self.llm.chat(messages=messages, temperature=0.3, max_tokens=4000)

    def interpret(self, input_data: PaperInterpretInput) -> PaperInterpretOutput:
        if input_data.session_id and session_manager.session_exists(input_data.session_id):
            session_id = input_data.session_id
        else:
            session_id = session_manager.create_session(agent_type="paper")

        document = self.parse_pdf(
            input_data.pdf_file,
            filename="uploaded_paper.pdf"
        )

        paper_images = self.analyze_pdf_images(document)

        key_concepts = self.extract_key_concepts(document)

        sources = self.retrieve_knowledge(key_concepts)
        logger.info(f"Retrieved {len(sources)} knowledge sources")

        user_msg = f"[论文解读]\n阅读目的: {input_data.reading_purpose or '全面解读'}\n"
        if input_data.focus_questions:
            user_msg += f"关注问题: {'; '.join(input_data.focus_questions)}\n"
        session_manager.add_message(session_id, "user", user_msg)

        llm_output = self.generate_interpretation(
            document=document,
            sources=sources,
            reading_purpose=input_data.reading_purpose,
            focus_questions=input_data.focus_questions,
        )
        logger.info(f"Generated interpretation ({len(llm_output)} chars)")

        output = parse_interpretation_output(
            llm_output=llm_output,
            session_id=session_id,
            sources=sources,
            paper_images=paper_images,
            total_pages=document.total_pages,
        )

        if not output.recommended_reading and sources:
            output.recommended_reading = [
                KnowledgePoint(
                    name=s.title,
                    source_id=s.source_id,
                    description=s.snippet[:100],
                )
                for s in sources[:3]
            ]

        session_manager.add_message(session_id, "assistant", f"[论文解读结果]\n{llm_output[:2000]}")

        self._store_paper_context(session_id, document, llm_output)

        return output

    def _store_paper_context(self, session_id: str, document: PDFDocument, interpretation: str):
        try:
            context_msg = (
                f"[论文上下文]\n"
                f"总页数: {document.total_pages}\n"
                f"文件名: {document.filename}\n"
                f"论文内容(摘录):\n{document.get_full_text()[:10000]}"
            )
            session_manager.add_message(session_id, "system", context_msg)
        except Exception as e:
            logger.warning(f"Failed to store paper context: {e}")

    def followup(
        self,
        session_id: str,
        question: str,
    ) -> str:
        if not session_manager.session_exists(session_id):
            raise ValueError(f"Session not found: {session_id}")

        history_msgs = session_manager.get_messages_for_llm(session_id, limit=10)
        history_str = "\n\n".join([f"[{m['role']}]: {m['content'][:500]}" for m in history_msgs])

        paper_context = ""
        try:
            sys_msgs = session_manager.get_history(session_id, roles=["system"])
            for m in reversed(sys_msgs):
                if "[论文上下文]" in m["content"]:
                    paper_context = m["content"][:5000]
                    break
        except Exception:
            pass

        prev_interpretation = ""
        for m in reversed(history_msgs):
            if "[论文解读结果]" in m["content"]:
                prev_interpretation = m["content"]
                break

        sources = []
        try:
            results = self.retriever.search(query=question, top_k=2)
            if results.get("results"):
                for item in results["results"][:2]:
                    sources.append(
                        f"[知识来源] {item.get('title', '')}\n{item.get('content', '')[:500]}"
                    )
        except Exception:
            pass
        knowledge_context = "\n\n".join(sources) if sources else "无额外知识参考"

        prompt = PaperInterpreterPrompts.FOLLOWUP.format(
            previous_interpretation=prev_interpretation[:2000],
            conversation_history=history_str,
            paper_context=paper_context,
            knowledge_context=knowledge_context,
            question=question,
        )

        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages=messages, temperature=0.5, max_tokens=2000)

        session_manager.add_message(session_id, "user", question)
        session_manager.add_message(session_id, "assistant", response)

        return response


_service_instance: Optional[PaperInterpreterService] = None


def get_paper_interpreter_service() -> PaperInterpreterService:
    global _service_instance
    if _service_instance is None:
        _service_instance = PaperInterpreterService()
    return _service_instance
