from app.chat_tutor.models import DetectedIntent, ChatAttachment, AttachmentType


class IntentDetector:
    def __init__(self):
        self.art_keywords = [
            "画", "作品", "图片", "照片", "摄影", "绘画", "素描", "海报", "PPT",
            "构图", "色彩", "光影", "笔触", "创作", "修改", "诊断", "看看我的",
            "帮我看看", "这张图", "这幅画", "作品诊断", "美学分析", "视觉"
        ]
        self.paper_keywords = [
            "论文", "PDF", "文献", "文章", "解读", "理论", "概念", "观点",
            "论证", "页码", "作者", "研究", "帮我看一下这篇", "这篇论文",
            "文献解读", "学术", "美学理论"
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
        
        if intent == DetectedIntent.ART_DIAGNOSIS and not has_attachment:
            if any(kw in msg_lower for kw in ["图", "画", "作品", "照片"]):
                return True, "请上传作品图片，并说明创作意图或希望重点讨论的部分。"
            return True, "你可以上传作品图片、论文 PDF，或者直接提出一个美学问题。"
            
        if intent == DetectedIntent.PAPER_INTERPRET and not has_attachment:
            if any(kw in msg_lower for kw in ["论文", "文献", "pdf", "文章"]):
                return True, "请上传论文 PDF，并说明你的阅读目的或关注问题。"
            return True, "你可以上传作品图片、论文 PDF，或者直接提出一个美学问题。"
            
        return False, ""
