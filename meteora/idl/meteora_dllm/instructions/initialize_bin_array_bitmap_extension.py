from __future__ import annotations

import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

from ..program_id import PROGRAM_ID


class InitializeBinArrayBitmapExtensionAccounts(typing.TypedDict):
    lb_pair: Pubkey
    bin_array_bitmap_extension: Pubkey
    funder: Pubkey


def initialize_bin_array_bitmap_extension(
        accounts: InitializeBinArrayBitmapExtensionAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["bin_array_bitmap_extension"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(pubkey=accounts["funder"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"/\x9d\xe2\xb4\x0c\xf0!G"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
