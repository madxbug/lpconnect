import os
from dataclasses import dataclass, fields
from typing import Self

from dotenv import load_dotenv

from bots.base.bot_config import BotConfig


@dataclass
class LPArenaConfig(BotConfig):
    """Configuration container for the Discord bot"""
    anonymous_channel_id: int
    cleanup_timeout: int

    @classmethod
    def from_env(cls, dotenv_path: str) -> Self:
        """Create config from environment variables"""
        load_dotenv(dotenv_path)
        base = BotConfig.from_env(dotenv_path)

        # Get new config values
        anonymous_channel_id = int(os.getenv('ANONYMOUS_NOTIFICATIONS_CHANNEL_ID', '0'))
        cleanup_timeout = int(os.getenv('CLEANUP_TIMEOUT', '60'))

        # Get all fields from base dataclass
        base_fields = {field.name: getattr(base, field.name)
                       for field in fields(BotConfig)}

        # Combine base fields with new fields
        return cls(
            **base_fields,
            anonymous_channel_id=anonymous_channel_id,
            cleanup_timeout=cleanup_timeout
        )
