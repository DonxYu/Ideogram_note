"""
生图模块 (FLUX via Replicate)
专注使用 black-forest-labs/flux-dev 生成高质量图片
支持并发生成：ThreadPoolExecutor 加速批量处理
支持主题命名：文件按主题组织
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import replicate
import requests
from modules.storage import upload_to_oss_by_topic
from modules.utils import sanitize_filename, get_unique_dir

load_dotenv()

# 默认输出目录
DEFAULT_OUTPUT_DIR = Path("output/images")
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== FLUX 风格库 ==========

FLUX_STYLES = {
    # 情感风格映射
    "可爱治愈": "soft pastel colors, dreamy atmosphere, gentle lighting, kawaii aesthetic, warm and cozy vibe, studio ghibli inspired",
    "严肃深度": "cinematic lighting, shallow depth of field, shot on 35mm film, dramatic shadows, moody atmosphere, film grain",
    "日常生活": "natural lighting, slice of life aesthetic, realistic urban setting, warm color palette, candid photography style",
    "热血励志": "dynamic composition, vibrant saturated colors, dramatic angle, action shot, intense lighting, high energy",
    "悲伤低沉": "melancholic atmosphere, rainy day, desaturated colors, soft focus, lonely mood, cold blue tones",
    "职场日常": "modern office aesthetic, professional but casual, warm ambient lighting, realistic interior, lifestyle photography",
    # 技术风格（公众号架构图）
    "architecture": "technical diagram style, clean minimalist design, dark mode UI, neon accent colors, system architecture visualization, professional infographic",
    "flow": "data flow diagram, glowing connections, dark background, modern tech aesthetic, clean information design",
    "comparison": "side-by-side comparison layout, split view design, contrasting colors, clean infographic style, professional presentation",
}

FLUX_BASE_STYLE = "high quality, detailed, professional photography, 4k resolution, sharp focus"

# 并发配置
MAX_WORKERS = 5


# ========== FLUX 单图生成 ==========

def _generate_single_flux(
    scene: dict, 
    index: int, 
    output_dir: Path = None, 
    topic: str = None,
    use_schnell: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 FLUX 模型生成单张图片
    
    Args:
        scene: 分镜字典，包含 prompt 和可选的 sentiment
        index: 场景索引
        output_dir: 输出目录
        topic: 主题名称
        use_schnell: True 使用 flux-schnell（更快），False 使用 flux-dev（更高质量）
    
    Returns:
        (图片路径, 错误信息)
    """
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    try:
        base_prompt = scene.get('prompt', '')
        if not base_prompt:
            return None, "prompt 为空"
        
        # 获取风格修饰符
        sentiment = scene.get('sentiment', '')
        style_modifier = FLUX_STYLES.get(sentiment, FLUX_BASE_STYLE)
        
        # 组装最终 prompt
        final_prompt = f"{base_prompt}, {style_modifier}"
        
        model_name = "flux-schnell" if use_schnell else "flux-dev"
        print(f"[FLUX {model_name}] 场景 {index+1} ({sentiment or '默认'}) 生成中...")
        print(f"[FLUX] Prompt: {final_prompt[:100]}...")
        
        # 调用 Replicate FLUX 模型
        model_id = "black-forest-labs/flux-schnell" if use_schnell else "black-forest-labs/flux-dev"
        
        input_params = {
            "prompt": final_prompt,
            "aspect_ratio": "3:4",  # 小红书竖图
            "output_format": "webp",
            "output_quality": 90,
        }
        
        # flux-dev 支持 go_fast 参数
        if not use_schnell:
            input_params["go_fast"] = True
        
        output = replicate.run(model_id, input=input_params)
        
        # 处理输出（FileOutput 对象或 URL）
        if not output:
            return None, "FLUX 未返回图片"
        
        if hasattr(output, 'url'):
            image_url = output.url
        elif isinstance(output, str):
            image_url = output
        elif isinstance(output, list) and len(output) > 0:
            first_item = output[0]
            image_url = first_item.url if hasattr(first_item, 'url') else str(first_item)
        else:
            return None, f"无法解析 FLUX 返回: {type(output)}"
        
        # 下载图片
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        image_data = resp.content
        
        # 文件命名
        safe_topic = sanitize_filename(topic) if topic else ""
        filename = f"{safe_topic}_scene_{index+1:02d}.webp" if safe_topic else f"scene_{index+1:02d}.webp"
        local_path = str(output_dir / filename)
        
        with open(local_path, "wb") as f:
            f.write(image_data)
        
        # 上传到 OSS（按主题分类）
        oss_url = None
        if topic:
            oss_url = upload_to_oss_by_topic(image_data, topic, filename, "images")
        
        print(f"[FLUX] 场景 {index+1} 完成: {local_path}")
        return oss_url or local_path, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[FLUX Error] 场景 {index+1} 失败: {error_msg}")
        return None, error_msg


