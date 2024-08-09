from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class BinJSON(typing.TypedDict):
    amount_x: int
    amount_y: int
    price: int
    liquidity_supply: int
    reward_per_token_stored: list[int]
    fee_amount_x_per_token_stored: int
    fee_amount_y_per_token_stored: int
    amount_x_in: int
    amount_y_in: int


@dataclass
class Bin:
    layout: typing.ClassVar = borsh.CStruct(
        "amount_x" / borsh.U64,
        "amount_y" / borsh.U64,
        "price" / borsh.U128,
        "liquidity_supply" / borsh.U128,
        "reward_per_token_stored" / borsh.U128[2],
        "fee_amount_x_per_token_stored" / borsh.U128,
        "fee_amount_y_per_token_stored" / borsh.U128,
        "amount_x_in" / borsh.U128,
        "amount_y_in" / borsh.U128,
    )
    amount_x: int
    amount_y: int
    price: int
    liquidity_supply: int
    reward_per_token_stored: list[int]
    fee_amount_x_per_token_stored: int
    fee_amount_y_per_token_stored: int
    amount_x_in: int
    amount_y_in: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "Bin":
        return cls(
            amount_x=obj.amount_x,
            amount_y=obj.amount_y,
            price=obj.price,
            liquidity_supply=obj.liquidity_supply,
            reward_per_token_stored=obj.reward_per_token_stored,
            fee_amount_x_per_token_stored=obj.fee_amount_x_per_token_stored,
            fee_amount_y_per_token_stored=obj.fee_amount_y_per_token_stored,
            amount_x_in=obj.amount_x_in,
            amount_y_in=obj.amount_y_in,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "amount_x": self.amount_x,
            "amount_y": self.amount_y,
            "price": self.price,
            "liquidity_supply": self.liquidity_supply,
            "reward_per_token_stored": self.reward_per_token_stored,
            "fee_amount_x_per_token_stored": self.fee_amount_x_per_token_stored,
            "fee_amount_y_per_token_stored": self.fee_amount_y_per_token_stored,
            "amount_x_in": self.amount_x_in,
            "amount_y_in": self.amount_y_in,
        }

    def to_json(self) -> BinJSON:
        return {
            "amount_x": self.amount_x,
            "amount_y": self.amount_y,
            "price": self.price,
            "liquidity_supply": self.liquidity_supply,
            "reward_per_token_stored": self.reward_per_token_stored,
            "fee_amount_x_per_token_stored": self.fee_amount_x_per_token_stored,
            "fee_amount_y_per_token_stored": self.fee_amount_y_per_token_stored,
            "amount_x_in": self.amount_x_in,
            "amount_y_in": self.amount_y_in,
        }

    @classmethod
    def from_json(cls, obj: BinJSON) -> "Bin":
        return cls(
            amount_x=obj["amount_x"],
            amount_y=obj["amount_y"],
            price=obj["price"],
            liquidity_supply=obj["liquidity_supply"],
            reward_per_token_stored=obj["reward_per_token_stored"],
            fee_amount_x_per_token_stored=obj["fee_amount_x_per_token_stored"],
            fee_amount_y_per_token_stored=obj["fee_amount_y_per_token_stored"],
            amount_x_in=obj["amount_x_in"],
            amount_y_in=obj["amount_y_in"],
        )
