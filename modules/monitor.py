"""
监控模块 - 数据采集与存储
"""
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "monitor.db"


def _get_conn():
    """获取数据库连接"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = _get_conn()
    cursor = conn.cursor()
    
    # API 调用记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 访问日志
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            ip_address TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 生成历史
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            persona TEXT,
            titles TEXT,
            content_preview TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


# 初始化数据库
init_db()


def log_api_call(model: str, tokens_in: int = 0, tokens_out: int = 0):
    """记录 API 调用"""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_calls (model, tokens_in, tokens_out) VALUES (?, ?, ?)",
            (model, tokens_in, tokens_out)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Monitor] API 日志记录失败: {e}")


def log_access(session_id: Optional[str] = None, ip_address: Optional[str] = None):
    """记录访问日志"""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO access_logs (session_id, ip_address) VALUES (?, ?)",
            (session_id or str(uuid.uuid4())[:8], ip_address)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Monitor] 访问日志记录失败: {e}")


def log_generation(topic: str, persona: str, titles: list, content_preview: str):
    """记录生成历史"""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        titles_str = " | ".join(titles) if titles else ""
        cursor.execute(
            "INSERT INTO generation_history (topic, persona, titles, content_preview) VALUES (?, ?, ?, ?)",
            (topic, persona, titles_str, content_preview[:500])
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Monitor] 生成历史记录失败: {e}")


def get_stats() -> dict:
    """获取统计数据"""
    conn = _get_conn()
    cursor = conn.cursor()
    
    # 总调用次数
    cursor.execute("SELECT COUNT(*) as cnt FROM api_calls")
    total_calls = cursor.fetchone()['cnt']
    
    # 总 Token 消耗
    cursor.execute("SELECT COALESCE(SUM(tokens_in), 0) as t_in, COALESCE(SUM(tokens_out), 0) as t_out FROM api_calls")
    token_row = cursor.fetchone()
    total_tokens_in = token_row['t_in']
    total_tokens_out = token_row['t_out']
    
    # 今日调用
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) as cnt FROM api_calls WHERE DATE(created_at) = ?", (today,))
    today_calls = cursor.fetchone()['cnt']
    
    # 今日 Token
    cursor.execute(
        "SELECT COALESCE(SUM(tokens_in), 0) as t_in, COALESCE(SUM(tokens_out), 0) as t_out FROM api_calls WHERE DATE(created_at) = ?",
        (today,)
    )
    today_token_row = cursor.fetchone()
    today_tokens_in = today_token_row['t_in']
    today_tokens_out = today_token_row['t_out']
    
    # 总访问次数
    cursor.execute("SELECT COUNT(*) as cnt FROM access_logs")
    total_access = cursor.fetchone()['cnt']
    
    # 总生成次数
    cursor.execute("SELECT COUNT(*) as cnt FROM generation_history")
    total_generations = cursor.fetchone()['cnt']
    
    conn.close()
    
    return {
        "total_calls": total_calls,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "today_calls": today_calls,
        "today_tokens_in": today_tokens_in,
        "today_tokens_out": today_tokens_out,
        "total_access": total_access,
        "total_generations": total_generations,
    }


def get_api_calls(limit: int = 50) -> list:
    """获取最近 API 调用记录"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM api_calls ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_access_logs(limit: int = 50) -> list:
    """获取最近访问日志"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM access_logs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_generation_history(limit: int = 50, search: str = None) -> list:
    """获取生成历史"""
    conn = _get_conn()
    cursor = conn.cursor()
    
    if search:
        cursor.execute(
            "SELECT * FROM generation_history WHERE topic LIKE ? OR titles LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{search}%", f"%{search}%", limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM generation_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_daily_stats(days: int = 7) -> list:
    """获取每日统计（用于趋势图）"""
    conn = _get_conn()
    cursor = conn.cursor()
    
    results = []
    for i in range(days - 1, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        cursor.execute(
            "SELECT COUNT(*) as calls, COALESCE(SUM(tokens_in + tokens_out), 0) as tokens FROM api_calls WHERE DATE(created_at) = ?",
            (date,)
        )
        row = cursor.fetchone()
        
        results.append({
            "date": date,
            "calls": row['calls'],
            "tokens": row['tokens']
        })
    
    conn.close()
    return results