# ========== 火山引擎豆包（备用） ==========

def _generate_single_volcengine(
    scene: dict, 
    index: int, 
    output_dir: Path = None, 
    topic: str = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    使用火山引擎豆包生成单张图片（中文 Prompt 备用方案）
    """
    from openai import OpenAI
    
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    try:
        ark_api_key = os.getenv("ARK_API_KEY")
        if not ark_api_key:
            return None, "缺少 ARK_API_KEY"
        
        base_prompt = scene.get('prompt', '')
        if not base_prompt:
            return None, "prompt 为空"
        
        sentiment = scene.get('sentiment', '默认')
        print(f"[Volcengine] 场景 {index+1} ({sentiment}) 生成中...")
        
        client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=ark_api_key,
        )
        
        response = client.images.generate(
            model="doubao-seedream-4-0-250828",
            prompt=base_prompt,
            size="1024x1344",
            response_format="url",
            extra_body={"watermark": False},
        )
        
        image_url = response.data[0].url
        
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        image_data = resp.content
        
        safe_topic = sanitize_filename(topic) if topic else ""
        filename = f"{safe_topic}_scene_{index+1:02d}.png" if safe_topic else f"scene_{index+1:02d}.png"
        local_path = str(output_dir / filename)
        
        with open(local_path, "wb") as f:
            f.write(image_data)
        
        oss_url = None
        if topic:
            oss_url = upload_to_oss_by_topic(image_data, topic, filename, "images")
        
        print(f"[Volcengine] 场景 {index+1} 完成: {local_path}")
        return oss_url or local_path, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Volcengine Error] 场景 {index+1} 失败: {error_msg}")
        return None, error_msg


# ========== 统一入口 ==========

def generate_images(
    scenes: list, 
    provider: str = "replicate", 
    topic: str = None,
    use_schnell: bool = False
) -> list:
    """
    统一生图入口（并发版本）
    
    Args:
        scenes: 分镜列表，每个元素需包含 'prompt' 字段，可选 'sentiment'
        provider: "replicate"（默认，使用 FLUX）或 "volcengine"（备用）
        topic: 主题名称（用于创建子目录和文件命名）
        use_schnell: True 使用 flux-schnell（更快），False 使用 flux-dev（更高质量）
    
    Returns:
        图片路径列表（顺序与 scenes 一致，失败项为 None）
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
                return index, _generate_single_flux(scene, index, output_dir, topic, use_schnell)[0]
            elif provider == "volcengine":
                return index, _generate_single_volcengine(scene, index, output_dir, topic)[0]
            else:
                print(f"[Painter Error] 未知的 provider: {provider}，回退到 FLUX")
                return index, _generate_single_flux(scene, index, output_dir, topic, use_schnell)[0]
        except Exception as e:
            print(f"[Painter Error] 场景 {index+1} 异常: {e}")
            return index, None
    
    # 使用 ThreadPoolExecutor 并发执行
    results = [None] * len(scenes)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_generate_one, (i, scene)): i for i, scene in enumerate(scenes)}
        
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


def generate_diagrams(diagrams: list, topic: str = None) -> list:
    """
    公众号专用：生成架构图/示意图
    
    Args:
        diagrams: 架构图设计列表，每个元素需包含 'prompt' 和 'diagram_type'
        topic: 主题名称
    
    Returns:
        图片路径列表
    """
    if not diagrams:
        return []
    
    print(f"[Diagrams] 开始生成 {len(diagrams)} 张架构图...")
    
    # 转换为标准 scene 格式，添加风格
    scenes_with_style = []
    for diagram in diagrams:
        base_prompt = diagram.get('prompt', '')
        diagram_type = diagram.get('diagram_type', 'architecture')
        
        scenes_with_style.append({
            'prompt': base_prompt,
            'sentiment': diagram_type
        })
    
    return generate_images(scenes=scenes_with_style, provider="replicate", topic=topic)


def generate_single_image(
    scene: dict, 
    index: int, 
    provider: str = "replicate", 
    output_dir: Path = None, 
    topic: str = None,
    use_schnell: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """
    生成单张图片（用于重试）
    
    Args:
        scene: 分镜字典，需包含 'prompt' 字段，可选 'sentiment'
        index: 场景索引（0-based）
        provider: "replicate"（默认）或 "volcengine"
        output_dir: 输出目录
        topic: 主题名称
        use_schnell: 是否使用快速模式
    
    Returns:
        (图片路径, 错误信息)
    """
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    if provider == "replicate":
        return _generate_single_flux(scene, index, output_dir, topic, use_schnell)
    elif provider == "volcengine":
        return _generate_single_volcengine(scene, index, output_dir, topic)
    else:
        # 默认使用 FLUX
        return _generate_single_flux(scene, index, output_dir, topic, use_schnell)
