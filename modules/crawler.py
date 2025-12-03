"""
DrissionPage 爬虫模块
"""
from DrissionPage import ChromiumPage


def fetch_note_content(url: str) -> dict:
    """
    抓取小红书笔记内容
    
    Args:
        url: 小红书笔记 URL
    
    Returns:
        {'title': '...', 'content': '...'} 或失败时返回空 dict
    """
    page = None
    try:
        page = ChromiumPage()
        page.get(url)
        page.wait.load_start()
        
        # 提取标题 (h1 标签)
        title_el = page.ele('tag:h1')
        title = title_el.text if title_el else ''
        
        # 提取正文内容 (小红书笔记正文通常在 desc 区域)
        desc_el = page.ele('.note-content') or page.ele('#detail-desc') or page.ele('tag:article')
        content = desc_el.text if desc_el else ''
        
        return {'title': title, 'content': content}
    
    except Exception as e:
        print(f"[Crawler Error] 抓取失败: {e}")
        return {}
    
    finally:
        if page:
            page.quit()
