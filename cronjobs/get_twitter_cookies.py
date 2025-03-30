#!/usr/bin/env python
"""
腳本用於手動登入 Twitter 並保存 cookies 到文件。
"""

import os
import json
import time
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

def setup_driver():
    """設置並返回配置好的 Chrome WebDriver。"""
    chrome_options = Options()
    # 不使用無頭模式，以便可以看到登入過程
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def login_twitter(driver):
    """登入 Twitter 並返回 cookies。"""
    # 獲取環境變量中的登入憑證
    email = os.getenv('TWITTER_EMAIL')
    password = os.getenv('TWITTER_PASSWORD')
    
    if not email or not password:
        print("錯誤: 環境變量中未設置 TWITTER_EMAIL 或 TWITTER_PASSWORD")
        return None
    
    try:
        print("嘗試登入 Twitter...")
        
        # 訪問 Twitter 登入頁面
        driver.get("https://twitter.com/i/flow/login")
        
        # 等待登入頁面加載
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']"))
        )
        
        # 輸入電子郵件
        print("輸入電子郵件...")
        email_field = driver.find_element(By.CSS_SELECTOR, "input[autocomplete='username']")
        email_field.send_keys(email)
        email_field.send_keys(Keys.ENTER)
        
        # 等待可能出現的用戶名確認頁面
        try:
            print("檢查是否需要輸入用戶名...")
            username_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']"))
            )
            # 如果需要，請在這裡手動輸入您的 Twitter 用戶名
            username = 'a_kuafen'  # 替換為您的 Twitter 用戶名
            print(f"輸入用戶名: {username}")
            username_field.send_keys(username)
            username_field.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"無需輸入用戶名或出現錯誤: {str(e)}")
        
        # 等待密碼輸入欄位
        print("等待密碼輸入欄位...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='current-password']"))
        )
        
        # 輸入密碼
        print("輸入密碼...")
        password_field.send_keys(password)
        password_field.send_keys(Keys.ENTER)
        
        # 等待登入完成
        print("等待登入完成...")
        time.sleep(5)
        
        # 檢查是否登入成功
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='primaryColumn']"))
            )
            print("成功登入 Twitter!")
            
            # 獲取 cookies
            cookies = driver.get_cookies()
            print(f"獲取到 {len(cookies)} 個 cookies")
            
            return cookies
        except Exception as e:
            print(f"登入失敗或無法確認登入狀態: {str(e)}")
            return None
        
    except Exception as e:
        print(f"登入過程中出現錯誤: {str(e)}")
        return None

def save_cookies(cookies, filename='twitter_cookies.pkl'):
    """保存 cookies 到文件。"""
    if not cookies:
        print("沒有 cookies 可保存")
        return False
    
    try:
        # 保存為 pickle 格式
        with open(filename, 'wb') as f:
            pickle.dump(cookies, f)
        
        # 同時保存為 JSON 格式以便查看
        with open(f"{filename}.json", 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=4)
        
        print(f"Cookies 已保存到 {filename} 和 {filename}.json")
        return True
    except Exception as e:
        print(f"保存 cookies 時出現錯誤: {str(e)}")
        return False

def main():
    """主函數。"""
    driver = None
    try:
        driver = setup_driver()
        cookies = login_twitter(driver)
        if cookies:
            save_cookies(cookies)
            print("請手動檢查您是否已成功登入 Twitter。如果登入成功，cookies 已被保存。")
        else:
            print("獲取 cookies 失敗")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
