import os
import glob
import json
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.knowledge_base.document_parser import parse_document
from app.knowledge_base.chunker import chunk_paragraphs
from app.knowledge_base.models import KnowledgeItem, CATEGORY_MAP


def get_knowledge_base_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "knowledge_base")


def import_all_documents(kb_dir: str = None) -> List[KnowledgeItem]:
    if kb_dir is None:
        kb_dir = get_knowledge_base_dir()
    
    docx_files = sorted(glob.glob(os.path.join(kb_dir, "*.docx")))
    all_items = []
    other_doc_counter = 0
    
    for docx_path in docx_files:
        try:
            metadata, paragraphs = parse_document(docx_path)
            chunks = chunk_paragraphs(paragraphs)
            
            doc_id = metadata["doc_id"]
            if not doc_id:
                other_doc_counter += 1
                doc_id = f"OTHER-{other_doc_counter:03d}"
            
            for idx, chunk in enumerate(chunks):
                item_id = f"{doc_id}-{idx:03d}"
                item = KnowledgeItem(
                    id=item_id,
                    doc_id=doc_id,
                    category=metadata["category"],
                    title=metadata["title"],
                    content=chunk,
                    source=metadata["source"],
                    version=metadata["version"],
                    tags=[CATEGORY_MAP.get(metadata["category"], "其他")],
                    chunk_index=idx,
                    metadata={
                        "total_chunks": len(chunks),
                        "paragraph_count": len(paragraphs)
                    }
                )
                all_items.append(item)
            
            print(f"成功解析: {metadata['source']} -> {len(chunks)} 个块")
        except Exception as e:
            print(f"解析失败 {os.path.basename(docx_path)}: {e}")
    
    return all_items


def save_to_json(items: List[KnowledgeItem], output_path: str = None):
    if output_path is None:
        kb_dir = get_knowledge_base_dir()
        output_path = os.path.join(kb_dir, "knowledge_items.json")
    
    data = [item.to_dict() for item in items]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存 {len(data)} 个知识条目到: {output_path}")
    return output_path


def generate_summary(items: List[KnowledgeItem]) -> Dict[str, Any]:
    category_counts = {}
    doc_counts = set()
    total_chars = 0
    
    for item in items:
        cat = item.category
        category_counts[cat] = category_counts.get(cat, 0) + 1
        doc_counts.add(item.doc_id)
        total_chars += len(item.content)
    
    summary = {
        "total_items": len(items),
        "total_documents": len(doc_counts),
        "total_characters": total_chars,
        "category_distribution": category_counts,
        "documents": sorted(list(doc_counts))
    }
    return summary


if __name__ == "__main__":
    print("开始导入知识库文档...")
    items = import_all_documents()
    output_path = save_to_json(items)
    summary = generate_summary(items)
    
    print("\n=== 导入摘要 ===")
    print(f"总文档数: {summary['total_documents']}")
    print(f"总知识块数: {summary['total_items']}")
    print(f"总字符数: {summary['total_characters']}")
    print("\n分类分布:")
    for cat, count in summary["category_distribution"].items():
        print(f"  {cat} ({CATEGORY_MAP.get(cat, '其他')}): {count} 块")
