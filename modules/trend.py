"""
选题挖掘模块 (LLM via OpenRouter)
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def analyze_trends(niche: str) -> list:
    """
    根据赛道分析小红书热门选题
    
    Args:
        niche: 赛道/领域名称
    
    Returns:
        10 个热门选题方向的字符串列表
    """
    prompt = f"""你是一位资深的小红书数据分析师，精通平台算法和爆款内容规律。

请根据赛道「{niche}」，输出当前小红书最火的 10 个选题方向。

要求：
1. 选题要具体、可操作，不要太宽泛
2. 结合当下热点和用户痛点
3. 考虑小红书用户画像（年轻女性为主）
4. 选题要有爆款潜力

直接输出 10 个选题，每行一个，不要编号，不要其他解释。"""

    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.choices[0].message.content
    topics = [line.strip() for line in text.strip().split('\n') if line.strip()]
    return topics[:10]
