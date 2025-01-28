import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID

from ..program_id import PROGRAM_ID


class InitializeBinArrayArgs(typing.TypedDict):
    index: int


layout = borsh.CStruct("index" / borsh.I64)


class InitializeBinArrayAccounts(typing.TypedDict):
    lb_pair: Pubkey
    bin_array: Pubkey
    funder: Pubkey


def initialize_bin_array(
        args: InitializeBinArrayArgs,
        accounts: InitializeBinArrayAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["bin_array"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["funder"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"#V\x13\xb9N\xd4K\xd3"
    encoded_args = layout.build(
        {
            "index": args["index"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
