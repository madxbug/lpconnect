from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class FeeInfoJSON(typing.TypedDict):
    fee_x_per_token_complete: int
    fee_y_per_token_complete: int
    fee_x_pending: int
    fee_y_pending: int


@dataclass
class FeeInfo:
    layout: typing.ClassVar = borsh.CStruct(
        "fee_x_per_token_complete" / borsh.U128,
        "fee_y_per_token_complete" / borsh.U128,
        "fee_x_pending" / borsh.U64,
        "fee_y_pending" / borsh.U64,
    )
    fee_x_per_token_complete: int
    fee_y_per_token_complete: int
    fee_x_pending: int
    fee_y_pending: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "FeeInfo":
        return cls(
            fee_x_per_token_complete=obj.fee_x_per_token_complete,
            fee_y_per_token_complete=obj.fee_y_per_token_complete,
            fee_x_pending=obj.fee_x_pending,
            fee_y_pending=obj.fee_y_pending,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "fee_x_per_token_complete": self.fee_x_per_token_complete,
            "fee_y_per_token_complete": self.fee_y_per_token_complete,
            "fee_x_pending": self.fee_x_pending,
            "fee_y_pending": self.fee_y_pending,
        }

    def to_json(self) -> FeeInfoJSON:
        return {
            "fee_x_per_token_complete": self.fee_x_per_token_complete,
            "fee_y_per_token_complete": self.fee_y_per_token_complete,
            "fee_x_pending": self.fee_x_pending,
            "fee_y_pending": self.fee_y_pending,
        }

    @classmethod
    def from_json(cls, obj: FeeInfoJSON) -> "FeeInfo":
        return cls(
            fee_x_per_token_complete=obj["fee_x_per_token_complete"],
            fee_y_per_token_complete=obj["fee_y_per_token_complete"],
            fee_x_pending=obj["fee_x_pending"],
            fee_y_pending=obj["fee_y_pending"],
        )
