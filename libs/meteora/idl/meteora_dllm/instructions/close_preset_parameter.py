import typing

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class ClosePresetParameterAccounts(typing.TypedDict):
    preset_parameter: Pubkey
    admin: Pubkey
    rent_receiver: Pubkey


def close_preset_parameter(
        accounts: ClosePresetParameterAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(
            pubkey=accounts["preset_parameter"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["rent_receiver"], is_signer=False, is_writable=True
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x04\x94\x91d\x86\x1a\xb5="
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
