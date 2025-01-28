import typing

import borsh_construct as borsh
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

from ..program_id import PROGRAM_ID


class InitializePositionArgs(typing.TypedDict):
    lower_bin_id: int
    width: int


layout = borsh.CStruct("lower_bin_id" / borsh.I32, "width" / borsh.I32)


class InitializePositionAccounts(typing.TypedDict):
    payer: Pubkey
    position: Pubkey
    lb_pair: Pubkey
    owner: Pubkey
    event_authority: Pubkey
    program: Pubkey


def initialize_position(
        args: InitializePositionArgs,
        accounts: InitializePositionAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["position"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xdb\xc0\xeaG\xbe\xbffP"
    encoded_args = layout.build(
        {
            "lower_bin_id": args["lower_bin_id"],
            "width": args["width"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
