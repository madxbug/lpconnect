import asyncio
import logging
import traceback
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

import discord
from solana.rpc.async_api import AsyncClient

from bots.base.database.lbpair_token_manager import LBPairTokenStorage
from bots.base.database.position_index_manager import PositionIndexStorage
from bots.base.database.position_performance_manager import PositionPerformanceStorage
from bots.base.database.session_manager import SessionStorage
from bots.base.database.vote_manager import VoteStorage
from bots.base.database.wallet_manager import WalletStorage
from bots.base.token_thread_manager import TokenThreadManager
from bots.base.webhook_manager import TransactionProcessor
from bots.lparena.close_event_queue import CloseEventQueue
from bots.lparena.common import create_position_close_embed
from bots.lparena.pnl_calculator import fetch_dlmm_events, calculate_closed_position_performance
from bots.lparena.position_embed_utils import create_position_update_embed, create_chart, create_fee_claim_embed, \
    create_secondary_position_embed, create_new_position_embed
from config.constants import LPCONNECT
from libs.helius.helius_webhook_parser import helius_webhook_parse_dlmm_events
from libs.meteora.get_user_positions_info import get_position_info, ProcessedPosition
from libs.meteora.idl.meteora_dllm.events.decoder import AddLiquidityEvent, RemoveLiquidityEvent, ClaimFeeEvent, \
    PositionCreateEvent, PositionCloseEvent
from libs.meteora.pair_data import fetch_pair_data
from libs.solana.token_metadata import get_token_metadata
from libs.utils.utils import string_to_int_id

logger = logging.getLogger(LPCONNECT)


@dataclass
class StorageProviders:
    """Container for all service dependencies"""
    session_storage: SessionStorage
    position_index_storage: PositionIndexStorage
    position_performance_storage: PositionPerformanceStorage
    vote_storage: VoteStorage
    lbpair_token_storage: LBPairTokenStorage
    wallet_storage: WalletStorage


