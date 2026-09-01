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
    one_sentence_summary: str = Field(description="一句话概括")
    core_questions: List[str] = Field(description="论文试图回答的核心问题", default_factory=list)
    core_viewpoints: List[str] = Field(description="已呈现的核心观点", default_factory=list)
    key_concepts: List[dict] = Field(description="关键概念，每个带页码引用", default_factory=list)
    argument_process: List[str] = Field(description="已呈现的论证过程", default_factory=list)
    contributions_limitations: str = Field(description="已呈现内容的贡献与局限")
    course_creation_connections: List[str] = Field(description="与课程或创作的联系", default_factory=list)
    recommended_reading: List[KnowledgePoint] = Field(description="推荐延伸阅读，最多3项", default_factory=list)
    next_reflection_task: str = Field(description="下一步反思任务")
    sources: dict = Field(description="来源与使用边界，包含页码引用列表和RAG来源卡片", default_factory=dict)
    session_id: str = Field(description="会话ID")
    literature_info: str = Field(default="", description="兼容旧版：文献信息与解析范围")
    core_thesis: str = Field(default="", description="兼容旧版：一句话核心观点")
    research_questions: List[str] = Field(default_factory=list, description="兼容旧版：研究问题")
    argument_structure: List[dict] = Field(default_factory=list, description="兼容旧版：论证结构")
    classical_connections: List[dict] = Field(default_factory=list, description="兼容旧版：经典美学关联")
    paper_images: List[PaperImageRef] = Field(default_factory=list, description="兼容旧版：论文图片")
