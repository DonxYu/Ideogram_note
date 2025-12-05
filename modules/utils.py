"""
工具模块 - 状态缓存、安全调用、统一提示、文件命名
"""
import os
import re
import json
import traceback
from pathlib import Path
from typing import Any, Callable, Optional
from functools import wraps

# 缓存目录
CACHE_DIR = Path("output/.cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ========== 文件命名工具 ==========

def sanitize_filename(name: str, max_length: int = 50) -> str:
    """
    清理文件名中的非法字符，生成安全的文件名
    
    Args:
        name: 原始名称（如主题）
        max_length: 最大长度
    
    Returns:
        安全的文件名
    """
    if not name:
        return "untitled"
    
    # 替换非法字符为下划线
    # Windows 非法字符: \ / : * ? " < > |
    # 加上空格和一些特殊符号
    illegal_chars = r'[\\/:*?"<>|\s\n\r\t]+'
    safe_name = re.sub(illegal_chars, '_', name)
    
    # 移除开头和结尾的下划线
    safe_name = safe_name.strip('_')
    
    # 限制长度
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip('_')
    
    return safe_name or "untitled"


def get_unique_dir(base_dir: Path, topic: str) -> Path:
    """
    创建基于主题的唯一目录，重复时自动添加数字后缀
    
    Args:
        base_dir: 基础目录（如 output/images）
        topic: 主题名称
    
    Returns:
        唯一的目录路径（已创建）
    
    Example:
        topic = "职场攻略"
        第一次: output/images/职场攻略/
        第二次: output/images/职场攻略_2/
        第三次: output/images/职场攻略_3/
    """
    safe_topic = sanitize_filename(topic)
    
    # 尝试基础名称
    target_dir = base_dir / safe_topic
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir
    
    # 已存在，添加数字后缀
    counter = 2
    while True:
        target_dir = base_dir / f"{safe_topic}_{counter}"
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            return target_dir
        counter += 1
        if counter > 1000:  # 防止无限循环
            raise RuntimeError(f"无法创建目录: {base_dir}/{safe_topic}")


def get_topic_output_dir(topic: str, asset_type: str = "images") -> Path:
    """
    获取基于主题的输出目录
    
    Args:
        topic: 主题名称
        asset_type: 资产类型 ("images", "audio", "video")
    
    Returns:
        目录路径（已创建）
    """
    base_dirs = {
        "images": Path("output/images"),
        "audio": Path("output/audio"),
        "video": Path("output/video"),
    }
    base_dir = base_dirs.get(asset_type, Path(f"output/{asset_type}"))
    return get_unique_dir(base_dir, topic)


# ========== 状态缓存 ==========

def save_state(key: str, data: Any) -> bool:
    """
    保存状态到本地缓存
    
    Args:
        key: 缓存键名
        data: 要缓存的数据（需支持 JSON 序列化）
    
    Returns:
        成功返回 True，失败返回 False
    """
    try:
        cache_file = CACHE_DIR / f"{key}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Cache Error] 保存 {key} 失败: {e}")
        return False


def load_state(key: str, default: Any = None) -> Any:
    """
    从本地缓存加载状态
    
    Args:
        key: 缓存键名
        default: 缓存不存在时的默认值
    
    Returns:
        缓存数据或默认值
    """
    try:
        cache_file = CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return default
    except Exception as e:
        print(f"[Cache Error] 加载 {key} 失败: {e}")
        return default


def clear_state(key: str = None) -> bool:
    """
    清除缓存
    
    Args:
        key: 指定键名，为空则清除所有缓存
    
    Returns:
        成功返回 True
    """
    try:
        if key:
            cache_file = CACHE_DIR / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            for f in CACHE_DIR.glob("*.json"):
                f.unlink()
        return True
    except Exception as e:
        print(f"[Cache Error] 清除缓存失败: {e}")
        return False


# ========== 安全调用 ==========

