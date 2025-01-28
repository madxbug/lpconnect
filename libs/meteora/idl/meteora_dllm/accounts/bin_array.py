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

from .. import types
from ..program_id import PROGRAM_ID


class BinArrayJSON(typing.TypedDict):
    index: int
    version: int
    padding: list[int]
    lb_pair: str
    bins: list[types.bin.BinJSON]


@dataclass
class BinArray:
    index: int
    version: int
    padding: list[int]
    lb_pair: Pubkey
    bins: list[types.bin.Bin]

    discriminator: typing.ClassVar = b"\\\x8e\\\xdc\x05\x94F\xb5"
    layout: typing.ClassVar = borsh.CStruct(
        "index" / borsh.I64,
        "version" / borsh.U8,
        "padding" / borsh.U8[7],
        "lb_pair" / BorshPubkey,
        "bins" / types.bin.Bin.layout[70],
    )

    @classmethod
    async def fetch(
            cls,
            conn: AsyncClient,
            address: Pubkey,
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["BinArray"]:
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
    ) -> typing.List[typing.Optional["BinArray"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["BinArray"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "BinArray":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = BinArray.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            index=dec.index,
            version=dec.version,
            padding=dec.padding,
            lb_pair=dec.lb_pair,
            bins=list(map(lambda item: types.bin.Bin.from_decoded(item), dec.bins)),
        )

    def to_json(self) -> BinArrayJSON:
        return {
            "index": self.index,
            "version": self.version,
            "padding": self.padding,
            "lb_pair": str(self.lb_pair),
            "bins": list(map(lambda item: item.to_json(), self.bins)),
        }

    @classmethod
    def from_json(cls, obj: BinArrayJSON) -> "BinArray":
        return cls(
            index=obj["index"],
            version=obj["version"],
            padding=obj["padding"],
            lb_pair=Pubkey.from_string(obj["lb_pair"]),
            bins=list(map(lambda item: types.bin.Bin.from_json(item), obj["bins"])),
        )
