import logging
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.common.file_utils import save_upload_to_temp, cleanup_temp_file, is_allowed_image
from app.art_diagnosis.models import ArtDiagnosisOutput, ArtworkType
from app.art_diagnosis.service import get_diagnosis_service, ImageValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/art-diagnosis", tags=["art-diagnosis"])


class FollowupRequest(BaseModel):
    session_id: str = Field(description="会话ID")
    question: str = Field(description="追问问题")
    knowledge_point_name: Optional[str] = Field(default=None, description="相关知识点名称")


class FollowupResponse(BaseModel):
    answer: str
    session_id: str


@router.post("/diagnose", response_model=ArtDiagnosisOutput)
async def diagnose_artwork(
    image: UploadFile = File(..., description="艺术作品图片"),
    artwork_type: Optional[ArtworkType] = Form(default=None, description="作品类型"),
    scene: Optional[str] = Form(default=None, description="创作场景"),
    intent: Optional[str] = Form(default=None, description="创作意图"),
    focus_points: Optional[str] = Form(default=None, description="关注重点，逗号分隔"),
    session_id: Optional[str] = Form(default=None, description="会话ID"),
):
    temp_path = None
    try:
        if not is_allowed_image(image.filename or ""):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片格式，仅支持: {', '.join(settings.allowed_image_extensions)}"
            )

        temp_path = save_upload_to_temp(image, sub_dir="art")
        logger.info(f"Art image saved to temp: {temp_path}")

        image_bytes = await image.read()

        if len(image_bytes) > settings.max_image_size:
            raise HTTPException(
                status_code=400,
                detail=f"图片大小超过限制（最大{settings.max_image_size // 1024 // 1024}MB）"
            )

        focus_list = None
        if focus_points:
            focus_list = [fp.strip() for fp in focus_points.split(",") if fp.strip()]

        from app.art_diagnosis.models import ArtDiagnosisInput
        input_data = ArtDiagnosisInput(
            image=image_bytes,
            artwork_type=artwork_type,
            scene=scene,
            intent=intent,
            focus_points=focus_list,
            session_id=session_id,
        )

        service = get_diagnosis_service()
        result = service.diagnose(input_data)
        return result
    except HTTPException:
        raise
    except ImageValidationError as e:
        raise HTTPException(status_code=400, detail=f"图片验证失败: {str(e)}")
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")
    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


@router.post("/followup", response_model=FollowupResponse)
async def followup_question(request: FollowupRequest):
    try:
        service = get_diagnosis_service()
        answer = service.followup(
            session_id=request.session_id,
            question=request.question,
            knowledge_point_name=request.knowledge_point_name,
        )
        return FollowupResponse(answer=answer, session_id=request.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Followup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"追问处理失败: {str(e)}")


@router.get("/health")
async def art_diagnosis_health():
    return {"status": "ok", "service": "art-diagnosis", "mock_mode": settings.mock_mode}
