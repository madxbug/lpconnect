from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID

from .. import types
from ..program_id import PROGRAM_ID


class AddLiquidityByStrategyOneSideArgs(typing.TypedDict):
    liquidity_parameter: types.liquidity_parameter_by_strategy_one_side.LiquidityParameterByStrategyOneSide


layout = borsh.CStruct(
    "liquidity_parameter"
    / types.liquidity_parameter_by_strategy_one_side.LiquidityParameterByStrategyOneSide.layout
)


class AddLiquidityByStrategyOneSideAccounts(typing.TypedDict):
    position: Pubkey
    lb_pair: Pubkey
    bin_array_bitmap_extension: typing.Optional[Pubkey]
    user_token: Pubkey
    reserve: Pubkey
    token_mint: Pubkey
    bin_array_lower: Pubkey
    bin_array_upper: Pubkey
    sender: Pubkey
    event_authority: Pubkey
    program: Pubkey


def add_liquidity_by_strategy_one_side(
        args: AddLiquidityByStrategyOneSideArgs,
        accounts: AddLiquidityByStrategyOneSideAccounts,
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
        AccountMeta(pubkey=accounts["user_token"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["token_mint"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["bin_array_lower"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["bin_array_upper"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["sender"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b")\x05\xee\xafd\xe1\x06\xcd"
    encoded_args = layout.build(
        {
            "liquidity_parameter": args["liquidity_parameter"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
