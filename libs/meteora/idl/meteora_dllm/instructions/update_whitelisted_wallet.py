import typing

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class UpdateWhitelistedWalletArgs(typing.TypedDict):
    wallet: Pubkey


layout = borsh.CStruct("wallet" / BorshPubkey)


class UpdateWhitelistedWalletAccounts(typing.TypedDict):
    lb_pair: Pubkey
    creator: Pubkey


def update_whitelisted_wallet(
        args: UpdateWhitelistedWalletArgs,
        accounts: UpdateWhitelistedWalletAccounts,
        program_id: Pubkey = PROGRAM_ID,
        remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["lb_pair"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["creator"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x04i\\\xa7\x84\x1c\tZ"
    encoded_args = layout.build(
        {
            "wallet": args["wallet"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
