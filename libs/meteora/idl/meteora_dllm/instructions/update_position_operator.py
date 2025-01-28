import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class UpdatePositionOperatorArgs(typing.TypedDict):
    operator: Pubkey


layout = borsh.CStruct("operator" / BorshPubkey)


class UpdatePositionOperatorAccounts(typing.TypedDict):
    position: Pubkey
    owner: Pubkey
    event_authority: Pubkey
    program: Pubkey


def update_position_operator(
        args: UpdatePositionOperatorArgs,
        accounts: UpdatePositionOperatorAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["position"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xca\xb8g\x8f\xb4\xbft\xd9"
    encoded_args = layout.build(
        {
            "operator": args["operator"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
