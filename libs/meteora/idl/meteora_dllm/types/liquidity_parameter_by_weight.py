import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container, Construct

from . import (
    bin_liquidity_distribution_by_weight,
)


class LiquidityParameterByWeightJSON(typing.TypedDict):
    amount_x: int
    amount_y: int
    active_id: int
    max_active_bin_slippage: int
    bin_liquidity_dist: list[
        bin_liquidity_distribution_by_weight.BinLiquidityDistributionByWeightJSON
    ]


@dataclass
class LiquidityParameterByWeight:
    layout: typing.ClassVar = borsh.CStruct(
        "amount_x" / borsh.U64,
        "amount_y" / borsh.U64,
        "active_id" / borsh.I32,
        "max_active_bin_slippage" / borsh.I32,
        "bin_liquidity_dist"
        / borsh.Vec(
            typing.cast(
                Construct,
                bin_liquidity_distribution_by_weight.BinLiquidityDistributionByWeight.layout,
            )
        ),
    )
    amount_x: int
    amount_y: int
    active_id: int
    max_active_bin_slippage: int
    bin_liquidity_dist: list[
        bin_liquidity_distribution_by_weight.BinLiquidityDistributionByWeight
    ]

    @classmethod
    def from_decoded(cls, obj: Container) -> "LiquidityParameterByWeight":
        return cls(
            amount_x=obj.amount_x,
            amount_y=obj.amount_y,
            active_id=obj.active_id,
            max_active_bin_slippage=obj.max_active_bin_slippage,
            bin_liquidity_dist=list(
                map(
                    lambda item: bin_liquidity_distribution_by_weight.BinLiquidityDistributionByWeight.from_decoded(
                        item
                    ),
                    obj.bin_liquidity_dist,
                )
            ),
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "amount_x": self.amount_x,
            "amount_y": self.amount_y,
            "active_id": self.active_id,
            "max_active_bin_slippage": self.max_active_bin_slippage,
            "bin_liquidity_dist": list(
                map(lambda item: item.to_encodable(), self.bin_liquidity_dist)
            ),
        }

    def to_json(self) -> LiquidityParameterByWeightJSON:
        return {
            "amount_x": self.amount_x,
            "amount_y": self.amount_y,
            "active_id": self.active_id,
            "max_active_bin_slippage": self.max_active_bin_slippage,
            "bin_liquidity_dist": list(
                map(lambda item: item.to_json(), self.bin_liquidity_dist)
            ),
        }

    @classmethod
    def from_json(
            cls, obj: LiquidityParameterByWeightJSON
    ) -> "LiquidityParameterByWeight":
        return cls(
            amount_x=obj["amount_x"],
            amount_y=obj["amount_y"],
            active_id=obj["active_id"],
            max_active_bin_slippage=obj["max_active_bin_slippage"],
            bin_liquidity_dist=list(
                map(
                    lambda item: bin_liquidity_distribution_by_weight.BinLiquidityDistributionByWeight.from_json(
                        item
                    ),
                    obj["bin_liquidity_dist"],
                )
            ),
        )
