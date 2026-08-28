import logging
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.common.file_utils import save_upload_to_temp, cleanup_temp_file, is_allowed_document
from app.paper_interpreter.models import PaperInterpretOutput
from app.paper_interpreter.service import get_paper_interpreter_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/paper-interpreter", tags=["paper-interpreter"])


class FollowupRequest(BaseModel):
    session_id: str = Field(description="会话ID")
    question: str = Field(description="追问问题")


class FollowupResponse(BaseModel):
    answer: str
    session_id: str


@router.post("/interpret", response_model=PaperInterpretOutput)
async def interpret_paper(
    pdf_file: UploadFile = File(..., description="论文PDF文件"),
    reading_purpose: Optional[str] = Form(default=None, description="阅读目的"),
    focus_questions: Optional[str] = Form(default=None, description="关注问题，逗号分隔"),
    session_id: Optional[str] = Form(default=None, description="会话ID"),
):
    temp_path = None
    try:
        if not pdf_file.filename or not is_allowed_document(pdf_file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"请上传PDF格式文件，仅支持: {', '.join(settings.allowed_document_extensions)}"
            )

        temp_path = save_upload_to_temp(pdf_file, sub_dir="paper")
        logger.info(f"PDF saved to temp: {temp_path}")

        pdf_bytes = await pdf_file.read()

        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="PDF文件为空")

        if len(pdf_bytes) > settings.max_pdf_size:
            raise HTTPException(
                status_code=400,
                detail=f"PDF文件大小超过限制（最大{settings.max_pdf_size // 1024 // 1024}MB）"
            )

        focus_list = None
        if focus_questions:
            focus_list = [q.strip() for q in focus_questions.split(",") if q.strip()]

        from app.paper_interpreter.models import PaperInterpretInput
        input_data = PaperInterpretInput(
            pdf_file=pdf_bytes,
            reading_purpose=reading_purpose,
            focus_questions=focus_list,
            session_id=session_id,
        )

        service = get_paper_interpreter_service()
        result = service.interpret(input_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Paper interpretation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"论文解读失败: {str(e)}")
    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


@router.post("/followup", response_model=FollowupResponse)
async def followup_question(request: FollowupRequest):
    try:
        service = get_paper_interpreter_service()
        answer = service.followup(
            session_id=request.session_id,
            question=request.question,
        )
        return FollowupResponse(answer=answer, session_id=request.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Followup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"追问处理失败: {str(e)}")


@router.get("/health")
async def paper_interpreter_health():
    return {"status": "ok", "service": "paper-interpreter", "mock_mode": settings.mock_mode}
