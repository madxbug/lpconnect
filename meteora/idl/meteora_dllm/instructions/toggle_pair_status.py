from __future__ import annotations

import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class TogglePairStatusAccounts(typing.TypedDict):
    lb_pair: Pubkey
    admin: Pubkey


def toggle_pair_status(
        accounts: TogglePairStatusAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"=s4\x17.\r\x1f\x90"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
