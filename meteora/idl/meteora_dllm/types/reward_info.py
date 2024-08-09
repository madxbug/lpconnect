from __future__ import annotations

import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from construct import Container
from solders.pubkey import Pubkey


class RewardInfoJSON(typing.TypedDict):
    mint: str
    vault: str
    funder: str
    reward_duration: int
    reward_duration_end: int
    reward_rate: int
    last_update_time: int
    cumulative_seconds_with_empty_liquidity_reward: int


@dataclass
class RewardInfo:
    layout: typing.ClassVar = borsh.CStruct(
        "mint" / BorshPubkey,
        "vault" / BorshPubkey,
        "funder" / BorshPubkey,
        "reward_duration" / borsh.U64,
        "reward_duration_end" / borsh.U64,
        "reward_rate" / borsh.U128,
        "last_update_time" / borsh.U64,
        "cumulative_seconds_with_empty_liquidity_reward" / borsh.U64,
    )
    mint: Pubkey
    vault: Pubkey
    funder: Pubkey
    reward_duration: int
    reward_duration_end: int
    reward_rate: int
    last_update_time: int
    cumulative_seconds_with_empty_liquidity_reward: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "RewardInfo":
        return cls(
            mint=obj.mint,
            vault=obj.vault,
            funder=obj.funder,
            reward_duration=obj.reward_duration,
            reward_duration_end=obj.reward_duration_end,
            reward_rate=obj.reward_rate,
            last_update_time=obj.last_update_time,
            cumulative_seconds_with_empty_liquidity_reward=obj.cumulative_seconds_with_empty_liquidity_reward,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "mint": self.mint,
            "vault": self.vault,
            "funder": self.funder,
            "reward_duration": self.reward_duration,
            "reward_duration_end": self.reward_duration_end,
            "reward_rate": self.reward_rate,
            "last_update_time": self.last_update_time,
            "cumulative_seconds_with_empty_liquidity_reward": self.cumulative_seconds_with_empty_liquidity_reward,
        }

    def to_json(self) -> RewardInfoJSON:
        return {
            "mint": str(self.mint),
            "vault": str(self.vault),
            "funder": str(self.funder),
            "reward_duration": self.reward_duration,
            "reward_duration_end": self.reward_duration_end,
            "reward_rate": self.reward_rate,
            "last_update_time": self.last_update_time,
            "cumulative_seconds_with_empty_liquidity_reward": self.cumulative_seconds_with_empty_liquidity_reward,
        }

    @classmethod
    def from_json(cls, obj: RewardInfoJSON) -> "RewardInfo":
        return cls(
            mint=Pubkey.from_string(obj["mint"]),
            vault=Pubkey.from_string(obj["vault"]),
            funder=Pubkey.from_string(obj["funder"]),
            reward_duration=obj["reward_duration"],
            reward_duration_end=obj["reward_duration_end"],
            reward_rate=obj["reward_rate"],
            last_update_time=obj["last_update_time"],
            cumulative_seconds_with_empty_liquidity_reward=obj[
                "cumulative_seconds_with_empty_liquidity_reward"
            ],
        )
