from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

from .. import types
from ..program_id import PROGRAM_ID


class InitializePresetParameterArgs(typing.TypedDict):
    ix: types.init_preset_parameters_ix.InitPresetParametersIx


layout = borsh.CStruct(
    "ix" / types.init_preset_parameters_ix.InitPresetParametersIx.layout
)


class InitializePresetParameterAccounts(typing.TypedDict):
    preset_parameter: Pubkey
    admin: Pubkey


def initialize_preset_parameter(
        args: InitializePresetParameterArgs,
        accounts: InitializePresetParameterAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(
            pubkey=accounts["preset_parameter"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"B\xbcG\xd3bm\x0e\xba"
    encoded_args = layout.build(
        {
            "ix": args["ix"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
