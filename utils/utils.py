from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.token.state import Mint


async def get_mint_info(client: AsyncClient, mint_pubkey: Pubkey) -> Mint:
    mint_account = await client.get_account_info(mint_pubkey)

    if mint_account is None:
        raise ValueError(f"Mint account {mint_pubkey} not found")

    mint_data = mint_account.value.data
    mint_info = Mint.from_bytes(mint_data)

    return mint_info


async def get_token_decimals(client: AsyncClient, mint_pubkey: Pubkey) -> int:
    mint_info = await get_mint_info(client, mint_pubkey)
    return mint_info.decimals
