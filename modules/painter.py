"""
生图模块 (Replicate + 火山引擎 Seedream + Google Gemini Imagen 3)
支持多种模式：
- 视频模式：使用 Replicate 或豆包批量生成分镜图
- 图文模式：主图用 Gemini Imagen 3 高质量生成，配图用豆包
支持并发生成：ThreadPoolExecutor 加速批量处理
支持主题命名：文件按主题组织
"""
import os
import time
from pathlib import Path
from typing import Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import replicate
import requests
from modules.storage import upload_to_oss, upload_to_oss_by_topic
from modules.utils import sanitize_filename, get_unique_dir

load_dotenv()

# 默认输出目录
DEFAULT_OUTPUT_DIR = Path("output/images")
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ========== 二次元风格库（英文版，用于 Replicate）==========

ANIME_STYLES_EN = {
    "可爱治愈": "anime style, chibi, pastel colors, soft lighting, Ghibli inspired, cute and wholesome, highly detailed, 4k",
    "严肃深度": "anime style, seinen manga aesthetic, dark atmosphere, dramatic shadows, muted colors, serious expression, sharp lines, detailed background",
    "日常生活": "anime style, slice of life, natural lighting, detailed urban or home setting, warm colors, Kyoto Animation style",
    "热血励志": "anime style, shonen jump style, dynamic pose, intense effects, bright and vivid colors, determined expression, speed lines",
    "悲伤低沉": "anime style, melancholic atmosphere, rain, cold colors, lonely character, emotional, tearful, shallow depth of field"
}

BASE_NEGATIVE_EN = "low quality, ugly, deformed, bad anatomy, extra fingers, watermark, text, blurry, disfigured, malformed limbs, extra limbs, missing arms, missing legs, fused fingers, too many fingers, long neck"

DEFAULT_STYLE_EN = "anime style, high quality, detailed, vibrant colors, professional illustration"

# ========== 二次元风格库（中文版，用于火山引擎豆包）==========

ANIME_STYLES_CN = {
    "可爱治愈": "二次元动漫风格，Q版可爱，粉嫩柔和色调，柔光效果，吉卜力风格，治愈系，精细绘制，高清画质",
    "严肃深度": "二次元动漫风格，青年漫画美学，暗色氛围，戏剧性阴影，沉稳色调，严肃表情，锐利线条，精细背景",
    "日常生活": "二次元动漫风格，日常番风格，自然光照，都市或家居场景，温暖色调，京阿尼风格，生活气息",
    "热血励志": "二次元动漫风格，少年漫画风格，动感姿势，强烈特效，明亮鲜艳色彩，坚定表情，速度线",
    "悲伤低沉": "二次元动漫风格，忧郁氛围，雨天，冷色调，孤独角色，情感充沛，泪眼，浅景深"
}

NEGATIVE_PROMPT_CN = "文字，字母，拼音，水印，logo，签名，用户名，错误，低质量，模糊，变形，多余手指，解剖错误，畸形"

DEFAULT_STYLE_CN = "二次元动漫风格，高质量，精细绘制，鲜艳色彩，专业插画"

# 兼容旧代码
ANIME_STYLES = ANIME_STYLES_EN
BASE_NEGATIVE = BASE_NEGATIVE_EN
DEFAULT_STYLE = DEFAULT_STYLE_EN


# ========== Prompt 组装 ==========

def _build_anime_prompt(scene: dict, provider: str = "replicate") -> Tuple[str, str]:
    """
    根据场景的 sentiment 和 provider 组装风格化 Prompt
    
    Args:
        scene: 分镜字典，包含 prompt 和可选的 sentiment
        provider: "replicate" 使用英文，"volcengine" 使用中文
    
    Returns:
        (final_prompt, negative_prompt)
    """
    base_prompt = scene.get('prompt', '')
    sentiment = scene.get('sentiment', '')
    
    if provider == "volcengine":
        # 火山引擎豆包：使用中文风格库
        style_modifiers = ANIME_STYLES_CN.get(sentiment, DEFAULT_STYLE_CN)
        negative_prompt = NEGATIVE_PROMPT_CN
    else:
        # Replicate：使用英文风格库
        style_modifiers = ANIME_STYLES_EN.get(sentiment, DEFAULT_STYLE_EN)
        negative_prompt = BASE_NEGATIVE_EN
    
    # 组装最终 Prompt
    final_prompt = f"{style_modifiers}，{base_prompt}" if provider == "volcengine" else f"{style_modifiers}, {base_prompt}"
    
    return final_prompt, negative_prompt


