"""
Ideogram 生图与转存模块 (Replicate + OSS)
"""
import os
import time
from dotenv import load_dotenv
import replicate
import requests
from modules.storage import upload_to_oss

load_dotenv()


def generate_images_with_ideogram(designs_list: list) -> list:
    """
    根据设计方案批量生成图片并上传到 OSS
    
    Args:
        designs_list: writer 模块生成的 images_design 列表，包含2个设计字典
                      每个字典包含 type, main_text, sub_text(可选), visual_style
    
    Returns:
        OSS 图片 URL 列表 (2个)
    """
    urls = []
    
    for i, design in enumerate(designs_list):
        try:
            # 根据类型构建 Ideogram prompt
            prompt = _build_ideogram_prompt(design)
            print(f"[Painter] 图片 {i+1} prompt: {prompt[:100]}...")
            
            # 调用 Replicate Ideogram 模型生成图片
            output = replicate.run(
                "ideogram-ai/ideogram-v2",
                input={
                    "prompt": prompt,
                    "aspect_ratio": "3:4",  # 小红书竖图比例
                }
            )
            
            # output 是图片 URL
            image_url = output if isinstance(output, str) else str(output)
            
            # 下载图片数据
            resp = requests.get(image_url, timeout=60)
            resp.raise_for_status()
            image_data = resp.content
            
            # 生成带时间戳的文件名
            timestamp = int(time.time() * 1000)
            img_type = design.get('type', 'img')
            filename = f"rednote/{timestamp}_{img_type}.webp"
            
            # 上传到 OSS
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
    """
    根据设计类型构建 Ideogram prompt
    
    Args:
        design: 设计字典，包含 type, main_text, sub_text(可选), visual_style
    
    Returns:
        适合 Ideogram 的英文 prompt，包含中文文字渲染指令
    """
    design_type = design.get('type', 'cover')
    main_text = design.get('main_text', '')
    sub_text = design.get('sub_text', '')
    visual_style = design.get('visual_style', 'minimalist aesthetic')
    
    if design_type == 'cover':
        # 封面图：大标题 + 副标题
        prompt = (
            f"A poster design with text. "
            f"The Chinese text '{main_text}' is rendered in large bold font at the top. "
            f"Below it is '{sub_text}'. "
            f"The background style is {visual_style}. "
            f"Typography is integrated naturally. High quality, professional design."
        )
    else:
        # 配图：金句
        prompt = (
            f"An artistic photograph with text. "
            f"The Chinese text '{main_text}' is elegantly placed in the image. "
            f"The visual style is {visual_style}. "
            f"Clean typography, aesthetic composition."
        )
    
    return prompt
