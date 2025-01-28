import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

from ..program_id import PROGRAM_ID


class InitializePositionByOperatorArgs(typing.TypedDict):
    lower_bin_id: int
    width: int
    owner: Pubkey
    fee_owner: Pubkey


layout = borsh.CStruct(
    "lower_bin_id" / borsh.I32,
    "width" / borsh.I32,
    "owner" / BorshPubkey,
    "fee_owner" / BorshPubkey,
)


class InitializePositionByOperatorAccounts(typing.TypedDict):
    payer: Pubkey
    base: Pubkey
    position: Pubkey
    lb_pair: Pubkey
    operator: Pubkey
    event_authority: Pubkey
    program: Pubkey


def initialize_position_by_operator(
        args: InitializePositionByOperatorArgs,
        accounts: InitializePositionByOperatorAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["base"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["position"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["operator"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xfb\xbd\xbe\xf4u\xfe#\x94"
    encoded_args = layout.build(
        {
            "lower_bin_id": args["lower_bin_id"],
            "width": args["width"],
            "owner": args["owner"],
            "fee_owner": args["fee_owner"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
