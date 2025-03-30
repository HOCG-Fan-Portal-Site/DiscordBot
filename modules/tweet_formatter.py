"""
Tweet formatter module for organizing and formatting tweets for display and summarization.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TweetFormatter:
    """Formatter for organizing and formatting tweets for display and summarization."""
    
    def format_for_summary(self, tweets_by_user: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format tweets by user for AI summarization.
        
        Args:
            tweets_by_user: Dictionary mapping usernames to lists of their tweets
            
        Returns:
            Formatted string containing all tweets organized by user
        """
        formatted_text = []
        
        for username, tweets in tweets_by_user.items():
            if not tweets:
                continue
                
            # Sort tweets by creation time (newest first)
            sorted_tweets = sorted(tweets, key=lambda x: x['created_at'], reverse=True)
            
            # Add user section header
            formatted_text.append(f"## @{username} ({len(sorted_tweets)} tweets)")
            
            # Add each tweet with metadata
            for tweet in sorted_tweets:
                # Format the timestamp
                timestamp = tweet['created_at'].strftime("%Y-%m-%d %H:%M:%S UTC")
                
                # Format engagement metrics
                engagement = f"❤️ {tweet['likes']} | 🔄 {tweet['retweets']}"
                
                # Add the formatted tweet
                formatted_text.append(f"- **[{timestamp}]** {tweet['text']}")
                formatted_text.append(f"  {engagement} | {tweet['url']}")
                formatted_text.append("")  # Empty line for readability
            
            # Add separator between users
            formatted_text.append("-" * 40)
            formatted_text.append("")
        
        return "\n".join(formatted_text)
    
    def format_for_discord(self, tweets_by_user: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Format tweets by user for Discord display, respecting Discord's message length limits.
        
        Args:
            tweets_by_user: Dictionary mapping usernames to lists of their tweets
            
        Returns:
            List of formatted strings, each within Discord's message length limit
        """
        formatted_messages = []
        current_message = []
        current_length = 0
        
        # Discord message length limit (leaving some room for safety)
        MAX_LENGTH = 1900
        
        for username, tweets in tweets_by_user.items():
            if not tweets:
                continue
                
            # Sort tweets by creation time (newest first)
            sorted_tweets = sorted(tweets, key=lambda x: x['created_at'], reverse=True)
            
            # Create user section header
            user_header = f"**@{username}** ({len(sorted_tweets)} tweets)\n"
            
            # Check if adding this section would exceed the limit
            if current_length + len(user_header) > MAX_LENGTH and current_message:
                # Save current message and start a new one
                formatted_messages.append("\n".join(current_message))
                current_message = []
                current_length = 0
            
            # Add user section header
            current_message.append(user_header)
            current_length += len(user_header)
            
            # Add each tweet with metadata
            for tweet in sorted_tweets:
                # Format the timestamp
                timestamp = tweet['created_at'].strftime("%Y-%m-%d %H:%M:%S UTC")
                
                # Format the tweet
                tweet_text = f"• [{timestamp}] {tweet['text']}\n"
                tweet_meta = f"  ❤️ {tweet['likes']} | 🔄 {tweet['retweets']} | {tweet['url']}\n\n"
                
                # Check if adding this tweet would exceed the limit
                if current_length + len(tweet_text) + len(tweet_meta) > MAX_LENGTH:
                    # Save current message and start a new one
                    formatted_messages.append("\n".join(current_message))
                    current_message = []
                    current_length = 0
                
                # Add the tweet
                current_message.append(tweet_text)
                current_message.append(tweet_meta)
                current_length += len(tweet_text) + len(tweet_meta)
            
            # Add separator between users
            separator = "-" * 40 + "\n"
            
            # Check if adding the separator would exceed the limit
            if current_length + len(separator) > MAX_LENGTH:
                # Save current message and start a new one
                formatted_messages.append("\n".join(current_message))
                current_message = []
                current_length = 0
            
            # Add the separator
            current_message.append(separator)
            current_length += len(separator)
        
        # Add any remaining content
        if current_message:
            formatted_messages.append("\n".join(current_message))
        
        return formatted_messages
