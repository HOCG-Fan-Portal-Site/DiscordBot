# Twitter Summary Discord Bot

A modular Discord bot that fetches tweets from specified Twitter users, organizes them, and generates AI-powered summaries using either OpenAI or DeepSeek.

## Features

- Monitors tweets from multiple Twitter users
- Fetches tweets from the past 24 hours (configurable)
- Organizes tweets by user
- Generates AI-powered summaries using OpenAI or DeepSeek
- Provides Discord commands for on-demand summaries
- Optional scheduled daily summaries

## Project Structure

```
DiscordBot/
├── .env.example         # Example environment variables file
├── bot.py               # Main bot application file
├── requirements.txt     # Python dependencies
└── modules/             # Modular components
    ├── config.py        # Configuration handling
    ├── twitter_client.py # Twitter API integration
    ├── ai_summarizer.py # AI integration for summaries
    └── tweet_formatter.py # Tweet formatting utilities
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API keys and configuration
4. Run the bot:
   ```
   python bot.py
   ```

## Configuration

Create a `.env` file with the following variables:

```
# Discord Bot Token
DISCORD_TOKEN=your_discord_token_here

# Twitter API Credentials
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_SECRET=your_twitter_access_secret_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# DeepSeek API Key (Optional - uncomment if using DeepSeek)
# DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Twitter Users to Monitor (comma-separated usernames without @)
TWITTER_USERS=username1,username2,username3

# AI Model Selection (openai or deepseek)
AI_PROVIDER=openai

# OpenAI Model (if using OpenAI)
OPENAI_MODEL=gpt-3.5-turbo

# DeepSeek Model (if using DeepSeek)
DEEPSEEK_MODEL=deepseek-chat

# Optional: Channel ID for scheduled summaries
# SUMMARY_CHANNEL_ID=your_channel_id_here
```

## Discord Commands

- `!summary [hours]` - Get a summary of tweets from the last X hours (default: 24)
- `!users` - List all Twitter users being monitored
- `!provider` - Show the current AI provider being used

## Requirements

- Python 3.8+
- discord.py
- tweepy
- openai
- python-dotenv
- aiohttp
- python-dateutil

## License

See the [LICENSE](LICENSE) file for details.
