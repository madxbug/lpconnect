from __future__ import annotations

import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class UpdateFeeOwnerAccounts(typing.TypedDict):
    lb_pair: Pubkey
    new_fee_owner: Pubkey
    admin: Pubkey


def update_fee_owner(
        accounts: UpdateFeeOwnerAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["new_fee_owner"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"<?\x11@\r\xc4\xa6\xf3"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
