from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID

from .. import types
from ..program_id import PROGRAM_ID


class InitializePermissionLbPairArgs(typing.TypedDict):
    ix_data: types.init_permission_pair_ix.InitPermissionPairIx


layout = borsh.CStruct(
    "ix_data" / types.init_permission_pair_ix.InitPermissionPairIx.layout
)


class InitializePermissionLbPairAccounts(typing.TypedDict):
    base: Pubkey
    lb_pair: Pubkey
    bin_array_bitmap_extension: typing.Optional[Pubkey]
    token_mint_x: Pubkey
    token_mint_y: Pubkey
    reserve_x: Pubkey
    reserve_y: Pubkey
    oracle: Pubkey
    admin: Pubkey
    event_authority: Pubkey
    program: Pubkey


def initialize_permission_lb_pair(
        args: InitializePermissionLbPairArgs,
        accounts: InitializePermissionLbPairAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["base"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["bin_array_bitmap_extension"],
            is_signer=False,
            is_writable=True,
        )
        if accounts["bin_array_bitmap_extension"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["token_mint_x"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_mint_y"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["reserve_x"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve_y"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=True),
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
    identifier = b"lf\xd5U\xfb\x035\x15"
    encoded_args = layout.build(
        {
            "ix_data": args["ix_data"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
