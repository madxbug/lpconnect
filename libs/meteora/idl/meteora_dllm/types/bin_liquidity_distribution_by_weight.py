import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class BinLiquidityDistributionByWeightJSON(typing.TypedDict):
    bin_id: int
    weight: int


@dataclass
class BinLiquidityDistributionByWeight:
    layout: typing.ClassVar = borsh.CStruct("bin_id" / borsh.I32, "weight" / borsh.U16)
    bin_id: int
    weight: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "BinLiquidityDistributionByWeight":
        return cls(bin_id=obj.bin_id, weight=obj.weight)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"bin_id": self.bin_id, "weight": self.weight}

    def to_json(self) -> BinLiquidityDistributionByWeightJSON:
        return {"bin_id": self.bin_id, "weight": self.weight}

    @classmethod
    def from_json(
            cls, obj: BinLiquidityDistributionByWeightJSON
    ) -> "BinLiquidityDistributionByWeight":
        return cls(bin_id=obj["bin_id"], weight=obj["weight"])
