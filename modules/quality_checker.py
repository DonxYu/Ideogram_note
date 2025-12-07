"""
文案质量检测模块
检测 AI 生成文案的质量，识别 AI 套话、缺乏具体性等问题
"""
import re


# AI 套话黑名单
AI_CLICHES = [
    "众所周知", "不得不说", "可以说是", "值得一提的是",
    "在.*?方面", "进行.*?操作", "相关的",
    "总而言之", "综上所述", "由此可见",
    "首先.*?其次.*?最后", "第一.*?第二.*?第三",
]

# 强情绪词白名单（应该出现）
EMOTION_WORDS = [
    "绝了", "太爱了", "崩溃", "yyds", "救命", "爱了爱了",
    "真的", "超级", "巨", "疯了", "炸了", "绝绝子",
    "！", "？", "🔥", "💯", "✨", "❤️", "😭", "🥺"
]


def check_content_quality(content: str) -> dict:
    """
    检测文案质量，返回评分和问题诊断
    
    Args:
        content: 待检测的文案内容
    
    Returns:
        {
            "score": 0-100,
            "is_acceptable": bool,  # 分数 >= 70 为合格
            "issues": ["过于AI", "缺乏具体案例"],
            "suggestions": ["增加个人经历", "添加具体数字"],
            "details": {
                "ai_cliche_count": 数量,
                "number_count": 数量,
                "emotion_count": 数量,
                "length": 字数
            }
        }
    """
    score = 100
    issues = []
    suggestions = []
    
    # 1. 检测 AI 套话（每出现一次扣 10 分）
    ai_cliche_count = 0
    for cliche in AI_CLICHES:
        matches = re.findall(cliche, content)
        ai_cliche_count += len(matches)
    
    if ai_cliche_count > 0:
        score -= min(ai_cliche_count * 10, 40)  # 最多扣 40 分
        issues.append(f"检测到 {ai_cliche_count} 处 AI 套话")
        suggestions.append("避免使用'众所周知'、'不得不说'等机械表达")
    
    # 2. 检测具体数字（至少应有 2 个）
    number_pattern = r'\d+\.?\d*[万千百十]?[年月日天小时分钟秒次个人块元]|\d+%'
    numbers = re.findall(number_pattern, content)
    number_count = len(numbers)
    
    if number_count < 2:
        score -= 15
        issues.append(f"具体数字不足（仅 {number_count} 处）")
        suggestions.append("增加具体数字：如'涨粉 3000'、'连续 15 天'等")
    
    # 3. 检测个人经历标记（"我"、"我朋友"、"我同事"等）
    personal_patterns = [
        r'我[的是有在]', r'我朋友', r'我同事', r'我见过',
        r'上次.*?时', r'那天', r'当时',
    ]
    personal_count = sum(len(re.findall(p, content)) for p in personal_patterns)
    
    if personal_count < 1:
        score -= 15
        issues.append("缺乏个人经历")
        suggestions.append("加入个人故事：'我有个朋友...'、'上次我...'")
    
    # 4. 检测强情绪表达（至少 3 处）
    emotion_count = sum(content.count(word) for word in EMOTION_WORDS)
    
    if emotion_count < 3:
        score -= 10
        issues.append(f"情绪表达不足（仅 {emotion_count} 处）")
        suggestions.append("增加强情绪词：'绝了'、'太爱了'、感叹号、emoji 等")
    
    # 5. 检测反问句（至少 1 处）
    question_count = content.count("？") + content.count("吗？") + content.count("呢？")
    if question_count < 1:
        score -= 10
        issues.append("缺乏互动性反问")
        suggestions.append("加入反问句：'你知道为什么吗？'、'是不是很离谱？'")
    
    # 6. 检测字数（图文模式要求 800+ 字）
    length = len(content)
    if length < 800:
        score -= 20
        issues.append(f"字数不足（仅 {length} 字，要求 800+ 字）")
        suggestions.append("深化内容：每个要点展开至少 150-200 字")
    
    # 确保分数在 0-100 范围内
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "is_acceptable": score >= 70,
        "issues": issues,
        "suggestions": suggestions,
        "details": {
            "ai_cliche_count": ai_cliche_count,
            "number_count": number_count,
            "personal_count": personal_count,
            "emotion_count": emotion_count,
            "question_count": question_count,
            "length": length,
        }
    }


def format_quality_report(quality: dict) -> str:
    """格式化质量报告为可读文本"""
    report = f"【质量评分】{quality['score']}/100\n"
    
    if quality['is_acceptable']:
        report += "✅ 质量合格\n"
    else:
        report += "❌ 质量不达标\n"
    
    if quality['issues']:
        report += "\n【问题诊断】\n"
        for issue in quality['issues']:
            report += f"  - {issue}\n"
    
    if quality['suggestions']:
        report += "\n【优化建议】\n"
        for suggestion in quality['suggestions']:
            report += f"  - {suggestion}\n"
    
    return report

