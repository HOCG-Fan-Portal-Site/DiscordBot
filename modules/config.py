"""
Configuration module for the Discord bot.
Handles loading and providing access to all configuration settings.
"""

import os
from typing import List

class Config:
    """Configuration class that loads and provides access to all settings."""
    
    def __init__(self):
        """Initialize configuration by loading from environment variables."""
        # Discord settings
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.summary_channel_id = os.getenv('SUMMARY_CHANNEL_ID', '')
        self.discord_guild_id = os.getenv('DISCORD_GUILD_ID')
        self.discord_channel_id = os.getenv('DISCORD_CHANNEL_ID')
        
        # Twitter users to monitor
        twitter_users_str = os.getenv('TWITTER_USERS', '')
        self.twitter_users = [user.strip() for user in twitter_users_str.split(',') if user.strip()]
        
        # Twitter API settings (not needed with snscrape, but kept for compatibility)
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.twitter_api_secret = os.getenv('TWITTER_API_SECRET')
        self.twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.twitter_access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        self.twitter_email = os.getenv('TWITTER_EMAIL')
        self.twitter_password = os.getenv('TWITTER_PASSWORD')
        
        # AI provider settings
        self.ai_provider = os.getenv('AI_PROVIDER', 'openai').lower()
        
        # OpenAI settings
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        # DeepSeek settings
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.deepseek_model = os.getenv('DEEPSEEK_MODEL')
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required configuration is present."""
        if not self.discord_token:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        if not self.twitter_users:
            raise ValueError("TWITTER_USERS environment variable is required and must contain at least one username")
        
        if self.ai_provider not in ['openai', 'deepseek']:
            raise ValueError("AI_PROVIDER must be either 'openai' or 'deepseek'")
        
        if self.ai_provider == 'openai' and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required when using OpenAI")
        
        if self.ai_provider == 'deepseek' and not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required when using DeepSeek")
