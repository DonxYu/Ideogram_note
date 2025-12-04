"""
文案与设计模块 (LLM via OpenRouter)
"""
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

from modules.monitor import log_api_call, log_generation

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
    生成小红书笔记文案与视觉分镜脚本
    
    Args:
        topic: 选题/主题
        persona: 博主人设风格描述或完整 System Prompt
        reference_text: 参考内容（用于仿写）
    
    Returns:
        {
            'titles': [...],           # 5个备选标题
            'content': '...',          # 深度正文（800字左右）
            'visual_script': [         # 视觉分镜脚本（3-6张）
                {
                    'scene_type': '封面 / 流程图 / 细节展示',
                    'description_cn': '中文画面描述',
                    'prompt_en': 'Midjourney/Flux 英文提示词'
                },
                ...
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

    system_prompt = f"""你是小红书深度内容专家，同时也是一位专业的 AI 绘图提示词工程师。
你的风格是：{persona or '通用博主'}

【核心任务】
基于用户给定的选题创作一篇**深度长文案**（约800汉字），并设计**视觉分镜脚本**（3-6张图）。

【正文写作要求】
1. 字数目标：800汉字左右，拒绝泛泛而谈
2. 必须包含：具体案例、可操作步骤、或真实体验细节
3. 结构清晰：开篇hook → 核心内容（分点阐述）→ 金句收尾
4. 风格：口语化、有情绪价值、适当使用emoji
5. 分段：每段用\\n\\n分隔，重点句子可单独成段

【视觉分镜要求】
1. 根据正文内容自动规划图片数量（3-6张）
2. 必须包含：封面图 + 内页插图（流程图/细节展示/对比图等）
3. 封面要有强视觉冲击力，能在信息流中抓住眼球
4. 内页图要配合正文的关键段落，辅助信息传达

【英文提示词要求】
prompt_en 必须是专业的 Midjourney/Flux 提示词，包含：
- 主体描述（subject）
- 光影效果（lighting: soft light, golden hour, cinematic lighting...）
- 构图方式（composition: close-up, wide shot, flat lay...）
- 风格标签（style: minimalist, aesthetic, editorial...）
- 画面氛围（mood: cozy, energetic, luxurious...）
- 技术参数建议（如 --ar 3:4 --v 6）

【输出格式】
必须严格按照以下 JSON 结构输出，不要输出任何其他内容：
{{
    "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
    "content": "约800字的深度正文内容，分段并包含emoji，用\\n表示换行",
    "visual_script": [
        {{
            "scene_type": "封面",
            "description_cn": "中文画面描述：主体是什么、场景环境、想传达的感觉",
            "prompt_en": "详细英文提示词，包含主体、光影、构图、风格、氛围、参数"
        }},
        {{
            "scene_type": "流程图 / 细节展示 / 对比图 / 场景图",
            "description_cn": "中文画面描述",
            "prompt_en": "详细英文提示词"
        }}
    ]
}}

【写作规则】
1. 标题要有爆款潜力，使用数字、疑问句、惊叹句等吸睛技巧
2. 正文必须深度详实，不能敷衍了事
3. visual_script 数组包含 3-6 个元素
4. JSON 字符串中必须用 \\n 表示换行，不要使用实际换行符"""

    user_content = f"""选题：{topic}
{reference_section}
请创作深度长文案并设计视觉分镜脚本。只输出 JSON，不要其他内容。"""

    response = client.chat.completions.create(
        model="x-ai/grok-4.1-fast",
        max_tokens=4096,  # 增加 token 上限以支持长文案
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    
    # 记录 API 调用
    usage = response.usage
    if usage:
        log_api_call("x-ai/grok-4.1-fast", usage.prompt_tokens, usage.completion_tokens)
    
    text = response.choices[0].message.content
    
    # 提取 JSON（处理可能的 markdown 代码块）
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        text = json_match.group(1)
    
    # 兜底：修复可能存在的裸换行符
    text = _fix_json_newlines(text)
    
    try:
        result = json.loads(text)
        # 记录生成历史
        log_generation(
            topic=topic,
            persona=persona or "通用博主",
            titles=result.get("titles", []),
            content_preview=result.get("content", "")[:200]
        )
        return result
    except json.JSONDecodeError as e:
        print(f"[Writer Error] JSON 解析失败: {e}")
        print(f"[Writer Debug] 响应内容: {text[:500]}...")
        return {"titles": [], "content": "", "visual_script": []}
