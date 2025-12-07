"""
选题分析 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from modules.trend import analyze_trends

router = APIRouter()

# 简单内存缓存（生产环境建议用 Redis）
_topics_cache: Dict[str, dict] = {}


class TopicItem(BaseModel):
    title: str
    source: str = ""
    summary: str = ""
    outline: List[str] = []
    why_hot: str = ""


class AnalyzeRequest(BaseModel):
    keyword: str
    mode: str = "websearch"  # "websearch" | "llm"


class AnalyzeResponse(BaseModel):
    topics: List[TopicItem]
    source: str  # "websearch" | "fallback" | "error"


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_topic(req: AnalyzeRequest):
    """
    根据关键词分析热门选题
    
    使用火山引擎联网搜索，获取小红书/抖音/微博热点
    支持 6 小时缓存，相同关键词直接返回缓存结果
    """
    if not req.keyword or not req.keyword.strip():
        raise HTTPException(status_code=400, detail="关键词不能为空")
    
    # 统一关键词格式（小写，避免大小写重复）
    keyword = req.keyword.strip().lower()
    
    # 快速模式：直接用 LLM 推荐（不联网搜索）
    if req.mode == "llm":
        print(f"[Topics LLM Mode] 快速推荐: {keyword}")
        topics_raw, source = analyze_trends(req.keyword.strip(), force_fallback=True)
        
        topics = []
        for t in topics_raw:
            if isinstance(t, str):
                topics.append(TopicItem(title=t))
            elif isinstance(t, dict):
                topics.append(TopicItem(
                    title=t.get("title", ""),
                    source=t.get("source", "AI推荐"),
                    summary=t.get("summary", ""),
                    outline=t.get("outline", []),
                    why_hot=t.get("why_hot", ""),
                ))
        
        return AnalyzeResponse(topics=topics, source="llm")
    
    # 检查缓存（仅 websearch 模式）
    if keyword in _topics_cache:
        cached = _topics_cache[keyword]
        cached_time = datetime.fromisoformat(cached['timestamp'])
        
        # 6小时内有效
        if datetime.now() - cached_time < timedelta(hours=6):
            print(f"[Topics Cache Hit] 使用缓存数据: {keyword}")
            return AnalyzeResponse(
                topics=cached['topics'],
                source=cached['source'] + "_cached"
            )
        else:
            # 缓存过期，删除
            print(f"[Topics Cache Expired] 缓存已过期: {keyword}")
            del _topics_cache[keyword]
    
    # 缓存未命中，执行实际搜索
    print(f"[Topics Cache Miss] 执行实际搜索: {keyword}")
    
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
        
        # 只缓存成功的搜索结果（source == "websearch"）
        if source == "websearch" and topics:
            _topics_cache[keyword] = {
                'topics': [t.dict() for t in topics],
                'source': source,
                'timestamp': datetime.now().isoformat()
            }
            print(f"[Topics Cache Saved] 缓存已保存: {keyword}, 过期时间: {datetime.now() + timedelta(hours=6)}")
        else:
            print(f"[Topics Cache Skip] 跳过缓存（source={source}，仅缓存成功的websearch结果）")
        
        return AnalyzeResponse(topics=topics, source=source)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"选题分析失败: {str(e)}")

