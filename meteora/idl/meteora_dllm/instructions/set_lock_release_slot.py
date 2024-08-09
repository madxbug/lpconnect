from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class SetLockReleaseSlotArgs(typing.TypedDict):
    new_lock_release_slot: int


layout = borsh.CStruct("new_lock_release_slot" / borsh.U64)


class SetLockReleaseSlotAccounts(typing.TypedDict):
    position: Pubkey
    lb_pair: Pubkey
    sender: Pubkey
    event_authority: Pubkey
    program: Pubkey


def set_lock_release_slot(
        args: SetLockReleaseSlotArgs,
        accounts: SetLockReleaseSlotAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["position"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["sender"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xcf\xe0\xaa\x8f\xbd\x9f.\x96"
    encoded_args = layout.build(
        {
            "new_lock_release_slot": args["new_lock_release_slot"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
