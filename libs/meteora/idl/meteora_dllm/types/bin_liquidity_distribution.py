import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class BinLiquidityDistributionJSON(typing.TypedDict):
    bin_id: int
    distribution_x: int
    distribution_y: int


@dataclass
class BinLiquidityDistribution:
    layout: typing.ClassVar = borsh.CStruct(
        "bin_id" / borsh.I32, "distribution_x" / borsh.U16, "distribution_y" / borsh.U16
    )
    bin_id: int
    distribution_x: int
    distribution_y: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "BinLiquidityDistribution":
        return cls(
            bin_id=obj.bin_id,
            distribution_x=obj.distribution_x,
            distribution_y=obj.distribution_y,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "bin_id": self.bin_id,
            "distribution_x": self.distribution_x,
            "distribution_y": self.distribution_y,
        }

    def to_json(self) -> BinLiquidityDistributionJSON:
        return {
            "bin_id": self.bin_id,
            "distribution_x": self.distribution_x,
            "distribution_y": self.distribution_y,
        }

    @classmethod
    def from_json(cls, obj: BinLiquidityDistributionJSON) -> "BinLiquidityDistribution":
        return cls(
            bin_id=obj["bin_id"],
            distribution_x=obj["distribution_x"],
            distribution_y=obj["distribution_y"],
        )
