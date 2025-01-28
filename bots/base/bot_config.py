import os
from dataclasses import dataclass
from typing import Self

from dotenv import load_dotenv


@dataclass
class BotConfig:
    """Configuration container for the Discord bot"""
    discord_token: str
    channel_id: int
    solana_rpc: str
    webhook_host: str
    webhook_port: int
    helius_api_key: str
    helius_webhook_id: str
    storage_dir: str

    @classmethod
    def from_env(cls, dotenv_path: str) -> Self:
        """Create config from environment variables"""
        load_dotenv(dotenv_path)

        discord_token = os.getenv('DISCORD_TOKEN')
        channel_id = int(os.getenv('NOTIFICATION_CHANNEL_ID', '0'))
        solana_rpc = os.getenv('SOLANA_RPC')
        webhook_host = os.getenv('WEBHOOK_SERVER_HOST', '0.0.0.0')
        webhook_port = int(os.getenv('WEBHOOK_SERVER_PORT', 5000))
        helius_api_key = os.getenv('HELIUS_API_KEY')
        helius_webhook_id = os.getenv('HELIUS_WEBHOOK_ID')
        storage_dir = os.getenv('STORAGE_DIR')
        if not all([discord_token, channel_id, solana_rpc, helius_api_key, helius_webhook_id]):
            raise ValueError("Missing required environment variables")

        return cls(
            discord_token=discord_token,
            channel_id=channel_id,
            solana_rpc=solana_rpc,
            webhook_host=webhook_host,
            webhook_port=webhook_port,
            helius_api_key=helius_api_key,
            helius_webhook_id=helius_webhook_id,
            storage_dir=storage_dir,
        )
