import asyncio
import json
import traceback
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey
from solders.signature import Signature

from libs.meteora.idl.meteora_dllm.accounts import LbPair
from libs.meteora.idl.meteora_dllm.program_id import PROGRAM_ID
from .bin_array import PositionBinData, bin_id_to_bin_array_index, derive_bin_array, \
    get_bins_between_lower_and_upper_bound
from .get_positions import PositionInfo
from .idl.meteora_dllm.accounts.bin_array import BinArray
from .idl.meteora_dllm.accounts.position_v2 import PositionV2
from ..utils.utils import get_token_decimals


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


@dataclass
class ProcessedPosition:
    info: PositionInfo
    lb_pair_info: LbPair
    total_x_amount: Decimal
    total_y_amount: Decimal
    position_bin_data: List[PositionBinData]
    base_token_decimal: int
    quote_token_decimal: int

    def to_json(self):
        return json.dumps({
            'info': self.info.to_json(),
            'lb_pair_info': self.lb_pair_info.to_json(),
            'total_x_amount': str(self.total_x_amount),
            'total_y_amount': str(self.total_y_amount),
            'position_bin_data': [data.to_json() for data in self.position_bin_data],
            'base_token_decimal': self.base_token_decimal,
            'quote_token_decimal': self.quote_token_decimal
        }, cls=CustomJSONEncoder, indent=4)


def _process_position(
        version: int,
        lb_pair: LbPair,
        position_info: PositionInfo,
        base_token_decimal: int,
        quote_token_decimal: int,
        lower_bin_array: BinArray,
        upper_bin_array: BinArray
) -> Optional[ProcessedPosition]:
    bins = get_bins_between_lower_and_upper_bound(
        lb_pair,
        position_info.position.lower_bin_id,
        position_info.position.upper_bin_id,
        base_token_decimal,
        quote_token_decimal,
        lower_bin_array,
        upper_bin_array
    )

    if not bins:
        return None

    if bins[0].bin_id != position_info.position.lower_bin_id or bins[-1].bin_id != position_info.position.upper_bin_id:
        raise ValueError("Bin ID mismatch")

    position_data = []
    total_x_amount = Decimal(0)
    total_y_amount = Decimal(0)

    for idx, _bin in enumerate(bins):
        bin_supply = Decimal(_bin.supply)

        if _bin.version == 1 and version == 1:
            pos_share = Decimal(position_info.position.liquidity_shares[idx] << 64)
        else:
            pos_share = Decimal(position_info.position.liquidity_shares[idx])

        position_x_amount = Decimal(0) if bin_supply == 0 else pos_share * _bin.x_amount / bin_supply
        position_y_amount = Decimal(0) if bin_supply == 0 else pos_share * _bin.y_amount / bin_supply

        total_x_amount += position_x_amount
        total_y_amount += position_y_amount

        position_data.append(PositionBinData(
            bin_id=_bin.bin_id,
            price_per_token=_bin.price_per_token,
            bin_x_amount=_bin.x_amount,
            bin_y_amount=_bin.y_amount,
            bin_liquidity=_bin.supply,
            position_liquidity=pos_share,
            position_x_amount=position_x_amount,
            position_y_amount=position_y_amount,
        ))

    return ProcessedPosition(
        info=position_info,
        lb_pair_info=lb_pair,
        total_x_amount=total_x_amount,
        total_y_amount=total_y_amount,
        position_bin_data=position_data,
        base_token_decimal=base_token_decimal,
        quote_token_decimal=quote_token_decimal
    )


async def process_position(client: AsyncClient, position_info: PositionInfo) -> ProcessedPosition:
    bin_arrays = {}
    lower_bin_array_index = bin_id_to_bin_array_index(position_info.position.lower_bin_id)
    upper_bin_array_index = bin_id_to_bin_array_index(position_info.position.upper_bin_id)

    for index in {lower_bin_array_index, upper_bin_array_index}:
        bin_array_pubkey = derive_bin_array(position_info.position.lb_pair, index, PROGRAM_ID)
        bin_array_info = await client.get_account_info(bin_array_pubkey, commitment=Confirmed)
        bin_arrays[index] = BinArray.decode(bin_array_info.value.data)

    lb_pair_info = await client.get_account_info(position_info.position.lb_pair, commitment=Confirmed)
    lb_pair_state = LbPair.decode(lb_pair_info.value.data)

    processed_position = _process_position(
        2,  # FIXME hardcode v2 only support
        lb_pair_state,
        position_info,
        await get_token_decimals(client, lb_pair_state.token_x_mint),
        await get_token_decimals(client, lb_pair_state.token_y_mint),
        bin_arrays[lower_bin_array_index],
        bin_arrays[upper_bin_array_index]
    )

    return processed_position


async def get_position_info(client: AsyncClient, account_address: str, update_tx: str,
                            max_retries: int = 8, initial_delay: float = 1.0) -> Optional[ProcessedPosition]:
    for retry in range(max_retries):
        try:
            tx_info = await client.get_transaction(Signature.from_string(update_tx), commitment=Confirmed)
            if tx_info.value:
                pubkey = Pubkey.from_string(account_address)
                account_info = await client.get_account_info(pubkey, commitment=Confirmed)
                if account_info.value:
                    if tx_info.value.slot <= account_info.context.slot:
                        return await process_position(client, PositionInfo(PositionV2.decode(account_info.value.data),
                                                                           account_info.value.owner))
        except Exception as e:
            print(e)
            traceback.print_exc()
        delay_time = initial_delay * (2 ** retry)
        print(f"Get position info failed for {account_address}. "
              f"Retry attempt {retry + 1} after {delay_time}s delay.")
        await asyncio.sleep(delay_time)
    return None
