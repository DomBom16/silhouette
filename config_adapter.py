import os
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq
from anthropic import Anthropic
from modules.logger import Logger

# Load environment variables from .env file
load_dotenv()

# Recreate the settings dictionary structure from environment variables
settings = {
    "bot": {
        "tokens": {
            "discord": os.getenv("BOT_TOKENS_DISCORD", ""),
            "ai": {
                "openai": os.getenv("BOT_TOKENS_AI_OPENAI", "sk-xxxxx"),
                "openr": os.getenv("BOT_TOKENS_AI_OPENR", "sk-xxxxx"),
                "anthropic": os.getenv("BOT_TOKENS_AI_ANTHROPIC", "sk-xxxxx"),
                "groq": os.getenv("BOT_TOKENS_AI_GROQ", "gsk_xxxxx"),
            },
        },
        "version": os.getenv("BOT_VERSION", "2024.1"),
        "developer": {"logs": int(os.getenv("BOT_DEVELOPER_LOGS", "0"))},
    }
}

# Recreate the warnings dictionary structure from environment variables
warnings = {
    "only_show_warnings": os.getenv("WARNINGS_ONLY_SHOW_WARNINGS", "0") == "1",
    "local_run": os.getenv("WARNINGS_LOCAL_RUN", "0") == "1",
    "hb_block_10": os.getenv("WARNINGS_HB_BLOCK_10", "1") == "1",
}

# Get the active AI provider from environment
active_provider = os.getenv("ACTIVE_AI_PROVIDER", "groq").lower()

# Get the active model for each provider
active_models = {
    "openai": os.getenv("OPENAI_MODEL", "gpt-4o"),
    "openrouter": os.getenv("OPENROUTER_MODEL", "lynn/soliloquy-l3"),
    "groq": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
}

# Define the AI provider adapter
class AIProvider:
    def __init__(self):
        self.provider_name = active_provider
        self.openai_client = None
        self.groq_client = None
        self.anthropic_client = None
        self.model = ""
        self.is_claude = False
        self._initialize_provider()

    def _initialize_provider(self):
        try:
            if self.provider_name == "openai":
                self.openai_client = OpenAI(api_key=settings["bot"]["tokens"]["ai"]["openai"])
                self.model = active_models["openai"]
                Logger().info(f"Using OpenAI provider with model {self.model}")
            elif self.provider_name == "openrouter":
                self.openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings["bot"]["tokens"]["ai"]["openr"],
                )
                self.model = active_models["openrouter"]
                Logger().info(f"Using OpenRouter provider with model {self.model}")
            elif self.provider_name == "groq":
                self.groq_client = Groq(api_key=settings["bot"]["tokens"]["ai"]["groq"])
                self.model = active_models["groq"]
                Logger().info(f"Using Groq provider with model {self.model}")
            elif self.provider_name == "anthropic":
                self.anthropic_client = Anthropic(api_key=settings["bot"]["tokens"]["ai"]["anthropic"])
                self.model = active_models["anthropic"]
                self.is_claude = True
                Logger().info(f"Using Anthropic provider with model {self.model}")
            else:
                # Default to Groq if the provider is not recognized
                Logger().warning(f"Unrecognized provider: {self.provider_name}. Defaulting to Groq.")
                self.provider_name = "groq"
                self.groq_client = Groq(api_key=settings["bot"]["tokens"]["ai"]["groq"])
                self.model = active_models["groq"]
                Logger().info(f"Using Groq provider with model {self.model}")
        except Exception as e:
            Logger().error(f"Failed to initialize {self.provider_name} provider: {str(e)}")
            # Fallback to Groq
            self.provider_name = "groq"
            self.groq_client = Groq(api_key=settings["bot"]["tokens"]["ai"]["groq"])
            self.model = active_models["groq"]
            Logger().info(f"Fallback to Groq provider with model {self.model}")

    async def get_completion(self, messages, stream=True, max_tokens=1024, system_message=None):
        """Get a completion from the configured AI provider.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            stream: Whether to stream the response
            max_tokens: Maximum tokens to generate
            system_message: Optional system message to use if not provided in messages
            
        Returns:
            A streaming or non-streaming completion object from the provider
        """
        try:
            if self.is_claude:
                # Handle Claude differently because it has a different API
                from anthropic import AsyncAnthropic
                anthropic_async = AsyncAnthropic(api_key=settings["bot"]["tokens"]["ai"]["anthropic"])
                
                # Convert messages to Anthropic format
                anthropic_messages = []
                sys_msg = ""
                
                # First extract system message if it exists
                for msg in messages:
                    if msg["role"] == "system":
                        sys_msg = msg["content"]
                    else:
                        # Convert to Anthropic format
                        anthropic_messages.append({
                            "role": "user" if msg["role"] == "user" else "assistant", 
                            "content": msg["content"]
                        })
                
                # Use provided system message if none found in messages
                if not sys_msg and system_message:
                    sys_msg = system_message
                
                # Call Anthropic API
                return await anthropic_async.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=sys_msg,
                    messages=anthropic_messages,
                    stream=stream
                )
            elif self.provider_name == "groq" and self.groq_client is not None:
                # Groq client
                return self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=stream,
                    max_tokens=max_tokens
                )
            elif self.openai_client is not None:
                # OpenAI and OpenRouter use the same client structure
                return self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=stream,
                    max_tokens=max_tokens
                )
            else:
                # Fallback to Groq if all else fails
                Logger().error("No valid AI provider available. Falling back to Groq.")
                self.groq_client = Groq(api_key=settings["bot"]["tokens"]["ai"]["groq"])
                self.model = active_models["groq"]
                
                return self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=stream,
                    max_tokens=max_tokens
                )
        except Exception as e:
            Logger().error(f"Error during completion with {self.provider_name}: {str(e)}")
            raise

# Create a singleton instance
ai_provider = AIProvider()