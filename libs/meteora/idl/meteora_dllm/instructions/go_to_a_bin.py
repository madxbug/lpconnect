import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class GoToABinArgs(typing.TypedDict):
    bin_id: int


layout = borsh.CStruct("bin_id" / borsh.I32)


class GoToABinAccounts(typing.TypedDict):
    lb_pair: Pubkey
    bin_array_bitmap_extension: typing.Optional[Pubkey]
    from_bin_array: typing.Optional[Pubkey]
    to_bin_array: typing.Optional[Pubkey]
    event_authority: Pubkey
    program: Pubkey


def go_to_a_bin(
        args: GoToABinArgs,
        accounts: GoToABinAccounts,
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
        AccountMeta(
            pubkey=accounts["from_bin_array"], is_signer=False, is_writable=False
        )
        if accounts["from_bin_array"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["to_bin_array"], is_signer=False, is_writable=False)
        if accounts["to_bin_array"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x92H\xae\xe0(\xfdT\xae"
    encoded_args = layout.build(
        {
            "bin_id": args["bin_id"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
