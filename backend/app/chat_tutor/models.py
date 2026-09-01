from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE_UPLOADED = "image_uploaded"
    PDF_UPLOADED = "pdf_uploaded"
    ART_DIAGNOSIS_RESULT = "art_diagnosis_result"
    PAPER_INTERPRET_RESULT = "paper_interpret_result"
    FOLLOWUP_ANSWER = "followup_answer"
    WELCOME = "welcome"
    CLARIFICATION = "clarification"
    CONCEPT_LESSON = "concept_lesson"


class DetectedIntent(str, Enum):
    ART_DIAGNOSIS = "art_diagnosis"
    PAPER_INTERPRET = "paper_interpret"
    FOLLOWUP = "followup"
    CHAT = "chat"
    CLARIFICATION_NEEDED = "clarification_needed"
    CONCEPT_LEARNING = "concept_learning"


class AttachmentType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"


class ChatAttachment(BaseModel):
    type: AttachmentType
    filename: str
    content_type: str
    file_data: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    id: str
    role: MessageRole
    type: MessageType
    content: str
    attachments: Optional[List[ChatAttachment]] = None
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class ChatSession(BaseModel):
    session_id: str
    title: str = "新对话"
    messages: List[ChatMessage] = Field(default_factory=list)
    current_intent: Optional[DetectedIntent] = None
    art_session_id: Optional[str] = None
    paper_session_id: Optional[str] = None
    active_result_type: Optional[AttachmentType] = None
    pending_attachment: Optional[ChatAttachment] = None
    created_at: float
    updated_at: float


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    attachments: Optional[List[ChatAttachment]] = None
    followup_type: Optional[AttachmentType] = None
    followup_session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    reply_type: MessageType
    detected_intent: DetectedIntent
    requires_more_info: bool = False
    clarification_question: Optional[str] = None
    diagnosis_result: Optional[Any] = None
    interpret_result: Optional[Any] = None
    suggested_actions: Optional[List[str]] = None
