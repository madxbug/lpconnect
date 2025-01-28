import hashlib
import logging
import os
import time

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.token.state import Mint

from config.constants import LPCONNECT


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


def convert_value(value, token_decimal):
    return value / (10 ** token_decimal)


def string_to_int_id(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def setup_logger(log_dir: str, bot_type: str) -> logging.Logger:
    """Set up and configure the logger with both console and file output."""
    logger = logging.getLogger(LPCONNECT)

    logger.setLevel(logging.DEBUG)

    # Create formatters
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(
        filename=f'{log_dir}/{bot_type}_{time.strftime("%Y%m%d_%H%M%S")}.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
