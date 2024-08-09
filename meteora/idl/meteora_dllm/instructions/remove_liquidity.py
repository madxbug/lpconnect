from __future__ import annotations

import typing

import borsh_construct as borsh
from construct import Construct
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from .. import types
from ..program_id import PROGRAM_ID


class RemoveLiquidityArgs(typing.TypedDict):
    bin_liquidity_removal: list[types.bin_liquidity_reduction.BinLiquidityReduction]


layout = borsh.CStruct(
    "bin_liquidity_removal"
    / borsh.Vec(
        typing.cast(
            Construct, types.bin_liquidity_reduction.BinLiquidityReduction.layout
        )
    )
)


class RemoveLiquidityAccounts(typing.TypedDict):
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


def remove_liquidity(
        args: RemoveLiquidityArgs,
        accounts: RemoveLiquidityAccounts,
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
    identifier = b"PU\xd1H\x18\xce\xb1l"
    encoded_args = layout.build(
        {
            "bin_liquidity_removal": list(
                map(lambda item: item.to_encodable(), args["bin_liquidity_removal"])
            ),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)