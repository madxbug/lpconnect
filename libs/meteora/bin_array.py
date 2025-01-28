import logging
from dataclasses import asdict, dataclass
from decimal import Decimal
from functools import lru_cache
from typing import Tuple, List

from solders.pubkey import Pubkey

from config.constants import LPCONNECT
from libs.meteora.idl.meteora_dllm.accounts import LbPair
from libs.meteora.idl.meteora_dllm.accounts.bin_array import BinArray
from libs.meteora.idl.meteora_dllm.constants import MAX_BIN_ARRAY_SIZE, BASIS_POINT_MAX
from libs.meteora.idl.meteora_dllm.types import Bin

logger = logging.getLogger(LPCONNECT)


@dataclass
class BinLiquidity:
    bin_id: int
    x_amount: int
    y_amount: int
    supply: int
    price: Decimal
    version: int
    price_per_token: Decimal


@dataclass
class PositionBinData:
    bin_id: int
    price_per_token: Decimal
    bin_x_amount: int
    bin_y_amount: int
    bin_liquidity: int
    position_liquidity: Decimal
    position_x_amount: Decimal
    position_y_amount: Decimal

    def to_json(self):
        return asdict(self)


def js_divmod(a: int, b: int) -> Tuple[int, int]:
    q, r = divmod(a, b)
    if r != 0 and (a < 0) != (b < 0):  # Ensure the sign of the remainder matches the JavaScript BN behavior
        q += 1
        r -= b
    return q, r


@lru_cache(maxsize=None)
def bin_id_to_bin_array_index(bin_id: int) -> int:
    idx, mod = js_divmod(bin_id, MAX_BIN_ARRAY_SIZE)
    return idx - 1 if bin_id < 0 and mod != 0 else idx


@lru_cache(maxsize=None)
def get_bin_array_lower_upper_bin_id(bin_array_index: int) -> Tuple[int, int]:
    lower_bin_id = bin_array_index * MAX_BIN_ARRAY_SIZE
    upper_bin_id = lower_bin_id + MAX_BIN_ARRAY_SIZE - 1
    return lower_bin_id, upper_bin_id


def is_bin_id_within_bin_array(active_id: int, bin_array_index: int) -> bool:
    lower_bin_id, upper_bin_id = get_bin_array_lower_upper_bin_id(bin_array_index)
    return lower_bin_id <= active_id <= upper_bin_id


def get_bin_from_bin_array(bin_id: int, bin_array: BinArray) -> Bin:
    lower_bin_id, upper_bin_id = get_bin_array_lower_upper_bin_id(bin_array.index)

    if bin_id > 0:
        index = bin_id - lower_bin_id
    else:
        delta = upper_bin_id - bin_id
        index = MAX_BIN_ARRAY_SIZE - delta - 1

    return bin_array.bins[index]


def derive_bin_array_bitmap_extension(lb_pair: Pubkey, program_id: Pubkey) -> Pubkey:
    seeds = [b"bitmap", bytes(lb_pair)]
    pda, bump = Pubkey.find_program_address(seeds, program_id)
    return pda


def derive_bin_array(lb_pair: Pubkey, index: int, program_id: Pubkey) -> Pubkey:
    bin_array_bytes = index.to_bytes(8, byteorder='little', signed=True)
    seeds = [b"bin_array", bytes(lb_pair), bin_array_bytes]
    pda, bump = Pubkey.find_program_address(seeds, program_id)
    return pda


@lru_cache(maxsize=None)
def get_price_of_bin_by_bin_id(bin_step: int, bin_id: int) -> Decimal:
    bin_step_num = Decimal(bin_step) / BASIS_POINT_MAX
    return (bin_step_num + 1) ** bin_id


def get_bins_between_lower_and_upper_bound(
        lb_pair: LbPair,
        lower_bin_id: int,
        upper_bin_id: int,
        base_token_decimal: int,
        quote_token_decimal: int,
        lower_bin_arrays: BinArray,
        upper_bin_arrays: BinArray
) -> List[BinLiquidity]:
    logger.debug(f"lower_bin_id: {lower_bin_id}, upper_bin_id: {upper_bin_id}")
    lower_bin_array_index = bin_id_to_bin_array_index(lower_bin_id)
    upper_bin_array_index = bin_id_to_bin_array_index(upper_bin_id)
    logger.debug(f"lower_bin_array_index: {lower_bin_array_index}, upper_bin_array_index: {upper_bin_array_index}")

    bin_array_indexes = [lower_bin_arrays,
                         upper_bin_arrays] if lower_bin_array_index != upper_bin_array_index else [lower_bin_arrays]
    logger.debug(f"Number of bin arrays to process: {len(bin_array_indexes)}")

    bins = []
    for bin_array in bin_array_indexes:
        lower_bin_id_for_bin_array, _ = get_bin_array_lower_upper_bin_id(bin_array.index)

        logger.debug(f"Lower bin array: {lower_bin_id_for_bin_array}")

        for idx, _bin in enumerate(bin_array.bins):
            bin_id = lower_bin_id_for_bin_array + idx
            if lower_bin_id <= bin_id <= upper_bin_id:
                price_per_lamport = get_price_of_bin_by_bin_id(lb_pair.bin_step, bin_id)
                bins.append(BinLiquidity(
                    bin_id=bin_id,
                    x_amount=_bin.amount_x // (10 ** base_token_decimal),
                    y_amount=_bin.amount_y // (10 ** quote_token_decimal),
                    supply=_bin.liquidity_supply,
                    price=price_per_lamport,
                    version=bin_array.version,
                    price_per_token=price_per_lamport * Decimal(10 ** (base_token_decimal - quote_token_decimal))
                ))
    logger.debug(f"Total bins: {len(bins)}")
    return bins
