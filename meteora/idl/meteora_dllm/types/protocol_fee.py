from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class ProtocolFeeJSON(typing.TypedDict):
    amount_x: int
    amount_y: int


@dataclass
class ProtocolFee:
    layout: typing.ClassVar = borsh.CStruct(
        "amount_x" / borsh.U64, "amount_y" / borsh.U64
    )
    amount_x: int
    amount_y: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "ProtocolFee":
        return cls(amount_x=obj.amount_x, amount_y=obj.amount_y)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"amount_x": self.amount_x, "amount_y": self.amount_y}

    def to_json(self) -> ProtocolFeeJSON:
        return {"amount_x": self.amount_x, "amount_y": self.amount_y}

    @classmethod
    def from_json(cls, obj: ProtocolFeeJSON) -> "ProtocolFee":
        return cls(amount_x=obj["amount_x"], amount_y=obj["amount_y"])
