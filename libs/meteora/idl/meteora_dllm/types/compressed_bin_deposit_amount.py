import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class CompressedBinDepositAmountJSON(typing.TypedDict):
    bin_id: int
    amount: int


@dataclass
class CompressedBinDepositAmount:
    layout: typing.ClassVar = borsh.CStruct("bin_id" / borsh.I32, "amount" / borsh.U32)
    bin_id: int
    amount: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "CompressedBinDepositAmount":
        return cls(bin_id=obj.bin_id, amount=obj.amount)

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"bin_id": self.bin_id, "amount": self.amount}

    def to_json(self) -> CompressedBinDepositAmountJSON:
        return {"bin_id": self.bin_id, "amount": self.amount}

    @classmethod
    def from_json(
            cls, obj: CompressedBinDepositAmountJSON
    ) -> "CompressedBinDepositAmount":
        return cls(bin_id=obj["bin_id"], amount=obj["amount"])
