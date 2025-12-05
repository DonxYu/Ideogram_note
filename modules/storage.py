"""
阿里云 OSS 上传模块
支持按主题分类存储图片、音频、视频
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import oss2

load_dotenv()

OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT")
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME")
OSS_URL_PREFIX = os.getenv("OSS_URL_PREFIX")

# 懒加载 bucket 对象
_bucket = None


def _get_bucket():
    """懒加载获取 OSS bucket"""
    global _bucket
    if _bucket is None:
        try:
            auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
            _bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        except Exception as e:
            print(f"[OSS Error] 初始化失败: {e}")
            return None
    return _bucket


def _sanitize_topic(topic: str) -> str:
    """清理主题名称，移除特殊字符"""
    if not topic:
        return "default"
    safe = "".join(c for c in topic if c.isalnum() or c in "_ -").strip()
    return safe if safe else "default"


def upload_to_oss(image_data: bytes, filename: str) -> str:
    """
    上传图片二进制数据到阿里云 OSS（旧接口，保持兼容）
    
    Args:
        image_data: 图片二进制数据
        filename: 存储文件名
    
    Returns:
        成功返回可访问 URL，失败返回 None
    """
    try:
        bucket = _get_bucket()
        if bucket is None:
            return None
        bucket.put_object(filename, image_data)
        return f"{OSS_URL_PREFIX}/{filename}"
    except Exception as e:
        print(f"[OSS Error] 上传失败: {e}")
        return None


def upload_to_oss_by_topic(data: bytes, topic: str, filename: str, file_type: str = "images") -> str:
    """
    按主题上传文件到 OSS
    
    OSS 路径结构: {topic}/{file_type}/{filename}
    例如: 职场干货/images/scene_01.png
    
    Args:
        data: 文件二进制数据
        topic: 主题名称
        filename: 文件名
        file_type: 文件类型目录 (images/audio/video)
    
    Returns:
        成功返回可访问 URL，失败返回 None
    """
    try:
        bucket = _get_bucket()
        if bucket is None:
            return None
        
        safe_topic = _sanitize_topic(topic)
        oss_key = f"{safe_topic}/{file_type}/{filename}"
        
        bucket.put_object(oss_key, data)
        oss_url = f"{OSS_URL_PREFIX}/{oss_key}"
        print(f"[OSS] 上传成功: {oss_key}")
        return oss_url
        
    except Exception as e:
        print(f"[OSS Error] 上传失败: {e}")
        return None


def upload_file_to_oss_by_topic(local_path: str, topic: str, file_type: str = "images") -> str:
    """
    按主题上传本地文件到 OSS
    
    Args:
        local_path: 本地文件路径
        topic: 主题名称
        file_type: 文件类型目录 (images/audio/video)
    
    Returns:
        成功返回可访问 URL，失败返回 None
    """
    try:
        local_file = Path(local_path)
        if not local_file.exists():
            print(f"[OSS Error] 本地文件不存在: {local_path}")
            return None
        
        with open(local_file, "rb") as f:
            data = f.read()
        
        return upload_to_oss_by_topic(data, topic, local_file.name, file_type)
        
    except Exception as e:
        print(f"[OSS Error] 读取文件失败: {e}")
        return None


def is_oss_configured() -> bool:
    """检查 OSS 是否已配置"""
    return all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_ENDPOINT, OSS_BUCKET_NAME])
