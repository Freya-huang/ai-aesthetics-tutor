import re
from typing import List, Dict, Any, Optional
from app.paper_interpreter.models import (
    PaperInterpretOutput,
    SourceCard,
    KnowledgePoint,
    PaperImageRef,
    PageCitation,
)


SECTION_PATTERNS = {
    "literature_info": r"===LITERATURE_INFO_START===\s*(.*?)\s*===LITERATURE_INFO_END===",
    "core_thesis": r"===CORE_THESIS_START===\s*(.*?)\s*===CORE_THESIS_END===",
    "research_questions": r"===RESEARCH_QUESTIONS_START===\s*(.*?)\s*===RESEARCH_QUESTIONS_END===",
    "key_concepts": r"===KEY_CONCEPTS_START===\s*(.*?)\s*===KEY_CONCEPTS_END===",
    "argument_structure": r"===ARGUMENT_STRUCTURE_START===\s*(.*?)\s*===ARGUMENT_STRUCTURE_END===",
    "classical_connections": r"===CLASSICAL_CONNECTIONS_START===\s*(.*?)\s*===CLASSICAL_CONNECTIONS_END===",
    "contributions_limitations": r"===CONTRIBUTIONS_LIMITATIONS_START===\s*(.*?)\s*===CONTRIBUTIONS_LIMITATIONS_END===",
    "recommended_reading": r"===RECOMMENDED_READING_START===\s*(.*?)\s*===RECOMMENDED_READING_END===",
    "page_citations": r"===PAGE_CITATIONS_START===\s*(.*?)\s*===PAGE_CITATIONS_END===",
}


def _extract_section(text: str, pattern: str, default: str = "") -> str:
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return default


def _parse_list_items(section_text: str) -> List[str]:
    if not section_text:
        return []
    items = []
    for line in section_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "无充分证据" in line or "无相关" in line:
            continue
        line = re.sub(r"^[-*•·]\s*", "", line)
        line = re.sub(r"^\d+[.)、]\s*", "", line)
        if line:
            items.append(line.strip())
    return items


def _parse_pipe_separated(section_text: str, expected_fields: int) -> List[List[str]]:
    if not section_text:
        return []
    results = []
    for line in section_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "无充分证据" in line or "无相关" in line:
            continue
        parts = [p.strip() for p in line.split("|||")]
        if len(parts) >= expected_fields:
            results.append(parts[:expected_fields])
    return results


def _validate_page_number(page_str: str, total_pages: int) -> Optional[int]:
    if not page_str:
        return None
    match = re.search(r"第(\d+)页", page_str)
    if match:
        page_num = int(match.group(1))
        if 1 <= page_num <= total_pages:
            return page_num
    return None


def _parse_page_citations(section_text: str, total_pages: int) -> List[PageCitation]:
    citations = []
    rows = _parse_pipe_separated(section_text, 2)
    for row in rows:
        page_str, snippet = row[0], row[1]
        page_num = _validate_page_number(page_str, total_pages)
        if page_num and snippet:
            citations.append(PageCitation(
                page_number=page_num,
                quote_snippet=snippet
            ))
    return citations


def _parse_key_concepts(section_text: str, total_pages: int) -> List[Dict[str, Any]]:
    concepts = []
    rows = _parse_pipe_separated(section_text, 4)
    for row in rows:
        name, description, page_str, quote = row[0], row[1], row[2], row[3]
        page_num = _validate_page_number(page_str, total_pages)
        if name and description:
            concepts.append({
                "name": name,
                "description": description,
                "page_number": page_num,
                "quote": quote
            })
    return concepts


def _parse_argument_structure(section_text: str, total_pages: int) -> List[Dict[str, Any]]:
    structure = []
    rows = _parse_pipe_separated(section_text, 4)
    for row in rows:
        title, summary, page_range, argument = row[0], row[1], row[2], row[3]
        page_nums = []
        page_matches = re.findall(r"第(\d+)页", page_range)
        for pm in page_matches:
            pn = int(pm)
            if 1 <= pn <= total_pages:
                page_nums.append(pn)
        if title and summary:
            structure.append({
                "section_title": title,
                "summary": summary,
                "page_range": page_range,
                "page_numbers": page_nums,
                "core_argument": argument
            })
    return structure


