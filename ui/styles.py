"""
终端风格 CSS 样式
"""
import streamlit as st

CSS = """
<style>
    /* 导入 JetBrains Mono 等宽字体 */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    
    /* 全局样式 - 等宽字体 */
    .stApp, .stApp * {
        font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', 'Consolas', monospace !important;
    }
    
    /* 背景 */
    .stApp {
        background: #0d1117;
    }
    
    /* 主标题 - 终端风格 */
    h1 {
        color: #7ee787 !important;
        font-weight: 600 !important;
        font-size: 1.8rem !important;
        letter-spacing: 0;
        padding: 0;
        margin-bottom: 0.5rem !important;
    }
    
    h1::before {
        content: "$ ";
        color: #58a6ff;
    }
    
    /* 副标题 */
    h2 {
        color: #58a6ff !important;
        font-weight: 500 !important;
        font-size: 1.2rem !important;
        border: none !important;
        padding: 0 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    h2::before {
        content: "// ";
        color: #6e7681;
    }
    
    h3 {
        color: #c9d1d9 !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        border: none !important;
        padding: 0 !important;
    }
    
    h3::before {
        content: "# ";
        color: #6e7681;
    }
    
    /* 段落和文字 */
    p, span, label, .stMarkdown {
        color: #c9d1d9 !important;
        font-size: 14px !important;
    }
    
    /* Caption */
    .stCaption, small {
        color: #6e7681 !important;
        font-size: 12px !important;
    }
    
    /* 按钮 - 终端命令风格 */
    .stButton > button {
        background: transparent !important;
        color: #7ee787 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button::before {
        content: "> ";
        color: #58a6ff;
    }
    
    .stButton > button:hover {
        background: #161b22 !important;
        border-color: #58a6ff !important;
        color: #58a6ff !important;
        box-shadow: 0 0 10px rgba(88, 166, 255, 0.2) !important;
    }
    
    .stButton > button:active {
        background: #21262d !important;
    }
    
    /* Primary 按钮 */
    .stButton > button[kind="primary"] {
        background: #238636 !important;
        border-color: #238636 !important;
        color: #ffffff !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #2ea043 !important;
        border-color: #2ea043 !important;
        box-shadow: 0 0 15px rgba(46, 160, 67, 0.3) !important;
    }
    
    /* 输入框 - 终端输入风格 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
        color: #c9d1d9 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 14px !important;
        caret-color: #58a6ff !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 1px #58a6ff !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #484f58 !important;
    }
    
    /* 下拉选择框 */
    .stSelectbox > div > div {
        background: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #58a6ff !important;
    }
    
    [data-baseweb="select"] {
        background: #0d1117 !important;
    }
    
    [data-baseweb="select"] * {
        color: #c9d1d9 !important;
        background: #0d1117 !important;
    }
    
    /* Radio 按钮 - 选项列表风格 */
    .stRadio > div {
        background: #161b22;
        padding: 1rem;
        border-radius: 4px;
        border: 1px solid #30363d;
    }
    
    .stRadio > div > label {
        color: #c9d1d9 !important;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        transition: all 0.15s ease;
        border: 1px solid transparent;
    }
    
    .stRadio > div > label::before {
        content: "○ ";
        color: #6e7681;
    }
    
    .stRadio > div > label:hover {
        background: #21262d;
        border-color: #30363d;
    }
    
    .stRadio > div > label[data-checked="true"]::before {
        content: "● ";
        color: #7ee787;
    }
    
    /* 成功提示 */
    .stSuccess {
        background: rgba(46, 160, 67, 0.15) !important;
        border: 1px solid #238636 !important;
        border-radius: 4px !important;
        color: #7ee787 !important;
    }
    
    /* 信息提示 */
    .stInfo {
        background: rgba(88, 166, 255, 0.1) !important;
        border: 1px solid #1f6feb !important;
        border-radius: 4px !important;
        color: #58a6ff !important;
    }
    
    /* 警告提示 */
    .stWarning {
        background: rgba(210, 153, 34, 0.15) !important;
        border: 1px solid #9e6a03 !important;
        border-radius: 4px !important;
        color: #d29922 !important;
    }
    
    /* 分割线 */
    hr {
        border: none !important;
        height: 1px !important;
        background: #21262d !important;
        margin: 2rem 0 !important;
    }
    
    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background: #010409 !important;
        border-right: 1px solid #21262d !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #8b949e !important;
    }
    
    /* Expander - 折叠面板 */
    .stExpander {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
    }
    
    .stExpander > div > div > div {
        color: #c9d1d9 !important;
    }
    
    /* 代码块 */
    .stCodeBlock, code, pre {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
        color: #c9d1d9 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* 图片容器 */
    .stImage {
        border-radius: 4px;
        overflow: hidden;
        border: 1px solid #30363d;
    }
    
    /* 下载按钮 */
    .stDownloadButton > button {
        background: #21262d !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
    }
    
    .stDownloadButton > button:hover {
        background: #30363d !important;
        border-color: #58a6ff !important;
        color: #58a6ff !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #58a6ff !important;
    }
    
    /* 隐藏默认 footer */
    footer {
        visibility: hidden;
    }
    
    /* 隐藏 hamburger menu */
    #MainMenu {
        visibility: hidden;
    }
    
    /* 滚动条 - 终端风格 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0d1117;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }
    
    /* 标题卡片 */
    .title-card {
        background: #0d1117;
        border-left: 2px solid #7ee787;
        padding: 0.6rem 1rem;
        margin: 0.4rem 0;
        font-size: 14px;
    }
    
    .title-card .num {
        color: #7ee787;
        font-weight: 600;
    }
</style>
"""


def inject_css():
    """注入终端风格 CSS"""
    st.markdown(CSS, unsafe_allow_html=True)

