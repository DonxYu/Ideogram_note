"""
人设库读取模块
"""
import os
import json

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'personas.json')


def load_personas() -> dict:
    """加载人设库"""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_categories() -> list:
    """获取所有场景分类"""
    personas = load_personas()
    return list(personas.keys())


def get_personas_by_category(category: str) -> list:
    """获取指定分类下的所有人设"""
    personas = load_personas()
    return personas.get(category, [])


def get_persona_prompt(category: str, name: str) -> str:
    """获取指定人设的完整 prompt"""
    personas = get_personas_by_category(category)
    for p in personas:
        if p['name'] == name:
            return p.get('prompt', '')
    return ''

