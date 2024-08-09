import logging
from dataclasses import dataclass
from typing import List, Optional

import base58
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey

from meteora.idl.meteora_dllm.accounts.position_v2 import PositionV2
from meteora.idl.meteora_dllm.program_id import PROGRAM_ID

logger = logging.getLogger(__name__)


@dataclass
class PositionInfo:
    position: PositionV2
    public_key: Pubkey

    def to_json(self):
        return {
            'position': self.position.to_json(),
            'public_key': self.public_key.to_json()
        }


def _prepare_filters(wallet: Pubkey, pool: Optional[str] = None) -> List[MemcmpOpts]:
    try:
        discriminator_filter = MemcmpOpts(
            offset=0,
            bytes=base58.b58encode(PositionV2.discriminator).decode('ascii')
        )
        wallet_filter = MemcmpOpts(offset=40, bytes=str(wallet))

        filters = [discriminator_filter, wallet_filter]

        if pool is not None:
            pool_filter = MemcmpOpts(offset=8, bytes=pool)
            filters.append(pool_filter)

        return filters
    except Exception as e:
        logger.error(f"Error in _prepare_filters: {e}")
        raise


async def get_user_positions(client: AsyncClient, wallet: Pubkey, pool: Optional[str] = None) -> List[PositionInfo]:
    try:
        filters = _prepare_filters(wallet, pool)
        response = await client.get_program_accounts(PROGRAM_ID, encoding="base64", filters=filters)

        if isinstance(response, Exception):
            logger.error(f"RPC call failed: {response}")
            return []

        return [PositionInfo(PositionV2.decode(account.account.data), account.pubkey) for account in response.value]
    except Exception as e:
        logger.error(f"Error in get_user_positions: {e}")
        return []
