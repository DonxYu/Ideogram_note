"""
监控页面 - 密码保护
"""
import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.monitor import (
    get_stats,
    get_api_calls,
    get_access_logs,
    get_generation_history,
    get_daily_stats
)

load_dotenv()

# 页面配置
st.set_page_config(
    page_title="监控面板",
    page_icon="📊",
    layout="wide"
)

# ========== 密码验证 ==========
MONITOR_PASSWORD = os.getenv("MONITOR_PASSWORD", "admin123")

if "monitor_auth" not in st.session_state:
    st.session_state.monitor_auth = False

if not st.session_state.monitor_auth:
    st.markdown("# 🔐 监控面板")
    st.markdown("---")
    
    password = st.text_input("请输入访问密码", type="password")
    
    if st.button("登录", type="primary"):
        if password == MONITOR_PASSWORD:
            st.session_state.monitor_auth = True
            st.rerun()
        else:
            st.error("密码错误")
    
    st.stop()

# ========== 监控内容 ==========
st.markdown("# 📊 监控面板")
st.caption("API 调用统计 / 访问日志 / 生成历史")
st.markdown("---")

# 统计概览
stats = get_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总 API 调用", stats['total_calls'], f"今日 +{stats['today_calls']}")
with col2:
    st.metric("总 Token (输入)", f"{stats['total_tokens_in']:,}", f"今日 +{stats['today_tokens_in']:,}")
with col3:
    st.metric("总 Token (输出)", f"{stats['total_tokens_out']:,}", f"今日 +{stats['today_tokens_out']:,}")
with col4:
    st.metric("生成次数", stats['total_generations'])

st.markdown("---")

# 趋势图
st.markdown("### 📈 7日趋势")
daily_stats = get_daily_stats(7)

if daily_stats:
    df_daily = pd.DataFrame(daily_stats)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**API 调用次数**")
        st.bar_chart(df_daily.set_index('date')['calls'])
    with col2:
        st.markdown("**Token 消耗**")
        st.bar_chart(df_daily.set_index('date')['tokens'])

st.markdown("---")

# 详细记录
tab1, tab2, tab3 = st.tabs(["API 调用记录", "访问日志", "生成历史"])

with tab1:
    api_calls = get_api_calls(100)
    if api_calls:
        df_api = pd.DataFrame(api_calls)
        df_api = df_api[['created_at', 'model', 'tokens_in', 'tokens_out']]
        df_api.columns = ['时间', '模型', '输入Token', '输出Token']
        st.dataframe(df_api, use_container_width=True, hide_index=True)
    else:
        st.info("暂无记录")

with tab2:
    access_logs = get_access_logs(100)
    if access_logs:
        df_access = pd.DataFrame(access_logs)
        df_access = df_access[['created_at', 'session_id', 'ip_address']]
        df_access.columns = ['时间', 'Session ID', 'IP 地址']
        st.dataframe(df_access, use_container_width=True, hide_index=True)
    else:
        st.info("暂无记录")

with tab3:
    search = st.text_input("搜索话题/标题", placeholder="输入关键词...")
    history = get_generation_history(100, search if search else None)
    
    if history:
        for item in history:
            with st.expander(f"📝 {item['topic']} - {item['created_at']}"):
                st.markdown(f"**人设：** {item['persona'] or '未指定'}")
                st.markdown(f"**标题：** {item['titles']}")
                st.markdown(f"**内容预览：**\n{item['content_preview']}")
    else:
        st.info("暂无记录")

# 侧边栏 - 退出登录
with st.sidebar:
    st.markdown("### 当前状态")
    st.success("已登录")
    if st.button("退出登录"):
        st.session_state.monitor_auth = False
        st.rerun()

