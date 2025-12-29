"""
文案与设计模块 (LLM via OpenRouter)
"""
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any, Optional

from modules.monitor import log_api_call, log_generation
from modules.quality_checker import check_content_quality, format_quality_report

# 加载项目根目录的 .env 文件
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

# OpenRouter 客户端（延迟初始化）
_client = None

def get_openrouter_client():
    """延迟初始化 OpenRouter 客户端"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY 环境变量未设置，请在 .env 文件中配置")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client


def _fix_json_newlines(text: str) -> str:
    """修复 JSON 字符串值中的裸换行符（简化版，双引号由 Prompt 控制）"""
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


def _call_llm_and_parse(system_prompt: str, user_content: str, topic: str, persona: str, model_name: str = "deepseek/deepseek-chat", temperature: float = 0.8, log_result: bool = True) -> dict:
    """内部函数：调用 LLM 并解析 JSON 响应"""
    response = get_openrouter_client().chat.completions.create(
        model=model_name,
        max_tokens=8192,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    
    # 记录 API 调用
    usage = response.usage
    if usage:
        log_api_call(model_name, usage.prompt_tokens, usage.completion_tokens)
    
    text = response.choices[0].message.content
    
    # 提取 JSON（处理可能的 markdown 代码块）
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        text = json_match.group(1)
    
    # 移除所有代码块（如果 LLM 误输出了代码）
    # 保留 JSON 对象部分（以 { 开头）
    if not text.strip().startswith('{'):
        # 尝试找到第一个 { 开始的 JSON
        json_obj_match = re.search(r'\{[\s\S]*\}', text)
        if json_obj_match:
            text = json_obj_match.group(0)
    
    # 兜底：修复可能存在的裸换行符
    text = _fix_json_newlines(text)
    
    try:
        result = json.loads(text)
        # 记录生成历史（仅在最终结果时记录）
        if log_result:
            log_generation(
                topic=topic,
                persona=persona or "通用博主",
                titles=result.get("titles", []),
                content_preview=result.get("content", "")[:200]
            )
        return result
    except json.JSONDecodeError as e:
        print(f"\n{'='*60}")
        print(f"[Writer Error] JSON 解析失败")
        print(f"{'='*60}")
        print(f"错误详情: {e}")
        print(f"错误位置: 第 {e.lineno} 行，第 {e.colno} 列")
        print(f"\n完整响应内容（前500字符）:")
        print(f"{text[:500]}")
        print(f"\n完整响应内容（后200字符）:")
        print(f"{text[-200:]}")
        print(f"\n响应总长度: {len(text)} 字符")
        print(f"{'='*60}\n")
        # 抛出异常而不是返回空数据
        raise ValueError(f"LLM 返回格式错误，请检查日志。预览: {text[:200]}")


def load_few_shot_examples() -> str:
    """加载 Few-Shot 范文数据"""
    try:
        examples_path = _project_root / "data" / "examples" / "xiaohongshu_best_practices.json"
        if examples_path.exists():
            with open(examples_path, "r", encoding="utf-8") as f:
                examples = json.load(f)
                
            example_text = "\n【🌟 优质爆款范文参考】\n请仔细阅读以下范文，学习其语气、排版、emoji使用和结构：\n\n"
            for i, ex in enumerate(examples[:2]): # 取前两个作为示例
                example_text += f"--- 范文 {i+1} ({ex.get('type', '通用')}) ---\n"
                example_text += f"标题：{ex['title']}\n"
                example_text += f"正文：\n{ex['content']}\n"
                example_text += f"💡 亮点分析：{ex.get('analysis', '')}\n\n"
            return example_text
    except Exception as e:
        print(f"[Writer Warning] 加载范文失败: {e}")
    return ""


# ============================================================================
# 图文模式 - Chain of Thought 分步函数
# ============================================================================

def generate_outline_step(
    topic: str, 
    search_data: dict, 
    persona: str,
    model_name: str = "deepseek/deepseek-chat", 
    temperature: float = 0.7
) -> dict:
    """
    【Step 1】生成结构化大纲和标题
    """
    search_data = search_data or {}
    source = search_data.get('source', '未知来源')
    original_title = search_data.get('title', topic)
    why_hot = search_data.get('why_hot', '')
    summary = search_data.get('summary', '')
    raw_outline = search_data.get('outline', [])
    
    outline_text = ""
    if raw_outline and len(raw_outline) > 0:
        outline_text = json.dumps(raw_outline, indent=2, ensure_ascii=False)

    system_prompt = f"""你是内容策划专家，擅长分析热点话题并提炼结构化大纲。
