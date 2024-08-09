import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solders.pubkey import Pubkey

from ..program_id import PROGRAM_ID


class OracleJSON(typing.TypedDict):
    idx: int
    active_size: int
    length: int


@dataclass
class Oracle:
    discriminator: typing.ClassVar = b"\x8b\xc2\x83\xb3\x8c\xb3\xe5\xf4"
    layout: typing.ClassVar = borsh.CStruct(
        "idx" / borsh.U64, "active_size" / borsh.U64, "length" / borsh.U64
    )
    idx: int
    active_size: int
    length: int

    @classmethod
    async def fetch(
            cls,
            conn: AsyncClient,
            address: Pubkey,
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["Oracle"]:
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
    ) -> typing.List[typing.Optional["Oracle"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["Oracle"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "Oracle":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = Oracle.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            idx=dec.idx,
            active_size=dec.active_size,
            length=dec.length,
        )

    def to_json(self) -> OracleJSON:
        return {
            "idx": self.idx,
            "active_size": self.active_size,
            "length": self.length,
        }

    @classmethod
    def from_json(cls, obj: OracleJSON) -> "Oracle":
        return cls(
            idx=obj["idx"],
            active_size=obj["active_size"],
            length=obj["length"],
        )
