import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class BinLiquidityReductionJSON(typing.TypedDict):
    bin_id: int
    bps_to_remove: int


@dataclass
class BinLiquidityReduction:
    layout: typing.ClassVar = borsh.CStruct(
        "bin_id" / borsh.I32, "bps_to_remove" / borsh.U16
    )
    bin_id: int
    bps_to_remove: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "BinLiquidityReduction":
        return cls(bin_id=obj.bin_id, bps_to_remove=obj.bps_to_remove)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"bin_id": self.bin_id, "bps_to_remove": self.bps_to_remove}

    def to_json(self) -> BinLiquidityReductionJSON:
        return {"bin_id": self.bin_id, "bps_to_remove": self.bps_to_remove}

    @classmethod
    def from_json(cls, obj: BinLiquidityReductionJSON) -> "BinLiquidityReduction":
        return cls(bin_id=obj["bin_id"], bps_to_remove=obj["bps_to_remove"])
