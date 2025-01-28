import asyncio
import logging
import traceback
from typing import Dict, Any

import discord
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from bots.base.database.lbpair_token_manager import LBPairTokenStorage
from bots.base.database.wallet_manager import WalletStorage
from bots.base.token_thread_manager import TokenThreadManager
from bots.base.webhook_manager import TransactionProcessor
from config.constants import LPCONNECT
from libs.helius.helius_webhook_parser import helius_webhook_parse_dlmm_events
from libs.meteora.get_user_positions_info import get_position_info, ProcessedPosition
from libs.meteora.idl.meteora_dllm.accounts.position_v2 import PositionV2
from libs.meteora.idl.meteora_dllm.events.decoder import PositionCreateEvent, PositionCloseEvent
from libs.solana.token_metadata import get_token_metadata

logger = logging.getLogger(LPCONNECT)


class PositionService(TransactionProcessor):
    """Service for handling position-related operations"""

    def __init__(self, solana_rpc: str,
                 discord_client: discord.Client,
                 token_thread_manager: TokenThreadManager,
                 lbpair_token_storage: LBPairTokenStorage,
                 wallet_storage: WalletStorage):
        self.token_thread_manager = token_thread_manager
        self.discord_client = discord_client
        self.solana_client = AsyncClient(solana_rpc)
        self.transaction_semaphore = asyncio.Semaphore(10)
        self.lbpair_token_storage = lbpair_token_storage
        self.wallet_storage = wallet_storage

    async def process_transaction(self, transaction: Dict[str, Any]) -> None:
        """Process a single transaction and handle relevant events."""
        try:
            async with self.transaction_semaphore:
                events = helius_webhook_parse_dlmm_events(transaction)

                if not events:
                    logger.debug("No events found in transaction.")
                    return

                # Filter known events (PositionCreateEvent, PositionCloseEvent)
                known_events = [
                    event for event in events if isinstance(event, (PositionCreateEvent, PositionCloseEvent))
                ]

                if not known_events:
                    logger.debug(
                        f"Transaction has no known events: {transaction.get('transaction', {}).get('signatures')}")
                    return

                if not await self.wallet_storage.wallet_exists(known_events[0].owner):
                    logger.debug(f"Wallet does not exist for owner: {known_events[0].owner}")
                    return

                transaction_id = known_events[0].tx
                logger.debug(f"Processing transaction {transaction_id} with events: {len(known_events)}")

                create_position_event = next((event for event in events if isinstance(event, PositionCreateEvent)),
                                             None)
                if create_position_event:
                    await self.handle_create_position(create_position_event)
                    logger.info(
                        f"Processed CreatePosition event for transaction {transaction_id}, "
                        f"owner: {create_position_event.owner}"
                    )
                    return

                close_position_event = next((event for event in events if isinstance(event, PositionCloseEvent)), None)
                if close_position_event:
                    await self.handle_close_position(close_position_event)
                    logger.info(
                        f"Processed ClosePosition event for transaction {transaction_id}, "
                        f"owner: {close_position_event.owner}"
                    )
                    return

        except Exception as e:
            transaction_id = transaction.get("transaction", {}).get("signatures", "unknown")
            logger.error(
                f"Error processing transaction {transaction_id}: {e}", exc_info=True
            )

    async def handle_create_position(self, event: PositionCreateEvent) -> None:
        """Handle position creation events."""
        try:

            user, user_id, user_name = await self.get_user_name_by_wallet(event.owner)
            position = await get_position_info(self.solana_client, event.position, update_tx=event.tx)

            token_x, token_y = await self.get_lbpair_symbols(event, position)
            try:
                await self.token_thread_manager.handle_position_create(user_id, event.lbPair, token_x, token_y)
            except Exception as e:
                logger.error(f"Token thread manager failed: {e}")

        except Exception as e:
            logger.error(f"Failed to handle create position event {event}: {e}")
            logger.error(traceback.format_exc())

    async def handle_close_position(self, event: PositionCloseEvent) -> None:
        """Handle position closing events."""
        try:
            pubkey = Pubkey.from_string(event.position)
            account_info = await self.solana_client.get_account_info(pubkey)
            if account_info.value:
                position = PositionV2.decode(account_info.value.data)
                user, user_id, user_name = await self.get_user_name_by_wallet(event.owner)

                await self.token_thread_manager.handle_position_close(user_id, str(position.lb_pair))
            else:
                logger.error(f"Failed to handle position close event {event}, got empty account info: {account_info}")

        except Exception as e:
            logger.error(f"Failed to handle close position event {event}: {e}")
            logger.error(traceback.format_exc())

    async def get_user_name_by_wallet(self, wallet):
        user_id = await self.wallet_storage.get_discord_id_by_wallet(wallet)
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
        symbol_x, symbol_y = await self.lbpair_token_storage.get_tokens(event.lbPair)
        if symbol_x is not None and symbol_y is not None:
            return symbol_x, symbol_y
        token_x = await get_token_metadata(self.solana_client, position.lb_pair_info.token_x_mint)
        token_y = await get_token_metadata(self.solana_client, position.lb_pair_info.token_y_mint)
        if token_x is not None and token_y is not None:
            await self.lbpair_token_storage.set_tokens(event.lbPair, token_x.symbol, token_y.symbol)
            return token_x.symbol, token_y.symbol
        return 'N/A', 'N/A'
