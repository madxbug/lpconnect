import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class SwapArgs(typing.TypedDict):
    amount_in: int
    min_amount_out: int


layout = borsh.CStruct("amount_in" / borsh.U64, "min_amount_out" / borsh.U64)


class SwapAccounts(typing.TypedDict):
    lb_pair: Pubkey
    bin_array_bitmap_extension: typing.Optional[Pubkey]
    reserve_x: Pubkey
    reserve_y: Pubkey
    user_token_in: Pubkey
    user_token_out: Pubkey
    token_x_mint: Pubkey
    token_y_mint: Pubkey
    oracle: Pubkey
    host_fee_in: typing.Optional[Pubkey]
    user: Pubkey
    token_x_program: Pubkey
    token_y_program: Pubkey
    event_authority: Pubkey
    program: Pubkey


def swap(
        args: SwapArgs,
        accounts: SwapAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["bin_array_bitmap_extension"],
            is_signer=False,
            is_writable=False,
        )
        if accounts["bin_array_bitmap_extension"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["reserve_x"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve_y"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["user_token_in"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["user_token_out"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_x_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_y_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["host_fee_in"], is_signer=False, is_writable=True)
        if accounts["host_fee_in"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["user"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["token_x_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_y_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xf8\xc6\x9e\x91\xe1u\x87\xc8"
    encoded_args = layout.build(
        {
            "amount_in": args["amount_in"],
            "min_amount_out": args["min_amount_out"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
