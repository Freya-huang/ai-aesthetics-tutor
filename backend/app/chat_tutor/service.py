import time
import uuid
import logging
from typing import Optional, List, Dict, Any
from io import BytesIO

from app.chat_tutor.models import (
    ChatSession, ChatMessage, MessageRole, MessageType,
    DetectedIntent, ChatAttachment, AttachmentType,
    ChatRequest, ChatResponse
)
from app.chat_tutor.intent_detector import IntentDetector
from app.art_diagnosis.service import ArtDiagnosisService
from app.paper_interpreter.service import PaperInterpreterService
from app.art_diagnosis.models import ArtDiagnosisInput
from app.paper_interpreter.models import PaperInterpretInput
from app.llm.client import LLMClient
from app.common.persistence import persistence

logger = logging.getLogger(__name__)


class ChatTutorService:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.intent_detector = IntentDetector()
        self.art_service = ArtDiagnosisService()
        self.paper_service = PaperInterpreterService()
        self.llm = LLMClient()

    @staticmethod
    def _model_dump(model: Any) -> Dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump(mode="json")
        return model.dict()

    def _save_session(self, session: ChatSession) -> None:
        persistence.save_chat_session(
            session.session_id,
            session.title,
            self._model_dump(session),
        )

    def _get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        if session_id:
            stored = persistence.load_chat_session(session_id)
            if stored:
                session = ChatSession.model_validate(stored) if hasattr(ChatSession, "model_validate") else ChatSession.parse_obj(stored)
                self.sessions[session_id] = session
                return session
        new_id = session_id or f"chat_{uuid.uuid4().hex[:12]}"
        now = time.time()
        session = ChatSession(
            session_id=new_id,
            created_at=now,
            updated_at=now
        )
        self.sessions[new_id] = session
        self._add_welcome_message(session)
        self._save_session(session)
        return session

    def _add_welcome_message(self, session: ChatSession):
        welcome = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=MessageRole.ASSISTANT,
            type=MessageType.WELCOME,
            content="从一件作品、一个问题，或一篇论文开始。",
            timestamp=time.time()
        )
        session.messages.append(welcome)

    def _add_message(self, session: ChatSession, role: MessageRole, msg_type: MessageType,
                     content: str, attachments: List[ChatAttachment] = None,
                     metadata: Dict = None) -> ChatMessage:
        msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=role,
            type=msg_type,
            content=content,
            attachments=attachments,
            timestamp=time.time(),
            metadata=metadata
        )
        session.messages.append(msg)
        session.updated_at = time.time()
        if session.title == "新对话" and role == MessageRole.USER:
            cleaned_title = content.replace("\n", " ").strip()
            if cleaned_title:
                session.title = cleaned_title[:28]
        return msg

    def _mock_chat_response(self, message: str, intent: DetectedIntent) -> str:
        msg_lower = message.lower()
        
        greetings = ["你好", "您好", "hi", "hello", "在吗", "嗨", "哈喽"]
        if any(g in msg_lower for g in greetings) and len(message) < 10:
            return "你好。你可以上传作品图片、论文 PDF，或者直接提出一个美学问题。"
        
        if intent == DetectedIntent.ART_DIAGNOSIS:
            return "请上传作品图片，并补充以下信息：\n\n1. 作品类型（绘画、摄影、数字艺术、海报或演示文稿）\n2. 希望表达的内容\n3. 本次希望重点分析的部分"
        
        if intent == DetectedIntent.PAPER_INTERPRET:
            return "请上传论文 PDF，并说明阅读目的，以及希望重点理解的问题或概念。"
        
        if "构图" in msg_lower:
            return "构图决定画面元素如何被组织，以及观看者的视线如何移动。\n\n- **三分法**：将主体放在三分线交点附近，形成自然平衡\n- **中心构图**：强调稳定、秩序与庄重感\n- **对角线构图**：增加方向感与动态张力\n- **框架构图**：利用前景建立空间层次\n\n上传具体作品后，可以进一步分析这些原则如何作用于画面。"
        
        if "色彩" in msg_lower:
            return "色彩可以从三个基础维度理解：\n\n- **色相**：颜色的类别\n- **明度**：颜色的明暗程度\n- **饱和度**：颜色的鲜艳程度\n\n同类色更统一，邻近色更柔和，对比色更有张力，互补色则带来更强的视觉冲击。上传作品后，可以结合具体画面进一步判断。"
        
        return "当前处于 Mock 测试模式，因此这里只返回示例性回答。配置真实模型后，系统会结合对话上下文和知识库进行更深入的分析。你也可以上传作品图片或论文 PDF 来验证完整流程。"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        session = self._get_or_create_session(request.session_id)
        
        user_attachments = request.attachments or []
        has_attachment = len(user_attachments) > 0
        
        if user_attachments:
            att_descs = []
            for att in user_attachments:
                if att.type == AttachmentType.IMAGE:
                    att_descs.append(f"[图片] {att.filename}")
                elif att.type == AttachmentType.PDF:
                    att_descs.append(f"[PDF] {att.filename}")
            self._add_message(
                session, MessageRole.USER,
                MessageType.IMAGE_UPLOADED if any(a.type == AttachmentType.IMAGE for a in user_attachments) 
                else MessageType.PDF_UPLOADED,
                request.message or f"已上传文件：{'、'.join(att_descs)}",
                attachments=user_attachments
            )
            session.pending_attachment = user_attachments[-1] if user_attachments else None
        else:
            self._add_message(session, MessageRole.USER, MessageType.TEXT, request.message)
        
        previous_intent = session.current_intent
        intent = (
            DetectedIntent.FOLLOWUP
            if request.followup_type and request.followup_session_id
            else self.intent_detector.detect_from_message(request.message, user_attachments)
        )
        session.current_intent = intent
        
        needs_info, clarification_q = self.intent_detector.needs_more_info(
            intent, request.message, has_attachment
        )
        
        if needs_info:
            self._add_message(session, MessageRole.ASSISTANT, MessageType.CLARIFICATION, clarification_q)
            for attachment in user_attachments:
                attachment.file_data = None
            self._save_session(session)
            return ChatResponse(
                session_id=session.session_id,
                reply=clarification_q,
                reply_type=MessageType.CLARIFICATION,
                detected_intent=intent,
                requires_more_info=True,
                clarification_question=clarification_q
            )
        
        diagnosis_result = None
        interpret_result = None
        reply = ""
        reply_type = MessageType.TEXT
        
        try:
            if intent == DetectedIntent.ART_DIAGNOSIS and has_attachment:
                img_att = next((a for a in user_attachments if a.type == AttachmentType.IMAGE), None)
                if img_att:
                    import base64
                    img_bytes = base64.b64decode(img_att.file_data) if img_att.file_data else b''
                    
                    art_input = ArtDiagnosisInput(
                        image=img_bytes,
                        artwork_type="other",
                        intent=request.message or "请帮我诊断这幅作品",
                        session_id=session.art_session_id
                    )
                    
                    diag_result = self.art_service.diagnose(art_input)
                    session.art_session_id = diag_result.session_id
                    session.active_result_type = AttachmentType.IMAGE
                    diagnosis_result = diag_result
                    diagnosis_payload = self._model_dump(diag_result)
                    
                    reply = "作品分析已完成。以下内容涵盖创作目标、视觉观察、优势、改进方向与相关知识点。"
                    reply_type = MessageType.ART_DIAGNOSIS_RESULT
                    
                    self._add_message(
                        session, MessageRole.ASSISTANT, reply_type, reply,
                        metadata={"result_type": "art", "result": diagnosis_payload}
                    )
                    persistence.archive_report(
                        source_session_id=diag_result.session_id,
                        report_type="art",
                        title=user_attachments[0].filename or "作品诊断报告",
                        result=diagnosis_payload,
                        chat_session_id=session.session_id,
                    )
            
            elif intent == DetectedIntent.PAPER_INTERPRET and has_attachment:
                pdf_att = next((a for a in user_attachments if a.type == AttachmentType.PDF), None)
                if pdf_att:
                    import base64
                    pdf_bytes = base64.b64decode(pdf_att.file_data) if pdf_att.file_data else b''
                    
                    paper_input = PaperInterpretInput(
                        pdf_file=pdf_bytes,
                        reading_purpose=request.message or "全面了解论文的核心观点",
                        session_id=session.paper_session_id
                    )
                    
                    interp_result = self.paper_service.interpret(paper_input)
                    session.paper_session_id = interp_result.session_id
                    session.active_result_type = AttachmentType.PDF
                    interpret_result = interp_result
                    interpretation_payload = self._model_dump(interp_result)
                    
                    reply = "论文解读已完成。以下内容梳理了文献信息、核心观点、研究问题、关键概念与论证脉络。"
                    reply_type = MessageType.PAPER_INTERPRET_RESULT
                    
                    self._add_message(
                        session, MessageRole.ASSISTANT, reply_type, reply,
                        metadata={"result_type": "paper", "result": interpretation_payload}
                    )
                    persistence.archive_report(
                        source_session_id=interp_result.session_id,
                        report_type="paper",
                        title=pdf_att.filename or "论文解读报告",
                        result=interpretation_payload,
                        chat_session_id=session.session_id,
                    )
            
            elif intent == DetectedIntent.FOLLOWUP:
                active_session_id = request.followup_session_id
                followup_type = request.followup_type
                if not active_session_id:
                    if session.active_result_type == AttachmentType.PDF or previous_intent == DetectedIntent.PAPER_INTERPRET:
                        active_session_id = session.paper_session_id
                        followup_type = AttachmentType.PDF
                    else:
                        active_session_id = session.art_session_id or session.paper_session_id
                        followup_type = AttachmentType.IMAGE if session.art_session_id else AttachmentType.PDF
                if active_session_id:
                    if followup_type == AttachmentType.IMAGE:
                        answer = self.art_service.followup(active_session_id, request.message)
                    else:
                        answer = self.paper_service.followup(active_session_id, request.message)
                    reply = answer
                    reply_type = MessageType.FOLLOWUP_ANSWER
                else:
                    reply = self._mock_chat_response(request.message, intent)
                self._add_message(session, MessageRole.ASSISTANT, reply_type, reply)
            
            else:
                reply = self._mock_chat_response(request.message, intent)
                self._add_message(session, MessageRole.ASSISTANT, MessageType.TEXT, reply)
        
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            reply = "处理过程中出现问题。请检查文件后重新上传，或调整问题描述后再试。"
            self._add_message(session, MessageRole.ASSISTANT, MessageType.TEXT, reply)
        
        suggested_actions = []
        if diagnosis_result and hasattr(diagnosis_result, 'recommended_knowledge'):
            suggested_actions = [kp.name for kp in diagnosis_result.recommended_knowledge[:3]]
        elif interpret_result and hasattr(interpret_result, 'recommended_reading'):
            suggested_actions = [kp.name for kp in interpret_result.recommended_reading[:3]]

        for attachment in user_attachments:
            attachment.file_data = None
        self._save_session(session)
        
        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            reply_type=reply_type,
            detected_intent=intent,
            requires_more_info=False,
            diagnosis_result=diagnosis_result,
            interpret_result=interpret_result,
            suggested_actions=suggested_actions
        )

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        session = self._get_or_create_session(session_id)
        return session.messages if session else []

    def list_sessions(self) -> List[Dict[str, Any]]:
        return persistence.list_chat_sessions()

    def rename_session(self, session_id: str, title: str) -> bool:
        title = title.strip()[:60]
        if not title:
            return False
        if session_id in self.sessions:
            self.sessions[session_id].title = title
            self.sessions[session_id].updated_at = time.time()
            self._save_session(self.sessions[session_id])
            return True
        return persistence.rename_chat_session(session_id, title)

    def delete_session(self, session_id: str) -> bool:
        self.sessions.pop(session_id, None)
        return persistence.delete_chat_session(session_id)


_service_instance: Optional[ChatTutorService] = None


def get_chat_tutor_service() -> ChatTutorService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ChatTutorService()
    return _service_instance
