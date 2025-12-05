"""
视频合成 API
"""
import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.editor import create_video, get_total_duration, generate_srt

router = APIRouter()

ROOT_DIR = Path(__file__).parent.parent.parent


class SceneForVideo(BaseModel):
    narration: str = ""


class CreateVideoRequest(BaseModel):
    image_paths: List[str]
    audio_paths: List[str]
    scenes: Optional[List[SceneForVideo]] = None  # 用于生成字幕
    bgm_path: Optional[str] = None
    bgm_volume: float = 0.12
    topic: Optional[str] = None


class VideoResponse(BaseModel):
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    srt_path: Optional[str] = None
    srt_url: Optional[str] = None
    duration: float = 0.0
    error: Optional[str] = None


class DurationRequest(BaseModel):
    audio_paths: List[str]


class DurationResponse(BaseModel):
    total_duration: float


def _path_to_url(path: str, media_type: str) -> Optional[str]:
    """将本地路径转换为静态文件 URL"""
    if not path or not os.path.exists(path):
        return None
    
    output_dir = ROOT_DIR / "output" / media_type
    try:
        # 将两个路径都转为绝对路径再比较
        abs_path = Path(path).resolve()
        abs_output_dir = output_dir.resolve()
        rel_path = abs_path.relative_to(abs_output_dir)
        return f"/static/{media_type}/{rel_path}"
    except ValueError:
        return f"/static/{media_type}/{Path(path).name}"


@router.post("/create", response_model=VideoResponse)
async def create_video_endpoint(req: CreateVideoRequest):
    """
    合成视频（画音同步 + Ken Burns + BGM）
    """
    if not req.image_paths or not req.audio_paths:
        raise HTTPException(status_code=400, detail="图片和音频路径列表不能为空")
    
    if len(req.image_paths) != len(req.audio_paths):
        raise HTTPException(status_code=400, detail="图片和音频数量必须一致")
    
    # 验证文件存在
    missing_images = [p for p in req.image_paths if not os.path.exists(p)]
    missing_audio = [p for p in req.audio_paths if not os.path.exists(p)]
    
    if missing_images:
        raise HTTPException(status_code=400, detail=f"图片文件不存在: {missing_images}")
    if missing_audio:
        raise HTTPException(status_code=400, detail=f"音频文件不存在: {missing_audio}")
    
    try:
        # 转换 scenes 格式
        scenes = None
        if req.scenes:
            scenes = [{"narration": s.narration} for s in req.scenes]
        
        # 调用视频合成
        video_path = create_video(
            image_paths=req.image_paths,
            audio_paths=req.audio_paths,
            bgm_path=req.bgm_path,
            bgm_volume=req.bgm_volume,
            scenes=scenes,
            topic=req.topic,
        )
        
        if not video_path or not os.path.exists(video_path):
            return VideoResponse(error="视频合成失败")
        
        # 获取时长
        duration = get_total_duration(req.audio_paths)
        
        # SRT 路径
        srt_path = video_path.rsplit(".", 1)[0] + ".srt"
        srt_exists = os.path.exists(srt_path)
        
        return VideoResponse(
            video_path=video_path,
            video_url=_path_to_url(video_path, "video"),
            srt_path=srt_path if srt_exists else None,
            srt_url=_path_to_url(srt_path, "video") if srt_exists else None,
            duration=duration,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频合成失败: {str(e)}")


@router.post("/duration", response_model=DurationResponse)
async def get_duration(req: DurationRequest):
    """
    计算音频总时长
    """
    try:
        duration = get_total_duration(req.audio_paths)
        return DurationResponse(total_duration=duration)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算时长失败: {str(e)}")


@router.get("/bgm")
async def list_bgm():
    """
    获取可用的 BGM 列表
    """
    bgm_dir = ROOT_DIR / "assets/bgm"
    if not bgm_dir.exists():
        return {"bgm_list": []}
    
    bgm_files = []
    for ext in ["*.mp3", "*.wav", "*.m4a"]:
        bgm_files.extend(bgm_dir.glob(ext))
    
    return {
        "bgm_list": [
            {
                "name": f.stem,
                "filename": f.name,
                "path": str(f),
            }
            for f in sorted(bgm_files)
        ]
    }

