import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.borsh_extension import EnumForCodegen


class SpotOneSideJSON(typing.TypedDict):
    kind: typing.Literal["SpotOneSide"]


class CurveOneSideJSON(typing.TypedDict):
    kind: typing.Literal["CurveOneSide"]


class BidAskOneSideJSON(typing.TypedDict):
    kind: typing.Literal["BidAskOneSide"]


class SpotBalancedJSON(typing.TypedDict):
    kind: typing.Literal["SpotBalanced"]


class CurveBalancedJSON(typing.TypedDict):
    kind: typing.Literal["CurveBalanced"]


class BidAskBalancedJSON(typing.TypedDict):
    kind: typing.Literal["BidAskBalanced"]


class SpotImBalancedJSON(typing.TypedDict):
    kind: typing.Literal["SpotImBalanced"]


class CurveImBalancedJSON(typing.TypedDict):
    kind: typing.Literal["CurveImBalanced"]


class BidAskImBalancedJSON(typing.TypedDict):
    kind: typing.Literal["BidAskImBalanced"]


@dataclass
class SpotOneSide:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "SpotOneSide"

    @classmethod
    def to_json(cls) -> SpotOneSideJSON:
        return SpotOneSideJSON(
            kind="SpotOneSide",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SpotOneSide": {},
        }


@dataclass
class CurveOneSide:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "CurveOneSide"

    @classmethod
    def to_json(cls) -> CurveOneSideJSON:
        return CurveOneSideJSON(
            kind="CurveOneSide",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "CurveOneSide": {},
        }


@dataclass
class BidAskOneSide:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "BidAskOneSide"

    @classmethod
    def to_json(cls) -> BidAskOneSideJSON:
        return BidAskOneSideJSON(
            kind="BidAskOneSide",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "BidAskOneSide": {},
        }


@dataclass
class SpotBalanced:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "SpotBalanced"

    @classmethod
    def to_json(cls) -> SpotBalancedJSON:
        return SpotBalancedJSON(
            kind="SpotBalanced",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SpotBalanced": {},
        }


@dataclass
class CurveBalanced:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "CurveBalanced"

    @classmethod
    def to_json(cls) -> CurveBalancedJSON:
        return CurveBalancedJSON(
            kind="CurveBalanced",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "CurveBalanced": {},
        }


@dataclass
class BidAskBalanced:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "BidAskBalanced"

    @classmethod
    def to_json(cls) -> BidAskBalancedJSON:
        return BidAskBalancedJSON(
            kind="BidAskBalanced",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "BidAskBalanced": {},
        }


@dataclass
class SpotImBalanced:
    discriminator: typing.ClassVar = 6
    kind: typing.ClassVar = "SpotImBalanced"

    @classmethod
    def to_json(cls) -> SpotImBalancedJSON:
        return SpotImBalancedJSON(
            kind="SpotImBalanced",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SpotImBalanced": {},
        }


@dataclass
class CurveImBalanced:
    discriminator: typing.ClassVar = 7
    kind: typing.ClassVar = "CurveImBalanced"

    @classmethod
    def to_json(cls) -> CurveImBalancedJSON:
        return CurveImBalancedJSON(
            kind="CurveImBalanced",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "CurveImBalanced": {},
        }


@dataclass
class BidAskImBalanced:
    discriminator: typing.ClassVar = 8
    kind: typing.ClassVar = "BidAskImBalanced"

    @classmethod
    def to_json(cls) -> BidAskImBalancedJSON:
        return BidAskImBalancedJSON(
            kind="BidAskImBalanced",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "BidAskImBalanced": {},
        }


StrategyTypeKind = typing.Union[
    SpotOneSide,
    CurveOneSide,
    BidAskOneSide,
    SpotBalanced,
    CurveBalanced,
    BidAskBalanced,
    SpotImBalanced,
    CurveImBalanced,
    BidAskImBalanced,
]
StrategyTypeJSON = typing.Union[
    SpotOneSideJSON,
    CurveOneSideJSON,
    BidAskOneSideJSON,
    SpotBalancedJSON,
    CurveBalancedJSON,
    BidAskBalancedJSON,
    SpotImBalancedJSON,
    CurveImBalancedJSON,
    BidAskImBalancedJSON,
]


def from_decoded(obj: dict) -> StrategyTypeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "SpotOneSide" in obj:
        return SpotOneSide()
    if "CurveOneSide" in obj:
        return CurveOneSide()
    if "BidAskOneSide" in obj:
        return BidAskOneSide()
    if "SpotBalanced" in obj:
        return SpotBalanced()
    if "CurveBalanced" in obj:
        return CurveBalanced()
    if "BidAskBalanced" in obj:
        return BidAskBalanced()
    if "SpotImBalanced" in obj:
        return SpotImBalanced()
    if "CurveImBalanced" in obj:
        return CurveImBalanced()
    if "BidAskImBalanced" in obj:
        return BidAskImBalanced()
    raise ValueError("Invalid enum object")


def from_json(obj: StrategyTypeJSON) -> StrategyTypeKind:
    if obj["kind"] == "SpotOneSide":
        return SpotOneSide()
    if obj["kind"] == "CurveOneSide":
        return CurveOneSide()
    if obj["kind"] == "BidAskOneSide":
        return BidAskOneSide()
    if obj["kind"] == "SpotBalanced":
        return SpotBalanced()
    if obj["kind"] == "CurveBalanced":
        return CurveBalanced()
    if obj["kind"] == "BidAskBalanced":
        return BidAskBalanced()
    if obj["kind"] == "SpotImBalanced":
        return SpotImBalanced()
    if obj["kind"] == "CurveImBalanced":
        return CurveImBalanced()
    if obj["kind"] == "BidAskImBalanced":
        return BidAskImBalanced()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "SpotOneSide" / borsh.CStruct(),
    "CurveOneSide" / borsh.CStruct(),
    "BidAskOneSide" / borsh.CStruct(),
    "SpotBalanced" / borsh.CStruct(),
    "CurveBalanced" / borsh.CStruct(),
    "BidAskBalanced" / borsh.CStruct(),
    "SpotImBalanced" / borsh.CStruct(),
    "CurveImBalanced" / borsh.CStruct(),
    "BidAskImBalanced" / borsh.CStruct(),
)
