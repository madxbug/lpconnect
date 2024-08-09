from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class FeeParameterJSON(typing.TypedDict):
    protocol_share: int
    base_factor: int


@dataclass
class FeeParameter:
    layout: typing.ClassVar = borsh.CStruct(
        "protocol_share" / borsh.U16, "base_factor" / borsh.U16
    )
    protocol_share: int
    base_factor: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "FeeParameter":
        return cls(protocol_share=obj.protocol_share, base_factor=obj.base_factor)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"protocol_share": self.protocol_share, "base_factor": self.base_factor}

    def to_json(self) -> FeeParameterJSON:
        return {"protocol_share": self.protocol_share, "base_factor": self.base_factor}

    @classmethod
    def from_json(cls, obj: FeeParameterJSON) -> "FeeParameter":
        return cls(protocol_share=obj["protocol_share"], base_factor=obj["base_factor"])
