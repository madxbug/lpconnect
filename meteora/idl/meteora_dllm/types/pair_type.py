from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.borsh_extension import EnumForCodegen


class PermissionlessJSON(typing.TypedDict):
    kind: typing.Literal["Permissionless"]


class PermissionJSON(typing.TypedDict):
    kind: typing.Literal["Permission"]


@dataclass
class Permissionless:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Permissionless"

    @classmethod
    def to_json(cls) -> PermissionlessJSON:
        return PermissionlessJSON(
            kind="Permissionless",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Permissionless": {},
        }


@dataclass
class Permission:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Permission"

    @classmethod
    def to_json(cls) -> PermissionJSON:
        return PermissionJSON(
            kind="Permission",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Permission": {},
        }


PairTypeKind = typing.Union[Permissionless, Permission]
PairTypeJSON = typing.Union[PermissionlessJSON, PermissionJSON]


def from_decoded(obj: dict) -> PairTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Permissionless" in obj:
        return Permissionless()
    if "Permission" in obj:
        return Permission()
    raise ValueError("Invalid enum object")


def from_json(obj: PairTypeJSON) -> PairTypeKind:
    if obj["kind"] == "Permissionless":
        return Permissionless()
    if obj["kind"] == "Permission":
        return Permission()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Permissionless" / borsh.CStruct(), "Permission" / borsh.CStruct()
)
