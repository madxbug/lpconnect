import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class UpdateRewardFunderArgs(typing.TypedDict):
    reward_index: int
    new_funder: Pubkey


layout = borsh.CStruct("reward_index" / borsh.U64, "new_funder" / BorshPubkey)


class UpdateRewardFunderAccounts(typing.TypedDict):
    lb_pair: Pubkey
    admin: Pubkey
    event_authority: Pubkey
    program: Pubkey


def update_reward_funder(
        args: UpdateRewardFunderArgs,
        accounts: UpdateRewardFunderAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xd3\x1c0 \xd7\xa0#\x17"
    encoded_args = layout.build(
        {
            "reward_index": args["reward_index"],
            "new_funder": args["new_funder"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
