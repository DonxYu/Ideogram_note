"""
素材生成 API（图片 + 音频）
支持 SSE 流式进度推送
"""
import os
import asyncio
import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from modules.painter import generate_images, generate_single_image, generate_images_mixed
from modules.audio import generate_audio_for_scenes, generate_single_audio

router = APIRouter()

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent


class SceneInput(BaseModel):
    prompt: str
    narration: Optional[str] = None
    sentiment: Optional[str] = None


class ImageRequest(BaseModel):
    scenes: List[SceneInput]
    provider: str = "replicate"  # "replicate" | "volcengine"
    anime_model: str = "anything-v4"  # "anything-v4" | "flux-anime"
    topic: Optional[str] = None
    mode: str = "video"  # "image" | "video" - 图文模式主图用 Gemini


class AudioRequest(BaseModel):
    scenes: List[SceneInput]
    provider: str = "edge"  # "edge" | "volcengine"
    voice: Optional[str] = None
    topic: Optional[str] = None


class SingleImageRequest(BaseModel):
    scene: SceneInput
    index: int
    provider: str = "replicate"
    anime_model: str = "anything-v4"
    topic: Optional[str] = None


class SingleAudioRequest(BaseModel):
    scene: SceneInput
    index: int
    provider: str = "edge"
    voice: Optional[str] = None
    topic: Optional[str] = None


class MediaResult(BaseModel):
    index: int
    path: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class BatchMediaResponse(BaseModel):
    results: List[MediaResult]
    success_count: int
    total: int


def _path_to_url(path: str, media_type: str) -> Optional[str]:
    """将本地路径转换为静态文件 URL，或直接返回 OSS URL"""
    if not path:
        return None
    
    # 如果已经是 URL（OSS 链接），直接返回
    if path.startswith("http://") or path.startswith("https://"):
        return path
    
    # 本地路径：检查文件是否存在
    if not os.path.exists(path):
        return None
    
    # 获取相对于 output 目录的路径
    output_dir = ROOT_DIR / "output" / media_type
    try:
        # 将两个路径都转为绝对路径再比较
        abs_path = Path(path).resolve()
        abs_output_dir = output_dir.resolve()
        rel_path = abs_path.relative_to(abs_output_dir)
        return f"/static/{media_type}/{rel_path}"
    except ValueError:
        # 如果不在预期目录下，返回文件名
        return f"/static/{media_type}/{Path(path).name}"


@router.post("/images", response_model=BatchMediaResponse)
async def generate_images_batch(req: ImageRequest):
    """
    批量生成图片
    
    - 视频模式：使用指定 provider 统一生成
    - 图文模式：主图用 Gemini Imagen 3，配图用豆包
    """
    if not req.scenes:
        raise HTTPException(status_code=400, detail="分镜列表不能为空")
    
    try:
        # 转换为 modules 需要的格式
        scenes = [
            {"prompt": s.prompt, "sentiment": s.sentiment or ""}
            for s in req.scenes
        ]
        
        # 根据模式选择生图方式
        if req.mode == "image":
            # 图文模式：主图 Gemini + 配图豆包
            paths = generate_images_mixed(
                scenes=scenes,
                topic=req.topic,
            )
        else:
            # 视频模式：统一 provider
            paths = generate_images(
                scenes=scenes,
                provider=req.provider,
                anime_model=req.anime_model,
                topic=req.topic,
            )
        
        # 构造结果
        results = []
        for i, path in enumerate(paths):
            results.append(MediaResult(
                index=i,
                path=path,
                url=_path_to_url(path, "images") if path else None,
                error=None if path else "生成失败",
            ))
        
        success_count = sum(1 for r in results if r.path)
        
        return BatchMediaResponse(
            results=results,
            success_count=success_count,
            total=len(req.scenes),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")


@router.post("/images/single", response_model=MediaResult)
async def generate_image_single(req: SingleImageRequest):
    """
    生成单张图片（用于重试）
    """
    try:
        scene = {"prompt": req.scene.prompt, "sentiment": req.scene.sentiment or ""}
        
        path, error = generate_single_image(
            scene=scene,
            index=req.index,
            provider=req.provider,
            anime_model=req.anime_model,
            topic=req.topic,
        )
        
        return MediaResult(
            index=req.index,
            path=path,
            url=_path_to_url(path, "images") if path else None,
            error=error,
        )
        
    except Exception as e:
        return MediaResult(index=req.index, error=str(e))


@router.post("/audio", response_model=BatchMediaResponse)
async def generate_audio_batch(req: AudioRequest):
    """
    批量生成音频
    """
    if not req.scenes:
        raise HTTPException(status_code=400, detail="分镜列表不能为空")
    
    try:
        # 转换格式
        scenes = [{"narration": s.narration or ""} for s in req.scenes]
        
        # 调用音频模块
        paths = generate_audio_for_scenes(
            scenes=scenes,
            provider=req.provider,
            voice=req.voice,
            topic=req.topic,
        )
        
        # 构造结果
        results = []
        for i, path in enumerate(paths):
            results.append(MediaResult(
                index=i,
                path=path,
                url=_path_to_url(path, "audio") if path else None,
                error=None if path else "生成失败",
            ))
        
        success_count = sum(1 for r in results if r.path)
        
        return BatchMediaResponse(
            results=results,
            success_count=success_count,
            total=len(req.scenes),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频生成失败: {str(e)}")


@router.post("/audio/single", response_model=MediaResult)
async def generate_audio_single(req: SingleAudioRequest):
    """
    生成单段音频（用于重试）
    """
    try:
        scene = {"narration": req.scene.narration or ""}
        
        path, error = generate_single_audio(
            scene=scene,
            index=req.index,
            provider=req.provider,
            voice=req.voice,
            topic=req.topic,
        )
        
        return MediaResult(
            index=req.index,
            path=path,
            url=_path_to_url(path, "audio") if path else None,
            error=error,
        )
        
    except Exception as e:
        return MediaResult(index=req.index, error=str(e))


# ========== SSE 流式进度 ==========

async def _generate_images_stream(req: ImageRequest):
    """图片生成 SSE 流"""
    scenes = [
        {"prompt": s.prompt, "sentiment": s.sentiment or ""}
        for s in req.scenes
    ]
    
    for i, scene in enumerate(scenes):
        yield f"data: {json.dumps({'type': 'progress', 'index': i, 'total': len(scenes), 'status': 'generating'})}\n\n"
        
        try:
            path, error = generate_single_image(
                scene=scene,
                index=i,
                provider=req.provider,
                anime_model=req.anime_model,
                topic=req.topic,
            )
            
            result = {
                "type": "result",
                "index": i,
                "path": path,
                "url": _path_to_url(path, "images") if path else None,
                "error": error,
            }
            yield f"data: {json.dumps(result)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'result', 'index': i, 'error': str(e)})}\n\n"
        
        await asyncio.sleep(0.1)  # 小延迟让前端有时间处理
    
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/images/stream")
async def generate_images_stream(req: ImageRequest):
    """
    流式生成图片（SSE）
    
    实时推送每张图片的生成进度和结果
    """
    return StreamingResponse(
        _generate_images_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

