from __future__ import annotations

import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class ClosePositionAccounts(typing.TypedDict):
    position: Pubkey
    lb_pair: Pubkey
    bin_array_lower: Pubkey
    bin_array_upper: Pubkey
    sender: Pubkey
    rent_receiver: Pubkey
    event_authority: Pubkey
    program: Pubkey


def close_position(
        accounts: ClosePositionAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["position"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["bin_array_lower"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["bin_array_upper"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["sender"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["rent_receiver"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"{\x86Q\x001Dbb"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
