import typing
from dataclasses import dataclass

import borsh_construct as borsh
from construct import Container


class UserRewardInfoJSON(typing.TypedDict):
    reward_per_token_completes: list[int]
    reward_pendings: list[int]


@dataclass
class UserRewardInfo:
    layout: typing.ClassVar = borsh.CStruct(
        "reward_per_token_completes" / borsh.U128[2], "reward_pendings" / borsh.U64[2]
    )
    reward_per_token_completes: list[int]
    reward_pendings: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "UserRewardInfo":
        return cls(
            reward_per_token_completes=obj.reward_per_token_completes,
            reward_pendings=obj.reward_pendings,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "reward_per_token_completes": self.reward_per_token_completes,
            "reward_pendings": self.reward_pendings,
        }

    def to_json(self) -> UserRewardInfoJSON:
        return {
            "reward_per_token_completes": self.reward_per_token_completes,
            "reward_pendings": self.reward_pendings,
        }

    @classmethod
    def from_json(cls, obj: UserRewardInfoJSON) -> "UserRewardInfo":
        return cls(
            reward_per_token_completes=obj["reward_per_token_completes"],
            reward_pendings=obj["reward_pendings"],
        )
