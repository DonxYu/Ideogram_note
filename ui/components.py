"""
UI 组件模块
"""
import os
import time
import streamlit as st
import streamlit.components.v1 as components

from modules.trend import analyze_trends
from modules.crawler import fetch_note_content
from modules.writer import generate_note_package
# from modules.painter import generate_images_with_ideogram  # 断开生图链接
from modules.persona import get_categories, get_personas_by_category
from modules.monitor import log_access


def init_session_state():
    """初始化 Session State"""
    if "topics" not in st.session_state:
        st.session_state.topics = []
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = None
    if "note_result" not in st.session_state:
        st.session_state.note_result = None
    if "image_urls" not in st.session_state:
        st.session_state.image_urls = []
    # 访问日志（每个 session 只记录一次）
    if "access_logged" not in st.session_state:
        st.session_state.access_logged = True
        log_access()


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### 系统状态")
        
        openrouter_ok = os.getenv("OPENROUTER_API_KEY")
        replicate_ok = os.getenv("REPLICATE_API_TOKEN")
        oss_ok = os.getenv("OSS_ACCESS_KEY_ID")
        
        st.markdown(f"""
```
OPENROUTER  {'[OK]' if openrouter_ok else '[--]'}
REPLICATE   {'[OK]' if replicate_ok else '[--]'}
ALIYUN_OSS  {'[OK]' if oss_ok else '[--]'}
```
        """)
        
        st.markdown("---")
        
        with st.expander("环境变量"):
            manual_openrouter = st.text_input(
                "OPENROUTER_API_KEY", 
                type="password", 
                label_visibility="collapsed", 
                placeholder="sk-or-..."
            )
            manual_replicate = st.text_input(
                "REPLICATE_API_TOKEN", 
                type="password", 
                label_visibility="collapsed", 
                placeholder="r8_..."
            )
            if manual_openrouter:
                os.environ["OPENROUTER_API_KEY"] = manual_openrouter
            if manual_replicate:
                os.environ["REPLICATE_API_TOKEN"] = manual_replicate


def render_topic_selector():
    """Step 1: 选题雷达"""
    st.markdown("## 第一步：选题雷达")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input(
            "keyword",
            placeholder="输入关键词：酒局妆容 / 年终奖谈判 ...",
            label_visibility="collapsed"
        )
    with col2:
        analyze_btn = st.button("开始分析", type="primary", use_container_width=True)
    
    if analyze_btn and keyword:
        with st.spinner("分析中..."):
            topics = analyze_trends(keyword)
            st.session_state.topics = topics
            st.session_state.selected_topic = None
            st.session_state.note_result = None
            st.session_state.image_urls = []
    
    if st.session_state.topics:
        st.markdown("### 热门话题")
        selected = st.radio(
            "选择话题",
            st.session_state.topics,
            index=None,
            key="topic_radio",
            label_visibility="collapsed"
        )
        if selected:
            st.session_state.selected_topic = selected
    
    st.markdown("---")


def render_persona_config():
    """Step 2: 创作配置"""
    st.markdown("## 第二步：创作配置")
    
    if not st.session_state.selected_topic:
        st.info("请先在第一步选择话题")
        st.markdown("---")
        return
    
    st.success(f"已选：{st.session_state.selected_topic}")
    st.markdown("### 人设选择")
    
    # 赛道选择
    categories = get_categories()
    category_options = categories + ["自定义"]
    
    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox(
            "赛道",
            category_options,
            index=0,
            key="category_select"
        )
    
    persona_text = None
    
    if selected_category == "自定义":
        # 自定义人设
        with col2:
            persona_text = st.text_input(
                "人设风格", 
                placeholder="治愈系姐姐 / 毒舌闺蜜 ..."
            )
    else:
        # 根据赛道筛选人设
        personas = get_personas_by_category(selected_category)
        persona_options = [p['name'] for p in personas]
        
        with col2:
            selected_persona_idx = st.selectbox(
                "人设",
                range(len(persona_options)),
                format_func=lambda x: persona_options[x],
                key="persona_select"
            )
        
        if personas:
            selected_persona = personas[selected_persona_idx]
            persona_text = selected_persona.get('prompt', '')
            
            with st.expander(f"查看 {selected_persona['name']} 人设"):
                st.code(persona_text, language=None)
    
    # 参考链接
    ref_url = st.text_input("参考链接（可选）", placeholder="https://xiaohongshu.com/...")
    
    st.markdown("")
    generate_btn = st.button("开始生成", type="primary", use_container_width=True)
    
    if generate_btn:
        if not persona_text:
            st.warning("请先选择人设")
        else:
            with st.status("生成中...", expanded=True) as status:
                ref_content = None
                if ref_url:
                    status.update(label="📥 正在抓取参考内容...")
                    ref_data = fetch_note_content(ref_url)
                    if ref_data:
                        ref_content = f"标题：{ref_data.get('title', '')}\n\n{ref_data.get('content', '')}"
                        st.write("参考内容已加载")
                    else:
                        st.write("抓取失败，将创作原创内容")
                
                status.update(label="🧠 正在构思标题...")
                time.sleep(0.3)
                
                status.update(label="✍️ 正在撰写正文 & 设计分镜...")
                result = generate_note_package(
                    topic=st.session_state.selected_topic,
                    persona=persona_text,
                    reference_text=ref_content
                )
                
                status.update(label="✅ 生成完成!", state="complete")
                st.session_state.note_result = result
                st.session_state.image_urls = []
    
    st.markdown("---")


