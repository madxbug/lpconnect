import asyncio
import traceback
from dataclasses import dataclass
from typing import Optional

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey

METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")


@dataclass
class TokenMetadata:
    update_authority: str
    mint: str
    name: str
    symbol: str
    uri: str


class MetadataDecodeError(Exception):
    pass


async def get_token_metadata(
        client: AsyncClient,
        token_address: Pubkey,
        max_retries: int = 5,
        initial_delay: float = 1.0
) -> Optional[TokenMetadata]:
    for retry in range(max_retries):
        try:
            metadata_account = Pubkey.find_program_address(
                [b"metadata", bytes(METADATA_PROGRAM_ID), token_address.__bytes__()],
                METADATA_PROGRAM_ID
            )[0]

            account_info = await client.get_account_info(metadata_account, commitment=Confirmed)

            if account_info.value is not None:
                return decode_custom_metadata(account_info.value.data)
            else:
                print(f"No metadata found for token: {token_address}")
                return None

        except Exception as e:
            print(f"Error fetching token metadata: {str(e)}")
            traceback.print_exc()

        delay_time = initial_delay * (2 ** retry)
        print(f"Get token metadata failed. "
              f"Retry attempt {retry + 1} after {delay_time}s delay.")
        await asyncio.sleep(delay_time)

    print(f"Failed to get token metadata after {max_retries} attempts.")
    return None


def decode_custom_metadata(data: bytes) -> TokenMetadata:
    try:
        if data[0] != 4:  # Version check
            raise MetadataDecodeError("Invalid metadata version")

        update_authority = str(Pubkey(data[1:33]))
        mint = str(Pubkey(data[33:65]))
        name_length = int.from_bytes(data[65:69], 'little')
        name = data[69:69 + name_length].decode('utf-8').strip('\x00')

        symbol_start = 69 + name_length
        symbol_length = int.from_bytes(data[symbol_start:symbol_start + 4], 'little')
        symbol = data[symbol_start + 4:symbol_start + 4 + symbol_length].decode('utf-8').strip('\x00')

        uri_start = symbol_start + 4 + symbol_length
        uri_length = int.from_bytes(data[uri_start:uri_start + 4], 'little')
        uri = data[uri_start + 4:uri_start + 4 + uri_length].decode('utf-8').strip('\x00')

        return TokenMetadata(update_authority, mint, name, symbol, uri)

    except Exception as e:
        raise MetadataDecodeError(f"Error decoding metadata: {str(e)}")


async def main():
    client = AsyncClient('https://api.mainnet-beta.solana.com')
    token_address = "So11111111111111111111111111111111111111112"
    token_metadata = await get_token_metadata(client, Pubkey.from_string(token_address))

    if token_metadata:
        print(f"Token Address: {token_address}")
        print(f"Name: {token_metadata.name}")
        print(f"Symbol: {token_metadata.symbol}")
        print(f"URI: {token_metadata.uri}")
        print(f"Update Authority: {token_metadata.update_authority}")
        print(f"Mint: {token_metadata.mint}")


if __name__ == "__main__":
    asyncio.run(main())
