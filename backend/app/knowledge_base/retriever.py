import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.config import settings
from app.knowledge_base.models import KnowledgeItem, CATEGORY_MAP
from app.knowledge_base.embeddings import get_embedder, BaseEmbedder, TfidfEmbedder
from app.knowledge_base.vector_store import VectorStore

logger = logging.getLogger(__name__)


def get_data_dir() -> str:
    return settings.data_dir


def get_knowledge_items_path() -> str:
    return os.path.join(settings.knowledge_base_dir, "knowledge_items.json")


def get_chroma_db_path() -> str:
    return settings.chroma_db_dir


class KnowledgeRetriever:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.embedder: Optional[BaseEmbedder] = None
        self.vector_store: Optional[VectorStore] = None
        self._initialized = False
        self._initialize()
    
    def _initialize(self):
        if self._initialized:
            return
        
        logger.info("Initializing knowledge retriever...")
        
        self.embedder = get_embedder(self.model_name)
        chroma_path = get_chroma_db_path()
        self.vector_store = VectorStore(
            persist_directory=chroma_path,
            collection_name="aesthetics_kb",
            embedder=self.embedder
        )
        
        if self.vector_store.is_empty():
            logger.info("Vector store is empty, loading knowledge items from JSON...")
            self._load_knowledge_items()
        else:
            logger.info(f"Vector store already contains {self.vector_store.count()} items")
        
        self._initialized = True
        logger.info("Knowledge retriever initialized successfully")
    
    def _load_knowledge_items(self):
        json_path = get_knowledge_items_path()
        
        if not os.path.exists(json_path):
            logger.warning(f"Knowledge items file not found: {json_path}")
            logger.info("Please run the importer first to generate knowledge_items.json")
            return
        
        logger.info(f"Loading knowledge items from: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            items_data = json.load(f)
        
        items = []
        for item_dict in items_data:
            item = KnowledgeItem(
                id=item_dict["id"],
                doc_id=item_dict["doc_id"],
                category=item_dict["category"],
                title=item_dict["title"],
                content=item_dict["content"],
                source=item_dict["source"],
                version=item_dict.get("version", "V1"),
                tags=item_dict.get("tags", []),
                chunk_index=item_dict.get("chunk_index", 0),
                metadata=item_dict.get("metadata", {})
            )
            items.append(item)
        
        logger.info(f"Loaded {len(items)} knowledge items")
        
        if isinstance(self.embedder, TfidfEmbedder):
            texts = [f"{item.title}\n{item.content}" for item in items]
            self.embedder.fit(texts)
        
        self.vector_store.add_items(items)
        logger.info("Knowledge items added to vector store")
    
    def _rewrite_query(self, query: str) -> str:
        variants = {
            "模仿说": "摹仿说 模仿说",
            "摹仿说": "摹仿说 模仿说",
            "色彩": "色彩 颜色 色调",
            "构图": "构图 布局 结构",
            "机械复制": "机械复制 机械复制时代 本雅明",
            "气韵": "气韵 气韵生动",
            "意境": "意境 境界",
        }
        
        for key, expanded in variants.items():
            if key in query:
                return expanded
        
        return query
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self._initialized:
            self._initialize()
        
        logger.info(f"Searching for: '{query}' (top_k={top_k}, category={category})")
        
        rewritten_query = self._rewrite_query(query)
        logger.info(f"Rewritten query: '{rewritten_query}'")
        
        results = self.vector_store.search(
            query=rewritten_query,
            top_k=top_k,
            category=category
        )
        
        response = {
            "query": query,
            "rewritten_query": rewritten_query if rewritten_query != query else None,
            "top_k": top_k,
            "category": category,
            "category_name": CATEGORY_MAP.get(category, "全部") if category else "全部",
            "results": results,
            "result_count": len(results)
        }
        
        return response
    
    def get_status(self) -> Dict[str, Any]:
        if not self._initialized:
            self._initialize()
        
        stats = self.vector_store.get_stats()
        status = {
            "initialized": self._initialized,
            "model_name": self.model_name,
            "is_tfidf_fallback": isinstance(self.embedder, TfidfEmbedder),
            **stats
        }
        return status


_retriever_instance: Optional[KnowledgeRetriever] = None


def get_retriever() -> KnowledgeRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = KnowledgeRetriever()
    return _retriever_instance
