import time
import random
from typing import List, Dict, Optional, Any
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
import httpx
from app.config import settings


class BaseClient:
    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.mock_mode = not api_key or api_key.strip() == ""
        self.client = None
        if not self.mock_mode:
            self.client = OpenAI(
                base_url=api_base,
                api_key=api_key,
                http_client=httpx.Client(
                    timeout=60.0,
                    follow_redirects=True,
                ),
            )

    def _mock_response(self, messages: List[Dict[str, Any]]) -> str:
        raise NotImplementedError

    def _call_api(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        raise NotImplementedError

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        if self.mock_mode:
            return self._mock_response(messages)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                return self._call_api(
                    messages, temperature=temperature, max_tokens=max_tokens, **kwargs
                )
            except (APIError, APIConnectionError, RateLimitError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2**attempt) + random.uniform(0, 0.5)
                    time.sleep(sleep_time)
                else:
                    raise
        raise last_error


class LLMClient(BaseClient):
    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        super().__init__(
            api_base=api_base or settings.llm_api_base,
            api_key=api_key if api_key is not None else settings.llm_api_key,
            model=model or settings.llm_model,
        )

    def _detect_task_type(self, messages: List[Dict[str, Any]]) -> str:
        full_text = ""
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                full_text += content + "\n"
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        full_text += part.get("text", "") + "\n"
        followup_markers = ["【之前的诊断记录】", "【之前的解读记录】", "【学习者当前问题】", "FOLLOWUP_FEEDBACK", "conversation_history", "previous_diagnosis", "previous_paper"]
        is_followup = any(marker in full_text for marker in followup_markers)
        if is_followup:
            if "论文" in full_text or "PDF" in full_text or "解读" in full_text or "===LITERATURE_INFO" in full_text:
                return "paper_followup"
            return "art_followup"
        if "===CREATIVE_GOAL_START" in full_text:
            return "diagnosis"
        if "===LITERATURE_INFO_START" in full_text or "===ONE_SENTENCE_SUMMARY_START" in full_text:
            return "paper"
        return "general"

    def _mock_diagnosis_response(self) -> str:
        return """===CREATIVE_GOAL_START===
探索视觉美学表达，通过构图、色彩和明暗关系的处理来传达创作意图，提升作品的视觉表现力与艺术感染力。
===CREATIVE_GOAL_END===

===VISUAL_OBSERVATIONS_START===
- 画面主体位于画面中央区域，占据约60%的画面空间
- 构图采用中心构图方式，视觉重心居中
- 色彩以暖色调为主，搭配少量冷色形成对比关系
- 整体明暗适中，主体部分较亮，背景部分较暗
- 画面呈现出前景、中景、背景三个层次
- 推测为数字绘画作品，笔触较为柔和
===VISUAL_OBSERVATIONS_END===

===STRENGTHS_START===
- 作品展现了清晰的视觉焦点，主体突出明确
- 色彩搭配有基本的冷暖对比意识
- 构图层次分明，具有一定的空间深度表现
- 明暗关系处理基本到位，主体轮廓清晰
===STRENGTHS_END===

===KEY_LEARNING_START===
本次诊断建议聚焦"构图"这一核心美学概念。构图是视觉艺术中组织画面元素的基本原则，它决定了观众的视线流动路径和视觉体验。从作品中可以观察到中心构图的运用，这是最基础也最有效的构图方式之一。理解构图原理有助于创作者有意识地引导观众的注意力，强化作品的表达效果。
===KEY_LEARNING_END===

===AESTHETICS_KNOWLEDGE_START===
构图（Composition）是视觉艺术中将各种视觉元素按照一定原则组织起来的方法。核心原则包括：1）视觉中心：确定画面中最引人注目的位置；2）平衡：通过元素的大小、色彩、明暗分布达到视觉均衡；3）对比：利用差异（大小、明暗、色彩）创造视觉张力；4）节奏：通过元素的重复或变化创造视觉韵律。在中国传统美学中，构图被称为"章法"或"布局"，强调"虚实相生"、"疏密有致"的辩证关系。
===AESTHETICS_KNOWLEDGE_END===

===MULTIPLE_PERSPECTIVES_START===
- 从形式分析角度：关注画面中点、线、面的构成关系，色彩的和谐与对比，以及视觉平衡的建立
- 从情感表达角度：思考作品传达的情绪氛围，色彩和构图如何影响观者的情感反应
- 从媒介特性角度：考虑数字媒介带来的创作可能性，如层次叠加、色彩调整的灵活性
===MULTIPLE_PERSPECTIVES_END===

===REVISION_TASKS_START===
- 尝试三分法构图：将画面主体移至三分线交点位置，观察视觉效果的变化，理解"非中心"构图的表现力
- 强化明暗对比：在主体边缘增加明暗过渡层次，增强画面的立体感和空间深度
- 添加视觉引导线：利用画面中的线条元素（如边缘、方向）引导观众视线流向主体
===REVISION_TASKS_END===

===REFLECTION_QUESTIONS_START===
- 你最想让观众第一眼看到画面中的哪个部分？目前的构图是否有效实现了这一点？
- 如果改变色调（如从暖调改为冷调），作品传达的情感会有什么不同？
- 画面中的留白（负空间）是否起到了衬托主体的作用？
===REFLECTION_QUESTIONS_END===

===USAGE_BOUNDARIES_START===
本反馈基于视觉观察和美学知识的教学参考，不是对作品价值的唯一评判标准。美学理解具有多元性，不同的审美传统和个人视角会产生不同的解读。建议结合个人创作意图综合判断，选择性地采纳建议进行修改。当前处于Mock开发模式，返回的是模拟结构化数据。
===USAGE_BOUNDARIES_END===

===RECOMMENDED_KNOWLEDGE_START===
构图|||VIS-002|||构图是组织画面元素的核心原则，与本作品直接相关
视觉中心|||VIS-001|||理解视觉重心设置有助于提升作品表达效果
色彩关系|||VIS-005|||色彩搭配是影响作品氛围的关键因素
===RECOMMENDED_KNOWLEDGE_END==="""

    def _mock_paper_response(self) -> str:
        return """===ONE_SENTENCE_SUMMARY_START===
当前文本以当代艺术现象为入口，界定审美经验、媒介与语境等概念，并为后续讨论技术如何改变艺术生产和接受方式建立问题框架[第1页]。【Mock模式模拟数据】
===ONE_SENTENCE_SUMMARY_END===

===CORE_QUESTIONS_START===
- 审美判断的普遍性与文化特殊性之间是什么关系？[第2页]
- 媒介技术如何改变艺术的生产与接受方式？[第4页]
- 传统美学范畴在当代艺术语境中是否仍然有效？[第7页]
===CORE_QUESTIONS_END===

===CORE_VIEWPOINTS_START===
- 审美经验并非脱离语境的纯粹个人感受，而与文化和观看条件相关[第2页]。
- 媒介不仅承载作品，也参与构成作品的表达方式[第4页]。
- 传统美学概念需要结合当代艺术实践重新检验其解释范围[第7页]。
===CORE_VIEWPOINTS_END===

===KEY_CONCEPTS_START===
审美经验|||指主体在与艺术作品相遇时产生的感知与情感体验|||第2页|||"审美经验是艺术研究的核心对象"
媒介|||艺术表达所依托的物质载体和技术手段|||第4页|||"媒介不仅是形式，更是内容的构成要素"
语境|||艺术作品产生和被接受的社会文化背景|||第6页|||"脱离语境的审美判断是不完整的"
===KEY_CONCEPTS_END===

===ARGUMENT_PROCESS_START===
- 首先从当代艺术现象切入并提出研究问题[第1-2页]。
- 随后界定审美经验、媒介与语境三个概念，搭建分析框架[第3-5页]。
- 再通过具体案例检验这一框架的解释力[第6-8页]。
- 最后总结已呈现的发现并提出后续研究方向[第9-10页]。
===ARGUMENT_PROCESS_END===

===CONTRIBUTIONS_LIMITATIONS_START===
论文的主要贡献在于：1）构建了一个整合性的审美经验分析框架[第3页]；2）将媒介维度系统引入美学分析[第5页]。局限性在于案例选取范围较窄，主要集中在视觉艺术领域[第9页]。建议未来研究可以拓展到音乐、文学等其他艺术门类。【Mock模式数据】
===CONTRIBUTIONS_LIMITATIONS_END===

===COURSE_CREATION_CONNECTIONS_START===
- 可联系“媒介即讯息”，理解创作工具如何参与作品意义的形成[第4页][来源ID：THE-006]。
- 可用于比较传统媒介与生成式AI在创作控制、选择和接受方式上的差异[第4页]。
===COURSE_CREATION_CONNECTIONS_END===

===RECOMMENDED_READING_START===
论文后续章节|||论文后续章节|||继续核对作者如何展开创作机制与评价标准的完整论证
意境|||THE-001|||意境是中国古典美学的核心范畴，与论文讨论直接相关
媒介即讯息|||THE-006|||麦克卢汉的媒介理论为理解技术与艺术关系提供框架
===RECOMMENDED_READING_END===

===NEXT_REFLECTION_TASK_START===
请选择一件你熟悉的数字或AI艺术作品，判断媒介在其中只是承载内容，还是实际改变了作品的表达方式；至少引用本文一个概念说明理由。
===NEXT_REFLECTION_TASK_END===

===PAGE_CITATIONS_START===
第1页|||提出核心研究问题
第2页|||界定审美经验概念
第3-5页|||构建理论框架
第6-8页|||案例分析
第9-10页|||结论与展望
===PAGE_CITATIONS_END==="""

    def _mock_followup_response(self, messages: List[Dict[str, Any]]) -> str:
        full_context = ""
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                full_context += content + "\n"
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        full_context += part.get("text", "") + "\n"

        question = ""
        if "【学习者当前问题】" in full_context:
            parts = full_context.split("【学习者当前问题】")
            if len(parts) > 1:
                after_q = parts[1]
                end_markers = ["【相关知识参考】", "【之前的诊断记录】", "【对话历史】", "请根据上下文回答"]
                end_pos = len(after_q)
                for marker in end_markers:
                    pos = after_q.find(marker)
                    if pos != -1 and pos < end_pos:
                        end_pos = pos
                question = after_q[:end_pos].strip()

        if not question:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    c = msg.get("content", "")
                    if isinstance(c, str) and len(c) < 500 and "【" not in c:
                        question = c
                        break

        question_lower = question.lower() if question else ""

        if "构图" in question or "三分法" in question:
            return (
                f"【Mock模式 - 追问回复】\n\n"
                f"关于构图中的三分法，这是一个非常实用的构图原则：\n\n"
                f"**什么是三分法**\n"
                f"将画面用两条水平线和两条垂直线平均分成九个相等的区域，形成'井'字形网格。"
                f"四条线的四个交点就是'视觉兴趣点'，把主体放在这些交点或线上，画面会更有活力。\n\n"
                f"**具体应用方法**\n"
                f"1. 地平线放置：风景摄影中，地平线通常放在上三分之一或下三分之一线，而非正中间\n"
                f"2. 主体位置：人物眼睛、静物主体等关键元素放在交点位置\n"
                f"3. 视觉流向：利用三分线引导观众视线在画面中流动\n\n"
                f"**为什么有效**\n"
                f"三分法避免了中心构图的呆板感，同时保持视觉平衡。研究表明，人眼自然会被这些交点位置吸引。\n\n"
                f"**练习建议**\n"
                f"你可以打开手机相机的网格线，尝试拍摄时将主体放在交点位置，对比中心构图的效果差异。\n\n"
                f"【提示】当前处于Mock开发模式，配置真实API后将获得结合您具体作品的个性化指导。"
            )
        elif "色彩" in question:
            return (
                f"【Mock模式 - 追问回复】\n\n"
                f"关于色彩关系，这是视觉美学的核心要素之一：\n\n"
                f"**色彩三要素**\n"
                f"- 色相：色彩的相貌（红、橙、黄、绿等）\n"
                f"- 明度：色彩的明亮程度\n"
                f"- 饱和度：色彩的纯净鲜艳程度\n\n"
                f"**常用配色关系**\n"
                f"1. 同类色：色相相同，明度/饱和度不同，效果和谐统一\n"
                f"2. 邻近色：色环上相邻的颜色（如红-橙、蓝-紫），既有变化又协调\n"
                f"3. 对比色：色环上相隔120度左右，产生强烈视觉张力\n"
                f"4. 互补色：色环上相隔180度（如红-绿、蓝-橙），对比最强烈\n\n"
                f"结合您的作品（暖色调乡村风景），建议：\n"
                f"- 可以尝试在暖调为主的基础上，在阴影部分加入少量冷色（蓝紫）作为对比\n"
                f"- 注意色彩饱和度的节奏变化，避免所有颜色都一样鲜艳\n\n"
                f"配置真实API后，我可以结合您的具体作品分析色彩运用并给出修改建议。"
            )
        elif "明暗" in question or "光影" in question:
            return (
                f"【Mock模式 - 追问回复】\n\n"
                f"明暗关系（Chiaroscuro）是塑造体积感和空间感的关键：\n\n"
                f"**明暗五调子**\n"
                f"- 高光：物体受光最亮的部分\n"
                f"- 中间调：物体受光侧的灰色层次\n"
                f"- 明暗交界线：物体受光与背光的分界线\n"
                f"- 反光：物体暗部受到环境反射的部分\n"
                f"- 投影：物体投下的阴影\n\n"
                f"在真实API模式下，我可以分析您作品中明暗处理的具体问题。"
            )
        else:
            return (
                f"【Mock模式 - 追问回复】\n\n"
                f"感谢您的提问：「{question[:100] if question else '您的问题'}」\n\n"
                f"这是一个很好的美学思考方向。\n\n"
                f"在Mock开发模式下，我提供通用回答框架：\n"
                f"1. 这个问题涉及视觉美学的重要概念\n"
                f"2. 可以从形式分析、情感表达、媒介特性三个角度思考\n"
                f"3. 建议结合您的具体作品观察实际效果\n\n"
                f"配置真实LLM API Key后，系统将：\n"
                f"- 结合您之前的诊断记录\n"
                f"- 检索相关美学知识库内容\n"
                f"- 给出针对您作品的具体分析和建议\n\n"
                f"当前Mock模式仅用于验证流程，所有回答均为模拟数据。"
            )

    def _mock_response(self, messages: List[Dict[str, Any]]) -> str:
        task_type = self._detect_task_type(messages)
        if task_type == "diagnosis":
            return self._mock_diagnosis_response()
        elif task_type == "paper":
            return self._mock_paper_response()
        elif task_type in ("art_followup", "paper_followup"):
            return self._mock_followup_response(messages)
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                if isinstance(last_user_msg, list):
                    for part in last_user_msg:
                        if part.get("type") == "text":
                            last_user_msg = part.get("text", "")
                            break
                break
        return (
            f"【Mock模式】这是对您问题的模拟回答。\n\n"
            f"当前未配置真实API Key，处于开发模式。"
        )

    def _call_api(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            params["max_tokens"] = max_tokens
        params.update(kwargs)
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content


class VisionClient(BaseClient):
    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        super().__init__(
            api_base=api_base or settings.vision_api_base,
            api_key=api_key if api_key is not None else settings.vision_api_key,
            model=model or settings.vision_model,
        )

    def _mock_response(self, messages: List[Dict[str, Any]]) -> str:
        full_text = ""
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        full_text += part.get("text", "") + "\n"
            elif isinstance(content, str):
                full_text += content + "\n"

        if "IMAGE_OBSERVATION" in full_text or "page_number" in full_text:
            import re
            page_match = re.search(r'页码[：:]\s*(\d+)|page_number[=:]\s*(\d+)', full_text)
            img_id_match = re.search(r'image_id[=:]\s*(\S+)', full_text)
            page_num = 1
            img_suffix = "0"
            if page_match:
                page_num = int(page_match.group(1) or page_match.group(2) or 1)
            if img_id_match:
                img_id = img_id_match.group(1)
                if '_' in img_id:
                    parts = img_id.split('_')
                    img_suffix = parts[-1] if parts else "0"
            
            descriptions = [
                f"论文第{page_num}页包含一张学术示意图，展示核心理论框架的结构关系。",
                f"论文第{page_num}页包含一张数据图表，呈现研究结果的统计分析。",
                f"论文第{page_num}页包含一张案例图片，用于辅助说明理论应用。",
                f"论文第{page_num}页包含一张对比表格，展示不同概念之间的异同。",
                f"论文第{page_num}页包含一张流程图，说明研究方法或论证步骤。",
                f"论文第{page_num}页包含一张历史图片，作为研究背景的视觉佐证。",
            ]
            observations = [
                f"图片类型为学术示意图，位于页面中部区域。图中使用方框和带箭头的连线表示概念之间的逻辑关系，标注清晰，排版规整。该图用于直观展示论文的核心理论模型。",
                f"图片类型为数据可视化图表，包含坐标轴、数据曲线和图例。图表采用黑白或灰度配色，数据趋势清晰可见。用于支撑论文的实证分析部分。",
                f"图片类型为案例插图，展示具体艺术作品或视觉现象。图片配有说明文字，与正文论述紧密相关，用于帮助读者理解抽象理论。",
                f"图片类型为对比分析表格，多行多列布局，清晰呈现不同维度的比较内容。表格边框简洁，重点内容可能有加粗或底色标注。",
                f"图片类型为研究流程图，使用标准流程图符号（矩形、菱形、箭头）表示步骤和判断节点。流程方向清晰，从左到右或从上到下展开。",
                f"图片类型为历史资料图片，黑白或早期彩色照片风格，可能包含历史人物、作品或场景。图片有图注说明来源和内容，用于提供历史语境。",
            ]
            
            idx = (page_num + int(img_suffix) if img_suffix.isdigit() else 0) % len(descriptions)
            
            return f"""===IMAGE_DESCRIPTION_START===
{descriptions[idx]}
===IMAGE_DESCRIPTION_END===

===IMAGE_OBSERVATION_START===
{observations[idx]}
===IMAGE_OBSERVATION_END==="""

        return """【画面主体】
画面主体位于画面中央偏上区域，为一个主要的视觉对象，占据画面约40%-50%的空间比例。

【构图安排】
画面采用近似中心构图的方式，视觉重心位于画面几何中心偏上位置。存在由边缘向中心汇聚的隐形引导线。前景、中景、背景层次清晰可辨。

【色彩运用】
画面主要色彩为暖色系（橙、棕、黄），辅以冷色（蓝、灰）作为对比。色彩饱和度中等，色调偏向暖调。明暗对比区域形成了基本的色彩节奏。

【明暗关系】
画面整体亮度适中偏亮。光源方向大致来自左上方，主体正面受光较多，右侧和下方有自然阴影。明暗对比程度中等，明暗过渡较为柔和。

【空间表现】
画面具有一定的三维空间深度感。通过近大远小和明暗变化表现空间层次。透视方式近似焦点透视。正负形关系基本平衡。

【媒介技法】
推测为数字绘画或摄影作品。如果是绘画，笔触表现较为平滑柔和；如果是摄影，焦点清晰，景深适中。画面质感表现细腻。

【Mock模式说明】当前未配置真实Vision API Key，返回模拟视觉观察结果。"""

    def _build_image_message_content(
        self,
        text: str,
        image_base64: str,
        image_type: str = "jpeg",
    ) -> List[Dict[str, Any]]:
        return [
            {"type": "text", "text": text},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_type};base64,{image_base64}",
                    "detail": "high",
                },
            },
        ]

    def analyze_image(
        self,
        prompt: str,
        image_base64: str,
        image_type: str = "jpeg",
        temperature: float = 0.3,
        max_tokens: Optional[int] = 1024,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        messages = []
        if history:
            messages.extend(history)
        messages.append(
            {
                "role": "user",
                "content": self._build_image_message_content(
                    prompt, image_base64, image_type
                ),
            }
        )
        return self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _call_api(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            params["max_tokens"] = max_tokens
        params.update(kwargs)
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content