def _parse_classical_connections(section_text: str, total_pages: int) -> List[Dict[str, Any]]:
    connections = []
    rows = _parse_pipe_separated(section_text, 4)
    for row in rows:
        classical_problem, paper_discussion, page_str, strength = row[0], row[1], row[2], row[3]
        page_num = _validate_page_number(page_str, total_pages)
        if classical_problem and paper_discussion and page_num:
            connections.append({
                "classical_problem": classical_problem,
                "paper_discussion": paper_discussion,
                "page_number": page_num,
                "evidence_strength": strength
            })
    return connections


def _parse_recommended_reading(
    section_text: str,
    sources: List[SourceCard]
) -> List[KnowledgePoint]:
    points = []
    source_ids = {s.source_id for s in sources}
    rows = _parse_pipe_separated(section_text, 3)
    for row in rows[:3]:
        name, source_id, reason = row[0], row[1], row[2]
        if source_id not in source_ids and sources:
            source_id = sources[0].source_id
        if name and source_id:
            points.append(KnowledgePoint(
                name=name,
                source_id=source_id,
                description=reason
            ))
    return points[:3]


def parse_interpretation_output(
    llm_output: str,
    session_id: str,
    sources: List[SourceCard],
    paper_images: List[PaperImageRef],
    total_pages: int,
) -> PaperInterpretOutput:
    literature_info = _extract_section(llm_output, SECTION_PATTERNS["literature_info"])
    core_thesis = _extract_section(llm_output, SECTION_PATTERNS["core_thesis"])
    research_questions_text = _extract_section(llm_output, SECTION_PATTERNS["research_questions"])
    key_concepts_text = _extract_section(llm_output, SECTION_PATTERNS["key_concepts"])
    argument_structure_text = _extract_section(llm_output, SECTION_PATTERNS["argument_structure"])
    classical_connections_text = _extract_section(llm_output, SECTION_PATTERNS["classical_connections"])
    contributions_limitations = _extract_section(llm_output, SECTION_PATTERNS["contributions_limitations"])
    recommended_reading_text = _extract_section(llm_output, SECTION_PATTERNS["recommended_reading"])
    page_citations_text = _extract_section(llm_output, SECTION_PATTERNS["page_citations"])

    if not literature_info:
        literature_info = f"论文共{total_pages}页，本次解读基于完整文本内容"
    if not core_thesis:
        core_thesis = f"论文核心观点解析中（共{total_pages}页）"
    if not contributions_limitations:
        contributions_limitations = "论文贡献与局限分析：请结合具体页码标注进行参考"

    research_questions = _parse_list_items(research_questions_text)
    key_concepts = _parse_key_concepts(key_concepts_text, total_pages)
    argument_structure = _parse_argument_structure(argument_structure_text, total_pages)
    classical_connections = _parse_classical_connections(classical_connections_text, total_pages)
    recommended_reading = _parse_recommended_reading(recommended_reading_text, sources)
    page_citations = _parse_page_citations(page_citations_text, total_pages)

    sources_dict = {
        "page_citations": [citation.model_dump() for citation in page_citations],
        "rag_sources": [source.model_dump() for source in sources],
        "usage_boundary": "本解读基于PDF文本内容生成，所有观点已标注页码。经典美学问题关联仅在证据充分时建立，不虚构理论联系。推荐知识点均来自检索到的共享知识库。"
    }

    return PaperInterpretOutput(
        literature_info=literature_info,
        core_thesis=core_thesis,
        research_questions=research_questions,
        key_concepts=key_concepts,
        argument_structure=argument_structure,
        classical_connections=classical_connections,
        paper_images=paper_images,
        contributions_limitations=contributions_limitations,
        recommended_reading=recommended_reading,
        sources=sources_dict,
        session_id=session_id,
    )


def parse_image_observation(llm_output: str) -> tuple:
    desc_pattern = r"===IMAGE_DESCRIPTION_START===\s*(.*?)\s*===IMAGE_DESCRIPTION_END==="
    obs_pattern = r"===IMAGE_OBSERVATION_START===\s*(.*?)\s*===IMAGE_OBSERVATION_END==="

    description = _extract_section(llm_output, desc_pattern)
    observation = _extract_section(llm_output, obs_pattern)

    if not description:
        description = "图片内容解析中..."
    if not observation:
        observation = "图片观察记录生成中..."

    return description, observation
