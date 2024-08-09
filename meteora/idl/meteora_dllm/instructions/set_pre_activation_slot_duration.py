from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class SetPreActivationSlotDurationArgs(typing.TypedDict):
    pre_activation_slot_duration: int


layout = borsh.CStruct("pre_activation_slot_duration" / borsh.U16)


class SetPreActivationSlotDurationAccounts(typing.TypedDict):
    lb_pair: Pubkey
    creator: Pubkey


def set_pre_activation_slot_duration(
        args: SetPreActivationSlotDurationArgs,
        accounts: SetPreActivationSlotDurationAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["creator"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x18\xd5I\x91\x01\x95\x7f%"
    encoded_args = layout.build(
        {
            "pre_activation_slot_duration": args["pre_activation_slot_duration"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
