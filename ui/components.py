"""
UI 组件模块 - 图文模式
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import streamlit.components.v1 as components

from modules.trend import analyze_trends
from modules.crawler import fetch_note_content
from modules.writer import generate_note_package
from modules.painter import generate_images, generate_single_image
from modules.audio import generate_audio_for_scenes, generate_single_audio, EDGE_VOICES, VOLC_VOICES
from modules.editor import create_video, get_total_duration
from pathlib import Path
from modules.persona import get_categories, get_personas_by_category
from modules.monitor import log_access
from modules.utils import save_state, load_state, clear_state

# OpenRouter 模型配置（与 app.py 保持一致）
AVAILABLE_MODELS = {
    "DeepSeek V3 (高情商/国产梗)": "deepseek/deepseek-chat",
    "Claude 3.5 Sonnet (拟人感最强)": "anthropic/claude-3.5-sonnet",
    "GPT-4o (逻辑严密)": "openai/gpt-4o",
    "Gemini Pro 1.5 (长文强)": "google/gemini-pro-1.5",
    "Grok 2 (马斯克/幽默)": "x-ai/grok-2-1212"
}


def init_session_state():
    """初始化 Session State（支持从缓存恢复）"""
    # 工作流模式
    if "workflow_mode" not in st.session_state:
        st.session_state.workflow_mode = load_state("workflow_mode", "image")
    
    # 基础状态
    if "topics" not in st.session_state:
        st.session_state.topics = load_state("topics", [])
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = load_state("selected_topic", None)
    if "note_result" not in st.session_state:
        st.session_state.note_result = load_state("note_result", None)
    if "image_urls" not in st.session_state:
        st.session_state.image_urls = []
    
    # 素材生成状态
    if "image_paths" not in st.session_state:
        st.session_state.image_paths = load_state("image_paths", [])
    if "audio_paths" not in st.session_state:
        st.session_state.audio_paths = load_state("audio_paths", [])
    if "video_path" not in st.session_state:
        st.session_state.video_path = load_state("video_path", None)
    
    # 错误追踪
    if "image_errors" not in st.session_state:
        st.session_state.image_errors = load_state("image_errors", [])
    if "audio_errors" not in st.session_state:
        st.session_state.audio_errors = load_state("audio_errors", [])
    
    # 访问日志
    if "access_logged" not in st.session_state:
        st.session_state.access_logged = True
        log_access()


def _save_all_state():
    """保存所有重要状态到缓存"""
    save_state("workflow_mode", st.session_state.get("workflow_mode", "image"))
    save_state("topics", st.session_state.get("topics", []))
    save_state("selected_topic", st.session_state.get("selected_topic"))
    save_state("note_result", st.session_state.get("note_result"))
    save_state("image_paths", st.session_state.get("image_paths", []))
    save_state("audio_paths", st.session_state.get("audio_paths", []))
    save_state("video_path", st.session_state.get("video_path"))
    save_state("image_errors", st.session_state.get("image_errors", []))
    save_state("audio_errors", st.session_state.get("audio_errors", []))


def _reset_downstream_state():
    """重置下游状态（用于模式切换或选题改变）"""
    st.session_state.note_result = None
    st.session_state.image_paths = []
    st.session_state.audio_paths = []
    st.session_state.image_errors = []
    st.session_state.audio_errors = []
    st.session_state.video_path = None


def _get_status_icon(path, error) -> str:
    """获取状态图标"""
    if path and os.path.exists(path):
        return "✅"
    elif error:
        return "❌"
    else:
        return "⏳"


def render_header():
    """渲染页面标题（根据模式动态显示）"""
    mode = st.session_state.get("workflow_mode", "image")
    
    if mode == "video":
        st.markdown("# 🎬 小红书内容工作流")
        st.markdown("**视频模式** — 生成视频脚本（口播 + 画面）")
        st.caption("选题 → 创作 → 分镜 → 图片+音频 → 视频")
    else:
        st.markdown("# 📝 小红书内容工作流")
        st.markdown("**图文模式** — 生成深度长文案 + 配图")
        st.caption("选题 → 创作 → 预览 → 配图 → 导出")
    st.markdown("---")


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        # 工作流模式选择
        st.markdown("### 🔀 工作流模式")
        
        mode_options = {"image": "📝 图文模式", "video": "🎬 视频模式"}
        current_mode = st.session_state.get("workflow_mode", "image")
        
        new_mode = st.radio(
            "选择创作类型",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x],
            index=0 if current_mode == "image" else 1,
            key="mode_radio",
            label_visibility="collapsed"
        )
        
        # 模式切换时重置下游状态
        if new_mode != current_mode:
            st.session_state.workflow_mode = new_mode
            _reset_downstream_state()
            _save_all_state()
            st.toast(f"🔄 已切换到{'视频' if new_mode == 'video' else '图文'}模式，请重新生成内容")
            st.rerun()
        
        # 模式说明
        if new_mode == "video":
            st.caption("生成视频脚本，包含口播词和配套画面，支持自动合成视频")
        else:
            st.caption("生成 800 字深度长文案 + 配图提示词，适合小红书图文笔记")
        
        st.markdown("---")
        
        # 系统状态
        st.markdown("### 系统状态")
        
        openrouter_ok = os.getenv("OPENROUTER_API_KEY")
        replicate_ok = os.getenv("REPLICATE_API_TOKEN")
        oss_ok = os.getenv("OSS_ACCESS_KEY_ID")
        ark_ok = os.getenv("ARK_API_KEY")
        volc_tts_ok = os.getenv("VOLC_TTS_APPID")
        
        st.markdown(f"""
