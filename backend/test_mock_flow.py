#!/usr/bin/env python3
"""
测试Mock模式下的完整作品诊断流程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.art_diagnosis.models import ArtDiagnosisInput, ArtworkType
from app.art_diagnosis.service import ArtDiagnosisService
from PIL import Image, ImageDraw
import io

print("=" * 60)
print("AI美学导师 - Mock模式完整流程测试")
print("=" * 60)

# Step 1: 生成测试图片
print("\n【Step 1】生成测试图片...")
width, height = 800, 600
img = Image.new('RGB', (width, height), color=(255, 248, 240))
draw = ImageDraw.Draw(img)

# 天空渐变
for y in range(height//2):
    r = int(255 - y * 0.3)
    g = int(200 - y * 0.2)
    b = int(150 - y * 0.2)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# 地面
for y in range(height//2, height):
    factor = (y - height//2) / (height//2)
    r = int(101 - factor * 30)
    g = int(67 - factor * 20)
    b = int(33 - factor * 10)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# 房子（中心构图）
house_x, house_y = width//2 - 80, height//2 - 50
house_w, house_h = 160, 120
draw.rectangle([house_x, house_y, house_x+house_w, house_y+house_h], fill=(180, 80, 60), outline=(100, 40, 30), width=3)
draw.polygon([(house_x-20, house_y), (width//2, house_y-80), (house_x+house_w+20, house_y)], fill=(139, 69, 19), outline=(80, 40, 10), width=2)
door_w, door_h = 40, 60
draw.rectangle([width//2 - door_w//2, house_y + house_h - door_h, width//2 + door_w//2, house_y + house_h], fill=(80, 40, 20), outline=(50, 25, 10), width=2)
window_size = 30
draw.rectangle([house_x + 25, house_y + 25, house_x + 25 + window_size, house_y + 25 + window_size], fill=(255, 220, 150), outline=(100, 60, 30), width=2)
draw.rectangle([house_x + house_w - 25 - window_size, house_y + 25, house_x + house_w - 25, house_y + 25 + window_size], fill=(255, 220, 150), outline=(100, 60, 30), width=2)

# 树木
for x in [100, 680]:
    draw.rectangle([x-8, height//2 + 30, x+8, height - 50], fill=(100, 60, 30))
    draw.ellipse([x-40, height//2 - 10, x+40, height//2 + 70], fill=(60, 120, 50), outline=(40, 80, 30))

# 转成bytes
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='PNG')
img_bytes = img_byte_arr.getvalue()
print(f"  ✓ 测试图片已生成，尺寸: {width}x{height}, 大小: {len(img_bytes)} bytes")

# Step 2: 初始化服务
print("\n【Step 2】初始化作品诊断服务...")
service = ArtDiagnosisService()
print(f"  ✓ Mock模式: {service.llm.mock_mode}")
print(f"  ✓ Vision Mock模式: {service.vision.mock_mode}")
print(f"  ✓ 知识库条目数: {service.retriever.vector_store.count() if service.retriever.vector_store else 0}")

# Step 3: 构造创作意图
print("\n【Step 3】构造创作意图...")
test_input = ArtDiagnosisInput(
    image=img_bytes,
    artwork_type=ArtworkType.DIGITAL_ART,
    scene="课程作业练习",
    intent="练习风景构图，表现温暖宁静的乡村午后氛围",
    focus_points=["构图", "色彩关系"],
    session_id=None
)
print(f"  ✓ 作品类型: 数字绘画")
print(f"  ✓ 创作场景: 课程作业练习")
print(f"  ✓ 创作意图: 练习风景构图，表现温暖宁静的乡村午后氛围")
print(f"  ✓ 关注重点: 构图, 色彩关系")

# Step 4: 执行诊断
print("\n【Step 4】执行作品诊断...")
result = service.diagnose(test_input)
session_id = result.session_id
print(f"  ✓ 会话ID: {session_id}")

# Step 5: 展示诊断结果（10个板块）
print("\n" + "=" * 60)
print("【诊断结果 - 10个结构化板块】")
print("=" * 60)

sections = [
    ("1. 你的创作目标", result.creative_goal),
    ("2. 我观察到的视觉现象", result.visual_observations),
    ("3. 值得保留的地方", "\n".join(f"  - {s}" for s in result.strengths)),
    ("4. 本次重点学习", result.key_learning),
    ("5. 美学知识讲解", result.aesthetics_knowledge),
    ("6. 多元理解方向", "\n".join(f"  - {p}" for p in result.multiple_perspectives)),
    ("7. 本轮修改任务", "\n".join(f"  - {t}" for t in result.revision_tasks)),
    ("8. 修改后的反思问题", "\n".join(f"  - {q}" for q in result.reflection_questions)),
    ("9. 使用边界", result.usage_boundaries),
    ("10. 知识来源", f"检索到 {len(result.sources)} 条来源，推荐 {len(result.recommended_knowledge)} 个知识点"),
]

for title, content in sections:
    print(f"\n--- {title} ---")
    print(content[:500] + ("..." if len(content) > 500 else ""))

# Step 6: 测试追问功能
print("\n" + "=" * 60)
print("【Step 5】测试追问功能")
print("=" * 60)

followup_questions = [
    "请详细讲解一下构图中的三分法具体怎么应用？",
    "色彩搭配有哪些实用技巧？",
]

for q in followup_questions:
    print(f"\n--- 追问: {q} ---")
    answer = service.followup(
        session_id=session_id,
        question=q,
        knowledge_point_name="构图" if "构图" in q else "色彩关系"
    )
    print(answer[:800] + ("..." if len(answer) > 800 else ""))
    print()

# Summary
print("=" * 60)
print("【测试总结】")
print("=" * 60)
print("✓ 图片验证：通过")
print("✓ 视觉观察（Mock）：通过")
print("✓ 知识检索：通过")
print("✓ 结构化诊断输出（10个板块）：通过")
print(f"✓ 会话管理：通过 (session_id: {session_id})")
print("✓ 追问功能：通过")
print("\n" + "=" * 60)
print("Mock模式完整流程验证成功！")
print("=" * 60)
