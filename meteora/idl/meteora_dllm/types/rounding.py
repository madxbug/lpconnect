from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.borsh_extension import EnumForCodegen


class UpJSON(typing.TypedDict):
    kind: typing.Literal["Up"]


class DownJSON(typing.TypedDict):
    kind: typing.Literal["Down"]


@dataclass
class Up:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Up"

    @classmethod
    def to_json(cls) -> UpJSON:
        return UpJSON(
            kind="Up",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Up": {},
        }


@dataclass
class Down:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Down"

    @classmethod
    def to_json(cls) -> DownJSON:
        return DownJSON(
            kind="Down",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Down": {},
        }


RoundingKind = typing.Union[Up, Down]
RoundingJSON = typing.Union[UpJSON, DownJSON]


def from_decoded(obj: dict) -> RoundingKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Up" in obj:
        return Up()
    if "Down" in obj:
        return Down()
    raise ValueError("Invalid enum object")


def from_json(obj: RoundingJSON) -> RoundingKind:
    if obj["kind"] == "Up":
        return Up()
    if obj["kind"] == "Down":
        return Down()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("Up" / borsh.CStruct(), "Down" / borsh.CStruct())
