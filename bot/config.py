settings = {
    "bot": {
        "tokens": {
            "discord": "", # Discord bot token (https://discordapp.com/developers/applications/me)
            "ai": {
                "openai": "sk-xxxxx", # API key for OpenAI provider
                "openr": "sk-xxxxx", # API key for OpenRouter provider
                "anthropic": "sk-xxxxx", # API key for Anthropic provider
                "groq": "gsk_xxxxx", # API key for Groq provider, enabled by default
            },
        },
        "version": "2024.1",
        "developer": {"logs": 0}, # Place a valid channel ID here
    }
}

warnings = {
    "only_show_warnings": False,  # When set to true, only warnings will be printed to the console LOG.
    "local_run": False,  # Shows: Bot is running locally, and will go offline if you or your computer stops this program. If this bot happens to be running online, you can disable this warning by opening config.py and setting warnings[local_run] to False.
    "hb_block_10": True,  # Shows: Bot will stop running if hearbeat is blocked for 10 seconds or more.
}