```
OPENROUTER   {'[OK]' if openrouter_ok else '[--]'}
REPLICATE    {'[OK]' if replicate_ok else '[--]'}
ALIYUN_OSS   {'[OK]' if oss_ok else '[--]'}
ARK_API      {'[OK]' if ark_ok else '[--]'}
VOLC_TTS     {'[OK]' if volc_tts_ok else '[--]'}
```
        """)
        
        st.markdown("---")
        
        # 模型配置
        st.markdown("### 模型配置")
        
        # 写作大脑选择器（LLM 模型）
        model_names = list(AVAILABLE_MODELS.keys())
        selected_model_name = st.selectbox(
            "🧠 写作大脑 (Model)",
            model_names,
            index=0,  # 默认 DeepSeek
            key="writer_model_select"
        )
        st.session_state.writer_model = AVAILABLE_MODELS[selected_model_name]
        
        st.session_state.image_provider = st.selectbox(
            "生图服务",
            ["replicate", "volcengine"],
            format_func=lambda x: "Replicate (二次元)" if x == "replicate" else "火山引擎 (Seedream)",
            key="image_provider_select"
        )
        
        # Replicate 二次元模型选择
        if st.session_state.image_provider == "replicate":
            st.session_state.anime_model = st.selectbox(
                "二次元模型",
                ["anything-v4", "flux-anime"],
                format_func=lambda x: "Anything V4 (经典稳定)" if x == "anything-v4" else "Flux Anime (高质量)",
                key="anime_model_select"
            )
        else:
            st.session_state.anime_model = "anything-v4"  # 默认值
        
        # 视频模式才显示 TTS 配置
        if st.session_state.get("workflow_mode") == "video":
            st.session_state.tts_provider = st.selectbox(
                "TTS 服务",
                ["volcengine", "edge"],
                format_func=lambda x: "Edge TTS (免费)" if x == "edge" else "火山引擎 TTS",
                key="tts_provider_select"
            )
            
            # 语音选择
            if st.session_state.tts_provider == "edge":
                voice_options = list(EDGE_VOICES.keys())
                selected_voice = st.selectbox("语音角色", voice_options, key="voice_select")
                st.session_state.voice = EDGE_VOICES[selected_voice]
            else:
                voice_options = list(VOLC_VOICES.keys())
                selected_voice = st.selectbox("语音角色", voice_options, key="voice_select")
                st.session_state.voice = VOLC_VOICES[selected_voice]
        
        st.markdown("---")
        
        # 缓存管理
        with st.expander("缓存管理"):
            if st.button("🗑️ 清除所有缓存", use_container_width=True):
                clear_state()
                for key in ["topics", "selected_topic", "note_result", "image_paths", "audio_paths", "video_path", "image_errors", "audio_errors", "workflow_mode"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            st.caption("刷新页面会自动恢复上次进度")
        
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
    st.markdown("## // 第一步：选题雷达")
    st.caption("💡 输入关键词，AI 联网搜索热门内容，获取爆款大纲结构")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input(
            "keyword",
            placeholder="输入关键词：酒局妆容 / 年终奖谈判 ...",
            label_visibility="collapsed"
        )
    with col2:
        analyze_btn = st.button(">开始分析", type="primary", use_container_width=True)
    
    if analyze_btn and keyword:
        with st.spinner("🔍 联网搜索热点中..."):
            try:
                topics, source = analyze_trends(keyword)
                st.session_state.topics = topics
                st.session_state.selected_topic = None
                st.session_state.selected_topic_data = None  # 完整热点数据
                _reset_downstream_state()
                _save_all_state()
                
                # 显示数据来源
                if source == "websearch":
                    st.success("🌐 已获取实时热点数据（联网搜索）")
                elif source == "fallback":
                    st.warning("⚠️ 联网搜索失败，使用 AI 推测模式")
                else:  # error
                    st.error("❌ 获取热点失败，请检查网络后重试")
            except Exception as e:
                st.error(f"分析失败: {e}")
    
    # 展示热点卡片
    if st.session_state.topics:
        st.markdown("### 🔥 热门话题")
        st.caption("点击选择一个热点，查看详细大纲")
        
        for i, topic in enumerate(st.session_state.topics):
            # 兼容旧数据格式（纯字符串）
            if isinstance(topic, str):
                topic = {"title": topic, "source": "", "summary": "", "outline": [], "why_hot": ""}
            
            title = topic.get("title", "")
            source = topic.get("source", "")
            summary = topic.get("summary", "")
            outline = topic.get("outline", [])
            why_hot = topic.get("why_hot", "")
            
            # 判断是否是当前选中的
            is_selected = st.session_state.get("selected_topic") == title
            
            with st.container():
                col_select, col_content = st.columns([1, 9])
                
                with col_select:
                    if st.button("✓" if is_selected else "○", key=f"select_topic_{i}", 
                                 type="primary" if is_selected else "secondary"):
                        st.session_state.selected_topic = title
                        st.session_state.selected_topic_data = topic  # 保存完整数据
                        _reset_downstream_state()
                        _save_all_state()
                        st.toast(f"✅ 已选择：{title[:20]}...")
                        st.rerun()
                
                with col_content:
                    # 标题 + 来源
                    st.markdown(f"**{title}**")
                    if source:
                        st.caption(f"📍 {source}")
                    
                    # 可展开的详情
                    with st.expander("查看大纲详情", expanded=is_selected):
                        if summary:
                            st.markdown(f"**📄 内容摘要**：{summary}")
                        
                        if outline:
                            st.markdown("**📋 内容大纲**：")
                            for j, point in enumerate(outline):
                                st.markdown(f"　{j+1}. {point}")
                        
                        if why_hot:
                            st.markdown(f"**🔥 火爆原因**：{why_hot}")
                
                st.markdown("---")
    
    st.markdown("")


def render_persona_config():
    """Step 2: 创作配置"""
    mode = st.session_state.get("workflow_mode", "image")
    
    st.markdown("## // 第二步：创作配置")
    
    if mode == "video":
        st.caption("🎬 选择人设风格，AI 将基于热点大纲生成视频脚本")
    else:
        st.caption("📝 选择人设风格，AI 将基于热点大纲生成 800 字深度文案")
    
    if not st.session_state.selected_topic:
        st.info("👆 请先在第一步选择话题")
        st.markdown("---")
        return
    
    # 展示选中的热点和大纲
    topic_data = st.session_state.get("selected_topic_data", {})
    title = st.session_state.selected_topic
    outline = topic_data.get("outline", []) if isinstance(topic_data, dict) else []
    summary = topic_data.get("summary", "") if isinstance(topic_data, dict) else ""
    
    st.success(f"已选话题：{title}")
    
    # 显示参考大纲
    if outline:
        with st.expander("📋 参考大纲（AI 将基于此结构创作）", expanded=True):
            for i, point in enumerate(outline):
                st.markdown(f"**{i+1}.** {point}")
            if summary:
                st.caption(f"💡 {summary}")
    
    # 提示：重新生成会清除后续步骤
    if st.session_state.get("note_result"):
        st.warning("⚠️ 重新生成将清除后续步骤的所有素材")
    
    st.markdown("### 人设选择")
    
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
        with col2:
            persona_text = st.text_input(
                "人设风格", 
                placeholder="治愈系姐姐 / 毒舌闺蜜 ..."
            )
    else:
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
    
    ref_url = st.text_input("参考链接（可选）", placeholder="https://xiaohongshu.com/...")
    
    st.markdown("")
    generate_btn = st.button("🚀 开始生成", type="primary", use_container_width=True)
    
    if generate_btn:
        if not persona_text:
            st.warning("请先选择人设")
        else:
            with st.status("生成中...", expanded=True) as status:
                try:
                    ref_content = None
                    if ref_url:
                        status.update(label="📥 正在抓取参考内容...")
                        ref_data = fetch_note_content(ref_url)
                        if ref_data:
                            ref_content = f"标题：{ref_data.get('title', '')}\n\n{ref_data.get('content', '')}"
                            st.write("✅ 参考内容已加载")
                        else:
                            st.write("⚠️ 抓取失败，将创作原创内容")
                    
                    if mode == "video":
                        status.update(label="✍️ 正在生成视频脚本（口播词 + 分镜）...")
                    else:
                        status.update(label="✍️ 正在基于热点大纲撰写文案...")
                    
                    # 获取选择的写作模型
                    writer_model = st.session_state.get("writer_model", "deepseek/deepseek-chat")
                    
                    # 获取完整热点数据（用于深度演绎模式）
                    topic_data = st.session_state.get("selected_topic_data", {})
                    search_data = topic_data if isinstance(topic_data, dict) else {}
                    
                    result = generate_note_package(
                        topic=st.session_state.selected_topic,
                        persona=persona_text,
                        reference_text=ref_content,
                        mode=mode,
                        model_name=writer_model,
                        search_data=search_data  # 传入完整热点数据
                    )
                    
                    if result and result.get("titles"):
                        had_previous = st.session_state.get("note_result") is not None
                        st.session_state.note_result = result
                        st.session_state.image_paths = []
                        st.session_state.audio_paths = []
                        st.session_state.image_errors = []
                        st.session_state.audio_errors = []
                        st.session_state.video_path = None
                        _save_all_state()
                        status.update(label="✅ 生成完成!", state="complete")
                        if had_previous:
                            st.toast("🔄 内容已更新，素材需重新生成")
                    else:
                        status.update(label="❌ 生成失败，请重试", state="error")
                        
                except Exception as e:
                    status.update(label=f"❌ 生成失败: {e}", state="error")
    
    st.markdown("---")


def render_content_display():
    """Step 3: 内容展示"""
    mode = st.session_state.get("workflow_mode", "image")
    
    st.markdown("## // 第三步：内容预览")
    
    if mode == "video":
        st.caption("🎬 查看生成的分镜脚本，每个分镜包含口播词和对应画面提示词")
    else:
        st.caption("📝 查看生成的文案和配图方案，可复制提示词到生图工具")
    
    if not st.session_state.note_result:
        st.info("👆 请先在第二步生成内容")
        st.markdown("---")
        return
    
    result = st.session_state.note_result
    
    # 标题 + 正文并排布局
    col_titles, col_content = st.columns([3, 7])
    
    with col_titles:
        st.markdown("### 备选标题")
        titles = result.get("titles", [])
        for i, title in enumerate(titles):
            st.markdown(
                f'<div class="title-card"><span class="num">[{i}]</span> {title}</div>',
                unsafe_allow_html=True
            )
    
    with col_content:
        st.markdown("### 正文内容" if mode == "image" else "### 视频简介")
        content = result.get("content", "")
        st.text_area("content", content, height=250, key="content_area", label_visibility="collapsed")
        char_count = len(content.replace(" ", "").replace("\n", ""))
        st.caption(f"字数：{char_count}")
    
    # 图文模式：显示配图设计
    if mode == "image":
        image_designs = result.get("image_designs", [])
        
        if image_designs:
            st.markdown("### 配图方案")
            st.caption(f"共 {len(image_designs)} 张配图设计")
            
            for i, design in enumerate(image_designs):
                with st.expander(f"[{i+1}] {design.get('description', '')[:40]}...", expanded=(i == 0)):
                    st.markdown("**🖼️ 画面描述**")
                    st.write(design.get("description", ""))
                    
                    st.markdown("**🎨 生图提示词**")
                    prompt = design.get("prompt", "")
                    st.code(prompt, language="text")
                    
                    if st.button(f"📋 复制提示词", key=f"copy_img_prompt_{i}", use_container_width=True):
                        escaped_prompt = prompt.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                        components.html(f'''
                            <script>navigator.clipboard.writeText(`{escaped_prompt}`);</script>
                        ''', height=0)
                        st.toast(f"已复制第 {i+1} 张配图提示词")
    
    # 视频模式：显示分镜脚本
    else:
        visual_scenes = result.get("visual_scenes", [])
        
        if visual_scenes:
            st.markdown("### 分镜脚本（画音同步）")
            st.caption(f"共 {len(visual_scenes)} 个分镜，口播词连起来即为完整视频解说")
            
            # 分镜概览列表
            st.markdown("**快速预览**")
            for i, scene in enumerate(visual_scenes):
                narration = scene.get('narration', '')[:20]
                description = scene.get('description', '')[:25]
                st.markdown(f"`Scene {i+1}:` **[旁白]** {narration}... → **[画面]** {description}...")
            
            st.markdown("---")
            st.markdown("**详细分镜**")
            
            for i, scene in enumerate(visual_scenes):
                with st.expander(f"Scene {i+1}: [{scene.get('narration', '')[:15]}...] → [{scene.get('description', '')[:20]}...]", expanded=(i == 0)):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("**🎙️ 口播词 (Narration)**")
                        st.info(scene.get("narration", ""))
                    
                    with col2:
                        st.markdown("**🖼️ 画面描述**")
                        st.write(scene.get("description", ""))
                    
                    st.markdown("**🎨 生图提示词**")
                    prompt = scene.get("prompt", "")
                    st.code(prompt, language="text")
                    
                    if st.button(f"📋 复制提示词", key=f"copy_prompt_{i}", use_container_width=True):
                        escaped_prompt = prompt.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                        components.html(f'''
                            <script>navigator.clipboard.writeText(`{escaped_prompt}`);</script>
                        ''', height=0)
                        st.toast(f"已复制第 {i+1} 个分镜提示词")
    
    st.markdown("---")


def render_image_export():
    """Step 4: 导出 (根据模式不同)"""
    mode = st.session_state.get("workflow_mode", "image")
    
    if mode == "video":
        _render_video_studio()
    else:
        _render_image_export()


def _render_image_export():
    """图文模式：生成配图 + 导出 Markdown"""
    st.markdown("## // 第四步：生成配图 & 导出")
    st.caption("📸 点击生成配图，或复制提示词到其他生图工具，最后导出 Markdown 文档")
    
    if not st.session_state.note_result:
        st.info("👆 请先完成第三步")
        return
    
    result = st.session_state.note_result
    image_designs = result.get("image_designs", [])
    
    if not image_designs:
        st.warning("配图方案为空，无法生成")
        st.markdown("---")
        return
    
    # 确保列表长度正确
    image_paths = st.session_state.get("image_paths", [])
    image_errors = st.session_state.get("image_errors", [])
    
    while len(image_paths) < len(image_designs):
        image_paths.append(None)
    while len(image_errors) < len(image_designs):
        image_errors.append(None)
    
    # 进度概览
    col1, col2 = st.columns(2)
    with col1:
        provider = getattr(st.session_state, 'image_provider', 'replicate')
        st.metric("生图模型", "Replicate" if provider == "replicate" else "火山引擎")
    with col2:
        img_ok = len([p for p in image_paths if p and os.path.exists(p)])
        st.metric("配图进度", f"{img_ok}/{len(image_designs)}")
    
    st.markdown("---")
    
    # 生成配图
    st.markdown("### 生成配图")
    
    if st.button("🎨 一键生成所有配图", use_container_width=True, type="primary"):
        provider = getattr(st.session_state, 'image_provider', 'replicate')
        
        with st.status("生成配图中...", expanded=True) as status:
            for i, design in enumerate(image_designs):
                if image_paths[i] and os.path.exists(image_paths[i]):
                    st.write(f"✅ 配图 {i+1}: 已存在，跳过")
                    continue
                
                status.update(label=f"🎨 生成配图 {i+1}/{len(image_designs)}...")
                
                # 构造 scene 结构以复用 generate_single_image
                scene_like = {"prompt": design.get("prompt", "")}
                anime_model = getattr(st.session_state, 'anime_model', 'anything-v4')
                path, error = generate_single_image(scene_like, i, provider, anime_model)
                image_paths[i] = path
                image_errors[i] = error
                
                if path:
                    st.write(f"✅ 配图 {i+1}: 成功")
                else:
                    st.write(f"❌ 配图 {i+1}: {error}")
            
            st.session_state.image_paths = image_paths
            st.session_state.image_errors = image_errors
            _save_all_state()
            
            img_ok = len([p for p in image_paths if p and os.path.exists(p)])
            status.update(label=f"✅ 完成 (配图 {img_ok}/{len(image_designs)})", state="complete")
    
    st.markdown("---")
    
    # 配图预览
    st.markdown("### 配图预览")
    
    cols = st.columns(min(5, len(image_designs)))
    for i, design in enumerate(image_designs):
        col = cols[i % 5]
        img_path = image_paths[i] if i < len(image_paths) else None
        img_err = image_errors[i] if i < len(image_errors) else None
        
        with col:
            st.caption(f"配图 {i+1}")
            if img_path and os.path.exists(img_path):
                st.image(img_path, width=150)
            elif img_err:
                st.error(f"❌ {img_err[:30]}...")
                if st.button(f"🔄 重试", key=f"retry_img_{i}"):
                    provider = getattr(st.session_state, 'image_provider', 'replicate')
                    anime_model = getattr(st.session_state, 'anime_model', 'anything-v4')
                    with st.spinner("重新生成中..."):
                        scene_like = {"prompt": design.get("prompt", "")}
                        path, error = generate_single_image(scene_like, i, provider, anime_model)
                        image_paths[i] = path
                        image_errors[i] = error
                        st.session_state.image_paths = image_paths
                        st.session_state.image_errors = image_errors
                        _save_all_state()
                        st.rerun()
            else:
                st.info("待生成")
    
    st.markdown("---")
    
    # 导出文案
    st.markdown("### 导出文案")
    
    titles = result.get("titles", [])
    content = result.get("content", "")
    
    md_content = f"# {st.session_state.selected_topic or '小红书笔记'}\n\n"
    md_content += "## 备选标题\n\n"
    for i, title in enumerate(titles):
        md_content += f"{i+1}. {title}\n"
    md_content += f"\n## 正文\n\n{content}\n\n"
    md_content += "## 配图提示词\n\n"
    
    for i, design in enumerate(image_designs):
        description = design.get('description', '').replace('\n', ' ')
        prompt = design.get('prompt', '')
        md_content += f"### [{i+1}] {description}\n\n```\n{prompt}\n```\n\n"
    
    st.download_button(
        label="📄 下载 Markdown",
        data=md_content,
        file_name=f"{st.session_state.selected_topic or 'output'}.md",
        mime="text/markdown",
        use_container_width=True
    )


def _get_bgm_options():
    """扫描 assets/bgm 目录获取可用的 BGM 列表"""
    bgm_dir = Path("assets/bgm")
    if not bgm_dir.exists():
        return []
    
    bgm_files = []
    for ext in ['*.mp3', '*.wav', '*.m4a']:
        bgm_files.extend(bgm_dir.glob(ext))
    
    return sorted([f.name for f in bgm_files])


def _render_video_studio():
    """视频模式：生成素材 + 合成视频"""
    st.markdown("## // 第四步：视频工作室")
    st.caption("🎬 生成配图和音频素材，自动合成画音同步视频（含 Ken Burns 动态运镜）")
    
    if not st.session_state.note_result:
        st.info("👆 请先完成第三步")
        return
    
    result = st.session_state.note_result
    visual_scenes = result.get("visual_scenes", [])
    
    if not visual_scenes:
        st.warning("分镜脚本为空，无法生成视频")
        st.markdown("---")
        return
    
    # 确保列表长度正确
    image_paths = st.session_state.get("image_paths", [])
    audio_paths = st.session_state.get("audio_paths", [])
    image_errors = st.session_state.get("image_errors", [])
    audio_errors = st.session_state.get("audio_errors", [])
    
    while len(image_paths) < len(visual_scenes):
        image_paths.append(None)
    while len(audio_paths) < len(visual_scenes):
        audio_paths.append(None)
    while len(image_errors) < len(visual_scenes):
        image_errors.append(None)
    while len(audio_errors) < len(visual_scenes):
        audio_errors.append(None)
    
    # 显示配置和进度概览
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        provider = getattr(st.session_state, 'image_provider', 'replicate')
        st.metric("生图模型", "Replicate" if provider == "replicate" else "火山引擎")
    with col2:
        tts = getattr(st.session_state, 'tts_provider', 'edge')
        st.metric("TTS 服务", "Edge" if tts == "edge" else "火山引擎")
    with col3:
        img_ok = len([p for p in image_paths if p and os.path.exists(p)])
        st.metric("图片", f"{img_ok}/{len(visual_scenes)}")
    with col4:
        aud_ok = len([p for p in audio_paths if p and os.path.exists(p)])
        st.metric("音频", f"{aud_ok}/{len(visual_scenes)}")
    
    st.markdown("---")
    
    # 左右并排布局：左侧素材状态+生成，右侧预览
    col_left, col_right = st.columns([4, 6])
    
    with col_left:
        st.markdown("### 素材状态 & 生成")
        
        # 状态一览（紧凑网格）
        num_cols = min(6, len(visual_scenes))
        rows = (len(visual_scenes) + num_cols - 1) // num_cols
        for row in range(rows):
            status_cols = st.columns(num_cols)
            for col_idx in range(num_cols):
                i = row * num_cols + col_idx
                if i < len(visual_scenes):
                    img_icon = _get_status_icon(image_paths[i] if i < len(image_paths) else None, 
                                                 image_errors[i] if i < len(image_errors) else None)
                    aud_icon = _get_status_icon(audio_paths[i] if i < len(audio_paths) else None,
                                                 audio_errors[i] if i < len(audio_errors) else None)
                    status_cols[col_idx].markdown(f"**{i+1}** 🎨{img_icon}🎙️{aud_icon}")
        
        st.markdown("")
        
        # 一键生成按钮（并发版本：图音并行）
        if st.button("🚀 一键并发生成", use_container_width=True, type="primary"):
            provider = getattr(st.session_state, 'image_provider', 'replicate')
            anime_model = getattr(st.session_state, 'anime_model', 'anything-v4')
            tts_provider = getattr(st.session_state, 'tts_provider', 'edge')
            voice = getattr(st.session_state, 'voice', None)
            
            # 筛选需要生成的场景
            scenes_to_gen_img = []
            scenes_to_gen_aud = []
            img_indices = []
            aud_indices = []
            
            for i, scene in enumerate(visual_scenes):
                if not (image_paths[i] and os.path.exists(image_paths[i])):
                    scenes_to_gen_img.append(scene)
                    img_indices.append(i)
                if not (audio_paths[i] and os.path.exists(audio_paths[i])):
                    scenes_to_gen_aud.append(scene)
                    aud_indices.append(i)
            
            # 获取主题用于文件命名
            topic = st.session_state.get("selected_topic", None)
            
            with st.status("🚀 全速并发生成中...", expanded=True) as status:
                st.write(f"**并行任务**：{len(scenes_to_gen_img)} 张图片 + {len(scenes_to_gen_aud)} 段音频")
                st.write(f"📷 图片和 🎙️ 音频同时生成，主题: {topic or '默认'}")
                
                # 并行执行图片和音频生成
                with ThreadPoolExecutor(max_workers=2) as executor:
                    # 提交图片生成任务（带主题）
                    future_imgs = executor.submit(
                        generate_images, 
                        scenes_to_gen_img, 
                        provider, 
                        anime_model,
                        topic  # 传入主题
                    ) if scenes_to_gen_img else None
                    
                    # 提交音频生成任务（带主题）
                    future_auds = executor.submit(
                        generate_audio_for_scenes,
                        scenes_to_gen_aud,
                        tts_provider,
                        voice,
                        topic  # 传入主题
                    ) if scenes_to_gen_aud else None
                    
                    # 等待结果
                    new_img_paths = future_imgs.result() if future_imgs else []
                    new_aud_paths = future_auds.result() if future_auds else []
                
                # 合并结果到原数组
                for idx, new_idx in enumerate(img_indices):
                    if idx < len(new_img_paths):
                        image_paths[new_idx] = new_img_paths[idx]
                        image_errors[new_idx] = None if new_img_paths[idx] else "生成失败"
                
                for idx, new_idx in enumerate(aud_indices):
                    if idx < len(new_aud_paths):
                        audio_paths[new_idx] = new_aud_paths[idx]
                        audio_errors[new_idx] = None if new_aud_paths[idx] else "生成失败"
                
                st.session_state.image_paths = image_paths
                st.session_state.image_errors = image_errors
                st.session_state.audio_paths = audio_paths
                st.session_state.audio_errors = audio_errors
                _save_all_state()
                
                img_ok = len([p for p in image_paths if p and os.path.exists(p)])
                aud_ok = len([p for p in audio_paths if p and os.path.exists(p)])
                st.write(f"✅ 图片: {img_ok}/{len(visual_scenes)} | 音频: {aud_ok}/{len(visual_scenes)}")
                status.update(label=f"✅ 并发生成完成！", state="complete")
    
    with col_right:
        st.markdown("### 素材预览")
        st.caption("展开查看素材，可单独重试失败项")
        
        for i, scene in enumerate(visual_scenes):
            img_path = image_paths[i] if i < len(image_paths) else None
            aud_path = audio_paths[i] if i < len(audio_paths) else None
            img_err = image_errors[i] if i < len(image_errors) else None
            aud_err = audio_errors[i] if i < len(audio_errors) else None
            
            img_icon = _get_status_icon(img_path, img_err)
            aud_icon = _get_status_icon(aud_path, aud_err)
            
            with st.expander(f"场景 {i+1} {img_icon}🎨 {aud_icon}🎙️ | {scene.get('description', '')[:20]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**图片**")
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, width=150)
                    elif img_err:
                        st.error(f"失败: {img_err[:20]}")
                        if st.button(f"🔄 重试", key=f"retry_img_{i}"):
                            provider = getattr(st.session_state, 'image_provider', 'replicate')
                            anime_model = getattr(st.session_state, 'anime_model', 'anything-v4')
                            with st.spinner("生成中..."):
                                path, error = generate_single_image(scene, i, provider, anime_model)
                                image_paths[i] = path
                                image_errors[i] = error
                                st.session_state.image_paths = image_paths
                                st.session_state.image_errors = image_errors
                                _save_all_state()
                                st.rerun()
                    else:
                        st.warning("待生成")
                
                with col2:
                    st.markdown("**音频**")
                    if aud_path and os.path.exists(aud_path):
                        st.audio(aud_path)
                    elif aud_err:
                        st.error(f"失败: {aud_err[:20]}")
                        if st.button(f"🔄 重试", key=f"retry_aud_{i}"):
                            tts_provider = getattr(st.session_state, 'tts_provider', 'edge')
                            voice = getattr(st.session_state, 'voice', None)
                            with st.spinner("生成中..."):
                                path, error = generate_single_audio(scene, i, tts_provider, voice)
                                audio_paths[i] = path
                                audio_errors[i] = error
                                st.session_state.audio_paths = audio_paths
                                st.session_state.audio_errors = audio_errors
                                _save_all_state()
                                st.rerun()
                    else:
                        st.warning("待生成")
    
    st.markdown("---")
    
    # 合成视频 + 预览并排布局
    st.markdown("### 合成视频")
    
    has_all_images = all(p and os.path.exists(p) for p in image_paths[:len(visual_scenes)])
    has_all_audio = all(p and os.path.exists(p) for p in audio_paths[:len(visual_scenes)])
    
    col_compose, col_preview = st.columns([4, 6])
    
    with col_compose:
        if not has_all_images:
            failed_imgs = [i+1 for i, p in enumerate(image_paths[:len(visual_scenes)]) if not p or not os.path.exists(p)]
            st.warning(f"⚠️ 图片未完成: {failed_imgs}")
        if not has_all_audio:
            failed_auds = [i+1 for i, p in enumerate(audio_paths[:len(visual_scenes)]) if not p or not os.path.exists(p)]
            st.warning(f"⚠️ 音频未完成: {failed_auds}")
        
        # BGM 选择
        bgm_options = _get_bgm_options()
        selected_bgm = None
        
        if bgm_options:
            bgm_choice = st.selectbox(
                "🎵 背景音乐",
                ["无 BGM"] + bgm_options,
                key="bgm_select"
            )
            if bgm_choice != "无 BGM":
                selected_bgm = str(Path("assets/bgm") / bgm_choice)
        else:
            st.caption("💡 在 `assets/bgm/` 放入 MP3")
        
        bgm_volume = st.slider("BGM 音量", 0.05, 0.3, 0.12, 0.01, key="bgm_volume")
        
        if has_all_images and has_all_audio:
            total_duration = get_total_duration(audio_paths[:len(visual_scenes)])
            st.info(f"📊 时长: {total_duration:.1f}s")
            
            if st.button("🎬 合成视频", use_container_width=True, type="primary"):
                # 获取主题用于文件命名
                topic = st.session_state.get("selected_topic", None)
                
                with st.status("合成中...", expanded=True) as status:
                    try:
                        status.update(label="🎬 拼接 + Ken Burns + 生成字幕...")
                        video_path = create_video(
                            image_paths[:len(visual_scenes)], 
                            audio_paths[:len(visual_scenes)],
                            bgm_path=selected_bgm,
                            bgm_volume=bgm_volume,
                            scenes=visual_scenes,  # 传入分镜数据，自动生成 SRT 字幕
                            topic=topic  # 传入主题，用于文件命名
                        )
                        if video_path and os.path.exists(video_path):
                            st.session_state.video_path = video_path
                            _save_all_state()
                            status.update(label="✅ 完成!", state="complete")
                        else:
                            status.update(label="❌ 失败", state="error")
                    except Exception as e:
                        status.update(label=f"❌ {e}", state="error")
        else:
            st.button("🎬 合成视频", use_container_width=True, type="primary", disabled=True)
            st.caption("需完成所有素材")
    
    with col_preview:
        video_path = st.session_state.get("video_path")
        if video_path and os.path.exists(video_path):
            st.markdown("**成品预览**")
            st.video(video_path)
            with open(video_path, "rb") as f:
                st.download_button(
                    label="📥 下载视频",
                    data=f,
                    file_name=f"{st.session_state.selected_topic or 'output'}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        else:
            st.info("视频合成后在此预览")
    
    st.markdown("---")
    
    # 导出脚本
    st.markdown("### 导出脚本")
    
    titles = result.get("titles", [])
    content = result.get("content", "")
    
    md_content = f"# {st.session_state.selected_topic or '视频脚本'}\n\n"
    md_content += "## 备选标题\n\n"
    for i, title in enumerate(titles):
        md_content += f"{i+1}. {title}\n"
    md_content += f"\n## 视频简介\n\n{content}\n\n"
    md_content += "## 分镜脚本\n\n"
    md_content += "| 序号 | 口播词 | 画面描述 | 生图提示词 |\n"
    md_content += "|------|--------|----------|------------|\n"
    
    for i, scene in enumerate(visual_scenes):
        narration = scene.get('narration', '').replace('\n', ' ').replace('|', '\\|')
        description = scene.get('description', '').replace('\n', ' ').replace('|', '\\|')
        prompt = scene.get('prompt', '').replace('\n', ' ').replace('|', '\\|')
        md_content += f"| {i+1} | {narration} | {description} | {prompt} |\n"
    
    md_content += "\n## 提示词快速复制\n\n"
    for i, scene in enumerate(visual_scenes):
        prompt = scene.get('prompt', '')
        md_content += f"### [{i+1}] 场景 {i+1}\n\n```\n{prompt}\n```\n\n"
    
    st.download_button(
        label="📄 下载脚本 Markdown",
        data=md_content,
        file_name=f"{st.session_state.selected_topic or 'output'}_script.md",
        mime="text/markdown",
        use_container_width=True
    )
