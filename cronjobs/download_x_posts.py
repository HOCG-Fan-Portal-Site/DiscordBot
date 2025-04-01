#!/usr/bin/env python
"""
測試腳本，用於在本地直接測試 TwitterClient 的功能。
"""
import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config import Config
from modules.twitter_client import TwitterClient

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def save_tweets_to_markdown(tweets_by_user, output_file=None):
    if output_file is None:
        output_file = f"twitter_summary.md"
    
    # 同時保存為 JSON 文件
    json_output_file = output_file.replace('.md', '.json')
    with open(json_output_file, 'w', encoding='utf-8') as json_file:
        json.dump(tweets_by_user, json_file, ensure_ascii=False, indent=4, default=str)
    logger.info(f"已將推文保存到 JSON 文件: {json_output_file}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Twitter 摘要報告\n\n")
        f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for username, tweets in tweets_by_user.items():
            f.write(f"## 用戶: @{username}\n\n")
            f.write(f"共 {len(tweets)} 條推文\n\n")
            
            for i, tweet in enumerate(tweets, 1):
                f.write(f"### 推文 {i}\n\n")
                # 根據 is_retweet 顯示推文類型
                tweet_type = "轉推" if tweet['is_retweet'] else "推文"
                f.write(f"- **類型**: {tweet_type}\n")
                if tweet['is_retweet'] and 'original_author' in tweet:
                    f.write(f"- **原作者**: @{tweet['original_author']}\n")
                f.write(f"- **ID**: {tweet['id']}\n")
                f.write(f"- **時間**: {tweet['created_at']}\n")
                f.write(f"- **內容**: {tweet['text']}\n")
                f.write(f"- **鏈接**: {tweet['url']}\n")
                
                # 添加圖片
                if 'image_urls' in tweet and tweet['image_urls']:
                    f.write(f"\n#### 圖片 ({len(tweet['image_urls'])})\n\n")
                    for j, img_url in enumerate(tweet['image_urls'], 1):
                        f.write(f"![圖片 {j}]({img_url})\n\n")
                
                f.write("\n---\n\n")
    
    logger.info(f"已將推文保存到 Markdown 文件: {output_file}")
    return output_file

async def test_get_recent_tweets(client, username=None, hours=24, save_md=True):
    """測試獲取最近推文的功能"""
    logger.info(f"測試獲取最近 {hours} 小時的推文...")
    
    tweets_by_user = await client.get_recent_tweets(hours=hours)
    
    if username:
        # 處理單個用戶或多個用戶的情況
        if isinstance(username, list):
            # 如果是用戶列表，只處理列表中的用戶
            filtered_tweets = {}
            for user in username:
                user_lower = user.lower()
                if user_lower in tweets_by_user:
                    filtered_tweets[user_lower] = tweets_by_user[user_lower]
                    logger.info(f"獲取到 {user} 的 {len(filtered_tweets[user_lower])} 條推文")
                else:
                    logger.warning(f"未找到用戶 {user} 的推文")
        else:
            # 如果是單個用戶字符串
            user_lower = username.lower()
            if user_lower in tweets_by_user:
                filtered_tweets = {user_lower: tweets_by_user[user_lower]}
                logger.info(f"獲取到 {username} 的 {len(filtered_tweets[user_lower])} 條推文")
            else:
                logger.warning(f"未找到用戶 {username} 的推文")
                filtered_tweets = {}
    else:
        # 處理所有用戶的推文
        filtered_tweets = tweets_by_user
        for username, tweets in filtered_tweets.items():
            logger.info(f"獲取到 {username} 的 {len(tweets)} 條推文")
    # 保存為 Markdown 文件
    if save_md and filtered_tweets:
        save_tweets_to_markdown(filtered_tweets)
    
    return tweets_by_user

async def main():
    """主函數"""
    # 加載環境變量
    load_dotenv()
    
    # 創建配置對象
    config = Config()
    
    # 創建 TwitterClient 實例
    client = TwitterClient(config)
    hours = 24
    username = config.twitter_users
    await test_get_recent_tweets(client, username, hours)


if __name__ == "__main__":
    asyncio.run(main())
