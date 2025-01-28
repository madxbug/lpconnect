import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.borsh_extension import EnumForCodegen


class V0JSON(typing.TypedDict):
    kind: typing.Literal["V0"]


class V1JSON(typing.TypedDict):
    kind: typing.Literal["V1"]


@dataclass
class V0:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "V0"

    @classmethod
    def to_json(cls) -> V0JSON:
        return V0JSON(
            kind="V0",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "V0": {},
        }


@dataclass
class V1:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "V1"

    @classmethod
    def to_json(cls) -> V1JSON:
        return V1JSON(
            kind="V1",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "V1": {},
        }


LayoutVersionKind = typing.Union[V0, V1]
LayoutVersionJSON = typing.Union[V0JSON, V1JSON]


def from_decoded(obj: dict) -> LayoutVersionKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "V0" in obj:
        return V0()
    if "V1" in obj:
        return V1()
    raise ValueError("Invalid enum object")


def from_json(obj: LayoutVersionJSON) -> LayoutVersionKind:
    if obj["kind"] == "V0":
        return V0()
    if obj["kind"] == "V1":
        return V1()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("V0" / borsh.CStruct(), "V1" / borsh.CStruct())
