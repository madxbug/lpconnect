from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class VariableParametersJSON(typing.TypedDict):
    volatility_accumulator: int
    volatility_reference: int
    index_reference: int
    padding: list[int]
    last_update_timestamp: int
    padding1: list[int]


@dataclass
class VariableParameters:
    layout: typing.ClassVar = borsh.CStruct(
        "volatility_accumulator" / borsh.U32,
        "volatility_reference" / borsh.U32,
        "index_reference" / borsh.I32,
        "padding" / borsh.U8[4],
        "last_update_timestamp" / borsh.I64,
        "padding1" / borsh.U8[8],
    )
    volatility_accumulator: int
    volatility_reference: int
    index_reference: int
    padding: list[int]
    last_update_timestamp: int
    padding1: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "VariableParameters":
        return cls(
            volatility_accumulator=obj.volatility_accumulator,
            volatility_reference=obj.volatility_reference,
            index_reference=obj.index_reference,
            padding=obj.padding,
            last_update_timestamp=obj.last_update_timestamp,
            padding1=obj.padding1,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "volatility_accumulator": self.volatility_accumulator,
            "volatility_reference": self.volatility_reference,
            "index_reference": self.index_reference,
            "padding": self.padding,
            "last_update_timestamp": self.last_update_timestamp,
            "padding1": self.padding1,
        }

    def to_json(self) -> VariableParametersJSON:
        return {
            "volatility_accumulator": self.volatility_accumulator,
            "volatility_reference": self.volatility_reference,
            "index_reference": self.index_reference,
            "padding": self.padding,
            "last_update_timestamp": self.last_update_timestamp,
            "padding1": self.padding1,
        }

    @classmethod
    def from_json(cls, obj: VariableParametersJSON) -> "VariableParameters":
        return cls(
            volatility_accumulator=obj["volatility_accumulator"],
            volatility_reference=obj["volatility_reference"],
            index_reference=obj["index_reference"],
            padding=obj["padding"],
            last_update_timestamp=obj["last_update_timestamp"],
            padding1=obj["padding1"],
        )