你的任务是：基于热点数据，输出一份**逻辑清晰、角度独特**的文章大纲。

【你的身份】{persona or '深度内容博主'}

【大纲设计原则】
1. **3-5 个核心论点**：每个论点独立成章，形成递进或并列结构
2. **角度要独特**：不要复述原大纲，要基于火爆原因找到用户真正关心的切入点
3. **可扩展性**：每个论点必须能展开写 150-200 字

【标题设计原则】
1. 使用数字、疑问句、惊叹句等爆款技巧
2. 结合火爆原因，击中用户痛点
3. 5 个标题风格多样（干货型、情绪型、悬念型、对比型、故事型）

【输出格式】
严格输出 JSON：
{{
    "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
    "outline": [
        "论点1：简要描述（10-20字）",
        "论点2：简要描述",
        "论点3：简要描述"
    ]
}}

只输出 JSON，不要其他内容。"""

    user_content = f"""热门选题信息：
- 来源平台：{source}
- 原始标题：{original_title}
- 火爆原因：{why_hot}
- 核心摘要：{summary}
- 原始大纲（仅供参考，需要你重新提炼）：
{outline_text}

请分析以上信息，输出结构化大纲和 5 个爆款标题。"""

    print("[Writer] Step 1: 生成大纲和标题...")
    return _call_llm_and_parse(system_prompt, user_content, topic, persona, model_name, temperature, log_result=False)


def generate_content_step(
    topic: str,
    outline: list,
    titles: list,
    persona: str,
    search_data: dict = None,
    reference_text: str = None,
    model_name: str = "deepseek/deepseek-chat",
    temperature: float = 0.8
) -> dict:
    """
    【Step 2】基于大纲生成深度正文 (Few-Shot Enhanced)
    """
    search_data = search_data or {}
    why_hot = search_data.get('why_hot', '')
    summary = search_data.get('summary', '')
    
    outline_text = "\n".join([f"- {item}" for item in outline])
    titles_preview = titles[0] if titles else topic
    
    # 加载 Few-Shot 范文
    few_shot_examples = load_few_shot_examples()
    
    reference_section = ""
    if reference_text:
        reference_section = f"""
【参考内容】（仿写其风格）：
---
{reference_text}
---
"""

    system_prompt = f"""你是小红书{persona or '深度内容博主'}赛道的顶级博主，以"真诚分享、像朋友聊天"著称。

{few_shot_examples}

【🎯 核心任务】
将大纲扩展为一篇 **800+ 字** 的高质量正文，读起来像"一个真实的人在和朋友分享经验"，而不是"AI在总结知识点"。

【🚫 AI 味对照表 - 看到就改】
❌ AI 写法 → ✅ 真人写法

❌ "首先，我们需要了解..." → ✅ "说实话，我一开始也不懂这个..."
❌ "众所周知，职场中..." → ✅ "上周我同事被裁了，我才意识到..."  
❌ "值得一提的是..." → ✅ "对了，还有个坑我必须说一下..."
❌ "在沟通方面，我们应该..." → ✅ "每次跟老板汇报我都紧张，后来我发现..."
❌ "总而言之/综上所述" → ✅ "说了这么多，其实就一句话：..."
❌ "这对于我们来说非常重要" → ✅ "这点我真的吃过亏，当时..."
❌ "需要注意的是" → ✅ "千万别像我一样..."
❌ "很多人认为" → ✅ "我之前也这么以为，直到..."
❌ "进行深入分析" → ✅ "我琢磨了好几天，发现..."
❌ "提升自己的能力" → ✅ "我花了3个月死磕这个技能..."

【✨ 真人感写作公式】

