"""
选题挖掘模块 (火山引擎 Web Search 联网插件)
实时搜索互联网热点，获取热门内容详情和大纲结构
"""
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 火山引擎方舟客户端（支持联网搜索）
ark_client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv("ARK_API_KEY"),
)


def analyze_trends(niche: str) -> tuple[list, str]:
    """
    根据赛道分析小红书热门选题（基于实时联网搜索）
    返回热点详情 + 内容大纲，用于后续基于大纲生成笔记
    
    Args:
        niche: 赛道/领域名称
    
    Returns:
        (topics, source): 
        - topics: 热点详情列表，每个元素是 dict:
            {
                "title": "选题标题",
                "source": "来源平台",
                "summary": "热门内容摘要",
                "outline": ["大纲点1", "大纲点2", ...],
                "why_hot": "火爆原因"
            }
        - source: 数据来源标记 "websearch" | "fallback" | "error"
    """
    search_prompt = f"""请搜索小红书上关于「{niche}」的最新热门笔记和爆款内容。

你的任务是找到小红书上真正火爆的笔记，分析它们为什么火，并提取出内容大纲。

请输出 10 个小红书热门笔记，每个包含：
1. title: 选题标题（具体、有爆款潜力，20字以内）
2. source: 笔记类型（如：图文爆款、视频爆款、干货分享、情绪吐槽、好物分享）
3. summary: 这篇笔记在讲什么（50-100字摘要）
4. outline: 内容大纲结构（3-5个要点，每个要点15字以内）
5. why_hot: 为什么火（击中了什么情绪/痛点，30字以内）

必须严格输出以下 JSON 格式，不要输出任何其他内容：
[
    {{
        "title": "选题标题",
        "source": "图文爆款",
        "summary": "这篇笔记主要讲述...",
        "outline": ["引子：场景痛点", "核心观点1", "核心观点2", "金句收尾"],
        "why_hot": "击中了职场人的焦虑情绪"
    }}
]"""

    try:
        response = ark_client.responses.create(
            model="doubao-seed-1-6-250615",
            input=[{"role": "user", "content": search_prompt}],
            tools=[{"type": "web_search"}],
        )
        
        # 解析响应
        text = ""
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            text += content_item.text
        
        if not text and hasattr(response, 'choices'):
            text = response.choices[0].message.content
        
        if not text:
            text = str(response)
        
        # 解析 JSON
        topics = _parse_topics_json(text)
        if topics:
            return topics, "websearch"
        else:
            # JSON 解析失败，尝试降级
            print(f"[Trend Warning] JSON 解析失败，降级处理")
            return _fallback_analyze(niche)
        
    except Exception as e:
        print(f"[Trend Error] 火山引擎联网搜索失败: {e}")
        return _fallback_analyze(niche)


def _parse_topics_json(text: str) -> list:
    """解析 LLM 返回的 JSON 格式热点数据"""
    try:
        # 尝试提取 JSON 数组
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            json_str = json_match.group(0)
            topics = json.loads(json_str)
            
            # 验证数据结构
            valid_topics = []
            for t in topics:
                if isinstance(t, dict) and 'title' in t:
                    valid_topics.append({
                        "title": t.get("title", ""),
                        "source": t.get("source", "未知来源"),
                        "summary": t.get("summary", ""),
                        "outline": t.get("outline", []),
                        "why_hot": t.get("why_hot", "")
                    })
            return valid_topics[:10]
    except json.JSONDecodeError as e:
        print(f"[Trend Error] JSON 解析错误: {e}")
    return []


def _fallback_analyze(niche: str) -> tuple[list, str]:
    """
    降级方案：不使用联网搜索，直接让模型生成选题
    """
    try:
        response = ark_client.chat.completions.create(
            model="doubao-seed-1-6-250615",
            max_tokens=2048,
            messages=[{
                "role": "user", 
                "content": f"""你是一位资深的小红书数据分析师。

请根据赛道「{niche}」，基于你对小红书平台的了解，输出 10 个可能火爆的选题。

每个选题包含：
1. title: 选题标题（具体、有爆款潜力）
2. source: 内容类型（如：经验分享、情绪吐槽、干货教程）
3. summary: 内容方向描述（50-100字）
4. outline: 建议的内容大纲（3-5个要点）
5. why_hot: 为什么可能火（击中什么情绪/痛点）

必须严格输出 JSON 格式：
[
    {{
        "title": "选题标题",
        "source": "经验分享",
        "summary": "内容描述...",
        "outline": ["大纲点1", "大纲点2", "大纲点3"],
        "why_hot": "击中的情绪点"
    }}
]"""
            }]
        )
        
        text = response.choices[0].message.content
        topics = _parse_topics_json(text)
        
        if topics:
            return topics, "fallback"
        else:
            # 最终兜底
            return _create_fallback_topics(niche), "error"
        
    except Exception as e:
        print(f"[Trend Error] 降级方案也失败: {e}")
        return _create_fallback_topics(niche), "error"


def _create_fallback_topics(niche: str) -> list:
    """创建兜底的选题数据"""
    return [{
        "title": f"关于{niche}的热门话题",
        "source": "获取失败",
        "summary": "无法获取热点数据，请检查网络后重试",
        "outline": ["请重新搜索"],
        "why_hot": "—"
    }]
