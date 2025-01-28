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


class PresetParameterJSON(typing.TypedDict):
    bin_step: int
    base_factor: int
    filter_period: int
    decay_period: int
    reduction_factor: int
    variable_fee_control: int
    max_volatility_accumulator: int
    min_bin_id: int
    max_bin_id: int
    protocol_share: int


@dataclass
class PresetParameter:
    bin_step: int
    base_factor: int
    filter_period: int
    decay_period: int
    reduction_factor: int
    variable_fee_control: int
    max_volatility_accumulator: int
    min_bin_id: int
    max_bin_id: int
    protocol_share: int

    discriminator: typing.ClassVar = b'\xf2>\xf4"\xb5p:\xaa'
    layout: typing.ClassVar = borsh.CStruct(
        "bin_step" / borsh.U16,
        "base_factor" / borsh.U16,
        "filter_period" / borsh.U16,
        "decay_period" / borsh.U16,
        "reduction_factor" / borsh.U16,
        "variable_fee_control" / borsh.U32,
        "max_volatility_accumulator" / borsh.U32,
        "min_bin_id" / borsh.I32,
        "max_bin_id" / borsh.I32,
        "protocol_share" / borsh.U16,
    )

    @classmethod
    async def fetch(
            cls,
            conn: AsyncClient,
            address: Pubkey,
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["PresetParameter"]:
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
    ) -> typing.List[typing.Optional["PresetParameter"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["PresetParameter"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "PresetParameter":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = PresetParameter.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            bin_step=dec.bin_step,
            base_factor=dec.base_factor,
            filter_period=dec.filter_period,
            decay_period=dec.decay_period,
            reduction_factor=dec.reduction_factor,
            variable_fee_control=dec.variable_fee_control,
            max_volatility_accumulator=dec.max_volatility_accumulator,
            min_bin_id=dec.min_bin_id,
            max_bin_id=dec.max_bin_id,
            protocol_share=dec.protocol_share,
        )

    def to_json(self) -> PresetParameterJSON:
        return {
            "bin_step": self.bin_step,
            "base_factor": self.base_factor,
            "filter_period": self.filter_period,
            "decay_period": self.decay_period,
            "reduction_factor": self.reduction_factor,
            "variable_fee_control": self.variable_fee_control,
            "max_volatility_accumulator": self.max_volatility_accumulator,
            "min_bin_id": self.min_bin_id,
            "max_bin_id": self.max_bin_id,
            "protocol_share": self.protocol_share,
        }

    @classmethod
    def from_json(cls, obj: PresetParameterJSON) -> "PresetParameter":
        return cls(
            bin_step=obj["bin_step"],
            base_factor=obj["base_factor"],
            filter_period=obj["filter_period"],
            decay_period=obj["decay_period"],
            reduction_factor=obj["reduction_factor"],
            variable_fee_control=obj["variable_fee_control"],
            max_volatility_accumulator=obj["max_volatility_accumulator"],
            min_bin_id=obj["min_bin_id"],
            max_bin_id=obj["max_bin_id"],
            protocol_share=obj["protocol_share"],
        )
