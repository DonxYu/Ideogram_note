"""
文案与设计模块 (LLM via OpenRouter)
"""
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def _fix_json_newlines(text: str) -> str:
    """修复 JSON 字符串值中的裸换行符"""
    result = []
    in_string = False
    escape = False
    for char in text:
        if escape:
            result.append(char)
            escape = False
        elif char == '\\':
            result.append(char)
            escape = True
        elif char == '"':
            result.append(char)
            in_string = not in_string
        elif char == '\n' and in_string:
            result.append('\\n')
        else:
            result.append(char)
    return ''.join(result)


def generate_note_package(topic: str, persona: str = None, reference_text: str = None) -> dict:
    """
    生成小红书笔记文案与配图设计方案
    
    Args:
        topic: 选题/主题
        persona: 博主人设风格描述或完整 System Prompt
        reference_text: 参考内容（用于仿写）
    
    Returns:
        {
            'titles': [...],           # 5个备选标题
            'content': '...',          # 正文（带emoji、分段）
            'images_design': [         # 恰好2张图片的设计方案
                {
                    'type': 'cover',
                    'main_text': '封面核心中文大标题(8字内)',
                    'sub_text': '封面中文副标题(15字内)',
                    'visual_style': '英文画面风格描述'
                },
                {
                    'type': 'content_image',
                    'main_text': '文中关键中文金句(20字内)',
                    'visual_style': '与封面风格统一的英文画面描述'
                }
            ]
        }
    """
    reference_section = ""
    if reference_text:
        reference_section = f"""
参考内容（请仿写其结构和风格）：
---
{reference_text}
---
"""

    system_prompt = f"""你是小红书爆款内容专家，同时也是一位资深平面设计师。
你的风格是：{persona or '通用博主'}

【核心任务】
基于用户给定的选题创作一篇小红书笔记，并为笔记设计**恰好两张**图片的视觉方案。

【图片设计要求】
1. 封面图 (cover)：必须包含一个吸引眼球的中文大标题（8字内）和一个副标题（15字内）
2. 配图 (content_image)：必须包含一句核心中文金句（20字内），与正文呼应

【输出格式】
必须严格按照以下 JSON 结构输出，不要输出任何其他内容：
{{
    "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
    "content": "笔记正文内容，分段并包含emoji，用\\n表示换行",
    "images_design": [
        {{
            "type": "cover",
            "main_text": "封面核心中文大标题(8字内)",
            "sub_text": "封面中文副标题(15字内)",
            "visual_style": "英文画面风格描述，例如: cinematic lighting, high-end office view, soft gradient background"
        }},
        {{
            "type": "content_image",
            "main_text": "文中出现的关键中文金句(20字内)",
            "visual_style": "与封面风格统一的英文画面描述"
        }}
    ]
}}

【写作规则】
1. 标题要有爆款潜力，使用数字、疑问句、惊叹句等吸睛技巧
2. 正文要口语化、有情绪价值、适当使用emoji
3. visual_style 必须是英文，描述具体的视觉风格和氛围
4. images_design 数组必须恰好包含2个元素
5. JSON 字符串中必须用 \\n 表示换行，不要使用实际换行符"""

    user_content = f"""选题：{topic}
{reference_section}
请创作笔记并设计配图方案。只输出 JSON，不要其他内容。"""

    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        max_tokens=2048,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    
    text = response.choices[0].message.content
    
    # 提取 JSON（处理可能的 markdown 代码块）
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        text = json_match.group(1)
    
    # 兜底：修复可能存在的裸换行符
    text = _fix_json_newlines(text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[Writer Error] JSON 解析失败: {e}")
        print(f"[Writer Debug] 响应内容: {text[:500]}...")
        return {"titles": [], "content": "", "images_design": []}
