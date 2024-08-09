from decimal import Decimal
from typing import List, Optional, Set, Dict, Tuple

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from .bin_array import PositionBinData, bin_id_to_bin_array_index, derive_bin_array, \
    get_bins_between_lower_and_upper_bound
from .get_positions import get_user_positions, PositionInfo
from meteora.idl.meteora_dllm.accounts import LbPair, BinArray
from meteora.idl.meteora_dllm.program_id import PROGRAM_ID
from utils.datatypes import ProcessedPosition, CachedPositionInfo
from utils.utils import get_token_decimals


def process_position(
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
    )


async def get_user_positions_info(
        client: AsyncClient,
        user_pubkey: Pubkey,
        positions_cache: Dict[Pubkey, CachedPositionInfo] = None
) -> Tuple[List[ProcessedPosition], List[ProcessedPosition], List[Pubkey]]:
    if positions_cache is None:
        positions_cache = {}

    positions = await get_user_positions(client, user_pubkey)
    all_positions: Set[Pubkey] = {position.public_key for position in positions}
    closed_positions = [pk for pk in positions_cache if pk not in all_positions]

    new_positions, updated_positions = [], []
    for position in positions:
        pk = position.public_key
        if pk in positions_cache:
            if position.position.last_updated_at != positions_cache[pk].last_updated_at:
                updated_positions.append(position)
        else:
            new_positions.append(position)

    processed_new_positions = await process_positions(client, new_positions)
    processed_updated_positions = await process_positions(client, updated_positions)

    return processed_new_positions, processed_updated_positions, closed_positions


async def process_positions(client: AsyncClient, positions: List[PositionInfo]) -> List[ProcessedPosition]:
    processed_positions = []
    for position_info in positions:
        bin_arrays = {}
        lower_bin_array_index = bin_id_to_bin_array_index(position_info.position.lower_bin_id)
        upper_bin_array_index = bin_id_to_bin_array_index(position_info.position.upper_bin_id)

        for index in {lower_bin_array_index, upper_bin_array_index}:
            bin_array_pubkey = derive_bin_array(position_info.position.lb_pair, index, PROGRAM_ID)
            bin_array_info = await client.get_account_info(bin_array_pubkey)
            bin_arrays[index] = BinArray.decode(bin_array_info.value.data)

        lb_pair_info = await client.get_account_info(position_info.position.lb_pair)
        lb_pair_state = LbPair.decode(lb_pair_info.value.data)

        processed_position = process_position(
            2,  # FIXME hardcode v2 only support
            lb_pair_state,
            position_info,
            await get_token_decimals(client, lb_pair_state.token_x_mint),
            await get_token_decimals(client, lb_pair_state.token_y_mint),
            bin_arrays[lower_bin_array_index],
            bin_arrays[upper_bin_array_index]
        )

        if processed_position:
            processed_positions.append(processed_position)
    return processed_positions