class PositionService(TransactionProcessor):
    """Service for handling position-related operations"""

    def __init__(self, solana_rpc: str, discord_channel: discord.TextChannel,
                 discord_client: discord.Client,
                 token_thread_manager: TokenThreadManager,
                 storage_providers: StorageProviders):
        self.token_thread_manager = token_thread_manager
        self.discord_channel = discord_channel
        self.discord_client = discord_client
        self.solana_client = AsyncClient(solana_rpc)
        self.message_lock = asyncio.Lock()
        self.transaction_semaphore = asyncio.Semaphore(10)
        self.storage = storage_providers
        self.close_event_queue = CloseEventQueue(self.handle_close_position)

    async def process_transaction(self, transaction: Dict[str, Any]) -> None:
        """Process a single transaction and handle relevant events."""
        try:
            async with self.transaction_semaphore:
                events = helius_webhook_parse_dlmm_events(transaction)

                if not events:
                    return
                known_events = [event for event in events if isinstance(event, (
                    AddLiquidityEvent, RemoveLiquidityEvent, ClaimFeeEvent, PositionCreateEvent, PositionCloseEvent))]
                if not known_events or not await self.storage.wallet_storage.wallet_exists(known_events[0].owner):
                    return
                is_anonymous = await self.storage.wallet_storage.is_wallet_anonymous(known_events[0].owner)
                mode_suffix = " in anonymous mode" if is_anonymous else ""
                logger.debug(f"Processing transaction {known_events[0].tx}{mode_suffix}")
                create_position_event = next((event for event in events if isinstance(event, PositionCreateEvent)),
                                             None)
                if create_position_event:
                    await self.handle_create_position(create_position_event, self.discord_channel, is_anonymous)
                    return

                close_position_event = next((event for event in events if isinstance(event, PositionCloseEvent)), None)
                if close_position_event:
                    await self.close_event_queue.add_event(close_position_event, self.discord_channel, is_anonymous)
                    return
                if is_anonymous:
                    return

                for event in events:
                    if isinstance(event, (AddLiquidityEvent, RemoveLiquidityEvent, ClaimFeeEvent)):
                        await self.handle_liquidity_event(event, self.discord_channel)
                    else:
                        logger.debug(f"Ignore {event}")

        except Exception as e:
            logger.error(f"Error processing transaction {transaction.get('transaction', {}).get('signatures')}: {e}")
            logger.error(traceback.format_exc())

    async def get_thread_and_position_index(self,
                                            event: AddLiquidityEvent | RemoveLiquidityEvent | ClaimFeeEvent | PositionCreateEvent,
                                            discord_channel: discord.TextChannel
                                            ) -> Tuple[Optional[discord.Thread], Optional[int]]:
        """Get the thread and position index for a given event."""
        thread = await self.storage.session_storage.get_thread(event.lbPair, event.owner, discord_channel)
        if not thread:
            return None, None
        position_index = await self.storage.position_index_storage.get_position_index(event.lbPair, event.owner,
                                                                                      event.position)
        if position_index is None:
            return None, None
        return thread, position_index

    async def handle_liquidity_event(self, event: AddLiquidityEvent | RemoveLiquidityEvent | ClaimFeeEvent,
                                     discord_channel: discord.TextChannel) -> None:
        """Handle liquidity-related events."""
        try:
            thread, position_index = await self.get_thread_and_position_index(event, discord_channel)
            if thread is None or position_index is None:
                return
            position = await get_position_info(self.solana_client, event.position, update_tx=event.tx)
            if position is None:
                logger.error(f"Failed to fetch position {event.position} info [tx:{event.tx}]")
                return
            token_x, token_y = await self.storage.lbpair_token_storage.get_tokens(event.lbPair)
            chart_file = None
            if isinstance(event, (AddLiquidityEvent, RemoveLiquidityEvent)):
                embed = create_position_update_embed(position, event, position_index, token_x, token_y)
                chart_file = await create_chart(position, event.position)
            elif isinstance(event, ClaimFeeEvent):
                embed = create_fee_claim_embed(position, event.feeX, event.feeY, position_index, event, token_x,
                                               token_y)
            else:
                logger.error(f"Ignore liquidity event {event}")
                return
            message = await thread.send(embed=embed, file=chart_file)
            logger.debug(f"Message: {message.id} TX:{event.tx}")
        except Exception as e:
            logger.error(f"Failed to handle liquidity event {event}: {e}")
            logger.error(traceback.format_exc())

    async def handle_create_position(self, event: PositionCreateEvent,
                                     discord_channel: discord.TextChannel, is_anonymous: bool) -> None:
        """Handle position creation events."""
        try:

            # Should be called in both cases, event if index is not used
            position_index = await self.storage.position_index_storage.create_position_index(event.lbPair, event.owner,
                                                                                             event.position)
            thread = await self.storage.session_storage.get_thread(event.lbPair, event.owner, discord_channel)
            user, user_id, user_name = await self.get_user_name_by_wallet(event.owner)
            position = await get_position_info(self.solana_client, event.position, update_tx=event.tx)

            if thread:
                chart_file = await create_chart(position, event.position)
                await self.storage.session_storage.open_position(event.lbPair, event.owner)

                token_x, token_y = await self.storage.lbpair_token_storage.get_tokens(event.lbPair)

                embed = create_secondary_position_embed(position, position_index, event, token_x, token_y)

                message = await thread.send(embed=embed, file=chart_file)
                logger.debug(f"Message: {message.id} TX:{event.tx}")
                return

            token_x, token_y = await self.get_lbpair_symbols(event, position)
            try:
                await self.token_thread_manager.handle_position_create(user_id, event.lbPair, token_x, token_y)
            except Exception as e:
                logger.error(f"Token thread manager failed: {e}")

            if is_anonymous:
                return

            chart_file = await create_chart(position, event.position)
            title = f"{token_x}-{token_y} by {user_name} "
            pair_data = await fetch_pair_data(position.info.position.lb_pair)

            async with self.message_lock:  # ensure those 2 messages are sent together
                thread = await self.storage.session_storage.create_thread(event.lbPair, event.owner,
                                                                          discord_channel, title)
                embed = create_new_position_embed(position, pair_data, token_x, token_y, thread,
                                                  user_name, event)
                message = await discord_channel.send(embed=embed, file=chart_file)
                placeholder_msg = await discord_channel.send(
                    "||🎣 Fishing for gains... The big catch will be revealed here!||")

            if user is not None:
                await thread.send(f"👀 {user.mention} no pressure! good luck ✨")

            logger.debug(f"Message: {message.id} TX:{event.tx}")
            if isinstance(user_id, str):
                user_id = string_to_int_id(user_id)
            await self.storage.vote_storage.record_votable_message(message.id, user_id)
            await message.add_reaction("🟢")
            await message.add_reaction("🔴")

            await self.storage.session_storage.set_session_message_ids(event.lbPair, event.owner,
                                                                       message.id, placeholder_msg.id)
        except Exception as e:
            logger.error(f"Failed to handle create position event {event}: {e}")
            logger.error(traceback.format_exc())

    async def get_user_name_by_wallet(self, wallet):
        user_id = await self.storage.wallet_storage.get_discord_id_by_wallet(wallet)
        if not user_id:
            user_id = 0
        user_name = user_id
        user = None
        try:
            user = await self.discord_client.fetch_user(int(user_id))
            user_name = user.display_name
        except Exception as e:
            logger.error(f"1 New fail {e}")
        return user, user_id, user_name

    async def get_lbpair_symbols(self, event: PositionCreateEvent, position: ProcessedPosition):
        """Retrieve or fetch and cache LB pair token symbols."""
        symbol_x, symbol_y = await self.storage.lbpair_token_storage.get_tokens(event.lbPair)
        if symbol_x is not None and symbol_y is not None:
            return symbol_x, symbol_y
        token_x = await get_token_metadata(self.solana_client, position.lb_pair_info.token_x_mint)
        token_y = await get_token_metadata(self.solana_client, position.lb_pair_info.token_y_mint)
        if token_x is not None and token_y is not None:
            await self.storage.lbpair_token_storage.set_tokens(event.lbPair, token_x.symbol, token_y.symbol)
            return token_x.symbol, token_y.symbol
        return 'N/A', 'N/A'

    async def handle_close_position(self, event: PositionCloseEvent,
                                    discord_channel: discord.TextChannel,
                                    is_anonymous: bool) -> None:
        """Handle position closing events."""
        try:
            events = await fetch_dlmm_events(self.solana_client, event.position)

            create_position_event = next((event for event in events if isinstance(event, PositionCreateEvent)), None)
            if not create_position_event:
                logger.error(f'No create position event found for {event}, found only {create_position_event}')
                return
            user, user_id, user_name = await self.get_user_name_by_wallet(event.owner)
            try:
                await self.token_thread_manager.handle_position_close(user_id, create_position_event.lbPair)
            except Exception as e:
                logger.error(f"Token thread manager failed: {e}")
            if is_anonymous:
                return

            thread, position_index = await self.get_thread_and_position_index(create_position_event, discord_channel)
            if thread is None or position_index is None:
                return

            performance = await calculate_closed_position_performance(self.solana_client, events)
            token_x, token_y = await self.storage.lbpair_token_storage.get_tokens(create_position_event.lbPair)
            embed, table_image = create_position_close_embed(performance,
                                                             position_index, create_position_event.block_time, event,
                                                             token_x, token_y)

            message = await thread.send(embed=embed, file=discord.File(table_image, filename="performance_table.png"))
            logger.debug(f"Message: {message.id} TX:{event.tx}")
            await self.storage.position_performance_storage.update_position_performance(
                create_position_event.owner, thread.id, create_position_event.lbPair,
                event.position, performance)
            await self.storage.session_storage.close_position(create_position_event.lbPair,
                                                              create_position_event.owner)

        except Exception as e:
            logger.error(f"Failed to handle close position event {event}: {e}")
            logger.error(traceback.format_exc())