def render_content_display():
    """Step 3: 内容展示"""
    st.markdown("## 第三步：内容输出")
    
    if not st.session_state.note_result:
        st.info("请先在第二步生成内容")
        st.markdown("---")
        return
    
    result = st.session_state.note_result
    
    # 标题
    st.markdown("### 备选标题")
    titles = result.get("titles", [])
    for i, title in enumerate(titles):
        st.markdown(
            f'<div class="title-card"><span class="num">[{i}]</span> {title}</div>',
            unsafe_allow_html=True
        )
    
    # 正文
    st.markdown("### 正文内容")
    content = result.get("content", "")
    st.text_area("content", content, height=400, key="content_area", label_visibility="collapsed")
    
    # 字数统计
    char_count = len(content.replace(" ", "").replace("\n", ""))
    st.caption(f"字数：{char_count}")
    
    st.markdown("---")


def render_image_export():
    """Step 4: 视觉脚本与交付"""
    st.markdown("## 第四步：视觉脚本")
    
    if not st.session_state.note_result:
        st.info("请先完成第三步")
        return
    
    result = st.session_state.note_result
    visual_script = result.get("visual_script", [])
    
    if not visual_script:
        st.warning("visual_script 为空")
        st.markdown("---")
        return
    
    # 展示视觉分镜脚本
    st.markdown(f"### 分镜列表 ({len(visual_script)} 张)")
    
    for i, item in enumerate(visual_script):
        scene_type = item.get('scene_type', f'场景{i+1}')
        description_cn = item.get('description_cn', '')
        prompt_en = item.get('prompt_en', '')
        
        with st.expander(f"[{i}] {scene_type}", expanded=(i == 0)):
            st.markdown(f"**画面描述：** {description_cn}")
            st.markdown("**英文提示词：**")
            st.code(prompt_en, language="text")
            
            # 复制按钮
            copy_key = f"copy_btn_{i}"
            if st.button("📋 复制提示词", key=copy_key, use_container_width=True):
                # 转义特殊字符
                escaped_prompt = prompt_en.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                components.html(f'''
                    <script>navigator.clipboard.writeText(`{escaped_prompt}`);</script>
                ''', height=0)
                st.toast(f"已复制第 {i+1} 张分镜提示词")
    
    st.markdown("---")
    
    # 导出
    st.markdown("### 导出")
    
    titles = result.get("titles", [])
    content = result.get("content", "")
    
    # 构建 Markdown 内容
    md_content = f"# {st.session_state.selected_topic}\n\n"
    
    # 标题部分
    md_content += "## 备选标题\n\n"
    for i, title in enumerate(titles):
        md_content += f"{i+1}. {title}\n"
    
    # 正文部分
    md_content += f"\n## 正文\n\n{content}\n\n"
    
    # 视觉脚本表格
    md_content += "## 视觉分镜脚本\n\n"
    md_content += "| 序号 | 类型 | 中文描述 | 英文提示词 |\n"
    md_content += "|------|------|----------|------------|\n"
    
    for i, item in enumerate(visual_script):
        scene_type = item.get('scene_type', f'场景{i+1}')
        description_cn = item.get('description_cn', '').replace('\n', ' ').replace('|', '\\|')
        prompt_en = item.get('prompt_en', '').replace('\n', ' ').replace('|', '\\|')
        md_content += f"| {i+1} | {scene_type} | {description_cn} | {prompt_en} |\n"
    
    # 单独列出提示词（方便复制）
    md_content += "\n## 提示词快速复制\n\n"
    for i, item in enumerate(visual_script):
        scene_type = item.get('scene_type', f'场景{i+1}')
        prompt_en = item.get('prompt_en', '')
        md_content += f"### [{i+1}] {scene_type}\n\n```\n{prompt_en}\n```\n\n"
    
    st.download_button(
        label="下载 Markdown",
        data=md_content,
        file_name=f"{st.session_state.selected_topic}.md",
        mime="text/markdown",
        use_container_width=True
    )
