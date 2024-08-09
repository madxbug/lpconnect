from __future__ import annotations

import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class SetPreActivationSwapAddressArgs(typing.TypedDict):
    pre_activation_swap_address: Pubkey


layout = borsh.CStruct("pre_activation_swap_address" / BorshPubkey)


class SetPreActivationSwapAddressAccounts(typing.TypedDict):
    lb_pair: Pubkey
    creator: Pubkey


def set_pre_activation_swap_address(
        args: SetPreActivationSwapAddressArgs,
        accounts: SetPreActivationSwapAddressAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["creator"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"9\x8b/{\xd8P\xdf\n"
    encoded_args = layout.build(
        {
            "pre_activation_swap_address": args["pre_activation_swap_address"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
