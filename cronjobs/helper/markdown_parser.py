"""
Markdown 解析工具，用於將 Markdown 格式的 AI 摘要轉換為 Discord 訊息格式。
"""

def parse_ai_summary_to_discord_embeds(summary, hours, twitter_users_text=None):
    """
    將 AI 生成的 Markdown 摘要解析為 Discord embed 格式。
    
    Args:
        summary (str): Markdown 格式的 AI 摘要
        hours (int): 資料涵蓋的小時數
        twitter_users_text (str, optional): Twitter 用戶列表文本
        
    Returns:
        list: Discord embeds 列表
    """
    embeds = []
    
    # 分段處理摘要，每個主要段落作為一個單獨的 embed
    # 這樣可以避免超過 Discord 的字數限制，並且提高可讀性
    sections = summary.split("####")
    
    # 處理總體摘要部分 (如果存在)
    if len(sections) > 1:
        main_summary = sections[0].strip()
        if main_summary:
            embeds.append({
                "title": f"過去 {hours} 小時推特摘要報告（Hololive 卡牌遊戲相關）",
                "description": main_summary,
                "color": 5814783,  # 紫色
                "footer": {
                    "text": f"追蹤用戶: {twitter_users_text}" if twitter_users_text else None
                }
            })
    
    # 處理各個子標題部分
    for i, section in enumerate(sections[1:], 1):
        if not section.strip():
            continue
            
        # 分離標題和內容
        lines = section.strip().split("\n")
        title = lines[0].strip().strip("*").strip()
        content = "\n".join(lines[1:]).strip()
        
        # 添加為 embed
        embeds.append({
            "title": title,
            "description": content,
            "color": 5814783  # 紫色
        })
    
    return embeds

def create_discord_message(summary, hours, twitter_users_text=None, date_str=None):
    """
    創建完整的 Discord 訊息，包含標題和 embeds。
    
    Args:
        summary (str): Markdown 格式的 AI 摘要
        hours (int): 資料涵蓋的小時數
        twitter_users_text (str, optional): Twitter 用戶列表文本
        date_str (str, optional): 日期字符串，格式為 MM/DD
        
    Returns:
        dict: Discord 訊息數據
    """
    # 創建主要內容
    message = {
        "content": f"### **{date_str or ''} 過去 {hours} 小時推特內容摘要報告**",
        "embeds": parse_ai_summary_to_discord_embeds(summary, hours, twitter_users_text)
    }
    
    return message
