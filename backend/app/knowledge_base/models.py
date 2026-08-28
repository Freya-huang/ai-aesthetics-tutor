from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


CATEGORY_MAP = {
    "AIA": "人工智能美学",
    "THE": "美学理论",
    "VIS": "视觉美学",
    "OTHER": "其他"
}


@dataclass
class KnowledgeItem:
    id: str
    doc_id: str
    category: str
    title: str
    content: str
    source: str
    version: str = "V1"
    tags: List[str] = field(default_factory=list)
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
