from __future__ import annotations

import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class UpdateFeesAndRewardsAccounts(typing.TypedDict):
    position: Pubkey
    lb_pair: Pubkey
    bin_array_lower: Pubkey
    bin_array_upper: Pubkey
    owner: Pubkey


def update_fees_and_rewards(
        accounts: UpdateFeesAndRewardsAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["position"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["bin_array_lower"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["bin_array_upper"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x9a\xe6\xfa\r\xec\xd1K\xdf"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
