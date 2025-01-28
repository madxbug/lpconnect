import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import discord
from aiohttp import web
from discord import app_commands

from bots.base.bot_config import BotConfig
from bots.base.database.wallet_manager import WalletManager
from bots.base.database.wallet_manager import WalletStorage
from bots.base.webhook_manager import WebhookManager, TransactionProcessor
from config.constants import LPCONNECT
from libs.helius.helius_webhook_api import HeliusWebhookAPI

logger = logging.getLogger(LPCONNECT)


async def _webhook_shutdown(app):
    """Shutdown handler for the web application"""
    await app['webhook_manager'].stop()


async def _webhook_startup(app):
    """Startup handler for the web application"""
    await app['webhook_manager'].start()


async def _health_check(request: web.Request) -> web.Response:
    """Health check endpoint"""
    status = request.app['webhook_manager'].get_status()
    return web.json_response(status)


async def _webhook_handler(request: web.Request) -> web.Response:
    """Handle incoming webhook requests"""
    try:
        content = await request.json()
        asyncio.create_task(request.app['webhook_manager'].add_webhook(content))
        return web.Response(status=202)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return web.Response(status=500)


def _setup_discord_client() -> discord.Client:
    """Initialize the Discord client"""
    intents = discord.Intents.default()
    intents.messages = True
    return discord.Client(intents=intents)


class BaseLPBot(ABC):
    def __init__(self, config: BotConfig):
        self.config = config
        self.discord_client = _setup_discord_client()
        self.discord_ready = asyncio.Event()

        storage_dir = Path(config.storage_dir)
        storage_dir.mkdir(exist_ok=True, parents=True)
        self.wallet_storage = WalletStorage(storage_dir / "wallets.msgpack")
        self.webhook_api = HeliusWebhookAPI(config.helius_api_key)
        self.wallet_manager = WalletManager(
            self.webhook_api,
            self.wallet_storage,
            config.helius_webhook_id
        )

        self.tree = app_commands.CommandTree(self.discord_client)
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        @self.discord_client.event
        async def on_ready():
            await self._handle_ready()

    async def _handle_ready(self):
        """Handle the Discord client ready event"""
        logger.info(f'Logged in as {self.discord_client.user} (ID: {self.discord_client.user.id})')

        discord_channel = self.discord_client.get_channel(self.config.channel_id)
        if discord_channel:
            logger.info(f'Connected to Discord channel: {discord_channel.name}')
        else:
            logger.error(f'Could not find a channel with ID {self.config.channel_id}')

        self.discord_ready.set()

        await self.tree.sync()

    async def start(self):
        """Start the bot and all its components"""
        # Initialize storages
        discord_task = asyncio.create_task(self._start_discord_bot())

        # Wait for Discord to be ready before setting up services
        await self.discord_ready.wait()
        transaction_processor = await self.setup_services()

        tasks = [
            discord_task,
            asyncio.create_task(self.periodic_update()),
            asyncio.create_task(self._run_webhook_server(transaction_processor))
        ]

        await asyncio.gather(*tasks)

    async def _start_discord_bot(self):
        """Start the Discord bot"""
        async with self.discord_client:
            await self.discord_client.start(self.config.discord_token)

    async def periodic_update(self):
        """Run periodic update tasks"""
        pass

    @abstractmethod
    async def setup_services(self) -> TransactionProcessor:  # FIXME find better name
        """Setup bot-specific services"""
        pass

    async def _run_webhook_server(self, transaction_processor: TransactionProcessor):
        """Run the webhook server"""
        app = web.Application()
        app['webhook_manager'] = WebhookManager(transaction_processor)

        app.router.add_post('/', _webhook_handler)
        app.router.add_get('/health', _health_check)
        app.on_startup.append(_webhook_startup)
        app.on_shutdown.append(_webhook_shutdown)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.webhook_host, self.config.webhook_port)
        await site.start()

        logger.info(f"Webhook server started on https://{self.config.webhook_host}:{self.config.webhook_port}")
