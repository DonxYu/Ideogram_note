"""
阿里云 OSS 上传模块
"""
import os
from dotenv import load_dotenv
import oss2

load_dotenv()

OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT")
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME")
OSS_URL_PREFIX = os.getenv("OSS_URL_PREFIX")


def upload_to_oss(image_data: bytes, filename: str) -> str:
    """
    上传图片二进制数据到阿里云 OSS
    
    Args:
        image_data: 图片二进制数据
        filename: 存储文件名
    
    Returns:
        成功返回可访问 URL，失败返回 None
    """
    try:
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        bucket.put_object(filename, image_data)
        return f"{OSS_URL_PREFIX}/{filename}"
    except Exception as e:
        print(f"[OSS Error] 上传失败: {e}")
        return None
