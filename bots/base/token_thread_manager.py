import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Set

from discord import TextChannel, ChannelType, NotFound, Embed, Color
from solders.pubkey import Pubkey

from bots.base.database.lp_storage import LPStorage
from config.constants import LPCONNECT
from libs.meteora.pair_data import fetch_pair_data

logger = logging.getLogger(LPCONNECT)


class TokenThreadConfig:
    """Configuration class to hold constants and settings"""
    KNOWN_TOKENS: Set[str] = {'SOL', 'USDC', 'USDT'}
    GOOSE_EMOJI: str = '🪿'
    UPDATE_INTERVAL: int = 300  # 5 minutes
    THREAD_AUTO_ARCHIVE_DURATION: int = 10080
    RATE_LIMIT_DELAY: int = 5  # seconds between thread updates


@dataclass
class ThreadInfo:
    thread_id: int
    needs_update: bool = False
    last_updated: float = 0.0


def _format_thread_name(unique_owners: int, token: str) -> str:
    """Format thread name based on number of owners"""
    if unique_owners == 0:
        return f"❌ | {token}"
    return (f"({unique_owners}) {TokenThreadConfig.GOOSE_EMOJI} │ {token}"
            if unique_owners > 1
            else f"{TokenThreadConfig.GOOSE_EMOJI} │ {token}")


