from __future__ import annotations

import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID

from ..program_id import PROGRAM_ID


class MigratePositionAccounts(typing.TypedDict):
    position_v2: Pubkey
    position_v1: Pubkey
    lb_pair: Pubkey
    bin_array_lower: Pubkey
    bin_array_upper: Pubkey
    owner: Pubkey
    rent_receiver: Pubkey
    event_authority: Pubkey
    program: Pubkey


def migrate_position(
        accounts: MigratePositionAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["position_v2"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["position_v1"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["bin_array_lower"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["bin_array_upper"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
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
    identifier = b"\x0f\x84;2\xc7\x06\xfb."
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
