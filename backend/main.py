"""
FastAPI 后端入口
提供 REST API 封装现有 Python modules
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径，以便 import modules
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

from backend.routers import topics, content, media, video, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：确保输出目录存在
    (ROOT_DIR / "output/images").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "output/audio").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "output/video").mkdir(parents=True, exist_ok=True)
    print("[Backend] 输出目录已就绪")
    yield
    # 关闭时清理（如需要）


app = FastAPI(
    title="小红书内容工作流 API",
    description="Notion 风格 UI 的后端 API 服务",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 配置（允许本地开发）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（输出的图片/音频/视频）
app.mount("/static/images", StaticFiles(directory=str(ROOT_DIR / "output/images")), name="images")
app.mount("/static/audio", StaticFiles(directory=str(ROOT_DIR / "output/audio")), name="audio")
app.mount("/static/video", StaticFiles(directory=str(ROOT_DIR / "output/video")), name="video")

# 注册路由
app.include_router(topics.router, prefix="/api/topics", tags=["选题分析"])
app.include_router(content.router, prefix="/api/content", tags=["内容生成"])
app.include_router(media.router, prefix="/api/media", tags=["素材生成"])
app.include_router(video.router, prefix="/api/video", tags=["视频合成"])
app.include_router(config.router, prefix="/api/config", tags=["配置"])


@app.get("/")
async def root():
    return {"message": "小红书内容工作流 API", "version": "2.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        "replicate": bool(os.getenv("REPLICATE_API_TOKEN")),
        "ark": bool(os.getenv("ARK_API_KEY")),
        "volc_tts": bool(os.getenv("VOLC_TTS_APPID")),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8501, reload=True)

