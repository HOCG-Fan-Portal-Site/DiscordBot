#!/usr/bin/env python
"""
使用 Discord API 發送 Twitter 資料到 Discord 頻道。
這個腳本可以在 test_twitter_client.py 生成文件後被調用。
"""
import os
import json
import argparse
import logging
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def send_message_to_discord(token, channel_id, message_data=None, json_path=None, md_path=None, hours=24):
    """
    通過 Discord API 發送訊息或 Twitter 資料。
    
    Args:
        token: Discord Bot Token
        channel_id: Discord 頻道 ID
        message_data: 要發送的訊息資料 (dict)，如果提供則直接發送此訊息
        json_path: JSON 文件路徑 (可選，如果提供 message_data 則忽略)
        md_path: Markdown 文件路徑 (可選，如果提供 message_data 則忽略)
        hours: 資料涵蓋的小時數 (僅用於 Twitter 資料)
        
    Returns:
        bool: 是否成功發送
    """
    try:
        # 設置 API URL
        api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        
        # 設置 headers
        headers = {
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json'
        }
        
        # 如果提供了 message_data，直接發送
        if message_data:
            response = requests.post(api_url, headers=headers, json=message_data)
            response.raise_for_status()
            logger.info(f"成功發送訊息到 Discord")
            return True
        
        # 否則，處理 Twitter 資料
        if not json_path or not md_path:
            logger.error("未提供 message_data 或 json_path/md_path")
            return False
            
        # 檢查文件是否存在
        if not os.path.exists(json_path):
            logger.error(f"JSON 文件不存在: {json_path}")
            return False
        
        if not os.path.exists(md_path):
            logger.error(f"Markdown 文件不存在: {md_path}")
            return False
        
        # 讀取 JSON 文件
        with open(json_path, 'r', encoding='utf-8') as f:
            tweets_data = json.load(f)
        
        # 創建一個摘要消息
        summary_message = {
            "content": f"📊 過去 {hours} 小時的 Twitter 摘要報告",
            "embeds": [
                {
                    "title": "Twitter 摘要報告",
                    "description": f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "color": 1942002,  # Twitter 藍色
                    "fields": []
                }
            ]
        }
        
        # 添加每個用戶的摘要
        for username, tweets in tweets_data.items():
            summary_message["embeds"][0]["fields"].append({
                "name": f"@{username}",
                "value": f"共 {len(tweets)} 條推文",
                "inline": True
            })
        
        # 發送摘要消息
        response = requests.post(api_url, headers=headers, json=summary_message)
        response.raise_for_status()
        logger.info(f"成功發送摘要消息到 Discord")
        
        # 為每個用戶創建一個聚合消息
        for username, tweets in tweets_data.items():
            # 只處理最近的 5 條推文，避免超過 Discord 的 embed 限制
            recent_tweets = tweets[:5]
            if not recent_tweets:
                continue
                
            # 創建用戶推文聚合消息
            user_message = {
                "content": f"📢 @{username} 的最近推文 (共 {len(tweets)} 條)",
                "embeds": []
            }
            
            # 添加每條推文作為單獨的 embed
            for tweet in recent_tweets:
                tweet_type = "轉推" if tweet.get('is_retweet', False) else "推文"
                
                # 創建 embed
                embed = {
                    "title": f"{tweet_type}: {tweet['text'][:100] + ('...' if len(tweet['text']) > 100 else '')}",
                    "description": tweet['text'] if len(tweet['text']) <= 500 else tweet['text'][:497] + '...',
                    "url": tweet['url'],
                    "color": 1942002 if not tweet.get('is_retweet', False) else 15844367,  # 藍色或橙色
                    "footer": {
                        "text": f"🕒 {tweet['created_at']} | Tweet ID: {tweet['id']}"
                    }
                }
                
                # 如果是轉推，添加原作者信息
                if tweet.get('is_retweet', False) and 'original_author' in tweet:
                    embed["author"] = {
                        "name": f"原作者: @{tweet['original_author']}",
                        "icon_url": "https://abs.twimg.com/responsive-web/client-web/icon-default.522d363a.png"
                    }
                
                # 如果有圖片，添加到 embed
                if 'image_urls' in tweet and tweet['image_urls']:
                    embed["image"] = {
                        "url": tweet['image_urls'][0]
                    }
                    
                    # 添加 embed 到消息
                    user_message["embeds"].append(embed)
                    
                    # 如果有多張圖片，為每張額外的圖片創建新的 embed
                    for img_url in tweet['image_urls'][1:]:
                        img_embed = {
                            "url": tweet['url'],
                            "image": {
                                "url": img_url
                            }
                        }
                        user_message["embeds"].append(img_embed)
                else:
                    # 沒有圖片的推文，直接添加 embed
                    user_message["embeds"].append(embed)
            
            # 發送用戶推文聚合消息
            response = requests.post(api_url, headers=headers, json=user_message)
            response.raise_for_status()
            logger.info(f"成功發送 @{username} 的推文聚合消息到 Discord")
        
        # 上傳 JSON 文件作為附件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        files = {
            'file': (f"twitter_data_{timestamp}.json", open(json_path, 'rb'))
        }
        
        file_message = {
            'content': f"過去 {hours} 小時的 Twitter 資料 (JSON 格式)"
        }
        
        # 發送文件需要不同的 headers
        file_headers = {
            'Authorization': f'Bot {token}'
        }
        
        response = requests.post(api_url, headers=file_headers, data=file_message, files=files)
        response.raise_for_status()
        logger.info(f"成功發送 JSON 文件到 Discord")
        
        return True
        
    except Exception as e:
        logger.error(f"發送消息到 Discord 時出錯: {str(e)}")
        return False

def main():
    """主函數，處理命令行參數並調用發送函數。"""
    # 載入環境變數
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='通過 Discord API 發送 Twitter 資料')
    parser.add_argument('--json', required=True, help='JSON 文件路徑')
    parser.add_argument('--md', required=True, help='Markdown 文件路徑')
    parser.add_argument('--hours', type=int, default=24, help='資料涵蓋的小時數')
    parser.add_argument('--channel', help='Discord 頻道 ID，如果未提供則從環境變數獲取')
    parser.add_argument('--token', help='Discord Bot Token，如果未提供則從環境變數獲取')
    
    args = parser.parse_args()
    
    # 獲取頻道 ID
    channel_id = args.channel or os.getenv('DISCORD_CHANNEL_ID')
    if not channel_id:
        logger.error("未提供頻道 ID，且環境變數 DISCORD_CHANNEL_ID 未設置")
        return False
    
    # 獲取 Bot Token
    token = args.token or os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("未提供 Bot Token，且環境變數 DISCORD_TOKEN 未設置")
        return False
    
    # 發送消息
    return send_message_to_discord(token, channel_id, json_path=args.json, md_path=args.md, hours=args.hours)

if __name__ == "__main__":
    main()
