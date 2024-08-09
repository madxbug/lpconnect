from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from .. import types
from ..program_id import PROGRAM_ID


class UpdateFeeParametersArgs(typing.TypedDict):
    fee_parameter: types.fee_parameter.FeeParameter


layout = borsh.CStruct("fee_parameter" / types.fee_parameter.FeeParameter.layout)


class UpdateFeeParametersAccounts(typing.TypedDict):
    lb_pair: Pubkey
    admin: Pubkey
    event_authority: Pubkey
    program: Pubkey


def update_fee_parameters(
        args: UpdateFeeParametersArgs,
        accounts: UpdateFeeParametersAccounts,
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
    identifier = b"\x80\x80\xd0[\xf65\x1f\xb0"
    encoded_args = layout.build(
        {
            "fee_parameter": args["fee_parameter"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
