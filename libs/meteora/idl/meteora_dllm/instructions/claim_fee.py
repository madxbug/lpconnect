import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID

from ..program_id import PROGRAM_ID


class ClaimFeeAccounts(typing.TypedDict):
    lb_pair: Pubkey
    position: Pubkey
    bin_array_lower: Pubkey
    bin_array_upper: Pubkey
    sender: Pubkey
    reserve_x: Pubkey
    reserve_y: Pubkey
    user_token_x: Pubkey
    user_token_y: Pubkey
    token_x_mint: Pubkey
    token_y_mint: Pubkey
    event_authority: Pubkey
    program: Pubkey


def claim_fee(
        accounts: ClaimFeeAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["position"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["bin_array_lower"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["bin_array_upper"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["sender"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["reserve_x"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["reserve_y"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_token_x"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_token_y"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["token_x_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_y_mint"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xa9 O\x89\x88\xe8F\x89"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
