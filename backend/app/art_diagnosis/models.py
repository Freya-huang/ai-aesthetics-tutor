from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ArtworkType(str, Enum):
    PAINTING = "painting"
    DIGITAL_ART = "digital_art"
    PHOTOGRAPHY = "photography"
    SKETCH = "sketch"
    POSTER = "poster"
    PPT = "ppt"
    OTHER = "other"


class ArtDiagnosisInput(BaseModel):
    image: bytes
    artwork_type: Optional[ArtworkType] = Field(default=None, description="作品类型")
    scene: Optional[str] = Field(default=None, description="创作场景描述")
    intent: Optional[str] = Field(default=None, description="创作意图")
    focus_points: Optional[List[str]] = Field(default=None, description="关注重点")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class SourceCard(BaseModel):
    source_id: str = Field(description="来源ID")
    title: str = Field(description="来源标题")
    category: str = Field(description="分类")
    snippet: str = Field(description="内容片段")
    relevance: float = Field(description="相关性分数", ge=0.0, le=1.0)


class KnowledgePoint(BaseModel):
    name: str = Field(description="知识点名称")
    source_id: str = Field(description="关联来源ID")
    description: str = Field(description="知识点描述")


class ArtDiagnosisOutput(BaseModel):
    creative_goal: str = Field(description="你的创作目标")
    visual_observations: str = Field(description="我观察到的视觉现象")
    strengths: List[str] = Field(description="值得保留的地方", default_factory=list)
    key_learning: str = Field(description="本次重点学习")
    aesthetics_knowledge: str = Field(description="美学知识讲解")
    multiple_perspectives: List[str] = Field(description="多元理解方向", default_factory=list)
    revision_tasks: List[str] = Field(description="本轮修改任务", default_factory=list)
    reflection_questions: List[str] = Field(description="修改后的反思问题", default_factory=list)
    usage_boundaries: str = Field(description="使用边界")
    sources: List[SourceCard] = Field(description="知识来源", default_factory=list)
    recommended_knowledge: List[KnowledgePoint] = Field(
        description="推荐知识点，最多3个", default_factory=list
    )
    session_id: str = Field(description="会话ID")
