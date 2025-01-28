import asyncio
import logging
from pathlib import Path

from bots.base.base_lp_bot import BaseLPBot
from bots.base.bot_config import BotConfig
from bots.base.database.lbpair_token_manager import LBPairTokenStorage
from bots.base.token_thread_manager import TokenThreadManager
from bots.base.webhook_manager import TransactionProcessor
from bots.lpfeed.commands import setup_commands
from bots.lpfeed.transaction_processor import PositionService
from config.constants import LPCONNECT

logger = logging.getLogger(LPCONNECT)

PERIODIC_UPDATE_INTERVAL_SECONDS = 60


class LPFeedBot(BaseLPBot):
    """Main bot class that orchestrates all components"""

    def __init__(self, config: BotConfig):
        self.lbpair_token_storage = LBPairTokenStorage(Path(config.storage_dir) / "lbpair_tokens.msgpack")
        self.token_thread_manager = TokenThreadManager(Path(config.storage_dir) / "lp_sessions.msgpack")
        super().__init__(config)
        setup_commands(
            self.tree,
            self.wallet_manager,
            self.wallet_storage
        )

    async def setup_services(self) -> TransactionProcessor:
        """Setup bot-specific services"""

        discord_channel = self.discord_client.get_channel(self.config.channel_id)
        if not discord_channel:
            raise ValueError("Discord channel not found")

        await self.token_thread_manager.initialize(discord_channel)

        return PositionService(
            self.config.solana_rpc,
            self.discord_client,
            self.token_thread_manager,
            self.lbpair_token_storage,
            self.wallet_storage
        )

    async def start(self):
        """Start the bot and all its components"""
        # Initialize storages
        await self.lbpair_token_storage.initialize()
        await self.wallet_storage.initialize()
        await self.wallet_manager.sync_webhook_with_db()
        await super().start()

    async def periodic_update(self):
        """Run periodic update tasks"""
        while True:
            await asyncio.sleep(PERIODIC_UPDATE_INTERVAL_SECONDS)
            try:
                await self.token_thread_manager.update_threads()
            except Exception as e:
                logger.error(f"Token thread manager failed: {e}")