class TokenThreadManager:
    def __init__(self, storage_path: str | Path):
        self.channel = None
        self._storage_path = storage_path
        self.storage = None
        self._lock = asyncio.Lock()

    async def initialize(self, channel: TextChannel):
        """Initialize the position storage"""
        self.channel = channel
        self.storage = LPStorage(self._storage_path)
        await self.storage.initialize()

    async def cleanup(self):
        """Cleanup resources"""
        if self.storage:
            await self.storage.close()

    async def _create_token_thread(self, token: str, unique_owners: int) -> Optional[ThreadInfo]:
        """Create a new thread for a token"""
        try:
            thread = await self.channel.create_thread(
                name=_format_thread_name(unique_owners, token),
                type=ChannelType.public_thread,
                auto_archive_duration=TokenThreadConfig.THREAD_AUTO_ARCHIVE_DURATION
            )
            return ThreadInfo(thread_id=thread.id)
        except Exception as e:
            logger.error(f"Error creating thread for {token}: {e}")
            return None

    async def _update_token_threads(self, token_x: str, token_y: str) -> None:
        """Update thread info for a token pair"""
        async with self._lock:
            for token in (token_x, token_y):
                if token in TokenThreadConfig.KNOWN_TOKENS:
                    continue
                thread = await self.storage.get_thread(token)
                if thread:
                    await self.storage.update_thread_status(token, True)
                    continue

                unique_owners = await self.storage.get_unique_owners_count(token)
                thread_info = await self._create_token_thread(token, unique_owners)

                if thread_info:
                    await self.storage.add_thread(token, thread_info)

    async def _update_single_thread(self, token: str, thread_info: ThreadInfo) -> bool:
        """Update a single thread"""
        try:
            thread = await self.channel.guild.fetch_channel(thread_info.thread_id)
            if thread and not thread.archived:
                unique_owners = await self.storage.get_unique_owners_count(token)
                try:
                    await asyncio.wait_for(
                        thread.edit(name=_format_thread_name(unique_owners, token)),
                        timeout=5
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Timeout while editing thread {thread_info.thread_id}. Skipping operation."
                    )
                # FIXME in case of timeout failure thread will be marked as updated in upper method
                return True  # even if it fails on timeout, consider successful
            return False
        except NotFound:
            logger.info(f"Thread {thread_info.thread_id} not found, removing from tracking")
            return False
        except Exception as e:
            logger.error(f"Error updating thread {thread_info.thread_id}: {e}")
            return False

    @asynccontextmanager
    async def batch_update(self):
        """Context manager for batching multiple updates"""
        try:
            yield
            await self.update_threads()
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            raise

    async def update_threads(self) -> None:
        """Update all threads that need updating"""
        current_time = time.time()
        tokens_to_remove = set()

        async with self._lock:
            threads = await self.storage.get_all_threads()
            for token, thread_info in threads.items():
                if (not thread_info.needs_update or
                        current_time - thread_info.last_updated < TokenThreadConfig.UPDATE_INTERVAL):
                    continue

                success = await self._update_single_thread(token, thread_info)

                if success:
                    await self.storage.update_thread_status(
                        token,
                        needs_update=False,
                        last_updated=current_time
                    )
                    await asyncio.sleep(TokenThreadConfig.RATE_LIMIT_DELAY)
                else:
                    tokens_to_remove.add(token)

            # Remove deleted threads
            for token in tokens_to_remove:
                await self.storage.remove_thread(token)

    async def _get_pool_users(self, token: str, pool: str) -> str:
        """Get formatted list of users in a pool for a token"""
        try:
            users = await self.storage.get_pool_users(token, pool)
            if not users:
                return "No active positions"

            total_users = len(users)
            return f"👥 Users: `{total_users}`"
        except Exception as e:
            logger.error(f"Error getting pool users: {e}")
            return "Error retrieving positions"

    async def _send_thread_message(self, thread_id: int, token: str, pool: str, is_create: bool = True) -> None:
        """Send message in thread about position updates"""
        try:
            thread = await self.channel.guild.fetch_channel(thread_id)
            if thread and not thread.archived:
                formatted_pool = f"{pool[:4]}...{pool[-4:]}"
                action = "opened" if is_create else "closed"

                # Create embed
                embed = Embed(
                    title=f"Position {action}",
                    color=Color.green() if is_create else Color.red()
                )

                try:
                    pool_data = await fetch_pair_data(Pubkey.from_string(pool))
                    if pool_data:
                        liquidity = int(float(pool_data.liquidity))
                        fees_24h = int(float(pool_data.fees_24h))

                        embed.add_field(
                            name="",
                            value=f"📊 Step: `{pool_data.bin_step}`\u2003|\u2003💰 Fee: `{pool_data.base_fee_percentage}%`",
                            inline=False
                        )
                        embed.add_field(
                            name="",
                            value=f"💧 Liquidity: `${liquidity:,}`",
                            inline=False
                        )
                        embed.add_field(
                            name="",
                            value=f"📈 24h Fees: `${fees_24h:,}`",
                            inline=False
                        )
                except Exception as e:
                    logger.debug(f"Failed to fetch pool data: {e}")

                users_list = await self._get_pool_users(token, pool)
                embed.add_field(name="", value=users_list, inline=False)
                embed.add_field(name="", value=f"Pool: [`{formatted_pool}`](<https://edge.meteora.ag/dlmm/{pool}>)",
                                inline=False)

                await thread.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending thread message: {e}")

    async def _notify_threads(self, token_x: str, token_y: str, pool: str, is_create: bool = True) -> None:
        """Send notifications to both token threads"""
        for token in (token_x, token_y):
            thread_info = await self.storage.get_thread(token)
            if thread_info:
                await self._send_thread_message(
                    thread_info.thread_id,
                    token,
                    pool,
                    is_create
                )

    async def handle_position_create(self, owner: str, pool: str, token_x: str, token_y: str) -> bool:
        """Handle creation of a new position"""
        try:
            new_position = await self.storage.add_position(token_x, token_y, owner, pool)
            await self._update_token_threads(token_x, token_y)
            if new_position:
                await self._notify_threads(token_x, token_y, pool, True)
            return True
        except Exception as e:
            logger.error(f"Error in handle_position_create: {e}")
            return False

    async def handle_position_close(self, owner: str, pool: str) -> Optional[Tuple[str, str]]:
        """Handle closing of a position"""
        try:
            tokens_tuple, is_last_position = await self.storage.remove_position(owner, pool)
            if tokens_tuple:  # If we got tokens (not None)
                token_x, token_y = tokens_tuple
                await self._update_token_threads(token_x, token_y)
                if is_last_position:
                    await self._notify_threads(token_x, token_y, pool, False)
                return token_x, token_y
            return None
        except Exception as e:
            logger.error(f"Error in handle_position_close: {e}")
            return None
