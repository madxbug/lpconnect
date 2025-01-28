import asyncio
from typing import NamedTuple

import aiohttp
from solders.pubkey import Pubkey


class TokenInfo(NamedTuple):
    name_x: str
    name_y: str
    price: float


async def fetch_token_price(token_x: Pubkey, token_y: Pubkey,
                            max_retries: int = 3, initial_delay: float = 1.0) -> TokenInfo:
    url = f"https://price.jup.ag/v6/price?ids={token_x}&vsToken={token_y}"

    async with aiohttp.ClientSession() as session:
        for retry in range(max_retries):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                token_data = data['data'][str(token_x)]

                return TokenInfo(
                    name_x=token_data['mintSymbol'],
                    name_y=token_data['vsTokenSymbol'],
                    price=token_data['price']
                )
            except (aiohttp.ClientError, KeyError, ValueError) as error:
                delay_time = initial_delay * (2 ** retry)
                print(f"{url} Fetch token price failed. "
                      f"Retry attempt {retry + 1} after {delay_time}s delay. Error: {str(error)}\n{data}")
                await asyncio.sleep(delay_time)

    print(f"Max retries ({max_retries}) reached. Returning default values.")
    return TokenInfo(name_x='N/A', name_y='N/A', price=-1)
