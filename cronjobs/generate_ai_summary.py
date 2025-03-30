#!/usr/bin/env python
"""
Script to generate AI summaries from Twitter data using DeepSeek.
This script reads the Twitter JSON data and uses the AI Summarizer to generate a summary.
"""

import asyncio
import argparse
import logging
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from modules.config import Config
from modules.ai_summarizer import AISummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to generate AI summaries from Twitter data."""
    parser = argparse.ArgumentParser(description='Generate AI summaries from Twitter data')
    parser.add_argument('--json', help='Path to the JSON file with Twitter data', default='twitter_summary.json')
    parser.add_argument('--output', help='Path to save the summary output', default='twitter_ai_summary.md')
    parser.add_argument('--hours', type=int, help='Number of hours the data covers', default=24)
    parser.add_argument('--send_discord', action='store_true', help='Send the summary to Discord')
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    
    # Initialize config and AI summarizer
    config = Config()
    summarizer = AISummarizer(config)
    
    # Ensure the JSON file exists
    json_path = args.json
    if not os.path.isabs(json_path):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', json_path)
    
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return 1
    
    try:
        # Generate summary from JSON
        logger.info(f"Generating AI summary from {json_path}...")
        summary = await summarizer.generate_summary_from_json(json_path, args.hours)
        
        # Save summary to file
        output_path = args.output
        if not os.path.isabs(output_path):
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Twitter 摘要報告 (過去 {args.hours} 小時)\n\n")
            f.write(summary)
        
        logger.info(f"Summary saved to {output_path}")
        
        # Send to Discord if requested
        if args.send_discord and config.discord_channel_id:
            from cronjobs.send_webhook import send_message_to_discord
            from datetime import datetime
            
            # 取得今天的日期
            today = datetime.now().strftime("%m/%d")
            
            # 從 JSON 文件中獲取 Twitter 用戶名
            with open(json_path, 'r', encoding='utf-8') as f:
                tweets_data = json.load(f)
                twitter_users_text = ", ".join([f"@{user}" for user in tweets_data.keys()]) if tweets_data else "無監控用戶"
            
            # 創建主要內容
            message = {
                "content": f"### **{today} 過去 {args.hours} 小時推特內容摘要報告**",
                "embeds": []
            }
            
            # 將 AI 生成的摘要格式化為 Discord 訊息
            # 注意：Discord 的 embed 描述有字數限制，所以我們將長文本分成多個 embed
            
            # 分段處理摘要，每個主要段落作為一個單獨的 embed
            # 這樣可以避免超過 Discord 的字數限制，並且提高可讀性
            sections = summary.split("####")
            
            # 處理總體摘要部分 (如果存在)
            if len(sections) > 1:
                main_summary = sections[0].strip()
                if main_summary:
                    message["embeds"].append({
                        "title": f"過去 {args.hours} 小時推特摘要報告（Hololive 卡牌遊戲相關）",
                        "description": main_summary,
                        "color": 5814783,  # 紫色
                        "footer": {
                            "text": f"追蹤用戶: {twitter_users_text}"
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
                message["embeds"].append({
                    "title": title,
                    "description": content,
                    "color": 5814783  # 紫色
                })
            
            # 發送訊息
            logger.info("Sending AI summary to Discord...")
            send_message_to_discord(
                token=config.discord_token,
                channel_id=config.discord_channel_id,
                message_data=message
            )
            logger.info("AI summary sent to Discord successfully")
            
            # 發送原始推文連結
            links_message = {"content": "**原始推文連結：**\n"}
            for username, tweets in tweets_data.items():
                links_content = f"**User: {username}**\n"
                for tweet in tweets:
                    links_content += f"{tweet['url']}\n"
                links_content += "\n"
                
                # 檢查訊息長度，Discord 有 2000 字元的限制
                if len(links_message["content"] + links_content) > 1900:  # 留一些餘量
                    # 發送當前訊息並創建新的
                    send_message_to_discord(
                        token=config.discord_token,
                        channel_id=config.discord_channel_id,
                        message_data=links_message
                    )
                    links_message = {"content": ""}
                
                links_message["content"] += links_content
            
            # 發送最後的連結訊息（如果有內容）
            if links_message["content"].strip():
                send_message_to_discord(
                    token=config.discord_token,
                    channel_id=config.discord_channel_id,
                    message_data=links_message
                )
                logger.info("Tweet links sent to Discord successfully")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error generating AI summary: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
