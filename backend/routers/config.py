"""
配置 API（语音列表、模型列表、人设库等）
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

from modules.persona import get_categories, get_personas_by_category
from modules.audio import EDGE_VOICES, VOLC_VOICES

router = APIRouter()


# ========== 模型配置 ==========

AVAILABLE_MODELS = {
    "DeepSeek V3 (高情商/国产梗)": "deepseek/deepseek-chat",
    "Claude 3.5 Sonnet (拟人感最强)": "anthropic/claude-3.5-sonnet",
    "GPT-4o (逻辑严密)": "openai/gpt-4o",
    "Gemini Pro 1.5 (长文强)": "google/gemini-pro-1.5",
    "Grok 2 (马斯克/幽默)": "x-ai/grok-2-1212",
}

IMAGE_PROVIDERS = {
    "replicate": "Replicate (二次元)",
    "volcengine": "火山引擎 (Seedream)",
}

TTS_PROVIDERS = {
    "edge": "Edge TTS (免费)",
    "volcengine": "火山引擎 TTS",
}


class VoiceOption(BaseModel):
    label: str
    value: str


class ModelOption(BaseModel):
    label: str
    value: str


class PersonaItem(BaseModel):
    name: str
    prompt: str


class PersonaCategory(BaseModel):
    category: str
    personas: List[PersonaItem]


@router.get("/models")
async def get_models():
    """获取可用的 LLM 模型列表"""
    return {
        "models": [
            ModelOption(label=label, value=value)
            for label, value in AVAILABLE_MODELS.items()
        ]
    }


@router.get("/image-providers")
async def get_image_providers():
    """获取生图服务列表"""
    return {
        "providers": [
            {"label": label, "value": value}
            for value, label in IMAGE_PROVIDERS.items()
        ]
    }


@router.get("/tts-providers")
async def get_tts_providers():
    """获取 TTS 服务列表"""
    return {
        "providers": [
            {"label": label, "value": value}
            for value, label in TTS_PROVIDERS.items()
        ]
    }


@router.get("/voices")
async def get_voices():
    """获取所有可用语音角色"""
    return {
        "edge": [
            VoiceOption(label=label, value=value)
            for label, value in EDGE_VOICES.items()
        ],
        "volcengine": [
            VoiceOption(label=label, value=value)
            for label, value in VOLC_VOICES.items()
        ],
    }


@router.get("/voices/{provider}")
async def get_voices_by_provider(provider: str):
    """获取指定 TTS 服务的语音角色"""
    if provider == "edge":
        voices = EDGE_VOICES
    elif provider == "volcengine":
        voices = VOLC_VOICES
    else:
        return {"voices": []}
    
    return {
        "voices": [
            VoiceOption(label=label, value=value)
            for label, value in voices.items()
        ]
    }


@router.get("/personas")
async def get_personas():
    """获取所有人设分类和人设"""
    categories = get_categories()
    
    result = []
    for cat in categories:
        personas = get_personas_by_category(cat)
        result.append(PersonaCategory(
            category=cat,
            personas=[
                PersonaItem(name=p["name"], prompt=p.get("prompt", ""))
                for p in personas
            ],
        ))
    
    return {"categories": result}


@router.get("/personas/{category}")
async def get_personas_in_category(category: str):
    """获取指定分类下的人设"""
    personas = get_personas_by_category(category)
    return {
        "personas": [
            PersonaItem(name=p["name"], prompt=p.get("prompt", ""))
            for p in personas
        ]
    }

