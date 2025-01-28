import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class BinArrayBitmapExtensionJSON(typing.TypedDict):
    lb_pair: str
    positive_bin_array_bitmap: list[list[int]]
    negative_bin_array_bitmap: list[list[int]]


@dataclass
class BinArrayBitmapExtension:
    discriminator: typing.ClassVar = b"Po|q7\xed\x12\x05"
    layout: typing.ClassVar = borsh.CStruct(
        "lb_pair" / BorshPubkey,
        "positive_bin_array_bitmap" / borsh.U64[8][12],
        "negative_bin_array_bitmap" / borsh.U64[8][12],
    )
    lb_pair: Pubkey
    positive_bin_array_bitmap: list[list[int]]
    negative_bin_array_bitmap: list[list[int]]

    @classmethod
    async def fetch(
            cls,
            conn: AsyncClient,
            address: Pubkey,
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["BinArrayBitmapExtension"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
            cls,
            conn: AsyncClient,
            addresses: list[Pubkey],
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["BinArrayBitmapExtension"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["BinArrayBitmapExtension"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "BinArrayBitmapExtension":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = BinArrayBitmapExtension.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            lb_pair=dec.lb_pair,
            positive_bin_array_bitmap=dec.positive_bin_array_bitmap,
            negative_bin_array_bitmap=dec.negative_bin_array_bitmap,
        )

    def to_json(self) -> BinArrayBitmapExtensionJSON:
        return {
            "lb_pair": str(self.lb_pair),
            "positive_bin_array_bitmap": self.positive_bin_array_bitmap,
            "negative_bin_array_bitmap": self.negative_bin_array_bitmap,
        }

    @classmethod
    def from_json(cls, obj: BinArrayBitmapExtensionJSON) -> "BinArrayBitmapExtension":
        return cls(
            lb_pair=Pubkey.from_string(obj["lb_pair"]),
            positive_bin_array_bitmap=obj["positive_bin_array_bitmap"],
            negative_bin_array_bitmap=obj["negative_bin_array_bitmap"],
        )