**开头（必须二选一）：**
A. 场景代入："昨天发生了一件事，让我必须来说这个..."
B. 情绪炸裂："救命！我终于想明白了一件事..."

**中间（每个论点必须有）：**
- 一个具体的故事/场景（时间+地点+人物+细节）
- 一个反直觉的观点或踩坑经验
- 一个可执行的方法（话术/步骤/清单）

**结尾（必须二选一）：**
A. 真诚互动："你们遇到过类似的情况吗？评论区聊聊"
B. 金句升华："（一句有力量的话，不要鸡汤）"

【📝 细节要求】
1. **短句为主**：每句不超过20字，多用句号，少用逗号
2. **具体数字**：至少3处（如：3年、5个方法、涨薪40%）
3. **情绪词**：每200字至少1个（绝了/离谱/崩溃/太真实了/救命）
4. **内心戏**：用括号补充内心独白，如：（当时我真的想翻白眼）
5. **段落短**：每段最多3行，关键观点独立成段

【🎨 排版规范】
- 每段之间空一行
- 重点句子可以加粗
- 适当使用 emoji 作为情绪标点（💡📌🔥✨）
- 使用 1️⃣ 2️⃣ 3️⃣ 或 · 作为列表符号

【输出格式】
严格输出 JSON：
{{
    "content": "不少于800字的深度正文内容，分段并包含emoji，用\\n表示换行，对话用中文引号「」"
}}

**重要**：对话和引用必须使用中文引号「」，禁止使用英文双引号 "
只输出 JSON，不要其他内容。"""

    user_content = f"""【文章标题方向】{titles_preview}

【火爆原因】{why_hot}

【核心摘要】{summary}

【文章大纲】（必须严格遵循）
{outline_text}

{reference_section}
请基于以上大纲，按照【深度扩充法则】，将这篇笔记扩写至 800 字以上。
哪怕某个论点只有一句话，你也要通过举例、讲故事、列步骤，将其丰富成一段有血有肉的内容。"""

    print("[Writer] Step 2: 基于大纲生成深度正文...")
    return _call_llm_and_parse(system_prompt, user_content, topic, persona, model_name, temperature, log_result=False)


def generate_visuals_step(
    topic: str,
    content: str,
    model_name: str = "deepseek/deepseek-chat",
    temperature: float = 0.7,
    global_style: Optional[str] = None
) -> dict:
    """
    【Step 3】基于正文生成配图设计 (Style Consistent)
    
    新增功能：先定义全局美术风格，确保配图一致性。
    """
    # 截取正文核心部分（避免 token 过长）
    content_preview = content[:3000] if len(content) > 3000 else content

    # 如果没有指定全局风格，让 LLM 自己生成一个
    style_instruction = ""
    if global_style:
        style_instruction = f"【全局美术风格】必须严格遵循此风格：{global_style}"
    else:
        style_instruction = "【全局美术风格】请先定义一个统一的视觉风格（Art Direction），例如：'Warm cinematic lighting with soft pastel tones' 或 'Cyberpunk neon aesthetic with high contrast'，并确保所有配图都遵循此风格。"

    system_prompt = f"""你是**资深艺术总监 (Art Director)**，专精于为社交媒体内容设计配图。
你现在要阅读一篇完整的小红书文章，并为其设计 3-5 张配图。

【核心任务】
1. 设定或遵循统一的**全局美术风格 (Art Direction)**，确保所有图片看起来是一套图。
2. 阅读正文，提取 3-5 个**视觉化关键场景**
3. 为每个场景设计 FLUX 优化的生图提示词

{style_instruction}

【配图设计原则】
- 第一张图（Index 1）必须是最吸睛的「钩子图」，构图干净、视觉冲击力强
- 每张图独立表达一个视觉主题，与正文段落呼应
- 配图要能**脱离文字独立传达信息**
- **一致性**：所有图片的光影、色调、滤镜风格必须保持高度一致

