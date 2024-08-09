from __future__ import annotations

import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID

from ..program_id import PROGRAM_ID


class InitializeLbPairArgs(typing.TypedDict):
    active_id: int
    bin_step: int


layout = borsh.CStruct("active_id" / borsh.I32, "bin_step" / borsh.U16)


class InitializeLbPairAccounts(typing.TypedDict):
    lb_pair: Pubkey
    bin_array_bitmap_extension: typing.Optional[Pubkey]
    token_mint_x: Pubkey
    token_mint_y: Pubkey
    reserve_x: Pubkey
    reserve_y: Pubkey
    oracle: Pubkey
    preset_parameter: Pubkey
    funder: Pubkey
    event_authority: Pubkey
    program: Pubkey


def initialize_lb_pair(
        args: InitializeLbPairArgs,
        accounts: InitializeLbPairAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
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
        AccountMeta(
            pubkey=accounts["preset_parameter"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["funder"], is_signer=True, is_writable=True),
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
    identifier = b"-\x9a\xed\xd2\xdd\x0f\xa6\\"
    encoded_args = layout.build(
        {
            "active_id": args["active_id"],
            "bin_step": args["bin_step"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
