from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class InitPermissionPairIxJSON(typing.TypedDict):
    active_id: int
    bin_step: int
    base_factor: int
    min_bin_id: int
    max_bin_id: int
    lock_duration_in_slot: int


@dataclass
class InitPermissionPairIx:
    layout: typing.ClassVar = borsh.CStruct(
        "active_id" / borsh.I32,
        "bin_step" / borsh.U16,
        "base_factor" / borsh.U16,
        "min_bin_id" / borsh.I32,
        "max_bin_id" / borsh.I32,
        "lock_duration_in_slot" / borsh.U64,
    )
    active_id: int
    bin_step: int
    base_factor: int
    min_bin_id: int
    max_bin_id: int
    lock_duration_in_slot: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "InitPermissionPairIx":
        return cls(
            active_id=obj.active_id,
            bin_step=obj.bin_step,
            base_factor=obj.base_factor,
            min_bin_id=obj.min_bin_id,
            max_bin_id=obj.max_bin_id,
            lock_duration_in_slot=obj.lock_duration_in_slot,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "active_id": self.active_id,
            "bin_step": self.bin_step,
            "base_factor": self.base_factor,
            "min_bin_id": self.min_bin_id,
            "max_bin_id": self.max_bin_id,
            "lock_duration_in_slot": self.lock_duration_in_slot,
        }

    def to_json(self) -> InitPermissionPairIxJSON:
        return {
            "active_id": self.active_id,
            "bin_step": self.bin_step,
            "base_factor": self.base_factor,
            "min_bin_id": self.min_bin_id,
            "max_bin_id": self.max_bin_id,
            "lock_duration_in_slot": self.lock_duration_in_slot,
        }

    @classmethod
    def from_json(cls, obj: InitPermissionPairIxJSON) -> "InitPermissionPairIx":
        return cls(
            active_id=obj["active_id"],
            bin_step=obj["bin_step"],
            base_factor=obj["base_factor"],
            min_bin_id=obj["min_bin_id"],
            max_bin_id=obj["max_bin_id"],
            lock_duration_in_slot=obj["lock_duration_in_slot"],
        )
