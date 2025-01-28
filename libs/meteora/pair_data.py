import asyncio
from dataclasses import dataclass
from typing import Optional

import aiohttp
from solders.pubkey import Pubkey


@dataclass
class PairData:
    address: str
    name: str
    mint_x: str
    mint_y: str
    reserve_x: str
    reserve_y: str
    reserve_x_amount: int
    reserve_y_amount: int
    bin_step: int
    base_fee_percentage: str
    max_fee_percentage: str
    protocol_fee_percentage: str
    liquidity: str
    reward_mint_x: str
    reward_mint_y: str
    fees_24h: float
    today_fees: float
    trade_volume_24h: float
    cumulative_trade_volume: str
    cumulative_fee_volume: str
    current_price: float
    apr: float
    apy: float
    farm_apr: float
    farm_apy: float
    hide: bool


async def fetch_pair_data(lp_pair_pubkey: Pubkey,
                          max_retries: int = 6,
                          initial_delay: float = 1.0) -> Optional[PairData]:
    url = f"https://dlmm-api.meteora.ag/pair/{lp_pair_pubkey}"

    async with aiohttp.ClientSession() as session:
        for retry in range(max_retries):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                return PairData(**data)

            except aiohttp.ClientError as e:
                if retry == max_retries - 1:
                    print(f"Max retries reached. Error fetching data: {e}")
                    return None
                delay = initial_delay * (2 ** retry)
                print(f"Error fetching data: {e}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

            except (KeyError, TypeError) as e:
                print(f"Error parsing data: {e}")
                return None
