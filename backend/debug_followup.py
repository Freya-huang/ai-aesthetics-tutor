#!/usr/bin/env python3
"""调试追问prompt格式"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.art_diagnosis.models import ArtDiagnosisInput, ArtworkType
from app.art_diagnosis.service import ArtDiagnosisService
from app.art_diagnosis.prompts import DiagnosisPrompts
from PIL import Image, ImageDraw
import io

# 生成测试图片
width, height = 800, 600
img = Image.new('RGB', (width, height), color=(255, 248, 240))
draw = ImageDraw.Draw(img)
# 简单画点东西
draw.rectangle([300, 200, 500, 400], fill=(180, 80, 60))
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='PNG')
img_bytes = img_byte_arr.getvalue()

# 初始化服务
service = ArtDiagnosisService()

# 先做一次诊断
test_input = ArtDiagnosisInput(
    image=img_bytes,
    artwork_type=ArtworkType.DIGITAL_ART,
    intent="测试构图",
    focus_points=["构图"],
)
result = service.diagnose(test_input)
session_id = result.session_id
print(f"诊断完成，session_id: {session_id}")
print()

# 现在模拟followup，看看生成的prompt是什么
from app.llm.session import session_manager

history_msgs = session_manager.get_messages_for_llm(session_id, limit=10)
history_str = "\n\n".join([f"[{m['role']}]: {m['content'][:500]}" for m in history_msgs])

prev_diagnosis = ""
for m in reversed(history_msgs):
    if "[诊断反馈]" in m["content"]:
        prev_diagnosis = m["content"]
        break

question = "请详细讲解一下构图中的三分法具体怎么应用？"

prompt = DiagnosisPrompts.FOLLOWUP_FEEDBACK.format(
    previous_diagnosis=prev_diagnosis[:2000],
    conversation_history=history_str,
    question=question,
    knowledge_context="",
)

print("=" * 80)
print("FOLLOWUP PROMPT CONTENT:")
print("=" * 80)
print(prompt)
print("=" * 80)
print()
print(f"Looking for '【学习者当前问题】'...")
if "【学习者当前问题】" in prompt:
    idx = prompt.find("【学习者当前问题】")
    print(f"Found at position {idx}")
    print(f"Content after marker: {repr(prompt[idx:idx+200])}")
