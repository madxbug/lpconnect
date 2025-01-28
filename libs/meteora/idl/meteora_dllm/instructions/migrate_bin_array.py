import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class MigrateBinArrayAccounts(typing.TypedDict):
    lb_pair: Pubkey


def migrate_bin_array(
        accounts: MigrateBinArrayAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=False)
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x11\x17\x9f\xd3e\xb8)\xf1"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
