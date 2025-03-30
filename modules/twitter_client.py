"""
Twitter client module for fetching tweets from specified users.
Uses Selenium to scrape Twitter without API limitations.
"""

import logging
import asyncio
import time
import json
import re
import os
import pickle
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import concurrent.futures
from modules.config import Config
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class TwitterClient:
    """Client for interacting with Twitter using Selenium."""
    
    def __init__(self, config: Config):
        """Initialize the Twitter client with the provided configuration.
        
        Args:
            config: Configuration object containing Twitter usernames to monitor
        """
        self.config = config
        # 創建執行緒池
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        
        # 添加緩存以減少請求
        self._user_ids_cache = None
        self._user_ids_cache_time = None
        self._tweets_cache = {}
        self._tweets_cache_time = {}
        self._search_cache = {}
        self._search_cache_time = {}
        
        # 緩存有效期（分鐘）
        self.cache_ttl_minutes = 5
        
        # Cookie 文件路徑
        self.cookie_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'twitter_cookies.pkl')
        
        # 嘗試加載 cookies
        self._cookies = self._load_cookies()
    
    def _load_cookies(self):
        """從文件加載 Twitter cookies。
        
        Returns:
            List of cookie dictionaries or None if file not found or error
        """
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                logger.info(f"已從 {self.cookie_file} 加載 {len(cookies)} 個 cookies")
                return cookies
            else:
                logger.warning(f"Cookie 文件 {self.cookie_file} 不存在")
                return None
        except Exception as e:
            logger.error(f"加載 cookies 時出錯: {str(e)}")
            return None
    
    def _setup_driver(self):
        """Set up and return a configured Chrome WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無頭模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    
    def _apply_cookies(self, driver):
        if not self._cookies:
            logger.error("沒有可用的 cookies，請先運行 'python get_twitter_cookies.py' 手動登入並保存 cookies")
            logger.error("注意：get_twitter_cookies.py 會打開瀏覽器並需要您手動完成登入操作")
            
            # 檢查 cookies 文件是否存在
            cookies_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "twitter_cookies.pkl")
            if not os.path.exists(cookies_path):
                logger.error(f"找不到 cookies 文件: {cookies_path}")
            else:
                logger.error(f"cookies 文件存在但無法載入，可能已過期或損壞，請重新運行 get_twitter_cookies.py")
            
            return False
        
        try:
            # 首先訪問 Twitter 域名
            driver.get("https://twitter.com")
            time.sleep(2)
            
            # 添加保存的 cookies
            for cookie in self._cookies:
                try:
                    # 確保 cookie 有正確的域名
                    if 'domain' in cookie and cookie['domain'].startswith('.'):
                        cookie['domain'] = cookie['domain'][1:] if cookie['domain'].startswith('.') else cookie['domain']
                    
                    # 添加 cookie
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加 cookie 時出錯: {str(e)}")
            
            # 刷新頁面以應用 cookies
            driver.refresh()
            time.sleep(3)
            
            # 檢查是否已登入
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='primaryColumn']"))
                )
                logger.info("成功使用 cookies 登入 Twitter")
                return True
            except TimeoutException:
                logger.warning("使用 cookies 登入失敗")
                return False
            
        except Exception as e:
            logger.error(f"應用 cookies 時出錯: {str(e)}")
            return False
    
    async def get_recent_tweets(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        cache_key = f"tweets_{hours}"
        current_time = datetime.now(timezone.utc)
        
        if (cache_key in self._tweets_cache and 
            cache_key in self._tweets_cache_time and 
            (current_time - self._tweets_cache_time[cache_key]).total_seconds() < self.cache_ttl_minutes * 60):
            logger.info(f"Using cached tweets for {hours} hours")
            return self._tweets_cache[cache_key]
        
        tweets_by_user = {username.lower(): [] for username in self.config.twitter_users}
        
        # Calculate the start time for tweet retrieval
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        logger.info(f"start time: {start_time}")
        
        def _get_user_tweets(username):
            driver = None
            try:
                driver = self._setup_driver()
                
                # 嘗試使用 cookies 登入
                if not self._apply_cookies(driver):
                    logger.warning("無法使用 cookies 登入 Twitter，請先運行 get_twitter_cookies.py 獲取有效的 cookies")
                    logger.warning("注意：get_twitter_cookies.py 會打開瀏覽器並需要您手動完成登入操作")
                    
                    # 檢查 cookies 文件是否存在
                    cookies_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "twitter_cookies.pkl")
                    if not os.path.exists(cookies_path):
                        logger.error(f"找不到 cookies 文件: {cookies_path}")
                    else:
                        logger.error(f"cookies 文件存在但無法載入，可能已過期或損壞，請重新運行 get_twitter_cookies.py")
                    
                    return []
                
                user_tweets = []
                
                # 訪問用戶頁面
                url = f"https://twitter.com/{username}"
                logger.info(f"Fetching tweets for {username} from {url}")
                driver.get(url)
                
                # 等待頁面加載
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']"))
                    )
                except TimeoutException:
                    logger.warning(f"No tweets found for {username} or page not loaded properly")
                    return []
                
                # 使用增量滾動和批處理方式獲取推文
                max_scrolls = 10  # 設置最大滾動次數
                processed_ids = set()  # 用於追踪已處理的推文ID
                
                # 先處理當前可見的推文
                tweet_elements = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                logger.info(f"Initially found {len(tweet_elements)} visible tweets for {username}")
                
                # 處理推文的函數
                def process_tweet_elements(elements):
                    processed = []
                    for tweet_element in elements:
                        try:
                            # 提取推文 ID
                            tweet_links = tweet_element.find_elements(By.CSS_SELECTOR, "a[href*='/status/']")
                            if not tweet_links:
                                continue
                            
                            tweet_url = tweet_links[0].get_attribute("href")
                            tweet_id_match = re.search(r"/status/(\d+)", tweet_url)
                            if not tweet_id_match:
                                continue
                            
                            tweet_id = tweet_id_match.group(1)
                            
                            # 如果已經處理過這個推文，則跳過
                            if tweet_id in processed_ids:
                                continue
                            
                            processed_ids.add(tweet_id)
                            
                            # 檢查是否為轉推
                            is_retweet = False
                            original_author = None
                            try:
                                # 尋找推文作者資訊
                                author_elements = tweet_element.find_elements(By.CSS_SELECTOR, "div[data-testid='User-Name']")
                                if author_elements:
                                    # 提取用戶名（通常在第一個 span 中的第二個 a 標籤）
                                    author_links = author_elements[0].find_elements(By.TAG_NAME, "a")
                                    if len(author_links) >= 2:
                                        author_href = author_links[1].get_attribute("href")
                                        author_username = author_href.split("/")[-1].lower()
                                        
                                        # 檢查作者是否與查詢的用戶名匹配
                                        if author_username != username.lower():
                                            logger.info(f"檢測到轉推: 作者 @{author_username} 不是 @{username}")
                                            is_retweet = True
                                            original_author = author_username
                            except Exception as e:
                                logger.warning(f"檢查轉推狀態時出錯: {str(e)}")
                            
                            # 提取推文內容
                            tweet_text_element = tweet_element.find_elements(By.CSS_SELECTOR, "div[data-testid='tweetText']")
                            tweet_text = tweet_text_element[0].text if tweet_text_element else ""
                            
                            # 記錄推文內容以進行調試
                            logger.info(f"Tweet ID: {tweet_id}, Content: {tweet_text}")
                            
                            # 提取時間戳（可能需要進一步處理）
                            time_elements = tweet_element.find_elements(By.CSS_SELECTOR, "time")
                            created_at = datetime.now(timezone.utc)
                            if time_elements:
                                timestamp = time_elements[0].get_attribute("datetime")
                                if timestamp:
                                    # 確保時間戳包含時區信息
                                    created_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                                    logger.info(f"Tweet created at: {created_at}")
                            
                            # 如果推文早於指定時間，則跳過
                            if created_at < start_time:
                                continue
                            
                            # 提取推文中的圖片 URL
                            image_urls = []
                            try:
                                # 尋找圖片容器
                                image_containers = tweet_element.find_elements(By.CSS_SELECTOR, "div[data-testid='tweetPhoto']")
                                for container in image_containers:
                                    # 尋找圖片元素
                                    img_elements = container.find_elements(By.TAG_NAME, "img")
                                    for img in img_elements:
                                        img_url = img.get_attribute("src")
                                        if img_url and "https://pbs.twimg.com/media" in img_url:
                                            # 獲取高質量圖片 URL (移除尺寸限制參數)
                                            img_url = re.sub(r"&name=\w+", "&name=orig", img_url)
                                            image_urls.append(img_url)
                                            logger.info(f"Found image: {img_url}")
                            except Exception as e:
                                logger.error(f"Error extracting images: {str(e)}")
                            
                            # 構建推文數據
                            tweet_data = {
                                'id': tweet_id,
                                'text': tweet_text,
                                'created_at': created_at,
                                'image_urls': image_urls,
                                'url': tweet_url,
                                'is_retweet': is_retweet
                            }
                            
                            # 如果是轉推，添加原作者資訊
                            if is_retweet and original_author:
                                tweet_data['original_author'] = original_author
                            processed.append(tweet_data)
                        except StaleElementReferenceException:
                            logger.warning("Stale element reference when processing tweet, skipping")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing tweet for {username}: {str(e)}")
                    return processed
                
                # 處理初始可見的推文
                initial_tweets = process_tweet_elements(tweet_elements)
                user_tweets.extend(initial_tweets)
                logger.info(f"Processed {len(initial_tweets)} initial tweets")
                
                # 逐步滾動並處理新出現的推文
                for scroll_count in range(max_scrolls):
                    # 滾動頁面，但不是直接到底部，而是增量滾動
                    scroll_height = driver.execute_script("return window.innerHeight") * 0.8
                    driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                    time.sleep(2)  # 等待頁面加載
                    
                    # 獲取當前可見的推文
                    new_tweet_elements = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                    logger.info(f"Found {len(new_tweet_elements)} tweets after scroll {scroll_count+1}")
                    
                    # 處理新出現的推文
                    new_tweets = process_tweet_elements(new_tweet_elements)
                    user_tweets.extend(new_tweets)
                    logger.info(f"Processed {len(new_tweets)} new tweets after scroll {scroll_count+1}")
                    
                    # 如果沒有新推文，可以提前結束滾動
                    if len(new_tweets) == 0:
                        break
                
                logger.info(f"Total tweets collected for {username}: {len(user_tweets)}")
                return user_tweets
            except TimeoutException:
                logger.error(f"Timeout while fetching tweets for {username}")
                return []
            except Exception as e:
                logger.error(f"Error fetching tweets for {username}: {str(e)}", exc_info=True)
                return []
            finally:
                if driver:
                    driver.quit()
        
        #處理每個用戶
        for username in self.config.twitter_users:
            logger.info(f"Fetching tweets for {username}")
            
            # 使用 run_in_executor 執行阻塞操作
            loop = asyncio.get_event_loop()
            tweets = await loop.run_in_executor(
                self.executor, 
                _get_user_tweets, 
                username
            )
            
            tweets_by_user[username.lower()] = tweets
            
            # 添加短暫延遲以避免過度請求
            await asyncio.sleep(1)
        
        # 更新緩存
        self._tweets_cache[cache_key] = tweets_by_user
        self._tweets_cache_time[cache_key] = current_time
        
        return tweets_by_user
