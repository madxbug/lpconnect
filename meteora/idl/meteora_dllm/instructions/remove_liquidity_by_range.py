from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class RemoveLiquidityByRangeArgs(typing.TypedDict):
    from_bin_id: int
    to_bin_id: int
    bps_to_remove: int


layout = borsh.CStruct(
    "from_bin_id" / borsh.I32, "to_bin_id" / borsh.I32, "bps_to_remove" / borsh.U16
)


class RemoveLiquidityByRangeAccounts(typing.TypedDict):
    position: Pubkey
    lb_pair: Pubkey
    bin_array_bitmap_extension: typing.Optional[Pubkey]
    user_token_x: Pubkey
    user_token_y: Pubkey
    reserve_x: Pubkey
    reserve_y: Pubkey
    token_x_mint: Pubkey
    token_y_mint: Pubkey
    bin_array_lower: Pubkey
    bin_array_upper: Pubkey
    sender: Pubkey
    token_x_program: Pubkey
    token_y_program: Pubkey
    event_authority: Pubkey
    program: Pubkey


def remove_liquidity_by_range(
        args: RemoveLiquidityByRangeArgs,
        accounts: RemoveLiquidityByRangeAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["position"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["bin_array_bitmap_extension"],
            is_signer=False,
            is_writable=True,
        )
        if accounts["bin_array_bitmap_extension"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["user_token_x"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_token_y"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve_x"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve_y"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["token_x_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_y_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["bin_array_lower"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["bin_array_upper"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["sender"], is_signer=True, is_writable=False),
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
    identifier = b"\x1aRf\x98\xf0Ji\x1a"
    encoded_args = layout.build(
        {
            "from_bin_id": args["from_bin_id"],
            "to_bin_id": args["to_bin_id"],
            "bps_to_remove": args["bps_to_remove"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