# ========== 单张图片生成（核心函数） ==========

def _generate_single_anime(scene: dict, index: int, anime_model: str = "anything-v4", output_dir: Path = None, topic: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 Replicate 二次元模型生成单张图片
    
    Args:
        scene: 分镜字典，包含 prompt 和可选的 sentiment
        index: 场景索引
        anime_model: "anything-v4" 或 "flux-anime"
        output_dir: 输出目录（为空则使用默认）
        topic: 主题名称（用于文件命名）
    
    Returns:
        (本地路径, 错误信息)
    """
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    try:
        # 组装英文风格化 Prompt（Replicate 模型）
        prompt, negative_prompt = _build_anime_prompt(scene, provider="replicate")
        
        if not prompt:
            return None, "prompt 为空"
        
        sentiment = scene.get('sentiment', '默认')
        print(f"[Anime] 场景 {index+1} ({sentiment}) 生成中...")
        print(f"[Anime] Prompt: {prompt[:100]}...")
        
        if anime_model == "flux-anime":
            # Flux Dev Anime 模型（不指定版本，使用最新）
            output = replicate.run(
                "lucataco/flux-dev-anime",
                input={
                    "prompt": prompt,
                    "aspect_ratio": "3:4",
                    "output_format": "webp",
                    "output_quality": 90,
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                }
            )
        else:
            # Anything V4.0 模型
            output = replicate.run(
                "cjwbw/anything-v4.0",
                input={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": 512,
                    "height": 768,
                    "num_inference_steps": 25,
                    "guidance_scale": 7,
                    "scheduler": "DPMSolverMultistep",
                }
            )
        
        # 处理输出
        if isinstance(output, list):
            image_url = output[0] if output else None
        else:
            image_url = str(output) if output else None
        
        if not image_url:
            return None, "模型未返回图片"
        
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        image_data = resp.content
        
        # 文件命名：主题_scene_01.ext
        ext = "webp" if anime_model == "flux-anime" else "png"
        safe_topic = sanitize_filename(topic) if topic else ""
        filename = f"{safe_topic}_scene_{index+1:02d}.{ext}" if safe_topic else f"scene_{index+1:02d}.{ext}"
        local_path = str(output_dir / filename)
        
        with open(local_path, "wb") as f:
            f.write(image_data)
        
        # 上传到 OSS（按主题分类）
        oss_url = None
        if topic:
            oss_url = upload_to_oss_by_topic(image_data, topic, filename, "images")
        
        print(f"[Anime] 场景 {index+1} 完成: {local_path}")
        # 优先返回 OSS URL，否则返回本地路径
        return oss_url or local_path, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Anime Error] 场景 {index+1} 失败: {error_msg}")
        return None, error_msg


def _generate_single_volcengine(scene: dict, index: int, output_dir: Path = None, topic: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    使用火山引擎豆包生成单张图片（中文 Prompt + 纯净画面）
    
    Args:
        scene: 分镜字典
        index: 场景索引
        output_dir: 输出目录
        topic: 主题名称
    
    Returns:
        (本地路径, 错误信息)
    """
    from openai import OpenAI
    
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    try:
        ark_api_key = os.getenv("ARK_API_KEY")
        if not ark_api_key:
            return None, "缺少 ARK_API_KEY"
        
        # 组装中文风格化 Prompt
        prompt, negative_prompt = _build_anime_prompt(scene, provider="volcengine")
        
        if not prompt:
            return None, "prompt 为空"
        
        sentiment = scene.get('sentiment', '默认')
        print(f"[Volcengine] 场景 {index+1} ({sentiment}) 生成中...")
        print(f"[Volcengine] Prompt: {prompt[:80]}...")
        
        client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=ark_api_key,
        )
        
        response = client.images.generate(
            model="doubao-seedream-4-0-250828",
            prompt=prompt,
            size="1024x1344",
            response_format="url",
            extra_body={"watermark": False},
        )
        
        image_url = response.data[0].url
        
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        image_data = resp.content
        
        # 文件命名：主题_scene_01.png
        safe_topic = sanitize_filename(topic) if topic else ""
        filename = f"{safe_topic}_scene_{index+1:02d}.png" if safe_topic else f"scene_{index+1:02d}.png"
        local_path = str(output_dir / filename)
        
        with open(local_path, "wb") as f:
            f.write(image_data)
        
        # 上传到 OSS（按主题分类）
        oss_url = None
        if topic:
            oss_url = upload_to_oss_by_topic(image_data, topic, filename, "images")
        
        print(f"[Volcengine] 场景 {index+1} 完成: {local_path}")
        # 优先返回 OSS URL，否则返回本地路径
        return oss_url or local_path, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Volcengine Error] 场景 {index+1} 失败: {error_msg}")
        return None, error_msg


