from pydantic import BaseModel, Field
from typing import List, Optional


class PaperInterpretInput(BaseModel):
    pdf_file: bytes = Field(description="PDF文件二进制内容")
    reading_purpose: Optional[str] = Field(default=None, description="阅读目的")
    focus_questions: Optional[List[str]] = Field(default=None, description="关注的问题列表")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class PageCitation(BaseModel):
    page_number: int = Field(description="页码", ge=1)
    quote_snippet: str = Field(description="引用片段")


class PaperImageRef(BaseModel):
    image_id: str = Field(description="图片ID")
    page_number: int = Field(description="所在页码", ge=1)
    description: str = Field(description="图片内容描述")
    observation: str = Field(description="观察记录")


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


class PaperInterpretOutput(BaseModel):
    literature_info: str = Field(description="文献信息与解析范围")
    core_thesis: str = Field(description="一句话核心观点")
    research_questions: List[str] = Field(description="研究问题", default_factory=list)
    key_concepts: List[dict] = Field(description="关键概念，每个带页码引用", default_factory=list)
    argument_structure: List[dict] = Field(description="论证结构，每个部分带页码", default_factory=list)
    classical_connections: List[dict] = Field(description="与经典美学问题的关联", default_factory=list)
    paper_images: List[PaperImageRef] = Field(description="论文中的图片或案例", default_factory=list)
    contributions_limitations: str = Field(description="贡献、局限与待讨论问题")
    recommended_reading: List[KnowledgePoint] = Field(description="建议继续阅读的知识点，最多3个", default_factory=list)
    sources: dict = Field(description="来源与使用边界，包含页码引用列表和RAG来源卡片", default_factory=dict)
    session_id: str = Field(description="会话ID")
