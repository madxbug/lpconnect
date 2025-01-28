import logging
from decimal import Decimal
from typing import List

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from bots.base.database.position_performance_manager import PositionPerformance, TokenBalance
from config.constants import LPCONNECT
from libs.birdeye.birdeye import determine_optimal_time_interval, get_historical_price, AddressType, \
    determine_interval_index
from libs.meteora.bin_array import get_price_of_bin_by_bin_id
from libs.meteora.idl.meteora_dllm.accounts import LbPair
from libs.meteora.idl.meteora_dllm.events.decoder import DLMMEvent, ClaimFeeEvent, AddLiquidityEvent
from libs.meteora.idl.meteora_dllm.events.decoder import RemoveLiquidityEvent, PositionCreateEvent
from libs.meteora.parse_dlmm_events import parse_dlmm_events
from libs.solana.get_transactions import get_all_transactions
from libs.utils.datatypes import PricePoint
from libs.utils.utils import get_token_decimals

logger = logging.getLogger(LPCONNECT)


async def fetch_dlmm_events(client: AsyncClient, account: str) -> List[DLMMEvent]:
    transactions = await get_all_transactions(client, account)
    logging.debug(f"Fetched {len(transactions)} DLMM events transactions: {transactions}")
    events = []
    for transaction in reversed(transactions):
        events.extend(parse_dlmm_events(transaction))
    return events


async def calculate_closed_position_performance(client: AsyncClient, events: List[DLMMEvent]) -> PositionPerformance:
    create_position_event = next(event for event in events if isinstance(event, PositionCreateEvent))
    lb_pair = await LbPair.fetch(client, Pubkey.from_string(create_position_event.lbPair))

    base_token_decimal = await get_token_decimals(client, lb_pair.token_x_mint)
    quote_token_decimal = await get_token_decimals(client, lb_pair.token_y_mint)

    performance = PositionPerformance()
    fee_claim_events: List[ClaimFeeEvent] = []
    price_points: List[PricePoint] = []
    for event in events:
        if isinstance(event, AddLiquidityEvent):
            price = update_balance_on_liquidity_change(performance.deposits, event, lb_pair, base_token_decimal,
                                                       quote_token_decimal)
            price_points.append(PricePoint(price, event.block_time))
        elif isinstance(event, RemoveLiquidityEvent):
            price = update_balance_on_liquidity_change(performance.withdrawals, event, lb_pair, base_token_decimal,
                                                       quote_token_decimal)
            price_points.append(PricePoint(price, event.block_time))
        elif isinstance(event, ClaimFeeEvent):
            fee_claim_events.append(event)
    if fee_claim_events:
        birdeye_interval = determine_optimal_time_interval(fee_claim_events[0].block_time,
                                                           fee_claim_events[-1].block_time)
        price_data = await get_historical_price(fee_claim_events[0].lbPair, AddressType.PAIR, birdeye_interval,
                                                fee_claim_events[0].block_time, fee_claim_events[-1].block_time)
        for event in fee_claim_events:
            index = determine_interval_index(fee_claim_events[0].block_time, birdeye_interval, event.block_time)
            try:
                price = price_data[index].price
                update_fee_balance_on_liquidity_change(performance.fees_earned, event, base_token_decimal,
                                                       quote_token_decimal, price)
            except:
                # First sort price points by block time to ensure correct chronological ordering
                sorted_price_points = sorted(price_points, key=lambda x: x.block_time)

                # Split price points into two groups: before/at and after the event's block time
                prices_before = [point.price for point in sorted_price_points if point.block_time <= event.block_time]
                prices_after = [point.price for point in sorted_price_points if point.block_time > event.block_time]

                # Calculate interpolated price if we have points on both sides of the event
                # Otherwise fallback to the last known price before the event
                if prices_before and prices_after:
                    # Interpolate price as average between the closest points before and after
                    price = (prices_before[-1] + prices_after[0]) / 2
                else:
                    # Use last price before event (guaranteed to exist per business logic)
                    price = prices_before[-1]
                update_fee_balance_on_liquidity_change(performance.fees_earned, event, base_token_decimal,
                                                       quote_token_decimal, price)
    return performance


def update_fee_balance_on_liquidity_change(balance: TokenBalance, event: ClaimFeeEvent,
                                           x_decimals: int, y_decimals: int, price_per_token: Decimal):
    token_x_change = convert_to_decimal(event.feeX, x_decimals)
    token_y_change = convert_to_decimal(event.feeY, y_decimals)

    value_change = price_per_token * token_x_change + token_y_change

    balance.amount_x += token_x_change
    balance.amount_y += token_y_change
    balance.value_in_y += value_change


def update_balance_on_liquidity_change(balance: TokenBalance, event: AddLiquidityEvent | RemoveLiquidityEvent,
                                       pair: LbPair, x_decimals: int, y_decimals: int) -> Decimal:
    token_x_change = convert_to_decimal(event.amounts[0], x_decimals)
    token_y_change = convert_to_decimal(event.amounts[1], y_decimals)

    price_per_unit = get_price_of_bin_by_bin_id(pair.bin_step, event.activeBinId)
    price = price_per_unit * Decimal(10 ** (x_decimals - y_decimals))
    value_change = price * token_x_change + token_y_change

    balance.amount_x += token_x_change
    balance.amount_y += token_y_change
    balance.value_in_y += value_change
    return price


def convert_to_decimal(value: int, decimals: int) -> Decimal:
    return Decimal(value) / Decimal(10 ** decimals)
