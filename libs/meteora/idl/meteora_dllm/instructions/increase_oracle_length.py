import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID

from ..program_id import PROGRAM_ID


class IncreaseOracleLengthArgs(typing.TypedDict):
    length_to_add: int


layout = borsh.CStruct("length_to_add" / borsh.U64)


class IncreaseOracleLengthAccounts(typing.TypedDict):
    oracle: Pubkey
    funder: Pubkey
    event_authority: Pubkey
    program: Pubkey


def increase_oracle_length(
        args: IncreaseOracleLengthArgs,
        accounts: IncreaseOracleLengthAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["funder"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xbe=}WgO\x9e\xad"
    encoded_args = layout.build(
        {
            "length_to_add": args["length_to_add"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
