#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main Discord Bot application file.
This script initializes and runs the Discord bot with all its components.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import datetime

# Import modules
from modules.twitter_client import TwitterClient
from modules.ai_summarizer import AISummarizer
from modules.tweet_formatter import TweetFormatter
from modules.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discord_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TwitterSummaryBot(commands.Bot):
    """Main Discord bot class for Twitter summary functionality."""
    
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=None, intents=intents)
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize components
        self.twitter_client = TwitterClient(self.config)
        self.ai_summarizer = AISummarizer(self.config)
        self.tweet_formatter = TweetFormatter()
        
        # Add commands
        self.add_commands()
    
    async def setup_hook(self):
        """Setup hook for registering app commands."""
        # 註冊 slash commands
        guild_id = self.config.discord_guild_id
        
        if guild_id and guild_id.strip():  # 檢查 guild_id 是否存在且不為空白字符串
            try:
                guild = discord.Object(id=int(guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Slash commands synced to test guild: {guild_id}")
            except ValueError:
                logger.warning(f"Invalid guild ID: {guild_id}. Syncing commands globally instead.")
                await self.tree.sync()
                logger.info("Slash commands synced globally")
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally")
    
    async def on_ready(self):
        """Event triggered when the bot is ready and connected to Discord."""
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        logger.info(f'Bot is now running!')
        logger.info(f'Monitoring tweets from: {", ".join(self.config.twitter_users)}')
        logger.info(f'Using AI provider: {self.config.ai_provider}')
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="龍乳"
        ))
    
    def add_commands(self):
        """Register all bot commands."""
        # 只保留斜線命令
        @self.tree.command(name="users", description="列出所有正在監控的 Twitter 用戶")
        async def twitter_users(interaction: discord.Interaction):
            """List all Twitter users being monitored."""
            users = self.config.twitter_users
            await interaction.response.send_message(f"目前正在監控的 Twitter 用戶: {', '.join(users)}")
        
        @self.tree.command(name="provider", description="顯示目前使用的 AI 提供者")
        async def ai_provider(interaction: discord.Interaction):
            """Show the current AI provider being used."""
            provider = self.config.ai_provider
            model = self.config.openai_model if provider == "openai" else self.config.deepseek_model
            await interaction.response.send_message(f"目前使用 {provider.upper()} 與模型: {model}")


def main():
    """Main function to start the bot."""
    bot = TwitterSummaryBot()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()
