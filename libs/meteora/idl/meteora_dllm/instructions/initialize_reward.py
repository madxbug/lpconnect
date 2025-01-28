import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID

from ..program_id import PROGRAM_ID


class InitializeRewardArgs(typing.TypedDict):
    reward_index: int
    reward_duration: int
    funder: Pubkey


layout = borsh.CStruct(
    "reward_index" / borsh.U64, "reward_duration" / borsh.U64, "funder" / BorshPubkey
)


class InitializeRewardAccounts(typing.TypedDict):
    lb_pair: Pubkey
    reward_vault: Pubkey
    reward_mint: Pubkey
    admin: Pubkey
    event_authority: Pubkey
    program: Pubkey


def initialize_reward(
        args: InitializeRewardArgs,
        accounts: InitializeRewardAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reward_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reward_mint"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"_\x87\xc0\xc4\xf2\x81\xe6D"
    encoded_args = layout.build(
        {
            "reward_index": args["reward_index"],
            "reward_duration": args["reward_duration"],
            "funder": args["funder"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
