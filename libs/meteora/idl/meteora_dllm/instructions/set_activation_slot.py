import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class SetActivationSlotArgs(typing.TypedDict):
    activation_slot: int


layout = borsh.CStruct("activation_slot" / borsh.U64)


class SetActivationSlotAccounts(typing.TypedDict):
    lb_pair: Pubkey
    admin: Pubkey


def set_activation_slot(
        args: SetActivationSlotArgs,
        accounts: SetActivationSlotAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xc8\xe3ZS\x1bO\xbfX"
    encoded_args = layout.build(
        {
            "activation_slot": args["activation_slot"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
