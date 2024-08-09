from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container

from . import (
    strategy_parameters,
)


class LiquidityParameterByStrategyOneSideJSON(typing.TypedDict):
    amount: int
    active_id: int
    max_active_bin_slippage: int
    strategy_parameters: strategy_parameters.StrategyParametersJSON


@dataclass
class LiquidityParameterByStrategyOneSide:
    layout: typing.ClassVar = borsh.CStruct(
        "amount" / borsh.U64,
        "active_id" / borsh.I32,
        "max_active_bin_slippage" / borsh.I32,
        "strategy_parameters" / strategy_parameters.StrategyParameters.layout,
    )
    amount: int
    active_id: int
    max_active_bin_slippage: int
    strategy_parameters: strategy_parameters.StrategyParameters

    @classmethod
    def from_decoded(cls, obj: Container) -> "LiquidityParameterByStrategyOneSide":
        return cls(
            amount=obj.amount,
            active_id=obj.active_id,
            max_active_bin_slippage=obj.max_active_bin_slippage,
            strategy_parameters=strategy_parameters.StrategyParameters.from_decoded(
                obj.strategy_parameters
            ),
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "amount": self.amount,
            "active_id": self.active_id,
            "max_active_bin_slippage": self.max_active_bin_slippage,
            "strategy_parameters": self.strategy_parameters.to_encodable(),
        }

    def to_json(self) -> LiquidityParameterByStrategyOneSideJSON:
        return {
            "amount": self.amount,
            "active_id": self.active_id,
            "max_active_bin_slippage": self.max_active_bin_slippage,
            "strategy_parameters": self.strategy_parameters.to_json(),
        }

    @classmethod
    def from_json(
            cls, obj: LiquidityParameterByStrategyOneSideJSON
    ) -> "LiquidityParameterByStrategyOneSide":
        return cls(
            amount=obj["amount"],
            active_id=obj["active_id"],
            max_active_bin_slippage=obj["max_active_bin_slippage"],
            strategy_parameters=strategy_parameters.StrategyParameters.from_json(
                obj["strategy_parameters"]
            ),
        )
