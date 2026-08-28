from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class PDFImage:
    image_id: str
    page_number: int
    position: Tuple[float, float, float, float]
    image_data: Optional[str] = None
    width: int = 0
    height: int = 0
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PDFPage:
    page_number: int
    text: str
    images: List[PDFImage] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["images"] = [img.to_dict() for img in self.images]
        return result


@dataclass
class PDFSection:
    title: str
    level: int
    page_number: int
    start_pos: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PDFDocument:
    filename: str
    total_pages: int
    pages: List[PDFPage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: List[PDFSection] = field(default_factory=list)

    def get_full_text(self) -> str:
        return "\n\n".join([f"[第{page.page_number}页]\n{page.text}" for page in self.pages])

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "filename": self.filename,
            "total_pages": self.total_pages,
            "metadata": self.metadata,
            "pages": [page.to_dict() for page in self.pages],
            "sections": [sec.to_dict() for sec in self.sections]
        }
        return result
