from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container, Construct

from . import (
    compressed_bin_deposit_amount,
)


class AddLiquiditySingleSidePreciseParameterJSON(typing.TypedDict):
    bins: list[compressed_bin_deposit_amount.CompressedBinDepositAmountJSON]
    decompress_multiplier: int


@dataclass
class AddLiquiditySingleSidePreciseParameter:
    layout: typing.ClassVar = borsh.CStruct(
        "bins"
        / borsh.Vec(
            typing.cast(
                Construct,
                compressed_bin_deposit_amount.CompressedBinDepositAmount.layout,
            )
        ),
        "decompress_multiplier" / borsh.U64,
    )
    bins: list[compressed_bin_deposit_amount.CompressedBinDepositAmount]
    decompress_multiplier: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "AddLiquiditySingleSidePreciseParameter":
        return cls(
            bins=list(
                map(
                    lambda item: compressed_bin_deposit_amount.CompressedBinDepositAmount.from_decoded(
                        item
                    ),
                    obj.bins,
                )
            ),
            decompress_multiplier=obj.decompress_multiplier,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "bins": list(map(lambda item: item.to_encodable(), self.bins)),
            "decompress_multiplier": self.decompress_multiplier,
        }

    def to_json(self) -> AddLiquiditySingleSidePreciseParameterJSON:
        return {
            "bins": list(map(lambda item: item.to_json(), self.bins)),
            "decompress_multiplier": self.decompress_multiplier,
        }

    @classmethod
    def from_json(
            cls, obj: AddLiquiditySingleSidePreciseParameterJSON
    ) -> "AddLiquiditySingleSidePreciseParameter":
        return cls(
            bins=list(
                map(
                    lambda item: compressed_bin_deposit_amount.CompressedBinDepositAmount.from_json(
                        item
                    ),
                    obj["bins"],
                )
            ),
            decompress_multiplier=obj["decompress_multiplier"],
        )
