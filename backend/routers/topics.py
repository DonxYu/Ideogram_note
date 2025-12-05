"""
选题分析 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from modules.trend import analyze_trends

router = APIRouter()


class TopicItem(BaseModel):
    title: str
    source: str = ""
    summary: str = ""
    outline: List[str] = []
    why_hot: str = ""


class AnalyzeRequest(BaseModel):
    keyword: str


class AnalyzeResponse(BaseModel):
    topics: List[TopicItem]
    source: str  # "websearch" | "fallback" | "error"


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_topic(req: AnalyzeRequest):
    """
    根据关键词分析热门选题
    
    使用火山引擎联网搜索，获取小红书/抖音/微博热点
    """
    if not req.keyword or not req.keyword.strip():
        raise HTTPException(status_code=400, detail="关键词不能为空")
    
    try:
        topics_raw, source = analyze_trends(req.keyword.strip())
        
        # 标准化数据格式
        topics = []
        for t in topics_raw:
            if isinstance(t, str):
                # 兼容旧格式
                topics.append(TopicItem(title=t))
            elif isinstance(t, dict):
                topics.append(TopicItem(
                    title=t.get("title", ""),
                    source=t.get("source", ""),
                    summary=t.get("summary", ""),
                    outline=t.get("outline", []),
                    why_hot=t.get("why_hot", ""),
                ))
        
        return AnalyzeResponse(topics=topics, source=source)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"选题分析失败: {str(e)}")

