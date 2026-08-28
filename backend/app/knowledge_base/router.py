from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any

from app.knowledge_base.retriever import get_retriever
from app.knowledge_base.models import CATEGORY_MAP

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/status")
async def get_knowledge_status() -> Dict[str, Any]:
    try:
        retriever = get_retriever()
        status = retriever.get_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base status: {str(e)}")


@router.get("/search")
async def search_knowledge(
    query: str = Query(..., description="搜索查询文本"),
    category: Optional[str] = Query(None, description="分类过滤 (AIA/THE/VIS/OTHER)"),
    top_k: int = Query(3, ge=1, le=20, description="返回结果数量")
) -> Dict[str, Any]:
    if not query.strip():
        raise HTTPException(status_code=400, detail="查询文本不能为空")
    
    if category and category not in CATEGORY_MAP:
        valid_categories = ", ".join(CATEGORY_MAP.keys())
        raise HTTPException(
            status_code=400,
            detail=f"无效的分类，有效分类为: {valid_categories}"
        )
    
    try:
        retriever = get_retriever()
        results = retriever.search(
            query=query,
            top_k=top_k,
            category=category
        )
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
