from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class ObservationJSON(typing.TypedDict):
    cumulative_active_bin_id: int
    created_at: int
    last_updated_at: int


@dataclass
class Observation:
    layout: typing.ClassVar = borsh.CStruct(
        "cumulative_active_bin_id" / borsh.I128,
        "created_at" / borsh.I64,
        "last_updated_at" / borsh.I64,
    )
    cumulative_active_bin_id: int
    created_at: int
    last_updated_at: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "Observation":
        return cls(
            cumulative_active_bin_id=obj.cumulative_active_bin_id,
            created_at=obj.created_at,
            last_updated_at=obj.last_updated_at,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "cumulative_active_bin_id": self.cumulative_active_bin_id,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
        }

    def to_json(self) -> ObservationJSON:
        return {
            "cumulative_active_bin_id": self.cumulative_active_bin_id,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
        }

    @classmethod
    def from_json(cls, obj: ObservationJSON) -> "Observation":
        return cls(
            cumulative_active_bin_id=obj["cumulative_active_bin_id"],
            created_at=obj["created_at"],
            last_updated_at=obj["last_updated_at"],
        )
