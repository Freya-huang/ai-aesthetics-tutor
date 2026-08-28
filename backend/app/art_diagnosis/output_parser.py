import re
from typing import List, Optional
from app.art_diagnosis.models import (
    ArtDiagnosisOutput,
    SourceCard,
    KnowledgePoint,
)


SECTION_PATTERNS = {
    "creative_goal": r"===CREATIVE_GOAL_START===\s*(.*?)\s*===CREATIVE_GOAL_END===",
    "visual_observations": r"===VISUAL_OBSERVATIONS_START===\s*(.*?)\s*===VISUAL_OBSERVATIONS_END===",
    "strengths": r"===STRENGTHS_START===\s*(.*?)\s*===STRENGTHS_END===",
    "key_learning": r"===KEY_LEARNING_START===\s*(.*?)\s*===KEY_LEARNING_END===",
    "aesthetics_knowledge": r"===AESTHETICS_KNOWLEDGE_START===\s*(.*?)\s*===AESTHETICS_KNOWLEDGE_END===",
    "multiple_perspectives": r"===MULTIPLE_PERSPECTIVES_START===\s*(.*?)\s*===MULTIPLE_PERSPECTIVES_END===",
    "revision_tasks": r"===REVISION_TASKS_START===\s*(.*?)\s*===REVISION_TASKS_END===",
    "reflection_questions": r"===REFLECTION_QUESTIONS_START===\s*(.*?)\s*===REFLECTION_QUESTIONS_END===",
    "usage_boundaries": r"===USAGE_BOUNDARIES_START===\s*(.*?)\s*===USAGE_BOUNDARIES_END===",
    "recommended_knowledge": r"===RECOMMENDED_KNOWLEDGE_START===\s*(.*?)\s*===RECOMMENDED_KNOWLEDGE_END===",
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
        line = re.sub(r"^[-*•·]\s*", "", line)
        line = re.sub(r"^\d+[.)、]\s*", "", line)
        if line:
            items.append(line.strip())
    return items


def _parse_recommended_knowledge(section_text: str, sources: List[SourceCard]) -> List[KnowledgePoint]:
    if not section_text:
        return []
    points = []
    source_ids = {s.source_id for s in sources}
    lines = [l.strip() for l in section_text.split("\n") if l.strip()]
    for line in lines[:3]:
        parts = [p.strip() for p in line.split("|||")]
        if len(parts) >= 2:
            name = parts[0]
            source_id = parts[1] if parts[1] in source_ids else (sources[0].source_id if sources else "")
            description = parts[2] if len(parts) >= 3 else ""
            if name and source_id:
                points.append(KnowledgePoint(
                    name=name,
                    source_id=source_id,
                    description=description
                ))
    return points[:3]


def parse_diagnosis_output(
    llm_output: str,
    session_id: str,
    sources: List[SourceCard],
) -> ArtDiagnosisOutput:
    creative_goal = _extract_section(llm_output, SECTION_PATTERNS["creative_goal"])
    visual_observations = _extract_section(llm_output, SECTION_PATTERNS["visual_observations"])
    strengths_text = _extract_section(llm_output, SECTION_PATTERNS["strengths"])
    key_learning = _extract_section(llm_output, SECTION_PATTERNS["key_learning"])
    aesthetics_knowledge = _extract_section(llm_output, SECTION_PATTERNS["aesthetics_knowledge"])
    perspectives_text = _extract_section(llm_output, SECTION_PATTERNS["multiple_perspectives"])
    tasks_text = _extract_section(llm_output, SECTION_PATTERNS["revision_tasks"])
    questions_text = _extract_section(llm_output, SECTION_PATTERNS["reflection_questions"])
    usage_boundaries = _extract_section(llm_output, SECTION_PATTERNS["usage_boundaries"])
    recommended_text = _extract_section(llm_output, SECTION_PATTERNS["recommended_knowledge"])

    if not creative_goal:
        creative_goal = "基于提供的作品，探索视觉美学表达，提升创作技巧"
    if not visual_observations:
        visual_observations = "视觉观察记录解析失败，请重试"
    if not key_learning:
        key_learning = "视觉构成与美学表达的关系"
    if not aesthetics_knowledge:
        aesthetics_knowledge = "知识讲解解析中..."
    if not usage_boundaries:
        usage_boundaries = "本反馈为教学参考，美学理解具有多元性，请结合个人创作意图综合判断。"

    strengths = _parse_list_items(strengths_text) or ["作品展现了真诚的创作探索"]
    multiple_perspectives = _parse_list_items(perspectives_text) or ["从视觉形式角度理解", "从情感表达角度理解", "从媒介特性角度理解"]
    revision_tasks = _parse_list_items(tasks_text) or ["继续观察作品，思考视觉元素之间的关系"]
    reflection_questions = _parse_list_items(questions_text) or ["你想通过作品表达什么？"]

    recommended_knowledge = _parse_recommended_knowledge(recommended_text, sources)

    return ArtDiagnosisOutput(
        creative_goal=creative_goal,
        visual_observations=visual_observations,
        strengths=strengths,
        key_learning=key_learning,
        aesthetics_knowledge=aesthetics_knowledge,
        multiple_perspectives=multiple_perspectives,
        revision_tasks=revision_tasks,
        reflection_questions=reflection_questions,
        usage_boundaries=usage_boundaries,
        sources=sources,
        recommended_knowledge=recommended_knowledge,
        session_id=session_id,
    )