【prompt 字段要求（FLUX 优化）】
1. **必须使用英文**
2. **必须是描述性自然语言句子**，不是标签堆砌
3. **结构**：[Global Style] + Subject + Action/Context + Lighting/Atmosphere
4. 示例：
   - ✅ "Cinematic warm lighting, A young professional woman working in a cozy coffee shop, sunlight streaming through the window, soft bokeh"
   - ✅ "Cinematic warm lighting, Close-up of hands typing on a laptop keyboard, coffee cup on table, cozy atmosphere"
   - ❌ "girl, office, working, natural light, anime" （标签堆砌，禁止）

【description 字段要求】
- 中文描述画面主体、场景、氛围
- 说明该图在文章中承担的角色（如：开场图、转折点、总结图）

【sentiment 字段要求】
- 图片风格情感，如："职场日常"、"温馨治愈"、"励志奋斗"

【输出格式】
严格输出 JSON：
{{
    "global_style": "简短的英文风格定义，如 'Cinematic lighting, warm tones, 35mm film grain'",
    "image_designs": [
        {{
            "index": 1,
            "description": "钩子封面图：职场女性站在现代办公室窗边，阳光洒落，构图干净",
            "sentiment": "职场日常",
            "prompt": "Cinematic lighting, warm tones, 35mm film grain, A young professional woman standing by large office windows, morning sunlight streaming in, modern minimalist workspace, confident atmosphere"
        }},
        {{
            "index": 2,
            "description": "配图描述：该图在文章中的作用",
            "sentiment": "情感基调",
            "prompt": "Cinematic lighting, warm tones, 35mm film grain, Subject + Action/Context + Lighting/Atmosphere"
        }}
    ]
}}

只输出 JSON，不要其他内容。"""

    user_content = f"""【文章选题】{topic}

【完整正文】
{content_preview}

