"""
AI Summarizer module for generating summaries of tweets.
Supports DeepSeek API integration.
"""

import logging
import asyncio
import json
import os
from typing import Dict, List, Any
from openai import OpenAI
from modules.config import Config
import concurrent.futures

logger = logging.getLogger(__name__)

class AISummarizer:
    """AI-powered summarizer for generating summaries of tweets."""
    
    def __init__(self, config: Config):
        """Initialize the AI summarizer with the provided configuration.
        
        Args:
            config: Configuration object containing API keys and settings
        """
        self.config = config
        self.client = None
        self._initialize_client()
        # 創建執行緒池
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    
    def _initialize_client(self):
        """Initialize the DeepSeek client based on configuration."""
        self.client = OpenAI(
            api_key=self.config.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        logger.info("DeepSeek client initialized")
    
    async def generate_summary_from_json(self, json_file_path: str, hours: int = 24) -> str:
        """Generate a summary from a JSON file containing tweet data.
        
        Args:
            json_file_path: Path to the JSON file containing tweet data
            hours: Number of hours the data covers
            
        Returns:
            Generated summary text
        """
        try:
            # 讀取 JSON 文件
            with open(json_file_path, 'r', encoding='utf-8') as file:
                tweets_data = json.load(file)
                logger.info(f"Loaded {len(tweets_data)} tweets from JSON file")
            return await self._generate_deepseek_json_summary(tweets_data, hours)

        except Exception as e:
            logger.error(f"Error generating summary from JSON: {str(e)}", exc_info=True)
            raise
    
    async def _generate_deepseek_json_summary(self, tweets_data: Dict, hours: int) -> str:
        """Generate a summary from JSON tweet data using DeepSeek's API.
        
        Args:
            tweets_data: Dictionary containing tweet data
            hours: Number of hours the data covers
            
        Returns:
            Generated summary text
        """
        try:
            # 計算所有推文的總數
            total_tweets = sum(len(tweets) for tweets in tweets_data.values())
            
            # 準備推文數據的簡短表示
            tweets_summary = []
            for username, tweets in tweets_data.items():
                for tweet in tweets:
                    tweet_type = "轉推" if tweet.get('is_retweet', False) else "推文"
                    tweet_info = {
                        "username": username,
                        "type": tweet_type,
                        "text": tweet['text'],
                        "created_at": tweet['created_at']
                    }
                    if tweet.get('is_retweet', False) and 'original_author' in tweet:
                        tweet_info["original_author"] = tweet['original_author']
                    tweets_summary.append(tweet_info)
                    logger.info(f"Processed tweet: {tweet['text']}")
            logger.info(f"Total tweets processed: {len(tweets_summary)}")
            
            # Define the system prompt for summarization
            system_prompt = """
            你是一個專業的推特內容摘要助手。你的任務是分析並總結過去時間內的所有推文，提供一個全面且條理清晰的摘要。
            """
            
            user_prompt = f"""
            請根據以下過去 {hours} 小時的推特數據，生成一份全面的摘要報告：

            {json.dumps(tweets_summary, ensure_ascii=False, indent=2)}

            要求：
            1. 對過去 {hours} 小時所有用戶發文加總起來做一個總體摘要
            2. 以條列式列出重要資訊和趨勢
            3. 必須使用繁體中文回覆
            4. 注意識別轉推與原創推文的區別
            5. 重點關注與卡牌遊戲、Hololive 相關的內容
            """
            
            # Run the DeepSeek API call in a thread pool to avoid blocking
            def _call_deepseek_api():
                response = self.client.chat.completions.create(
                    model=self.config.deepseek_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=1.3
                )
                return response.choices[0].message.content
            
            # 使用 run_in_executor 替代 to_thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.executor, _call_deepseek_api)
            logger.info(f"DeepSeek JSON summary generated: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating DeepSeek JSON summary: {str(e)}", exc_info=True)
            raise

# 提供一個簡單的命令行介面來測試摘要功能
async def main():
    """Command line interface for testing the summarizer."""
    import argparse
    from dotenv import load_dotenv
    
    # 加載環境變量
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Generate a summary from Twitter data')
    parser.add_argument('--json', required=True, help='Path to the JSON file containing tweet data')
    parser.add_argument('--hours', type=int, default=24, help='Number of hours the data covers')
    args = parser.parse_args()
    
    # 創建配置和摘要器
    config = Config()
    summarizer = AISummarizer(config)
    
    # 生成摘要
    summary = await summarizer.generate_summary_from_json(args.json, args.hours)
    print(summary)

if __name__ == "__main__":
    asyncio.run(main())
