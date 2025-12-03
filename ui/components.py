"""
UI 组件模块
"""
import os
import streamlit as st

from modules.trend import analyze_trends
from modules.crawler import fetch_note_content
from modules.writer import generate_note_package
from modules.painter import generate_images_with_ideogram
from modules.persona import get_categories, get_personas_by_category


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


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### sys.config")
        
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
        
        with st.expander("env.override"):
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
    st.markdown("## step_1: trend_radar")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        niche = st.text_input(
            "niche", 
            placeholder="输入赛道：美妆 / 职场 / 健身 ...", 
            label_visibility="collapsed"
        )
    with col2:
        analyze_btn = st.button("analyze()", type="primary", use_container_width=True)
    
    if analyze_btn and niche:
        with st.spinner("analyzing..."):
            topics = analyze_trends(niche)
            st.session_state.topics = topics
            st.session_state.selected_topic = None
            st.session_state.note_result = None
            st.session_state.image_urls = []
    
    if st.session_state.topics:
        st.markdown("### topics[]")
        selected = st.radio(
            "select topic:",
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
    st.markdown("## step_2: config")
    
    if not st.session_state.selected_topic:
        st.info(">> select topic in step_1 first")
        st.markdown("---")
        return
    
    st.success(f"selected: {st.session_state.selected_topic}")
    st.markdown("### persona")
    
    categories = get_categories()
    category_options = categories + ["custom"]
    
    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox(
            "category",
            category_options,
            index=0,
            key="category_select"
        )
    
    persona_text = None
    
    if selected_category == "custom":
        with col2:
            persona_text = st.text_input(
                "persona_style", 
                placeholder="治愈系姐姐 / 毒舌闺蜜 ..."
            )
    else:
        personas = get_personas_by_category(selected_category)
        persona_options = [p['name'] for p in personas]
        
        with col2:
            selected_persona_idx = st.selectbox(
                "select",
                range(len(persona_options)),
                format_func=lambda x: persona_options[x],
                key="persona_select"
            )
        
        if personas:
            selected_persona = personas[selected_persona_idx]
            persona_text = selected_persona.get('prompt', '')
            
            with st.expander(f"cat {selected_persona['name']}.prompt"):
                st.code(persona_text, language=None)
    
    ref_url = st.text_input("ref_url (optional)", placeholder="https://xiaohongshu.com/...")
    
    st.markdown("")
    generate_btn = st.button("generate()", type="primary", use_container_width=True)
    
    if generate_btn:
        if not persona_text:
            st.warning("error: persona not selected")
        else:
            with st.spinner("generating content & design..."):
                ref_content = None
                if ref_url:
                    with st.status("crawling reference..."):
                        ref_data = fetch_note_content(ref_url)
                        if ref_data:
                            ref_content = f"标题：{ref_data.get('title', '')}\n\n{ref_data.get('content', '')}"
                            st.write("[OK] reference loaded")
                        else:
                            st.write("[--] crawl failed, creating original")
                
                result = generate_note_package(
                    topic=st.session_state.selected_topic,
                    persona=persona_text,
                    reference_text=ref_content
                )
                st.session_state.note_result = result
                st.session_state.image_urls = []
    
    st.markdown("---")


def render_content_display():
    """Step 3: 内容展示"""
    st.markdown("## step_3: output")
    
    if not st.session_state.note_result:
        st.info(">> generate content in step_2 first")
        st.markdown("---")
        return
    
    result = st.session_state.note_result
    
    # 标题
    st.markdown("### titles[]")
    titles = result.get("titles", [])
    for i, title in enumerate(titles):
        st.markdown(
            f'<div class="title-card"><span class="num">[{i}]</span> {title}</div>',
            unsafe_allow_html=True
        )
    
    # 正文
    st.markdown("### content")
    content = result.get("content", "")
    st.text_area("content", content, height=300, key="content_area", label_visibility="collapsed")
    
    # 图片设计方案
    st.markdown("### images_design[]")
    designs = result.get("images_design", [])
    for i, design in enumerate(designs):
        design_type = design.get('type', 'unknown')
        main_text = design.get('main_text', '')
        sub_text = design.get('sub_text', '')
        visual_style = design.get('visual_style', '')
        
        with st.expander(f"[{i}] {design_type}: {main_text}"):
            st.markdown(f"**type:** `{design_type}`")
            st.markdown(f"**main_text:** {main_text}")
            if sub_text:
                st.markdown(f"**sub_text:** {sub_text}")
            st.markdown(f"**visual_style:** {visual_style}")
    
    st.markdown("---")


def render_image_export():
    """Step 4: 视觉与交付"""
    st.markdown("## step_4: render")
    
    if not st.session_state.note_result:
        st.info(">> complete step_3 first")
        return
    
    designs = st.session_state.note_result.get("images_design", [])
    
    if designs:
        image_btn = st.button("ideogram.generate()", type="primary", use_container_width=True)
        
        if image_btn:
            with st.spinner("rendering images with Ideogram..."):
                urls = generate_images_with_ideogram(designs)
                st.session_state.image_urls = urls
    
    # 展示图片
    if st.session_state.image_urls:
        st.markdown("### images[]")
        cols = st.columns(len(st.session_state.image_urls))
        for i, (col, url) in enumerate(zip(cols, st.session_state.image_urls)):
            with col:
                # 获取对应的设计类型
                design_type = designs[i].get('type', f'img_{i}') if i < len(designs) else f'img_{i}'
                st.image(url, caption=f"[{i}] {design_type}", use_container_width=True)
    
    st.markdown("---")
    
    # 导出
    st.markdown("### export")
    
    result = st.session_state.note_result
    titles = result.get("titles", [])
    content = result.get("content", "")
    
    md_content = f"# {st.session_state.selected_topic}\n\n## titles\n\n"
    for i, title in enumerate(titles):
        md_content += f"{i}. {title}\n"
    
    md_content += f"\n## content\n\n{content}\n\n"
    
    if st.session_state.image_urls:
        md_content += "## images\n\n"
        for i, url in enumerate(st.session_state.image_urls):
            design_type = designs[i].get('type', f'img_{i}') if i < len(designs) else f'img_{i}'
            md_content += f"![{design_type}]({url})\n\n"
    
    st.download_button(
        label="download.md",
        data=md_content,
        file_name="note.md",
        mime="text/markdown",
        use_container_width=True
    )
