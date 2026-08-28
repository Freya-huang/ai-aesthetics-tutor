import logging
import base64
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.chat_tutor.service import get_chat_tutor_service
from app.chat_tutor.models import (
    ChatRequest, ChatResponse, ChatAttachment, AttachmentType
)
from app.art_diagnosis.service import ImageValidator, ImageValidationError
from app.common.persistence import persistence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["统一对话"])


@router.post("/send", response_model=ChatResponse)
async def send_message(
    session_id: Optional[str] = Form(None),
    message: str = Form(""),
    image: Optional[UploadFile] = File(None),
    pdf: Optional[UploadFile] = File(None),
    followup_type: Optional[AttachmentType] = Form(None),
    followup_session_id: Optional[str] = Form(None),
):
    try:
        attachments = []
        
        if image:
            content = await image.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="图片大小不能超过10MB")
            if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WebP 图片")
            try:
                ImageValidator.validate(content)
            except ImageValidationError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            attachments.append(ChatAttachment(
                type=AttachmentType.IMAGE,
                filename=image.filename or "image.png",
                content_type=image.content_type or "image/png",
                file_data=base64.b64encode(content).decode("utf-8")
            ))
        
        if pdf:
            content = await pdf.read()
            if len(content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="PDF大小不能超过50MB")
            if pdf.content_type != "application/pdf" or not content.startswith(b"%PDF-"):
                raise HTTPException(status_code=400, detail="请上传有效的PDF文件")
            attachments.append(ChatAttachment(
                type=AttachmentType.PDF,
                filename=pdf.filename or "paper.pdf",
                content_type=pdf.content_type or "application/pdf",
                file_data=base64.b64encode(content).decode("utf-8")
            ))
        
        if not message.strip() and not attachments:
            raise HTTPException(status_code=400, detail="请输入消息或上传文件")
        
        request = ChatRequest(
            session_id=session_id,
            message=message,
            attachments=attachments if attachments else None,
            followup_type=followup_type,
            followup_session_id=followup_session_id,
        )
        
        service = get_chat_tutor_service()
        response = await service.chat(request)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    service = get_chat_tutor_service()
    messages = service.get_session_messages(session_id)
    return {
        "session_id": session_id,
        "messages": [msg.model_dump(mode="json") if hasattr(msg, "model_dump") else msg.dict() for msg in messages]
    }


class RenameSessionRequest(BaseModel):
    title: str


class ArchiveReportRequest(BaseModel):
    report_type: str
    title: str
    result: dict
    chat_session_id: Optional[str] = None


@router.get("/sessions")
async def list_sessions():
    return {"sessions": get_chat_tutor_service().list_sessions()}


@router.patch("/sessions/{session_id}")
async def rename_session(session_id: str, request: RenameSessionRequest):
    if not get_chat_tutor_service().rename_session(session_id, request.title):
        raise HTTPException(status_code=404, detail="会话不存在或名称为空")
    return {"success": True}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if not get_chat_tutor_service().delete_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"success": True}


@router.get("/reports")
async def list_reports():
    return {"reports": persistence.list_reports()}


@router.post("/reports")
async def archive_report(request: ArchiveReportRequest):
    source_session_id = str(request.result.get("session_id", "")).strip()
    if request.report_type not in {"art", "paper"} or not source_session_id:
        raise HTTPException(status_code=400, detail="报告类型或会话编号无效")
    return persistence.archive_report(
        source_session_id=source_session_id,
        report_type=request.report_type,
        title=request.title.strip() or "未命名报告",
        result=request.result,
        chat_session_id=request.chat_session_id,
    )


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    if not persistence.delete_report(report_id):
        raise HTTPException(status_code=404, detail="报告不存在")
    return {"success": True}
