"""
小红书内容工作流 - 主程序入口
"""
import streamlit as st
from dotenv import load_dotenv

# ========== OpenRouter 模型配置 ==========
AVAILABLE_MODELS = {
    "DeepSeek V3 (高情商/国产梗)": "deepseek/deepseek-chat",
    "Claude 3.5 Sonnet (拟人感最强)": "anthropic/claude-3.5-sonnet",
    "GPT-4o (逻辑严密)": "openai/gpt-4o",
    "Gemini Pro 1.5 (长文强)": "google/gemini-pro-1.5",
    "Grok 2 (马斯克/幽默)": "x-ai/grok-2-1212"
}

from ui.styles import inject_css
from ui.components import (
    init_session_state,
    render_header,
    render_sidebar,
    render_topic_selector,
    render_persona_config,
    render_content_display,
    render_image_export
)

load_dotenv()

# ========== 页面配置 ==========
st.set_page_config(
    page_title="内容工作流",
    page_icon="⌘",
    layout="wide"
)

# ========== 初始化 ==========
inject_css()
init_session_state()

# ========== 侧边栏 ==========
render_sidebar()

# ========== 主界面 ==========
render_header()  # 动态显示标题和模式

# ========== 工作流步骤 ==========
render_topic_selector()      # Step 1: 选题雷达
render_persona_config()      # Step 2: 创作配置
render_content_display()     # Step 3: 内容预览
render_image_export()        # Step 4: 导出（图文/视频）