def _generate_single_gemini(scene: dict, index: int, output_dir: Path = None, topic: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 Replicate 调用 Google Gemini 2.5 Flash Image 生成高质量图片（适合主图/封面图）
    
    Args:
        scene: 分镜字典，包含 prompt
        index: 场景索引
        output_dir: 输出目录
        topic: 主题名称
    
    Returns:
        (本地路径, 错误信息)
    """
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    try:
        base_prompt = scene.get('prompt', '')
        if not base_prompt:
            return None, "prompt 为空"
        
        # Gemini 使用英文 prompt 效果更好，添加高质量修饰词
        enhanced_prompt = f"Generate an image: High quality, professional illustration, masterpiece, best quality, {base_prompt}, detailed, 4k, sharp focus"
        
        print(f"[Gemini] 主图 {index+1} 生成中...")
        print(f"[Gemini] Prompt: {enhanced_prompt[:100]}...")
        
        # 通过 Replicate 调用 Gemini 2.5 Flash Image
        output = replicate.run(
            "google/gemini-2.5-flash-image",
            input={
                "prompt": enhanced_prompt,
                "aspect_ratio": "3:4",  # 小红书竖图比例
            }
        )
        
        # Replicate 返回的是 FileOutput 对象或 URL
        if not output:
            return None, "Gemini 未返回图片"
        
        # 获取图片 URL
        if hasattr(output, 'url'):
            image_url = output.url
        elif isinstance(output, str):
            image_url = output
        elif isinstance(output, list) and len(output) > 0:
            image_url = output[0].url if hasattr(output[0], 'url') else str(output[0])
        else:
            return None, f"无法解析 Gemini 返回: {type(output)}"
        
        # 下载图片
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        image_data = resp.content
        
        # 文件命名：主题_cover.png
        safe_topic = sanitize_filename(topic) if topic else ""
        filename = f"{safe_topic}_cover.png" if safe_topic else f"cover_{index+1:02d}.png"
        local_path = str(output_dir / filename)
        
        with open(local_path, "wb") as f:
            f.write(image_data)
        
        # 上传到 OSS（按主题分类）
        oss_url = None
        if topic:
            oss_url = upload_to_oss_by_topic(image_data, topic, filename, "images")
        
        print(f"[Gemini] 主图 {index+1} 完成: {local_path}")
        # 优先返回 OSS URL，否则返回本地路径
        return oss_url or local_path, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini Error] 主图 {index+1} 失败: {error_msg}")
        return None, error_msg


# ========== 统一入口 ==========

# 并发配置
MAX_WORKERS = 5  # 限制并发数，防止触发 API 速率限制 (429)


def generate_images(scenes: list, provider: str = "replicate", anime_model: str = "anything-v4", topic: str = None) -> list:
    """
    统一生图入口（并发版本）
    
    使用 ThreadPoolExecutor 并发生成图片，显著提升批量处理速度。
    文件按主题组织，重复生成时自动添加数字后缀。
    
    Args:
        scenes: 分镜列表，每个元素需包含 'prompt' 字段，可选 'sentiment'
        provider: "replicate" 或 "volcengine"
        anime_model: 二次元模型选择 "anything-v4" 或 "flux-anime"（仅 replicate 生效）
        topic: 主题名称（用于创建子目录和文件命名）
    
    Returns:
        本地图片路径列表（顺序与 scenes 一致，失败项为 None）
    """
    if not scenes:
        return []
    
    # 创建主题目录
    if topic:
        output_dir = get_unique_dir(DEFAULT_OUTPUT_DIR, topic)
        print(f"[Painter] 输出目录: {output_dir}")
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    
    print(f"[Painter] 开始并发生成 {len(scenes)} 张图片 (max_workers={MAX_WORKERS})...")
    
    def _generate_one(args):
        """单张图片生成（带索引）"""
        index, scene = args
        try:
            if provider == "replicate":
                path, error = _generate_single_anime(scene, index, anime_model, output_dir, topic)
            elif provider == "volcengine":
                path, error = _generate_single_volcengine(scene, index, output_dir, topic)
            else:
                print(f"[Painter Error] 未知的 provider: {provider}")
                return index, None
            return index, path
        except Exception as e:
            print(f"[Painter Error] 场景 {index+1} 异常: {e}")
            return index, None
    
    # 使用 ThreadPoolExecutor 并发执行
    results = [None] * len(scenes)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务（带索引）
        futures = {executor.submit(_generate_one, (i, scene)): i for i, scene in enumerate(scenes)}
        
        # 收集结果（保持顺序）
        for future in as_completed(futures):
            try:
                index, path = future.result()
                results[index] = path
            except Exception as e:
                index = futures[future]
                print(f"[Painter Error] 场景 {index+1} Future 异常: {e}")
                results[index] = None
    
    success_count = sum(1 for p in results if p is not None)
    print(f"[Painter] 并发生成完成: {success_count}/{len(scenes)} 成功")
    
    return results


def generate_images_mixed(scenes: list, topic: str = None) -> list:
    """
    图文模式专用：主图用 Gemini Imagen 3，配图用豆包
    
    第一张图（封面/主图）使用 Google Gemini Imagen 3 生成高质量图片
    其余配图使用火山引擎豆包 Seedream 生成
    
    Args:
        scenes: 配图设计列表，每个元素需包含 'prompt' 字段
        topic: 主题名称（用于创建子目录和文件命名）
    
    Returns:
        本地图片路径列表（顺序与 scenes 一致，失败项为 None）
    """
    if not scenes:
        return []
    
    # 创建主题目录
    if topic:
        output_dir = get_unique_dir(DEFAULT_OUTPUT_DIR, topic)
        print(f"[Painter Mixed] 输出目录: {output_dir}")
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    
    results = [None] * len(scenes)
    
    print(f"[Painter Mixed] 开始混合生成 {len(scenes)} 张图片...")
    print(f"[Painter Mixed] 主图: Gemini Imagen 3 | 配图: 豆包 Seedream")
    
    # 1. 生成主图（第一张，使用 Gemini）
    if len(scenes) > 0:
        print(f"\n[Painter Mixed] === 生成主图 (Gemini) ===")
        path, error = _generate_single_gemini(scenes[0], 0, output_dir, topic)
        results[0] = path
        if error:
            print(f"[Painter Mixed] 主图 Gemini 失败，降级到豆包: {error}")
            # 降级到豆包
            path, error = _generate_single_volcengine(scenes[0], 0, output_dir, topic)
            results[0] = path
    
    # 2. 生成配图（其余图片，使用豆包并发）
    if len(scenes) > 1:
        print(f"\n[Painter Mixed] === 生成配图 (豆包, {len(scenes)-1} 张) ===")
        
        def _generate_one(args):
            index, scene = args
            try:
                path, error = _generate_single_volcengine(scene, index, output_dir, topic)
                return index, path
            except Exception as e:
                print(f"[Painter Mixed Error] 配图 {index+1} 异常: {e}")
                return index, None
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 从 index=1 开始（跳过主图）
            futures = {
                executor.submit(_generate_one, (i, scene)): i 
                for i, scene in enumerate(scenes) if i > 0
            }
            
            for future in as_completed(futures):
                try:
                    index, path = future.result()
                    results[index] = path
                except Exception as e:
                    index = futures[future]
                    print(f"[Painter Mixed Error] 配图 {index+1} Future 异常: {e}")
                    results[index] = None
    
    success_count = sum(1 for p in results if p is not None)
    print(f"\n[Painter Mixed] 混合生成完成: {success_count}/{len(scenes)} 成功")
    
    return results


def generate_single_image(scene: dict, index: int, provider: str = "replicate", anime_model: str = "anything-v4", output_dir: Path = None, topic: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    生成单张图片（用于重试）
    
    Args:
        scene: 分镜字典，需包含 'prompt' 字段，可选 'sentiment'
        index: 场景索引（0-based）
        provider: "replicate" 或 "volcengine"
        anime_model: 二次元模型选择（仅 replicate 生效）
        output_dir: 输出目录（为空则使用默认）
        topic: 主题名称
    
    Returns:
        (本地路径, 错误信息)
    """
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    if provider == "replicate":
        return _generate_single_anime(scene, index, anime_model, output_dir, topic)
    elif provider == "volcengine":
        return _generate_single_volcengine(scene, index, output_dir, topic)
    else:
        return None, f"未知的 provider: {provider}"


# ========== 兼容旧接口（保留） ==========

def generate_images_with_ideogram(designs_list: list) -> list:
    """
    旧接口兼容层 - 根据设计方案批量生成图片并上传到 OSS
    
    Args:
        designs_list: writer 模块生成的 images_design 列表
    
    Returns:
        OSS 图片 URL 列表
    """
    urls = []
    
    for i, design in enumerate(designs_list):
        try:
            prompt = _build_ideogram_prompt(design)
            print(f"[Painter] 图片 {i+1} prompt: {prompt[:100]}...")
            
            output = replicate.run(
                "ideogram-ai/ideogram-v2",
                input={
                    "prompt": prompt,
                    "aspect_ratio": "3:4",
                }
            )
            
            image_url = output if isinstance(output, str) else str(output)
            
            resp = requests.get(image_url, timeout=60)
            resp.raise_for_status()
            image_data = resp.content
            
            timestamp = int(time.time() * 1000)
            img_type = design.get('type', 'img')
            filename = f"rednote/{timestamp}_{img_type}.webp"
            
            oss_url = upload_to_oss(image_data, filename)
            if oss_url:
                urls.append(oss_url)
                print(f"[Painter] 图片 {i+1} ({img_type}) 生成成功: {oss_url}")
            else:
                print(f"[Painter] 图片 {i+1} 上传失败")
                
        except Exception as e:
            print(f"[Painter Error] 图片 {i+1} 生成失败: {e}")
            continue
    
    return urls


def _build_ideogram_prompt(design: dict) -> str:
    """旧接口的 prompt 构建函数"""
    design_type = design.get('type', 'cover')
    main_text = design.get('main_text', '')
    sub_text = design.get('sub_text', '')
    visual_style = design.get('visual_style', 'minimalist aesthetic')
    
    if design_type == 'cover':
        prompt = (
            f"A poster design with text. "
            f"The Chinese text '{main_text}' is rendered in large bold font at the top. "
            f"Below it is '{sub_text}'. "
            f"The background style is {visual_style}. "
            f"Typography is integrated naturally. High quality, professional design."
        )
    else:
        prompt = (
            f"An artistic photograph with text. "
            f"The Chinese text '{main_text}' is elegantly placed in the image. "
            f"The visual style is {visual_style}. "
            f"Clean typography, aesthetic composition."
        )
    
    return prompt
