import asyncio
import logging
from pathlib import Path

from bots.base.base_lp_bot import BaseLPBot
from bots.base.database.cleanup_manager import CleanupManager
from bots.base.database.lbpair_token_manager import LBPairTokenStorage
from bots.base.database.position_index_manager import PositionIndexStorage
from bots.base.database.position_performance_manager import PositionPerformanceStorage
from bots.base.database.session_manager import SessionStorage
from bots.base.database.vote_manager import VoteStorage
from bots.base.token_thread_manager import TokenThreadManager
from bots.base.webhook_manager import TransactionProcessor
from bots.lparena.commands import setup_commands
from bots.lparena.lparena_config import LPArenaConfig
from bots.lparena.transaction_processor import PositionService, StorageProviders
from config.constants import LPCONNECT

logger = logging.getLogger(LPCONNECT)

PERIODIC_UPDATE_INTERVAL_SECONDS = 60


class LPArenaBot(BaseLPBot):
    """Main bot class that orchestrates all components"""

    def __init__(self, config: LPArenaConfig):
        super().__init__(config)
        self.config: LPArenaConfig = config
        self.vote_storage = VoteStorage(Path(config.storage_dir) / "votes.msgpack")
        self.position_index_storage = PositionIndexStorage(Path(config.storage_dir) / "position_index.msgpack")
        self.position_performance_storage = PositionPerformanceStorage(
            Path(config.storage_dir) / "position_performance.msgpack")
        self.token_thread_manager = TokenThreadManager(Path(config.storage_dir) / "lp_sessions.msgpack")

        self.session_storage = SessionStorage(Path(config.storage_dir) / "sessions.msgpack",
                                              self.config.cleanup_timeout)
        self.lbpair_token_storage = LBPairTokenStorage(Path(config.storage_dir) / "lbpair_tokens.msgpack")

        setup_commands(
            self.tree,
            self.wallet_manager,
            self.wallet_storage,
            self.vote_storage,
            self.discord_client
        )

    async def setup_services(self) -> TransactionProcessor:
        """Setup bot-specific services"""
        await self.vote_storage.initialize()

        discord_channel = self.discord_client.get_channel(self.config.channel_id)
        if not discord_channel:
            raise ValueError("Discord channel not found")

        try:
            anonymous_channel = self.discord_client.get_channel(self.config.anonymous_channel_id)
            if anonymous_channel:
                await self.token_thread_manager.initialize(anonymous_channel)
            else:
                logger.error("No channel found to initialize token thread manager")
        except Exception as e:
            logger.error(f"Token thread manager failed: {e}")

        storage_provider = StorageProviders(
            self.session_storage,
            self.position_index_storage,
            self.position_performance_storage,
            self.vote_storage,
            self.lbpair_token_storage,
            self.wallet_storage
        )

        return PositionService(
            self.config.solana_rpc,
            discord_channel,
            self.discord_client,
            self.token_thread_manager,
            storage_provider
        )

    def _setup_event_handlers(self):
        super()._setup_event_handlers()

        @self.discord_client.event
        async def on_reaction_add(reaction, user):
            if user.bot:
                return
            if reaction.emoji in ['🟢', '🔴']:
                await self.vote_storage.add_vote(reaction.message.id, user.id, reaction.emoji)

    async def start(self):
        """Start the bot and all its components"""
        await self.position_index_storage.initialize()
        await self.position_performance_storage.initialize()
        await self.lbpair_token_storage.initialize()
        await self.wallet_storage.initialize()
        await self.wallet_manager.sync_webhook_with_db()

        cleanup_manager = CleanupManager(
            self.position_index_storage,
            self.position_performance_storage,
            self.vote_storage,
            self.lbpair_token_storage,
            self.discord_client
        )

        await self.session_storage.initialize(cleanup_manager=cleanup_manager)

        await super().start()

    async def periodic_update(self):
        """Run periodic update tasks"""
        while True:
            await asyncio.sleep(PERIODIC_UPDATE_INTERVAL_SECONDS)
            try:
                await self.token_thread_manager.update_threads()
            except Exception as e:
                logger.error(f"Token thread manager failed: {e}")

            discord_channel = self.discord_client.get_channel(self.config.channel_id)
            if discord_channel:
                await self.session_storage.cleanup_old_sessions(discord_channel)
