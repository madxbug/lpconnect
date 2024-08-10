import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import aiosqlite
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(FILE_DIR))

from position_embed_utils import POSITION_CREATE, POSITION_UPDATE, send_position_embed, send_position_close_embed
from meteora.get_user_positions_info import get_user_positions_info
from meteora.jup import fetch_token_price
from meteora.pair_data import fetch_pair_data
from utils.storage import PositionStorage

load_dotenv()

solana_client = AsyncClient(os.getenv('SOLANA_RPC'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))  # Change this to channel ID
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
POSITIONS_CACHE_JSON = f'{FILE_DIR}/storage/positions.json'
DB_PATH = f'{FILE_DIR}/storage/wallets.db'
LOG_PATH = f'{FILE_DIR}/logs/goose_bot.log'

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

os.makedirs(os.path.dirname(POSITIONS_CACHE_JSON), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def setup_logger():
    logger = logging.getLogger('goose_bot')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()


async def create_wallet_thread(channel, wallet_address, alias):
    thread_name = f"{wallet_address[:4]}_{wallet_address[-4:]}"
    if alias:
        thread_name = f"{alias}-{thread_name}"
    thread = await channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.public_thread,
        auto_archive_duration=10080,  # 7 days
        reason="Wallet monitoring thread"
    )
    await thread.send(f"Monitoring started for wallet {wallet_address}")
    return thread


class GooseBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)
        self.wallets = {}  # Store wallet: (thread, alias) pairs
        self.position_storage = PositionStorage(POSITIONS_CACHE_JSON)
        self.db_path = DB_PATH
        self.add_commands()

    def add_commands(self):
        @self.command(name='add', aliases=['a'])
        async def add_wallet(ctx, wallet: str, alias: str = None):
            """
            Add a wallet to the monitoring list and create a public thread for it.
            Usage: !add <wallet_address> [alias] or !a <wallet_address> [alias]
            """
            if wallet:
                channel = self.get_channel(NOTIFICATION_CHANNEL_ID)
                if not channel:
                    await ctx.send("Notification channel not found. Please check the bot configuration.")
                    return
                thread = await create_wallet_thread(channel, wallet, alias)
                await self.save_wallet(wallet, thread.id, alias)
                self.wallets[wallet] = (thread, alias)
                logger.info(
                    f"Wallet {wallet} added to monitoring list with public thread {thread.name} and alias {alias}.")
                await ctx.send(
                    f"Wallet {wallet} added to monitoring list with alias {alias}. Public thread created: {thread.mention}")
            else:
                await ctx.send("Please provide a valid public key to add.")

        @self.command(name='alias', aliases=['al'])
        async def set_alias(ctx, wallet: str, new_alias: str):
            """
            Set or update the alias for a wallet.
            Usage: !alias <wallet_address> <new_alias> or !al <wallet_address> <new_alias>
            """
            if wallet in self.wallets:
                thread, old_alias = self.wallets[wallet]
                await self.update_wallet_alias(wallet, new_alias)
                self.wallets[wallet] = (thread, new_alias)
                new_thread_name = f"{new_alias}-{wallet[:4]}_{wallet[-4:]}"
                await thread.edit(name=new_thread_name)
                logger.info(f"Alias updated for wallet {wallet} from {old_alias} to {new_alias}.")
                await ctx.send(f"Alias updated for wallet {wallet} from {old_alias} to {new_alias}.")
            else:
                await ctx.send("Wallet not found in the monitoring list.")

        @self.command(name='remove', aliases=['r'])
        async def remove_wallet(ctx, wallet: str):
            """
            Remove a wallet from the monitoring list and mark its thread as inactive.
            Usage: !remove <wallet_address> or !r <wallet_address>
            """
            if wallet in self.wallets:
                thread, alias = self.wallets[wallet]
                await thread.edit(archived=True, locked=True)
                await self.remove_wallet(wallet)
                del self.wallets[wallet]
                logger.info(f"Wallet {wallet} (alias: {alias}) removed from monitoring list and thread archived.")
                await ctx.send(
                    f"Wallet {wallet} (alias: {alias}) removed from monitoring list and its thread archived.")
            else:
                await ctx.send("Wallet not found in the monitoring list.")

        @self.command(name='list', aliases=['l'])
        async def list_wallets(ctx):
            """
            List all wallets currently being monitored.
            Usage: !list or !l
            """
            if self.wallets:
                wallet_list = "\n".join(
                    [f"{alias} ({wallet[:4]}...{wallet[-4:]}): {channel.mention}" for wallet, (channel, alias) in
                     self.wallets.items()])
                await ctx.send(f"Registered wallets:\n{wallet_list}")
            else:
                await ctx.send("No wallets are currently registered.")

        @self.command(name='show', aliases=['s'])
        async def query_wallet(ctx, wallet: str):
            """
            Show positions for a specific wallet.
            Usage: !show <wallet_address> or !s <wallet_address>
            """
            if wallet in self.wallets:
                channel = self.wallets[wallet]
                await self.fetch_and_send_positions(channel, wallet)
            else:
                await ctx.send("Wallet not found in the monitoring list.")

        @self.command(name='vote')
        async def vote(ctx, wallet: str):
            """
            Vote for a wallet sub-group.
            Usage: !vote <wallet_address>
            """
            if wallet in self.wallets:
                channel = self.wallets[wallet]
                await channel.send(f"{ctx.author.mention} voted for this wallet!")
                # You can implement more sophisticated voting logic here
            else:
                await ctx.send("Invalid wallet address. Please choose from the registered wallets.")

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS wallets
                                (address TEXT PRIMARY KEY, thread_id INTEGER, alias TEXT)''')
            await db.commit()
        logger.info("Database initialized.")

    async def load_wallets(self):
        channel = self.get_channel(NOTIFICATION_CHANNEL_ID)
        if not channel:
            logger.error("Notification channel not found. Please check the bot configuration.")
            return

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT address, thread_id, alias FROM wallets') as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    thread = channel.get_thread(row[1])
                    if thread:
                        self.wallets[row[0]] = (thread, row[2])
        logger.info(f"Loaded {len(self.wallets)} wallets from database.")

    async def save_wallet(self, wallet, thread_id, alias):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR REPLACE INTO wallets (address, thread_id, alias) VALUES (?, ?, ?)',
                             (wallet, thread_id, alias))
            await db.commit()
        logger.info(f"Wallet {wallet} saved to database with thread ID {thread_id} and alias {alias}.")

    async def update_wallet_alias(self, wallet, new_alias):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('UPDATE wallets SET alias = ? WHERE address = ?', (new_alias, wallet))
            await db.commit()
        logger.info(f"Alias updated for wallet {wallet} to {new_alias} in database.")

    async def remove_wallet(self, wallet):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM wallets WHERE address = ?', (wallet,))
            await db.commit()
        logger.info(f"Wallet {wallet} removed from database.")

    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Loaded commands: {[command.name for command in self.commands]}')
        await self.init_db()
        await self.load_wallets()
        await self.position_storage.load_positions()
        self.check_wallets.start()

    @tasks.loop(minutes=1)
    async def check_wallets(self):
        for wallet, (thread, alias) in self.wallets.items():
            try:
                await self.fetch_and_send_positions(thread, wallet)
            except Exception as e:
                logger.error(f"Failed to check wallet {wallet} (alias: {alias}): {str(e)}", exc_info=True)

    async def fetch_and_send_positions(self, channel, wallet_address):
        try:
            wallet_pub = Pubkey.from_string(wallet_address)
            cache_info = await self.position_storage.get(wallet_pub)
            (new_positions,
             updated_positions,
             closed_positions) = await get_user_positions_info(solana_client,
                                                               wallet_pub,
                                                               cache_info)
            if new_positions:
                await self.position_storage.update(wallet_pub, new_positions)
                logger.info(f"New positions found for wallet {wallet_address}: {len(new_positions)}")

            for position in new_positions:
                pair_data = await fetch_pair_data(position.info.position.lb_pair)
                token_info = await fetch_token_price(position.lb_pair_info.token_x_mint,
                                                     position.lb_pair_info.token_y_mint)
                message = await send_position_embed(channel, position, pair_data, token_info, POSITION_CREATE)
                await message.add_reaction("🟢")
                await message.add_reaction("🔴")

            if updated_positions:
                await self.position_storage.update(wallet_pub, updated_positions)
                logger.info(f"Updated positions for wallet {wallet_address}: {len(updated_positions)}")

            for position in updated_positions:
                pair_data = await fetch_pair_data(position.info.position.lb_pair)
                token_info = await fetch_token_price(position.lb_pair_info.token_x_mint,
                                                     position.lb_pair_info.token_y_mint)
                await send_position_embed(channel, position, pair_data, token_info, POSITION_UPDATE)

            for position in closed_positions:
                position_info = cache_info[position]
                pair_data = await fetch_pair_data(position_info.lb_pair)
                await send_position_close_embed(channel, wallet_pub, position, pair_data)

            if closed_positions:
                await self.position_storage.delete(wallet_pub, closed_positions)
                logger.info(f"Closed positions for wallet {wallet_address}: {len(closed_positions)}")

        except ValueError:
            logger.error(f"Invalid wallet address: {wallet_address}")
            await channel.send(f"Invalid wallet address: {wallet_address}")
        except Exception as e:
            logger.error(f"Error fetching positions for {wallet_address}: {str(e)}", exc_info=True)
            await channel.send(f"Error fetching positions for {wallet_address}")


bot = GooseBot()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith(COMMAND_PREFIX):
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Invalid command. Use '{COMMAND_PREFIX}help' for a list of commands.")
    else:
        logger.error(f"An error occurred while processing a command", exc_info=error)
        await ctx.send("An error occurred while processing the command.")


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"An error occurred in event {event}", exc_info=True)


async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
