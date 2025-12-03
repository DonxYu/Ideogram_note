"""
小红书爆款工作流 - 主程序入口
"""
import streamlit as st
from dotenv import load_dotenv

from ui.styles import inject_css
from ui.components import (
    init_session_state,
    render_sidebar,
    render_topic_selector,
    render_persona_config,
    render_content_display,
    render_image_export
)

load_dotenv()

# ========== 页面配置 ==========
st.set_page_config(
    page_title="小红书爆款工作流",
    page_icon="⌘",
    layout="wide"
)

# ========== 初始化 ==========
inject_css()
init_session_state()

# ========== 侧边栏 ==========
render_sidebar()

# ========== 主界面 ==========
st.markdown("# 小红书工作流（长文案+提示词版）")
st.caption("选题 → 创作 → 分镜 → 导出")
st.markdown("---")

# ========== 工作流步骤 ==========
render_topic_selector()      # Step 1: 选题雷达
render_persona_config()      # Step 2: 创作配置
render_content_display()     # Step 3: 内容展示
render_image_export()        # Step 4: 视觉与交付