请基于以上正文内容，设计 3-5 张配图。
第一张必须是「钩子图」，视觉冲击力最强。
确保所有图片风格统一！"""

    print("[Writer] Step 3: 基于正文生成配图设计...")
    return _call_llm_and_parse(system_prompt, user_content, topic, None, model_name, temperature, log_result=False)


def generate_image_note(topic: str, persona: str = None, reference_text: str = None, model_name: str = "deepseek/deepseek-chat", search_data: dict = None, temperature: float = 0.8) -> dict:
    """
    【图文模式】生成小红书图文笔记（长文案 + 配图提示词）
    
    采用 Chain of Thought 三步流水线，分步生成以提高内容质量：
    1. generate_outline_step: 生成结构化大纲 + 5 个标题
    2. generate_content_step: 基于大纲深度扩展正文（800+ 字）
    3. generate_visuals_step: 基于正文设计配图（3-5 张）
    """
    print(f"\n{'='*60}")
    print(f"[Writer] 🚀 图文模式 - Chain of Thought 流水线启动")
    print(f"[Writer] 选题: {topic}")
    print(f"{'='*60}")
    
    # ========== Step 1: 生成大纲和标题 ==========
    step1_result = generate_outline_step(
        topic=topic,
        search_data=search_data,
        persona=persona,
        model_name=model_name,
        temperature=0.7  # 大纲生成用较低温度，保持结构稳定
    )
    
    titles = step1_result.get("titles", [])
    outline = step1_result.get("outline", [])
    
    print(f"[Writer] ✅ Step 1 完成 - 生成 {len(titles)} 个标题, {len(outline)} 个大纲要点")
    for i, point in enumerate(outline, 1):
        print(f"         {i}. {point}")
    
    # ========== Step 2: 基于大纲生成正文 ==========
    step2_result = generate_content_step(
        topic=topic,
        outline=outline,
        titles=titles,
        persona=persona,
        search_data=search_data,
        reference_text=reference_text,
        model_name=model_name,
        temperature=temperature  # 正文生成用用户指定的温度
    )
    
    content = step2_result.get("content", "")
    content_len = len(content)
    
    print(f"[Writer] ✅ Step 2 完成 - 正文 {content_len} 字")
    
    # ========== Step 3: 基于正文生成配图 ==========
    step3_result = generate_visuals_step(
        topic=topic,
        content=content,
        model_name=model_name,
        temperature=0.7  # 配图设计用较低温度
    )
    
    image_designs = step3_result.get("image_designs", [])
    
    print(f"[Writer] ✅ Step 3 完成 - 生成 {len(image_designs)} 张配图设计")
    
    # ========== 合并最终结果 ==========
    final_result = {
        "titles": titles,
        "content": content,
        "image_designs": image_designs
    }
    
    # 记录生成历史
    log_generation(
        topic=topic,
        persona=persona or "通用博主",
        titles=titles,
        content_preview=content[:200]
    )
    
    print(f"\n{'='*60}")
    print(f"[Writer] 🎉 图文模式流水线完成")
    print(f"[Writer] 标题数: {len(titles)}, 正文字数: {content_len}, 配图数: {len(image_designs)}")
    print(f"{'='*60}\n")
    
    return final_result


def generate_video_script(topic: str, persona: str = None, reference_text: str = None, model_name: str = "deepseek/deepseek-chat", temperature: float = 0.8) -> dict:
    """
    【视频模式】生成深度视频脚本（口播文稿 + 分镜画面 + 情感分析）
    
    采用"中视频"策略：时长不限，以把逻辑讲清楚为最高优先级。
    使用高频分镜防止视觉疲劳，每段解说词 20-40 字。
    
    Args:
        topic: 选题/主题
        persona: 博主人设风格描述
        reference_text: 参考内容（用于仿写）
    
    Returns:
        {
            'titles': [...],           # 5个备选标题
            'content': '...',          # 视频简介（200-300字）
            'visual_scenes': [         # 分镜列表（20-50个，高频分镜）
                {
                    'scene_index': 1,
                    'narration': '该分镜对应的口播解说词（20-40字）',
                    'description': '中文画面描述',
                    'sentiment': '情感基调',
                    'prompt': '纯画面描述（不含风格词）'
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

    system_prompt = f"""你是**顶级纪录片导演**，同时精通 AI 绘图提示词工程和情感分析。
你的核心能力是将"文案"翻译成"视觉画面"，并准确判断每段内容的情感基调。
你的风格是：{persona or '通用博主'}

【核心任务】
基于用户给定的选题创作一个**深度解析视频脚本**，包含视频简介和高频分镜脚本。
**时长不限**，以把逻辑讲清楚、把干货讲透彻为**最高优先级**。

【深度视频创作原则】
1. **宁多勿长**：不要让一张图片停留超过 8 秒。如果解说词很长，必须切分成多个画面来表达。
2. **逻辑可视化**：当解说词在讲"原理"时，画面要画"流程图"或"示意图"；当讲"案例"时，画面要画"场景图"。
3. **内容为王**：不需要为了凑时间说废话，但必须把核心干货的 Why 和 How 解释得连小学生都能听懂。

【视频简介要求】
1. 字数目标：200-300汉字
2. 内容：视频主题概述，说明观众能学到什么
3. 风格：有深度、有吸引力、带emoji

【分镜脚本要求 - 高频分镜策略】
你需要像**电影导演**一样，把内容拆解为 **20-50 个高频分镜**。
核心原则：讲完一个知识点或换气时，必须切换下一个分镜。

1. narration（口播解说词）- **高频切换原则**：
   - 每段控制在 **20-40 个汉字**（约 5-8 秒）
   - 必须**完全口语化**，像博主在面对面聊天
   - 多用连接词："大家看"、"注意这里"、"之所以这么做"、"换句话说"、"举个例子"
   - 所有分镜的 narration 连起来，是一段完整流畅的视频解说词
   
   **错误示范**：一个分镜包含"这里有三个步骤，第一步是...第二步是...第三步是..."（❌ 太长，应该拆成多个分镜）
   **正确示范**：
   - 分镜1："这里主要有三个核心步骤，我一个一个来讲。"
   - 分镜2："首先是第一步，我们需要找到设置入口。"
   - 分镜3："大家注意看这个按钮，点进去之后..."
   
2. description（画面描述）：
   - 中文描述画面主体、场景、氛围
   
3. sentiment（情感基调）- **必须从以下5个选项中选择一个**：
   - "可爱治愈"：温馨、软萌、治愈系内容
   - "严肃深度"：深刻、专业、知识型内容
   - "日常生活"：平常、自然、slice of life
   - "热血励志"：激励、奋斗、正能量
   - "悲伤低沉"：伤感、感慨、怀旧
   
4. prompt（生图提示词）- **中文纯净画面描述**：
   - **必须使用中文**描述画面（豆包模型对中文理解最好）
   - 只描述画面内容：主体 + 动作 + 场景 + 光影
   - **严禁出现任何文字元素**：不要描写招牌、对话框、字幕、logo、水印
   - **禁止添加风格词**（如 动漫风格, 4k, 高清 等），风格由画家模块添加
   - 画面要干净、构图高级

【视觉翻译公式 - 必须严格遵守】
根据 narration 内容类型，设计中文纯净画面描述的 prompt：

1. **具体事物**（如：多吃苹果）
   -> 画具象物体：一颗红苹果特写，表面带水珠，柔和自然光
   
2. **抽象概念**（如：职场压力大、坚持长期主义）
   -> 画具象隐喻：登山者在雪山顶峰插旗，逆光剪影，金色晚霞
   -> 或：疲惫的上班族双手抱头，电脑屏幕蓝光照亮面庞，深夜办公室
   
3. **流程步骤**（如：分三步完成）
   -> 画流程图示：三个圆形图标排列，箭头连接，简洁示意图风格
   
4. **情绪表达**（如：太开心了、好激动）
   -> 画表情特写：年轻女孩灿烂笑容，阳光洒落，温暖氛围

**错误示范**：prompt "一个人在思考，画面有'加油'文字"（❌ 不要有文字元素）
**正确示范**：prompt "马拉松选手冲过终点线，日出背景，胜利表情，暖色调"（✅ 中文纯净画面）

【输出格式】
必须严格按照以下 JSON 结构输出，不要输出任何其他内容：

**重要**：对话和引用必须使用中文引号「」，禁止使用英文双引号 "

{{
    "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
    "content": "200-300字视频简介，带emoji，对话用中文引号「」",
    "visual_scenes": [
        {{
            "scene_index": 1,
            "narration": "20-40字口播词（口语化，像聊天）",
            "description": "中文画面描述：主体、场景、感觉",
            "sentiment": "可爱治愈",
            "prompt": "中文纯净画面描述（无文字元素、无风格词）"
        }},
        {{
            "scene_index": 2,
            "narration": "20-40字口播词",
            "description": "中文画面描述",
            "sentiment": "严肃深度",
            "prompt": "中文具象化画面描述"
        }}
    ]
}}

【写作规则】
1. 标题要有爆款潜力，使用数字、疑问句、惊叹句等吸睛技巧
2. visual_scenes 数组包含 **20-50 个元素**，根据内容复杂度灵活调整
3. JSON 字符串中必须用 \\n 表示换行，不要使用实际换行符
4. 分镜的 narration 连起来要有逻辑性，像一个完整的深度讲解视频
5. 每个 prompt 必须是中文，描述纯净画面，**绝对不能有任何文字/招牌/logo**
6. sentiment 必须从5个选项中选择，根据该段 narration 的情感氛围判断
7. **内容深度优先**：宁可多几个分镜把事情讲清楚，也不要为了短而省略关键信息"""

    user_content = f"""选题：{topic}
{reference_section}
请创作深度解析视频脚本（时长不限，把逻辑讲清楚为第一优先级）。只输出 JSON，不要其他内容。"""

    return _call_llm_and_parse(system_prompt, user_content, topic, persona, model_name, temperature)


def generate_wechat_article(topic: str, persona: str = None, reference_text: str = None, model_name: str = "deepseek/deepseek-chat", search_data: dict = None, temperature: float = 0.8) -> dict:
    """
    【公众号模式】生成深度长文 + 架构图/示意图
    
    Args:
        topic: 选题/主题
        persona: 技术博主人设风格描述
        reference_text: 参考内容（用于仿写）
        model_name: OpenRouter 模型 ID
        search_data: websearch 返回的完整热点数据
        temperature: LLM 温度参数
    
    Returns:
        {
            'titles': [...],           # 5个备选标题
            'content': '...',          # 深度长文（不限字数，建议2000-5000字）
            'diagrams': [              # 架构图/示意图设计（2-4张）
                {
                    'index': 1,
                    'title': '架构图标题',
                    'description': '中文描述该图表达的技术架构',
                    'diagram_type': 'architecture' | 'flow' | 'comparison',
                    'prompt': '生图提示词（极客美学）'
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

    # 解析 search_data
    search_data = search_data or {}
    source = search_data.get('source', '未知来源')
    original_title = search_data.get('title', topic)
    why_hot = search_data.get('why_hot', '')
    summary = search_data.get('summary', '')
    outline = search_data.get('outline', [])
    
    # 格式化大纲
    outline_text = ""
    if outline and len(outline) > 0:
        outline_text = json.dumps(outline, indent=2, ensure_ascii=False)

    system_prompt = f"""你是{persona or '技术博主'}，专注于深度技术内容创作。
你现在要为微信公众号创作一篇**深度技术长文**，字数不限，以把技术讲透为第一优先级。

【核心要求】
1. **深度优先**：必须符合'金字塔原理'，结构为：背景/痛点 → 现有方案局限 → 深度原理拆解 → 架构设计/代码思路 → 商业/未来价值
2. **工程视角**：不仅讲算法原理，还要讲部署、成本、延迟优化、工程取舍
3. **对比分析**：必须有 Pros & Cons 对比，或技术方案 A vs B 的横向对比
4. **通俗化表达**：用类比和日常例子解释复杂概念（如：用'传话游戏'解释Transformer的Self-Attention机制）

【文章结构要求】
1. **标题**：硬核且吸引人，必须包含技术关键词。示例：《RAG已死？深度解析Long Context的工程边界》
2. **正文**：
   - 开头：抛出技术痛点或反直觉观点
   - 中间：分层递进拆解（Why → What → How）
   - 结尾：总结技术价值和未来展望
   - **代码处理**：可以用文字描述代码逻辑，不要输出实际代码块
3. **排版**：使用小标题（二级标题 ##）分段，关键概念**加粗**

【架构图设计要求】
必须设计 2-4 张架构图/示意图，用于可视化技术架构。

每张图需包含：
1. title：图表标题（如："RAG架构对比"）
2. description：中文描述该图表达的技术概念、组件关系
3. diagram_type：图表类型
   - "architecture"：系统架构图（组件、模块、数据流）
   - "flow"：流程图（步骤、决策树、时序）
   - "comparison"：对比图（方案A vs B，优缺点对比）
4. prompt：生图提示词（极客美学风格）
   - 必须包含：cyberpunk style, dark background, neon accents
   - 描述具体的技术组件、连接关系、数据流向
   - 示例："cyberpunk system architecture, RAG pipeline with vector database, embedding model, and LLM, glowing data connections, dark blue background, neon highlights"

【输出格式 - 严格遵守】
**重要**：必须且只能输出纯 JSON 对象，不要用 ```json 包裹，不要输出任何代码块。

**JSON 规范**：对话和引用必须使用中文引号「」，禁止使用英文双引号 "
示例：❌ "老板说："加油""  ✅ "老板说：「加油」"

输出格式：
{{
    "titles": ["标题1（必须包含技术关键词）", "标题2", "标题3", "标题4", "标题5"],
    "content": "深度技术长文，不限字数，建议2000-5000字，用\\n表示换行，**关键概念**用markdown加粗，对话用中文引号「」。可以在文字中描述代码逻辑，但不要输出实际的 ```python 代码块。",
    "diagrams": [
        {{
            "index": 1,
            "title": "架构图标题",
            "description": "中文描述该图表达的技术架构和组件关系",
            "diagram_type": "architecture",
            "prompt": "cyberpunk style system architecture, 具体组件描述, dark background, neon accents"
        }}
    ]
}}

**错误示范**（绝对禁止）：
```json
{{...}}
```
或者输出代码块：
```python
代码...
```

**正确示范**：
直接输出 {{"titles": [...], "content": "...", "diagrams": [...]}}

【写作规则】
1. 标题要有技术深度和吸引力，避免标题党
2. 正文必须深度详实，**建议2000-5000字**，把技术讲透
3. diagrams 数组包含 2-4 个元素
4. 每个 diagram 的 prompt 必须符合极客美学：深色背景、霓虹色、赛博朋克风格
5. JSON 字符串中必须用 \\n 表示换行，不要使用实际换行符
6. **绝对禁止**：不要输出 ```json、```python 等代码块，直接输出纯 JSON 对象"""

    user_content = f"""当前技术选题信息如下：
- 来源平台：{source}
- 原始标题：{original_title}
- 火爆原因：{why_hot}
- 核心摘要：{summary}
- 参考大纲：
{outline_text}

{reference_section}
请创作一篇微信公众号深度技术文章，把这个技术话题讲透彻。

**重要提醒**：
1. 直接输出 JSON 对象，不要用 ```json 包裹
2. 不要输出任何代码块（```python、```yaml 等）
3. 代码逻辑用文字描述即可
4. 只输出纯 JSON，格式如：{{"titles": [...], "content": "...", "diagrams": [...]}}"""

    return _call_llm_and_parse(system_prompt, user_content, topic, persona, model_name, temperature)


def generate_note_package(topic: str, persona: str = None, reference_text: str = None, mode: str = "image", model_name: str = "deepseek/deepseek-chat", search_data: dict = None, temperature: float = 0.8) -> dict:
    """
    统一入口：根据模式生成内容
    
    Args:
        topic: 选题/主题
        persona: 博主人设风格描述
        reference_text: 参考内容
        mode: "image"（图文模式）、"video"（视频模式）或 "wechat"（公众号模式）
        model_name: OpenRouter 模型 ID
        search_data: websearch 返回的完整热点数据
    
    Returns:
        对应模式的内容结构
    """
    if mode == "video":
        return generate_video_script(topic, persona, reference_text, model_name, temperature)
    elif mode == "wechat":
        return generate_wechat_article(topic, persona, reference_text, model_name, search_data, temperature)
    else:
        return generate_image_note(topic, persona, reference_text, model_name, search_data, temperature)


def generate_note_package_with_retry(
    topic: str,
    persona: str = None,
    reference_text: str = None,
    mode: str = "image",
    model_name: str = "deepseek/deepseek-chat",
    search_data: dict = None,
    temperature: float = 0.8,
    max_retries: int = 2,
    quality_threshold: int = 70
) -> dict:
    """
    带质量检测的生成函数
    
    如果生成的内容质量不达标，会自动重试（降低 temperature 提升稳定性）
    
    Args:
        max_retries: 最大重试次数
        quality_threshold: 质量分数阈值（0-100）
        其他参数同 generate_note_package
    
    Returns:
        生成结果（同 generate_note_package）
    """
    current_temp = temperature
    
    for attempt in range(max_retries + 1):
        print(f"[Writer] 生成尝试 {attempt + 1}/{max_retries + 1}，temperature={current_temp:.2f}")
        
        result = generate_note_package(
            topic=topic,
            persona=persona,
            reference_text=reference_text,
            mode=mode,
            model_name=model_name,
            search_data=search_data,
            temperature=current_temp
        )
        
        # 只检测图文模式的正文质量（视频和公众号模式跳过）
        if mode == "image" and result.get("content"):
            quality = check_content_quality(result["content"])
            print(f"[Quality] 评分: {quality['score']}/100")
            
            if quality["is_acceptable"]:
                print("[Quality] ✅ 质量合格")
                return result
            
            if attempt < max_retries:
                print(f"[Quality] ❌ 质量不达标 ({quality['score']}分 < {quality_threshold}分)")
                print(f"[Quality] 问题: {', '.join(quality['issues'])}")
                print(f"[Quality] 准备重试...")
                # 降低 temperature 提升稳定性
                current_temp = max(0.5, current_temp - 0.15)
            else:
                print(f"[Quality] ⚠️ 已达最大重试次数，返回当前结果")
                print(format_quality_report(quality))
        else:
            # 视频模式或无内容，直接返回
            return result
    
    return result