def safe_call(func: Callable, *args, default: Any = None, error_msg: str = None, **kwargs) -> Any:
    """
    安全调用函数，捕获所有异常
    
    Args:
        func: 要调用的函数
        *args: 位置参数
        default: 异常时的默认返回值
        error_msg: 自定义错误消息前缀
        **kwargs: 关键字参数
    
    Returns:
        函数返回值或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        prefix = error_msg or f"[{func.__name__}]"
        print(f"{prefix} 调用失败: {e}")
        traceback.print_exc()
        return default


def retry_call(func: Callable, *args, retries: int = 3, delay: float = 1.0, default: Any = None, **kwargs) -> Any:
    """
    带重试的安全调用
    
    Args:
        func: 要调用的函数
        *args: 位置参数
        retries: 最大重试次数
        delay: 重试间隔（秒）
        default: 全部失败后的默认值
        **kwargs: 关键字参数
    
    Returns:
        函数返回值或默认值
    """
    import time
    
    last_error = None
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            print(f"[Retry] 第 {attempt + 1}/{retries} 次尝试失败: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    
    print(f"[Retry] 全部 {retries} 次尝试均失败")
    return default


# ========== 结果包装 ==========

class Result:
    """统一的结果包装类"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
    
    @classmethod
    def ok(cls, data: Any = None):
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str):
        return cls(success=False, error=error)
    
    def __bool__(self):
        return self.success
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }


# ========== 素材状态 ==========

class AssetStatus:
    """素材生成状态追踪"""
    
    PENDING = "pending"      # 待生成
    GENERATING = "generating"  # 生成中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    
    def __init__(self, total: int):
        self.total = total
        self.statuses = [self.PENDING] * total
        self.paths = [None] * total
        self.errors = [None] * total
    
    def set_generating(self, index: int):
        self.statuses[index] = self.GENERATING
    
    def set_success(self, index: int, path: str):
        self.statuses[index] = self.SUCCESS
        self.paths[index] = path
    
    def set_failed(self, index: int, error: str):
        self.statuses[index] = self.FAILED
        self.errors[index] = error
    
    @property
    def success_count(self) -> int:
        return self.statuses.count(self.SUCCESS)
    
    @property
    def failed_count(self) -> int:
        return self.statuses.count(self.FAILED)
    
    @property
    def pending_indices(self) -> list:
        return [i for i, s in enumerate(self.statuses) if s == self.PENDING]
    
    @property
    def failed_indices(self) -> list:
        return [i for i, s in enumerate(self.statuses) if s == self.FAILED]
    
    @property
    def all_done(self) -> bool:
        return all(s in [self.SUCCESS, self.FAILED] for s in self.statuses)
    
    @property
    def all_success(self) -> bool:
        return all(s == self.SUCCESS for s in self.statuses)
    
    def get_status_icon(self, index: int) -> str:
        status = self.statuses[index]
        return {
            self.PENDING: "⏳",
            self.GENERATING: "🔄",
            self.SUCCESS: "✅",
            self.FAILED: "❌"
        }.get(status, "❓")
    
    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "statuses": self.statuses,
            "paths": self.paths,
            "errors": self.errors
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AssetStatus":
        obj = cls(data["total"])
        obj.statuses = data["statuses"]
        obj.paths = data["paths"]
        obj.errors = data["errors"]
        return obj


# ========== Streamlit 辅助 ==========

def init_session_key(st, key: str, default: Any = None, load_cache: bool = False):
    """
    初始化 session state 键，可选从缓存恢复
    
    Args:
        st: streamlit 模块
        key: 键名
        default: 默认值
        load_cache: 是否尝试从缓存加载
    """
    if key not in st.session_state:
        if load_cache:
            cached = load_state(key)
            st.session_state[key] = cached if cached is not None else default
        else:
            st.session_state[key] = default


def auto_save_state(st, key: str):
    """
    自动保存 session state 到缓存
    
    Args:
        st: streamlit 模块
        key: 要保存的键名
    """
    if key in st.session_state and st.session_state[key] is not None:
        save_state(key, st.session_state[key])

