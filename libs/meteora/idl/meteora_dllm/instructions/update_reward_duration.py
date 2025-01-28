import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class UpdateRewardDurationArgs(typing.TypedDict):
    reward_index: int
    new_duration: int


layout = borsh.CStruct("reward_index" / borsh.U64, "new_duration" / borsh.U64)


class UpdateRewardDurationAccounts(typing.TypedDict):
    lb_pair: Pubkey
    admin: Pubkey
    bin_array: Pubkey
    event_authority: Pubkey
    program: Pubkey


def update_reward_duration(
        args: UpdateRewardDurationArgs,
        accounts: UpdateRewardDurationAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["bin_array"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x8a\xae\xc4\xa9\xd5\xeb\xfek"
    encoded_args = layout.build(
        {
            "reward_index": args["reward_index"],
            "new_duration": args["new_duration"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
