from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container, Construct

from . import (
    bin_liquidity_distribution,
)


class LiquidityParameterJSON(typing.TypedDict):
    amount_x: int
    amount_y: int
    bin_liquidity_dist: list[bin_liquidity_distribution.BinLiquidityDistributionJSON]


@dataclass
class LiquidityParameter:
    layout: typing.ClassVar = borsh.CStruct(
        "amount_x" / borsh.U64,
        "amount_y" / borsh.U64,
        "bin_liquidity_dist"
        / borsh.Vec(
            typing.cast(
                Construct, bin_liquidity_distribution.BinLiquidityDistribution.layout
            )
        ),
    )
    amount_x: int
    amount_y: int
    bin_liquidity_dist: list[bin_liquidity_distribution.BinLiquidityDistribution]

    @classmethod
    def from_decoded(cls, obj: Container) -> "LiquidityParameter":
        return cls(
            amount_x=obj.amount_x,
            amount_y=obj.amount_y,
            bin_liquidity_dist=list(
                map(
                    lambda item: bin_liquidity_distribution.BinLiquidityDistribution.from_decoded(
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
            "bin_liquidity_dist": list(
                map(lambda item: item.to_encodable(), self.bin_liquidity_dist)
            ),
        }

    def to_json(self) -> LiquidityParameterJSON:
        return {
            "amount_x": self.amount_x,
            "amount_y": self.amount_y,
            "bin_liquidity_dist": list(
                map(lambda item: item.to_json(), self.bin_liquidity_dist)
            ),
        }

    @classmethod
    def from_json(cls, obj: LiquidityParameterJSON) -> "LiquidityParameter":
        return cls(
            amount_x=obj["amount_x"],
            amount_y=obj["amount_y"],
            bin_liquidity_dist=list(
                map(
                    lambda item: bin_liquidity_distribution.BinLiquidityDistribution.from_json(
                        item
                    ),
                    obj["bin_liquidity_dist"],
                )
            ),
        )
