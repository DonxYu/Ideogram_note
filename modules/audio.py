"""
音频生成模块 (Edge TTS + 火山引擎 TTS)
支持并发生成：EdgeTTS 使用 asyncio.Semaphore，火山引擎使用 ThreadPoolExecutor
支持主题命名：文件按主题组织
"""
import os
import asyncio
import uuid
import json
import base64
from pathlib import Path
from typing import Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from modules.utils import sanitize_filename, get_unique_dir
from modules.storage import upload_file_to_oss_by_topic

load_dotenv()

# 默认输出目录
DEFAULT_OUTPUT_DIR = Path("output/audio")
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ========== 单段音频生成（核心函数） ==========

def _generate_single_edge(text: str, voice: str, index: int) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 Edge TTS 生成单段音频
    
    Returns:
        (文件路径, 错误信息) - 成功时错误为 None
    """
    try:
        if not text:
            return None, "文本为空"
        
        import edge_tts
        
        file_path = str(DEFAULT_OUTPUT_DIR / f"scene_{index+1:02d}.mp3")
        
        async def _run():
            # rate="+50%" 实现 1.5 倍速
            communicate = edge_tts.Communicate(text, voice, rate="+50%")
            await communicate.save(file_path)
        
        asyncio.run(_run())
        
        if os.path.exists(file_path):
            print(f"[Edge TTS] 场景 {index+1} 完成: {file_path}")
            return file_path, None
        else:
            return None, "文件生成失败"
            
    except Exception as e:
        error_msg = str(e)
        print(f"[Edge TTS Error] 场景 {index+1} 失败: {error_msg}")
        return None, error_msg


def _generate_single_volc(text: str, voice: str, index: int) -> Tuple[Optional[str], Optional[str]]:
    """
    使用火山引擎 TTS 生成单段音频
    
    Returns:
        (文件路径, 错误信息)
    """
    import requests
    
    try:
        if not text:
            return None, "文本为空"
        
        appid = os.getenv("VOLC_TTS_APPID")
        token = os.getenv("VOLC_TTS_TOKEN")
        cluster = os.getenv("VOLC_TTS_CLUSTER", "volcano_tts")
        uid = os.getenv("VOLC_TTS_UID", "user_001")
        resource_id = os.getenv("VOLC_TTS_RESOURCE_ID", "volc.tts_async.default")
        
        if not appid or not token:
            return None, "缺少 VOLC_TTS_APPID 或 VOLC_TTS_TOKEN"
        
        file_path = str(DEFAULT_OUTPUT_DIR / f"scene_{index+1:02d}.mp3")
        
        api_url = "https://openspeech.bytedance.com/api/v1/tts"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{token}",
        }
        
        request_json = {
            "app": {"appid": appid, "token": token, "cluster": cluster},
            "user": {"uid": uid},
            "audio": {
                "voice_type": voice,
                "encoding": "mp3",
                "speed_ratio": 1.5,  # 1.5 倍速
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
                "extra_param": json.dumps({"aigc_watermark": False})
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "operation": "query"
            }
        }
        
        resp = requests.post(api_url, headers=headers, json=request_json, timeout=60)
        
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        
        # 解析 JSON 响应
        result = resp.json()
        
        # 检查返回码 (3000 = 成功)
        if result.get("code") != 3000:
            return None, f"API错误: {result.get('message', 'Unknown')}"
        
        # Base64 解码音频数据
        audio_base64 = result.get("data", "")
        if not audio_base64:
            return None, "返回的音频数据为空"
        
        audio_data = base64.b64decode(audio_base64)
        
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        print(f"[Volc TTS] 场景 {index+1} 完成: {file_path} ({len(audio_data)} bytes)")
        return file_path, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Volc TTS Error] 场景 {index+1} 失败: {error_msg}")
        return None, error_msg


# ========== 兼容旧接口 ==========

def generate_edge_audio(text: str, voice: str = "zh-CN-XiaoxiaoNeural", file_path: str = None) -> str:
    """使用 Edge TTS 生成音频（兼容旧接口）"""
    if not file_path:
        file_path = str(DEFAULT_OUTPUT_DIR / f"edge_{uuid.uuid4().hex[:8]}.mp3")
    
    try:
        import edge_tts
        
        async def _run():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(file_path)
        
        asyncio.run(_run())
        
        if os.path.exists(file_path):
            print(f"[Edge TTS] 生成成功: {file_path}")
            return file_path
    except Exception as e:
        print(f"[Edge TTS Error] {e}")
    
    return None


def generate_volc_audio(text: str, voice_type: str = "zh_female_meilinvyou_moon_bigtts", file_path: str = None) -> str:
    """使用火山引擎 TTS 生成音频（兼容旧接口）"""
    import requests
    
    appid = os.getenv("VOLC_TTS_APPID")
    token = os.getenv("VOLC_TTS_TOKEN")
    cluster = os.getenv("VOLC_TTS_CLUSTER", "volcano_tts")
    uid = os.getenv("VOLC_TTS_UID", "user_001")
    resource_id = os.getenv("VOLC_TTS_RESOURCE_ID", "volc.tts_async.default")
    
    if not appid or not token:
        print("[Volc TTS Error] 缺少 VOLC_TTS_APPID 或 VOLC_TTS_TOKEN")
        return None
    
    if not file_path:
        file_path = str(DEFAULT_OUTPUT_DIR / f"volc_{uuid.uuid4().hex[:8]}.mp3")
    
    api_url = "https://openspeech.bytedance.com/api/v1/tts"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer;{token}",
    }
    
    request_json = {
        "app": {"appid": appid, "token": token, "cluster": cluster},
        "user": {"uid": uid},
        "audio": {
            "voice_type": voice_type,
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "operation": "query"
        }
    }
    
    try:
        resp = requests.post(api_url, headers=headers, json=request_json, timeout=60)
        
        if resp.status_code != 200:
            print(f"[Volc TTS Error] HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        
        # 解析 JSON 响应
        result = resp.json()
        
        # 检查返回码 (3000 = 成功)
        if result.get("code") != 3000:
            print(f"[Volc TTS Error] API错误: {result.get('message', 'Unknown')}")
            return None
        
        # Base64 解码音频数据
        audio_base64 = result.get("data", "")
        if not audio_base64:
            print("[Volc TTS Error] 返回的音频数据为空")
            return None
        
        audio_data = base64.b64decode(audio_base64)
        
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        print(f"[Volc TTS] 生成成功: {file_path} ({len(audio_data)} bytes)")
        return file_path
        
    except Exception as e:
        print(f"[Volc TTS Error] {e}")
        return None


# ========== 统一入口 ==========

def generate_audio(text: str, provider: str = "edge", voice: str = None, output_path: str = None) -> str:
    """统一音频生成入口"""
    if provider == "edge":
        voice = voice or "zh-CN-XiaoxiaoNeural"
        return generate_edge_audio(text, voice, output_path)
    elif provider == "volcengine":
        voice = voice or "zh_female_meilinvyou_moon_bigtts"
        return generate_volc_audio(text, voice, output_path)
    else:
        print(f"[Audio Error] 未知的 provider: {provider}")
        return None


# 并发配置
EDGE_SEMAPHORE_LIMIT = 3  # EdgeTTS 并发限制（防止被微软封 IP）
VOLC_MAX_WORKERS = 5  # 火山引擎线程池大小


async def _generate_edge_async(text: str, voice: str, index: int, semaphore: asyncio.Semaphore, output_dir: Path = None, topic: str = None) -> Tuple[int, Optional[str]]:
    """异步生成单段 Edge TTS 音频（带信号量限制）"""
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    async with semaphore:
        try:
            if not text:
                return index, None
            
            import edge_tts
            
            # 文件命名：主题_scene_01.mp3
            safe_topic = sanitize_filename(topic) if topic else ""
            filename = f"{safe_topic}_scene_{index+1:02d}.mp3" if safe_topic else f"scene_{index+1:02d}.mp3"
            file_path = str(output_dir / filename)
            
            # rate="+50%" 实现 1.5 倍速
            communicate = edge_tts.Communicate(text, voice, rate="+50%")
            await communicate.save(file_path)
            
            if os.path.exists(file_path):
                print(f"[Edge TTS] 场景 {index+1} 完成")
                # 上传到 OSS（按主题分类）
                oss_url = None
                if topic:
                    oss_url = upload_file_to_oss_by_topic(file_path, topic, "audio")
                return index, oss_url or file_path
            else:
                return index, None
                
        except Exception as e:
            print(f"[Edge TTS Error] 场景 {index+1} 失败: {e}")
            return index, None


def _generate_edge_concurrent(scenes: list, voice: str, output_dir: Path = None, topic: str = None) -> list:
    """EdgeTTS 异步并发生成"""
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    async def _run_all():
        semaphore = asyncio.Semaphore(EDGE_SEMAPHORE_LIMIT)
        tasks = []
        
        for i, scene in enumerate(scenes):
            narration = scene.get("narration", "")
            task = _generate_edge_async(narration, voice, i, semaphore, output_dir, topic)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    # 运行异步任务
    raw_results = asyncio.run(_run_all())
    
    # 整理结果（保持顺序）
    audio_paths = [None] * len(scenes)
    for result in raw_results:
        if isinstance(result, Exception):
            continue
        index, path = result
        audio_paths[index] = path
    
    return audio_paths


def _generate_volc_concurrent(scenes: list, voice: str, output_dir: Path = None, topic: str = None) -> list:
    """火山引擎 ThreadPoolExecutor 并发生成"""
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    def _generate_one(args):
        index, scene = args
        narration = scene.get("narration", "")
        if not narration:
            return index, None
        
        # 文件命名：主题_scene_01.mp3
        safe_topic = sanitize_filename(topic) if topic else ""
        filename = f"{safe_topic}_scene_{index+1:02d}.mp3" if safe_topic else f"scene_{index+1:02d}.mp3"
        file_path = str(output_dir / filename)
        
        path, _ = _generate_single_volc(narration, voice, index)
        # 如果成功，重命名到正确位置
        if path and os.path.exists(path):
            import shutil
            shutil.move(path, file_path)
            # 上传到 OSS（按主题分类）
            oss_url = None
            if topic:
                oss_url = upload_file_to_oss_by_topic(file_path, topic, "audio")
            return index, oss_url or file_path
        return index, None
    
    audio_paths = [None] * len(scenes)
    
    with ThreadPoolExecutor(max_workers=VOLC_MAX_WORKERS) as executor:
        futures = {executor.submit(_generate_one, (i, scene)): i for i, scene in enumerate(scenes)}
        
        for future in as_completed(futures):
            try:
                index, path = future.result()
                audio_paths[index] = path
            except Exception as e:
                index = futures[future]
                print(f"[Volc TTS Error] 场景 {index+1} Future 异常: {e}")
    
    return audio_paths


def generate_audio_for_scenes(scenes: list, provider: str = "edge", voice: str = None, topic: str = None) -> list:
    """
    批量为分镜生成音频（并发版本）
    
    文件按主题组织，重复生成时自动添加数字后缀。
    
    Args:
        scenes: 分镜列表
        provider: "edge" 或 "volcengine"
        voice: 语音角色
        topic: 主题名称（用于创建子目录和文件命名）
    
    Returns:
        音频路径列表（顺序与 scenes 一致，失败项为 None）
    """
    if not scenes:
        return []
    
    voice = voice or ("zh-CN-XiaoxiaoNeural" if provider == "edge" else "zh_female_meilinvyou_moon_bigtts")
    
    # 创建主题目录
    if topic:
        output_dir = get_unique_dir(DEFAULT_OUTPUT_DIR, topic)
        print(f"[Audio] 输出目录: {output_dir}")
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    
    print(f"[Audio] 开始并发生成 {len(scenes)} 段音频 ({provider})...")
    
    if provider == "edge":
        audio_paths = _generate_edge_concurrent(scenes, voice, output_dir, topic)
    else:
        audio_paths = _generate_volc_concurrent(scenes, voice, output_dir, topic)
    
    success_count = sum(1 for p in audio_paths if p is not None)
    print(f"[Audio] 并发生成完成: {success_count}/{len(scenes)} 成功")
    
    return audio_paths


def generate_single_audio(scene: dict, index: int, provider: str = "edge", voice: str = None, output_dir: Path = None, topic: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    生成单段音频（用于重试）
    
    Args:
        scene: 分镜字典，需包含 'narration' 字段
        index: 场景索引（0-based）
        provider: "edge" 或 "volcengine"
        voice: 语音角色
        output_dir: 输出目录
        topic: 主题名称
    
    Returns:
        (文件路径, 错误信息)
    """
    narration = scene.get("narration", "")
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    
    # 文件命名：主题_scene_01.mp3
    safe_topic = sanitize_filename(topic) if topic else ""
    filename = f"{safe_topic}_scene_{index+1:02d}.mp3" if safe_topic else f"scene_{index+1:02d}.mp3"
    file_path = str(output_dir / filename)
    
    if provider == "edge":
        voice = voice or "zh-CN-XiaoxiaoNeural"
        path, error = _generate_single_edge(narration, voice, index)
        # 移动到正确位置
        if path and os.path.exists(path) and path != file_path:
            import shutil
            shutil.move(path, file_path)
            return file_path, None
        return path, error
    elif provider == "volcengine":
        voice = voice or "zh_female_meilinvyou_moon_bigtts"
        path, error = _generate_single_volc(narration, voice, index)
        if path and os.path.exists(path) and path != file_path:
            import shutil
            shutil.move(path, file_path)
            return file_path, None
        return path, error
    else:
        return None, f"未知的 provider: {provider}"


# ========== 语音角色列表 ==========

EDGE_VOICES = {
    "小晓 (女)": "zh-CN-XiaoxiaoNeural",
    "云扬 (男)": "zh-CN-YunyangNeural",
    "云希 (男)": "zh-CN-YunxiNeural",
    "晓涵 (女)": "zh-CN-XiaohanNeural",
    "晓墨 (女)": "zh-CN-XiaomoNeural",
    "晓秋 (女)": "zh-CN-XiaoqiuNeural",
    "晓睿 (女)": "zh-CN-XiaoruiNeural",
}

VOLC_VOICES = {
    "魅力女声": "zh_female_meilinvyou_moon_bigtts",
    "甜美女声": "zh_female_tianmei_moon_bigtts",
    "知性女声": "zh_female_zhixing_moon_bigtts",
    "温柔女声": "zh_female_wenrou_moon_bigtts",
    "磁性男声": "zh_male_cixing_moon_bigtts",
    "阳光男声": "zh_male_yangguang_moon_bigtts",
}

