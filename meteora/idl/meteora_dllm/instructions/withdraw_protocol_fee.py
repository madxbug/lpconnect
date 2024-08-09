from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class WithdrawProtocolFeeArgs(typing.TypedDict):
    amount_x: int
    amount_y: int


layout = borsh.CStruct("amount_x" / borsh.U64, "amount_y" / borsh.U64)


class WithdrawProtocolFeeAccounts(typing.TypedDict):
    lb_pair: Pubkey
    reserve_x: Pubkey
    reserve_y: Pubkey
    token_x_mint: Pubkey
    token_y_mint: Pubkey
    receiver_token_x: Pubkey
    receiver_token_y: Pubkey
    token_x_program: Pubkey
    token_y_program: Pubkey


def withdraw_protocol_fee(
        args: WithdrawProtocolFeeArgs,
        accounts: WithdrawProtocolFeeAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve_x"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve_y"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["token_x_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_y_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["receiver_token_x"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["receiver_token_y"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_x_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_y_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x9e\xc9\x9e\xbd!]\xa2g"
    encoded_args = layout.build(
        {
            "amount_x": args["amount_x"],
            "amount_y": args["amount_y"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
