import os
import json
import argparse
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def create_discord_headers(token, content_type=True):
    """
    創建用於 Discord API 請求的 headers
    
    Args:
        token: Discord Bot Token
        content_type: 是否包含 Content-Type 頭
        
    Returns:
        dict: Headers 字典
    """
    headers = {
        'Authorization': f'Bot {token}'
    }
    
    if content_type:
        headers['Content-Type'] = 'application/json'
        
    return headers

def send_discord_request(api_url, headers, json_data=None, files=None, data=None):
    """
    發送請求到 Discord API
    
    Args:
        api_url: Discord API URL
        headers: 請求頭
        json_data: JSON 數據 (可選)
        files: 文件數據 (可選)
        data: 表單數據 (可選)
        
    Returns:
        requests.Response: 響應對象
    """
    try:
        response = requests.post(api_url, headers=headers, json=json_data, files=files, data=data)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.error(f"發送請求到 Discord API 時出錯: {str(e)}")
        raise

def create_summary_message(tweets_data, hours):
    """
    創建摘要消息
    
    Args:
        tweets_data: Twitter 數據字典
        hours: 資料涵蓋的小時數
        
    Returns:
        dict: 摘要消息數據
    """
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
    
    return summary_message

def create_tweet_embed(tweet):
    """
    為單條推文創建 embed
    
    Args:
        tweet: 推文數據
        
    Returns:
        dict: Embed 數據
    """
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
    
    return embed

def create_user_message(username, tweets):
    """
    為用戶創建推文聚合消息
    
    Args:
        username: 用戶名
        tweets: 用戶的推文列表
        
    Returns:
        dict: 用戶消息數據
    """
    # 只處理最近的 5 條推文，避免超過 Discord 的 embed 限制
    recent_tweets = tweets[:5]
    if not recent_tweets:
        return None
        
    # 創建用戶推文聚合消息
    user_message = {
        "content": f"📢 @{username} 的最近推文 (共 {len(tweets)} 條)",
        "embeds": []
    }
    
    # 添加每條推文作為單獨的 embed
    for tweet in recent_tweets:
        embed = create_tweet_embed(tweet)
        
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
    
    return user_message

def send_file_to_discord(api_url, token, file_path, content, file_name=None):
    """
    將文件作為附件發送到 Discord
    
    Args:
        api_url: Discord API URL
        token: Discord Bot Token
        file_path: 文件路徑
        content: 消息內容
        file_name: 文件名 (可選)
        
    Returns:
        bool: 是否成功發送
    """
    try:
        if not file_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"file_{timestamp}{os.path.splitext(file_path)[1]}"
            
        files = {
            'file': (file_name, open(file_path, 'rb'))
        }
        
        file_message = {
            'content': content
        }
        
        # 發送文件需要不同的 headers
        file_headers = create_discord_headers(token, content_type=False)
        
        response = send_discord_request(api_url, file_headers, data=file_message, files=files)
        return True
    except Exception as e:
        logger.error(f"發送文件到 Discord 時出錯: {str(e)}")
        return False

def send_message_to_discord(token, channel_id, message_data=None, json_path=None, hours=24):
    """
    通過 Discord API 發送訊息或 Twitter 資料。
    
    Args:
        token: Discord Bot Token
        channel_id: Discord 頻道 ID
        message_data: 要發送的訊息資料 (dict)，如果提供則直接發送此訊息
        json_path: JSON 文件路徑 (可選，如果提供 message_data 則忽略)
        hours: 資料涵蓋的小時數 (僅用於 Twitter 資料)
        
    Returns:
        bool: 是否成功發送
    """
    try:
        # 設置 API URL
        api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        
        # 設置 headers
        headers = create_discord_headers(token)
        
        # 如果提供了 message_data，直接發送
        if message_data:
            send_discord_request(api_url, headers, json_data=message_data)
            logger.info(f"成功發送訊息到 Discord")
            return True
        
        # 否則，處理 Twitter 資料
        if not json_path:
            logger.error("未提供 message_data 或 json_path")
            return False
            
        # 檢查文件是否存在
        if not os.path.exists(json_path):
            logger.error(f"JSON 文件不存在: {json_path}")
            return False
        
        # 讀取 JSON 文件
        with open(json_path, 'r', encoding='utf-8') as f:
            tweets_data = json.load(f)
        
        # 創建並發送摘要消息
        summary_message = create_summary_message(tweets_data, hours)
        send_discord_request(api_url, headers, json_data=summary_message)
        logger.info(f"成功發送摘要消息到 Discord")
        
        # 為每個用戶創建並發送聚合消息
        for username, tweets in tweets_data.items():
            user_message = create_user_message(username, tweets)
            if user_message:
                send_discord_request(api_url, headers, json_data=user_message)
                logger.info(f"成功發送 @{username} 的推文聚合消息到 Discord")
        
        # 上傳 JSON 文件作為附件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"twitter_data_{timestamp}.json"
        content = f"過去 {hours} 小時的 Twitter 資料 (JSON 格式)"
        
        send_file_to_discord(api_url, token, json_path, content, file_name)
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
    parser.add_argument('--hours', type=int, default=24, help='資料涵蓋的小時數')
    
    args = parser.parse_args()
    
    # 獲取頻道 ID
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    if not channel_id:
        logger.error("未提供頻道 ID，且環境變數 DISCORD_CHANNEL_ID 未設置")
        return False
    
    # 獲取 Bot Token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("未提供 Bot Token，且環境變數 DISCORD_TOKEN 未設置")
        return False
    
    # 發送消息
    return send_message_to_discord(token, channel_id, json_path=args.json, hours=args.hours)

if __name__ == "__main__":
    main()
