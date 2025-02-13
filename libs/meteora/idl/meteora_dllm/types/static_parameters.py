import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class StaticParametersJSON(typing.TypedDict):
    base_factor: int
    filter_period: int
    decay_period: int
    reduction_factor: int
    variable_fee_control: int
    max_volatility_accumulator: int
    min_bin_id: int
    max_bin_id: int
    protocol_share: int
    padding: list[int]


@dataclass
class StaticParameters:
    layout: typing.ClassVar = borsh.CStruct(
        "base_factor" / borsh.U16,
        "filter_period" / borsh.U16,
        "decay_period" / borsh.U16,
        "reduction_factor" / borsh.U16,
        "variable_fee_control" / borsh.U32,
        "max_volatility_accumulator" / borsh.U32,
        "min_bin_id" / borsh.I32,
        "max_bin_id" / borsh.I32,
        "protocol_share" / borsh.U16,
        "padding" / borsh.U8[6],
    )
    base_factor: int
    filter_period: int
    decay_period: int
    reduction_factor: int
    variable_fee_control: int
    max_volatility_accumulator: int
    min_bin_id: int
    max_bin_id: int
    protocol_share: int
    padding: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "StaticParameters":
        return cls(
            base_factor=obj.base_factor,
            filter_period=obj.filter_period,
            decay_period=obj.decay_period,
            reduction_factor=obj.reduction_factor,
            variable_fee_control=obj.variable_fee_control,
            max_volatility_accumulator=obj.max_volatility_accumulator,
            min_bin_id=obj.min_bin_id,
            max_bin_id=obj.max_bin_id,
            protocol_share=obj.protocol_share,
            padding=obj.padding,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "base_factor": self.base_factor,
            "filter_period": self.filter_period,
            "decay_period": self.decay_period,
            "reduction_factor": self.reduction_factor,
            "variable_fee_control": self.variable_fee_control,
            "max_volatility_accumulator": self.max_volatility_accumulator,
            "min_bin_id": self.min_bin_id,
            "max_bin_id": self.max_bin_id,
            "protocol_share": self.protocol_share,
            "padding": self.padding,
        }

    def to_json(self) -> StaticParametersJSON:
        return {
            "base_factor": self.base_factor,
            "filter_period": self.filter_period,
            "decay_period": self.decay_period,
            "reduction_factor": self.reduction_factor,
            "variable_fee_control": self.variable_fee_control,
            "max_volatility_accumulator": self.max_volatility_accumulator,
            "min_bin_id": self.min_bin_id,
            "max_bin_id": self.max_bin_id,
            "protocol_share": self.protocol_share,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: StaticParametersJSON) -> "StaticParameters":
        return cls(
            base_factor=obj["base_factor"],
            filter_period=obj["filter_period"],
            decay_period=obj["decay_period"],
            reduction_factor=obj["reduction_factor"],
            variable_fee_control=obj["variable_fee_control"],
            max_volatility_accumulator=obj["max_volatility_accumulator"],
            min_bin_id=obj["min_bin_id"],
            max_bin_id=obj["max_bin_id"],
            protocol_share=obj["protocol_share"],
            padding=obj["padding"],
        )
