"""
Obsidian MD 文件导出模块
将生成的笔记导出为 Markdown 文件，保存到本地 Obsidian 目录
"""
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from modules.utils import sanitize_filename

load_dotenv()

# Obsidian 导出目录
OBSIDIAN_EXPORT_PATH = os.getenv(
    "OBSIDIAN_EXPORT_PATH", 
    "/Users/0xNiedlichX/Library/Mobile Documents/iCloud~md~obsidian/Documents/DonxYu Space/0-Inbox/Rednote_Auto"
)


def export_note(
    topic: str,
    title: str,
    content: str,
    image_urls: list = None,
    tags: list = None
) -> str | None:
    """
    导出笔记为 Obsidian MD 文件
    
    Args:
        topic: 主题/选题（用于文件命名）
        title: 笔记标题
        content: 笔记正文
        image_urls: OSS 图片 URL 列表（将嵌入到 MD 文件中）
        tags: 标签列表
    
    Returns:
        成功返回 MD 文件路径，失败返回 None
    """
    try:
        # 确保目录存在
        export_dir = Path(OBSIDIAN_EXPORT_PATH)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        safe_topic = sanitize_filename(topic) if topic else "untitled"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_topic}_{timestamp}.md"
        file_path = export_dir / filename
        
        # 构建 MD 内容
        md_lines = []
        
        # Frontmatter (YAML 元数据)
        md_lines.append("---")
        md_lines.append(f"title: {title}")
        md_lines.append(f"topic: {topic}")
        md_lines.append(f"created: {datetime.now().isoformat()}")
        if tags:
            md_lines.append(f"tags: [{', '.join(tags)}]")
        else:
            md_lines.append("tags: [小红书, 自动生成]")
        md_lines.append("---")
        md_lines.append("")
        
        # 标题
        md_lines.append(f"# {title}")
        md_lines.append("")
        
        # 正文
        # 处理换行符（\n -> 实际换行）
        formatted_content = content.replace("\\n", "\n")
        md_lines.append(formatted_content)
        md_lines.append("")
        
        # 配图
        if image_urls:
            md_lines.append("---")
            md_lines.append("")
            md_lines.append("## 配图")
            md_lines.append("")
            for i, url in enumerate(image_urls):
                if url:
                    md_lines.append(f"### 图片 {i+1}")
                    md_lines.append(f"![{topic}_image_{i+1}]({url})")
                    md_lines.append("")
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        
        print(f"[MD Export] 笔记导出成功: {file_path}")
        return str(file_path)
        
    except Exception as e:
        print(f"[MD Export Error] 导出失败: {e}")
        return None


def export_note_simple(
    topic: str,
    title: str,
    content: str
) -> str | None:
    """
    简化版导出（仅标题和正文）
    
    Args:
        topic: 主题
        title: 标题
        content: 正文
    
    Returns:
        MD 文件路径
    """
    return export_note(topic, title, content, image_urls=None, tags=None)


def get_export_path() -> str:
    """获取导出目录路径"""
    return OBSIDIAN_EXPORT_PATH

