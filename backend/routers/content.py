"""
内容生成 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from modules.writer import (
    generate_note_package_with_retry,
    generate_outline_step,
    generate_content_step,
    generate_visuals_step
)
from modules.crawler import fetch_note_content
from modules.md_exporter import export_note

router = APIRouter()


class ImageDesign(BaseModel):
    index: int = 0
    description: str = ""
    prompt: str = ""
    sentiment: str = ""
    cover_text: Optional[str] = None  # 主图文字（仅第一张图需要）


class VisualScene(BaseModel):
    scene_index: int = 0
    narration: str = ""
    description: str = ""
    sentiment: str = ""
    prompt: str = ""


class Diagram(BaseModel):
    index: int = 0
    title: str = ""
    description: str = ""
    diagram_type: str = "architecture"  # "architecture" | "flow" | "comparison"
    prompt: str = ""


class GenerateRequest(BaseModel):
    topic: str
    persona: Optional[str] = None
    reference_url: Optional[str] = None
    mode: str = "image"  # "image" | "video" | "wechat"
    llm_model: str = "deepseek/deepseek-chat"
    search_data: Optional[Dict[str, Any]] = None  # websearch 返回的完整热点数据
    temperature: float = 0.8  # LLM 温度参数，控制创意度 vs 稳定性
    
    model_config = {"protected_namespaces": ()}


class GenerateResponse(BaseModel):
    titles: List[str] = []
    content: str = ""
    image_designs: Optional[List[ImageDesign]] = None
    visual_scenes: Optional[List[VisualScene]] = None
    diagrams: Optional[List[Diagram]] = None


# ============================================================================
# 分步生成 API Request/Response Models
# ============================================================================

class OutlineRequest(BaseModel):
    topic: str
    persona: Optional[str] = None
    search_data: Optional[Dict[str, Any]] = None
    model_name: str = "deepseek/deepseek-chat"
    temperature: float = 0.7

class OutlineResponse(BaseModel):
    titles: List[str]
    outline: List[str]

class ContentRequest(BaseModel):
    topic: str
    outline: List[str]
    titles: List[str]
    persona: Optional[str] = None
    search_data: Optional[Dict[str, Any]] = None
    reference_url: Optional[str] = None
    model_name: str = "deepseek/deepseek-chat"
    temperature: float = 0.8

class ContentResponse(BaseModel):
    content: str

class VisualsRequest(BaseModel):
    topic: str
    content: str
    model_name: str = "deepseek/deepseek-chat"
    temperature: float = 0.7
    global_style: Optional[str] = None

class VisualsResponse(BaseModel):
    image_designs: List[ImageDesign]
    global_style: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/step/outline", response_model=OutlineResponse)
async def create_outline(req: OutlineRequest):
    """【Step 1】生成大纲和标题"""
    if not req.topic:
        raise HTTPException(status_code=400, detail="选题不能为空")
    
    try:
        result = generate_outline_step(
            topic=req.topic,
            search_data=req.search_data,
            persona=req.persona,
            model_name=req.model_name,
            temperature=req.temperature
        )
        return OutlineResponse(
            titles=result.get("titles", []),
            outline=result.get("outline", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")


@router.post("/step/content", response_model=ContentResponse)
async def create_content_step(req: ContentRequest):
    """【Step 2】生成正文"""
    try:
        # 抓取参考内容
        reference_text = None
        if req.reference_url:
            ref_data = fetch_note_content(req.reference_url)
            if ref_data:
                reference_text = f"标题：{ref_data.get('title', '')}\n\n{ref_data.get('content', '')}"

        result = generate_content_step(
            topic=req.topic,
            outline=req.outline,
            titles=req.titles,
            persona=req.persona,
            search_data=req.search_data,
            reference_text=reference_text,
            model_name=req.model_name,
            temperature=req.temperature
        )
        return ContentResponse(content=result.get("content", ""))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"正文生成失败: {str(e)}")


@router.post("/step/visuals", response_model=VisualsResponse)
async def create_visuals(req: VisualsRequest):
    """【Step 3】生成配图设计"""
    try:
        result = generate_visuals_step(
            topic=req.topic,
            content=req.content,
            model_name=req.model_name,
            temperature=req.temperature,
            global_style=req.global_style
        )
        
        designs = result.get("image_designs", [])
        image_designs = [
            ImageDesign(
                index=d.get("index", i + 1),
                description=d.get("description", ""),
                prompt=d.get("prompt", ""),
                sentiment=d.get("sentiment", ""),
                cover_text=d.get("cover_text"),
            )
            for i, d in enumerate(designs)
        ]
        
        return VisualsResponse(
            image_designs=image_designs,
            global_style=result.get("global_style")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配图设计失败: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(req: GenerateRequest):
    """
    生成内容（图文/视频模式）
    
    图文模式：返回 titles + content + image_designs
    视频模式：返回 titles + content + visual_scenes
    """
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="选题不能为空")
    
    try:
        # 抓取参考内容（如有）
        reference_text = None
        if req.reference_url:
            ref_data = fetch_note_content(req.reference_url)
            if ref_data:
                reference_text = f"标题：{ref_data.get('title', '')}\n\n{ref_data.get('content', '')}"
        
        # 调用写作模块（带质量检测和重试）
        result = generate_note_package_with_retry(
            topic=req.topic.strip(),
            persona=req.persona,
            reference_text=reference_text,
            mode=req.mode,
            model_name=req.llm_model,
            search_data=req.search_data,
            temperature=req.temperature,
            max_retries=2,
            quality_threshold=70,
        )
        
        if not result or not result.get("titles"):
            raise HTTPException(status_code=500, detail="内容生成失败，请重试")
        
        # 构造响应
        response = GenerateResponse(
            titles=result.get("titles", []),
            content=result.get("content", ""),
        )
        
        if req.mode == "video":
            scenes = result.get("visual_scenes", [])
            response.visual_scenes = [
                VisualScene(
                    scene_index=s.get("scene_index", i + 1),
                    narration=s.get("narration", ""),
                    description=s.get("description", ""),
                    sentiment=s.get("sentiment", ""),
                    prompt=s.get("prompt", ""),
                )
                for i, s in enumerate(scenes)
            ]
        elif req.mode == "wechat":
            diagrams_data = result.get("diagrams", [])
            response.diagrams = [
                Diagram(
                    index=d.get("index", i + 1),
                    title=d.get("title", ""),
                    description=d.get("description", ""),
                    diagram_type=d.get("diagram_type", "architecture"),
                    prompt=d.get("prompt", ""),
                )
                for i, d in enumerate(diagrams_data)
            ]
        else:
            designs = result.get("image_designs", [])
            response.image_designs = [
                ImageDesign(
                    index=d.get("index", i + 1),
                    description=d.get("description", ""),
                    prompt=d.get("prompt", ""),
                    sentiment=d.get("sentiment", ""),
                    cover_text=d.get("cover_text"),
                )
                for i, d in enumerate(designs)
            ]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容生成失败: {str(e)}")


class ExportRequest(BaseModel):
    topic: str
    title: str
    content: str
    image_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ExportResponse(BaseModel):
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None


@router.post("/export", response_model=ExportResponse)
async def export_note_to_obsidian(req: ExportRequest):
    """
    导出笔记到 Obsidian（MD 格式）
    
    将生成的笔记保存到本地 Obsidian 目录
    """
    if not req.topic or not req.title or not req.content:
        raise HTTPException(status_code=400, detail="主题、标题和内容不能为空")
    
    try:
        file_path = export_note(
            topic=req.topic,
            title=req.title,
            content=req.content,
            image_urls=req.image_urls,
            tags=req.tags,
        )
        
        if file_path:
            return ExportResponse(success=True, file_path=file_path)
        else:
            return ExportResponse(success=False, error="导出失败，请检查目录权限")
            
    except Exception as e:
        return ExportResponse(success=False, error=str(e))
