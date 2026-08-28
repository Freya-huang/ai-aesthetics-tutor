import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np

from app.knowledge_base.embeddings import BaseEmbedder, TfidfEmbedder
from app.knowledge_base.models import KnowledgeItem, CATEGORY_MAP

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "knowledge_base",
        embedder: Optional[BaseEmbedder] = None
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedder = embedder
        self.client = None
        self.collection = None
        self._is_chroma_available = False
        self._fallback_items = []
        self._fallback_embeddings = None
        
        os.makedirs(persist_directory, exist_ok=True)
        self._init_client()
    
    def _init_client(self):
        try:
            import chromadb
            from chromadb.config import Settings
            
            logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                count = self.collection.count()
                if count > 0:
                    peek = self.collection.peek(limit=1)
                    if peek and peek.get("embeddings") and len(peek["embeddings"]) > 0:
                        existing_dim = len(peek["embeddings"][0])
                        expected_dim = self.embedder.dimension if self.embedder else existing_dim
                        if expected_dim > 0 and existing_dim != expected_dim:
                            logger.warning(f"Embedding dimension mismatch: existing={existing_dim}, expected={expected_dim}. Recreating collection...")
                            self.client.delete_collection(name=self.collection_name)
                            self.collection = None
            except Exception as e:
                logger.warning(f"Error checking existing collection: {e}")
            
            if self.collection is None:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            elif not hasattr(self.collection, 'count'):
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            else:
                try:
                    self.client.get_or_create_collection(
                        name=self.collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                except:
                    pass
                    
            self._is_chroma_available = True
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize ChromaDB, using in-memory fallback: {e}")
            self._is_chroma_available = False
    
    def is_empty(self) -> bool:
        if self._is_chroma_available and self.collection is not None:
            return self.collection.count() == 0
        return len(self._fallback_items) == 0
    
    def count(self) -> int:
        if self._is_chroma_available and self.collection is not None:
            return self.collection.count()
        return len(self._fallback_items)
    
    def add_items(self, items: List[KnowledgeItem], batch_size: int = 32):
        if not items:
            logger.warning("No items to add")
            return
        
        if self.embedder is None:
            raise ValueError("Embedder not set")
        
        texts = []
        ids = []
        metadatas = []
        
        for item in items:
            text = f"{item.title}\n{item.content}"
            texts.append(text)
            ids.append(item.id)
            metadatas.append({
                "doc_id": item.doc_id,
                "category": item.category,
                "title": item.title,
                "source": item.source,
                "version": item.version,
                "tags": ",".join(item.tags),
                "chunk_index": item.chunk_index,
                "content": item.content,
                "metadata_json": json.dumps(item.metadata, ensure_ascii=False)
            })
        
        if isinstance(self.embedder, TfidfEmbedder) and not self.embedder._fitted:
            self.embedder.fit(texts)
        elif isinstance(self.embedder, TfidfEmbedder) and self.embedder._fitted:
            logger.info(f"TF-IDF already fitted (vocab size: {self.embedder.dimension}), skipping refit")
        
        if self._is_chroma_available and self.collection is not None:
            for i in range(0, len(items), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size]
                
                embeddings = self.embedder.embed(batch_texts)
                embeddings_list = embeddings.tolist()
                
                self.collection.add(
                    ids=batch_ids,
                    embeddings=embeddings_list,
                    metadatas=batch_metadatas,
                    documents=batch_texts
                )
                logger.info(f"Added batch {i//batch_size + 1}, {len(batch_ids)} items")
        else:
            embeddings = self.embedder.embed(texts)
            self._fallback_items.extend(items)
            if self._fallback_embeddings is None:
                self._fallback_embeddings = embeddings
            else:
                self._fallback_embeddings = np.vstack([self._fallback_embeddings, embeddings])
            logger.info(f"Added {len(items)} items to in-memory fallback store")
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if self.embedder is None:
            raise ValueError("Embedder not set")
        
        query_embedding = self.embedder.embed(query)
        
        if self._is_chroma_available and self.collection is not None:
            return self._search_chroma(query_embedding, top_k, category, query)
        else:
            return self._search_fallback(query_embedding, top_k, category, query)
    
    def _search_chroma(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        category: Optional[str],
        query_text: str = ""
    ) -> List[Dict[str, Any]]:
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k * 3,
            where=where_filter,
            include=["metadatas", "documents", "distances"]
        )
        
        candidates = []
        if results and results["ids"] and len(results["ids"]) > 0:
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            
            for i in range(len(ids)):
                item_id = ids[i]
                metadata = metadatas[i]
                distance = distances[i]
                similarity = 1.0 - distance
                
                item_metadata = {}
                if "metadata_json" in metadata:
                    try:
                        item_metadata = json.loads(metadata["metadata_json"])
                    except:
                        pass
                
                tags = []
                if "tags" in metadata and metadata["tags"]:
                    tags = metadata["tags"].split(",")
                
                title = metadata.get("title", "")
                content = metadata.get("content", "")
                
                if query_text:
                    import re
                    keywords = [k for k in re.split(r'[\s,，。、]+', query_text.lower()) if k]
                    if not keywords:
                        keywords = [query_text.lower()]
                    
                    bonus = 0.0
                    title_lower = title.lower()
                    content_lower = content.lower()
                    
                    for keyword in keywords:
                        if keyword in title_lower:
                            bonus += 0.3
                            break
                    
                    for keyword in keywords:
                        keyword_count = content_lower.count(keyword)
                        if keyword_count > 0:
                            bonus += min(0.3, keyword_count * 0.1)
                            break
                    
                    tags_lower = [tag.lower() for tag in tags]
                    for keyword in keywords:
                        for tag_lower in tags_lower:
                            if keyword in tag_lower:
                                bonus += 0.2
                                break
                    
                    similarity += bonus
                
                similarity = min(1.0, max(0.0, similarity))
                
                result_item = {
                    "id": item_id,
                    "doc_id": metadata.get("doc_id", ""),
                    "category": metadata.get("category", ""),
                    "title": title,
                    "content": content,
                    "source": metadata.get("source", ""),
                    "version": metadata.get("version", "V1"),
                    "tags": tags,
                    "chunk_index": metadata.get("chunk_index", 0),
                    "metadata": item_metadata,
                    "similarity": float(similarity)
                }
                candidates.append(result_item)
        
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates[:top_k]
    
    def _keyword_bonus(self, query: str, item: KnowledgeItem) -> float:
        bonus = 0.0
        import re
        keywords = [k for k in re.split(r'[\s,，。、]+', query.lower()) if k]
        if not keywords:
            keywords = [query.lower()]
        
        title_lower = item.title.lower()
        content_lower = item.content.lower()
        
        for keyword in keywords:
            if keyword in title_lower:
                bonus += 0.3
                break
        
        for keyword in keywords:
            keyword_count = content_lower.count(keyword)
            if keyword_count > 0:
                bonus += min(0.3, keyword_count * 0.1)
                break
        
        tags_lower = [tag.lower() for tag in item.tags]
        for keyword in keywords:
            for tag_lower in tags_lower:
                if keyword in tag_lower:
                    bonus += 0.2
                    break
        
        return bonus
    
    def _search_fallback(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        category: Optional[str],
        query_text: str = ""
    ) -> List[Dict[str, Any]]:
        if self._fallback_embeddings is None or len(self._fallback_items) == 0:
            return []
        
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_norm = query_embedding / (np.linalg.norm(query_embedding, axis=1, keepdims=True) + 1e-10)
        embeddings_norm = self._fallback_embeddings / (np.linalg.norm(self._fallback_embeddings, axis=1, keepdims=True) + 1e-10)
        similarities = np.dot(query_norm, embeddings_norm.T)[0]
        
        candidates = []
        for idx, item in enumerate(self._fallback_items):
            if category and item.category != category:
                continue
            
            sim = float(similarities[idx])
            if query_text:
                sim += self._keyword_bonus(query_text, item)
            
            sim = min(1.0, max(0.0, sim))
            candidates.append((idx, sim))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:top_k]
        
        search_results = []
        for idx, sim in top_candidates:
            item = self._fallback_items[idx]
            result_item = {
                "id": item.id,
                "doc_id": item.doc_id,
                "category": item.category,
                "title": item.title,
                "content": item.content,
                "source": item.source,
                "version": item.version,
                "tags": item.tags,
                "chunk_index": item.chunk_index,
                "metadata": item.metadata,
                "similarity": float(sim)
            }
            search_results.append(result_item)
        
        return search_results
    
    def get_stats(self) -> Dict[str, Any]:
        category_counts = {}
        doc_ids = set()
        
        if self._is_chroma_available and self.collection is not None:
            total_items = self.collection.count()
            if total_items > 0:
                all_items = self.collection.get(include=["metadatas"])
                if all_items and all_items["metadatas"]:
                    for metadata in all_items["metadatas"]:
                        cat = metadata.get("category", "OTHER")
                        category_counts[cat] = category_counts.get(cat, 0) + 1
                        doc_id = metadata.get("doc_id", "")
                        if doc_id:
                            doc_ids.add(doc_id)
        else:
            total_items = len(self._fallback_items)
            for item in self._fallback_items:
                cat = item.category
                category_counts[cat] = category_counts.get(cat, 0) + 1
                doc_ids.add(item.doc_id)
        
        category_distribution = {}
        for cat, count in category_counts.items():
            category_distribution[cat] = {
                "name": CATEGORY_MAP.get(cat, cat),
                "count": count
            }
        
        return {
            "total_items": total_items,
            "total_documents": len(doc_ids),
            "category_distribution": category_distribution,
            "using_chroma": self._is_chroma_available,
            "embedding_dimension": self.embedder.dimension if self.embedder else 0
        }
