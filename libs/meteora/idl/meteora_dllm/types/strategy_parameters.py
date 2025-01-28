import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container

from . import (
    strategy_type,
)


class StrategyParametersJSON(typing.TypedDict):
    min_bin_id: int
    max_bin_id: int
    strategy_type: strategy_type.StrategyTypeJSON
    parameteres: list[int]


@dataclass
class StrategyParameters:
    layout: typing.ClassVar = borsh.CStruct(
        "min_bin_id" / borsh.I32,
        "max_bin_id" / borsh.I32,
        "strategy_type" / strategy_type.layout,
        "parameteres" / borsh.U8[64],
    )
    min_bin_id: int
    max_bin_id: int
    strategy_type: strategy_type.StrategyTypeKind
    parameteres: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "StrategyParameters":
        return cls(
            min_bin_id=obj.min_bin_id,
            max_bin_id=obj.max_bin_id,
            strategy_type=strategy_type.from_decoded(obj.strategy_type),
            parameteres=obj.parameteres,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "min_bin_id": self.min_bin_id,
            "max_bin_id": self.max_bin_id,
            "strategy_type": self.strategy_type.to_encodable(),
            "parameteres": self.parameteres,
        }

    def to_json(self) -> StrategyParametersJSON:
        return {
            "min_bin_id": self.min_bin_id,
            "max_bin_id": self.max_bin_id,
            "strategy_type": self.strategy_type.to_json(),
            "parameteres": self.parameteres,
        }

    @classmethod
    def from_json(cls, obj: StrategyParametersJSON) -> "StrategyParameters":
        return cls(
            min_bin_id=obj["min_bin_id"],
            max_bin_id=obj["max_bin_id"],
            strategy_type=strategy_type.from_json(obj["strategy_type"]),
            parameteres=obj["parameteres"],
        )
