import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID

from ..program_id import PROGRAM_ID


class FundRewardArgs(typing.TypedDict):
    reward_index: int
    amount: int
    carry_forward: bool


layout = borsh.CStruct(
    "reward_index" / borsh.U64, "amount" / borsh.U64, "carry_forward" / borsh.Bool
)


class FundRewardAccounts(typing.TypedDict):
    lb_pair: Pubkey
    reward_vault: Pubkey
    reward_mint: Pubkey
    funder_token_account: Pubkey
    funder: Pubkey
    bin_array: Pubkey
    event_authority: Pubkey
    program: Pubkey


def fund_reward(
        args: FundRewardArgs,
        accounts: FundRewardAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reward_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reward_mint"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["funder_token_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["funder"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["bin_array"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xbc2\xf9\xa5]\x97&?"
    encoded_args = layout.build(
        {
            "reward_index": args["reward_index"],
            "amount": args["amount"],
            "carry_forward": args["carry_forward"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
