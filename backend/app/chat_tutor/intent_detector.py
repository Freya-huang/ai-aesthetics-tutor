from app.chat_tutor.models import DetectedIntent, ChatAttachment, AttachmentType


class IntentDetector:
    def __init__(self):
        self.art_keywords = [
            "画", "作品", "图片", "照片", "摄影", "绘画", "素描", "海报", "PPT",
            "构图", "色彩", "光影", "笔触", "创作", "修改", "诊断", "看看我的",
            "帮我看看", "这张图", "这幅画", "作品诊断", "美学分析", "视觉"
        ]
        self.paper_keywords = [
            "论文", "PDF", "文献", "文章", "观点",
            "论证", "页码", "作者", "研究", "帮我看一下这篇", "这篇论文",
            "文献解读", "学术", "美学理论"
        ]
        self.concept_learning_markers = [
            "双层解释法", "美学概念解读", "我想学习", "小白版", "专业版",
            "从类比到术语", "真正理解检查", "帮我理解", "解释这个概念",
        ]
        self.concept_terms = [
            "视觉中心", "构图", "对比", "视觉层级", "色彩关系", "明暗",
            "空间", "媒介", "意境", "气韵生动", "摹仿说", "模仿说",
            "崇高", "媒介即讯息", "机械复制", "人工智能主体性", "机器创造力",
            "作者与原创", "版权与伦理", "美学概念",
        ]
        self.learning_question_markers = [
            "什么是", "是什么意思", "有什么区别", "如何理解", "为什么", "学习", "讲解", "解释",
        ]
        self.followup_keywords = [
            "为什么", "怎么", "如何", "解释一下", "详细说说", "再讲", "追问",
            "刚才", "之前", "还有", "另外", "请问", "继续", "然后呢", "什么是",
            "为什么会", "能不能"
        ]

    def detect_from_message(self, message: str, attachments=None) -> DetectedIntent:
        msg_lower = message.lower() if message else ""
        
        if attachments:
            for att in attachments:
                if att.type == AttachmentType.IMAGE:
                    return DetectedIntent.ART_DIAGNOSIS
                elif att.type == AttachmentType.PDF:
                    return DetectedIntent.PAPER_INTERPRET

        if any(marker in msg_lower for marker in self.concept_learning_markers):
            return DetectedIntent.CONCEPT_LEARNING

        if (
            any(term in msg_lower for term in self.concept_terms)
            and any(marker in msg_lower for marker in self.learning_question_markers)
        ):
            return DetectedIntent.CONCEPT_LEARNING
        
        if any(kw in msg_lower for kw in self.paper_keywords):
            if any(kw in msg_lower for kw in self.art_keywords):
                pass
            else:
                return DetectedIntent.PAPER_INTERPRET
        
        if any(kw in msg_lower for kw in self.art_keywords):
            return DetectedIntent.ART_DIAGNOSIS
        
        if any(kw in msg_lower for kw in self.followup_keywords):
            return DetectedIntent.FOLLOWUP
        
        if len(msg_lower.strip()) < 10 and not attachments:
            return DetectedIntent.CHAT
        
        if ("上传" in msg_lower or "发" in msg_lower) and ("图" in msg_lower or "画" in msg_lower):
            return DetectedIntent.CLARIFICATION_NEEDED
        if ("上传" in msg_lower or "发" in msg_lower) and ("论文" in msg_lower or "pdf" in msg_lower or "文献" in msg_lower):
            return DetectedIntent.CLARIFICATION_NEEDED
            
        return DetectedIntent.CHAT

    def needs_more_info(self, intent: DetectedIntent, message: str, has_attachment: bool) -> tuple[bool, str]:
        msg_lower = message.lower() if message else ""

        if intent == DetectedIntent.CONCEPT_LEARNING:
            placeholders = ["【填写概念或问题】", "【请填写概念或问题】", "概念或问题：】"]
            if not message.strip() or any(item in message for item in placeholders):
                return True, "你想先理解哪个美学概念或问题？例如：意境、视觉中心、机器创造力或AI作者身份。"
            return False, ""
        
        if intent == DetectedIntent.ART_DIAGNOSIS and not has_attachment:
            if any(kw in msg_lower for kw in ["图", "画", "作品", "照片"]):
                return True, "请上传作品图片，并说明创作意图或希望重点讨论的部分。"
            return True, "你可以上传作品图片、论文 PDF，或者直接提出一个美学问题。"
            
        if intent == DetectedIntent.PAPER_INTERPRET and not has_attachment:
            if any(kw in msg_lower for kw in ["论文", "文献", "pdf", "文章"]):
                return True, "请上传论文 PDF，并说明你的阅读目的或关注问题。"
            return True, "你可以上传作品图片、论文 PDF，或者直接提出一个美学问题。"
            
        return False, ""
