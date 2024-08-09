import typing
from dataclasses import dataclass

import borsh_construct as borsh
from anchorpy.borsh_extension import BorshPubkey
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solders.pubkey import Pubkey

from .. import types
from ..program_id import PROGRAM_ID


class PositionJSON(typing.TypedDict):
    lb_pair: str
    owner: str
    liquidity_shares: list[int]
    reward_infos: list[types.user_reward_info.UserRewardInfoJSON]
    fee_infos: list[types.fee_info.FeeInfoJSON]
    lower_bin_id: int
    upper_bin_id: int
    last_updated_at: int
    total_claimed_fee_x_amount: int
    total_claimed_fee_y_amount: int
    total_claimed_rewards: list[int]
    reserved: list[int]


@dataclass
class Position:
    discriminator: typing.ClassVar = b"\xaa\xbc\x8f\xe4z@\xf7\xd0"
    layout: typing.ClassVar = borsh.CStruct(
        "lb_pair" / BorshPubkey,
        "owner" / BorshPubkey,
        "liquidity_shares" / borsh.U64[70],
        "reward_infos" / types.user_reward_info.UserRewardInfo.layout[70],
        "fee_infos" / types.fee_info.FeeInfo.layout[70],
        "lower_bin_id" / borsh.I32,
        "upper_bin_id" / borsh.I32,
        "last_updated_at" / borsh.I64,
        "total_claimed_fee_x_amount" / borsh.U64,
        "total_claimed_fee_y_amount" / borsh.U64,
        "total_claimed_rewards" / borsh.U64[2],
        "reserved" / borsh.U8[160],
    )
    lb_pair: Pubkey
    owner: Pubkey
    liquidity_shares: list[int]
    reward_infos: list[types.user_reward_info.UserRewardInfo]
    fee_infos: list[types.fee_info.FeeInfo]
    lower_bin_id: int
    upper_bin_id: int
    last_updated_at: int
    total_claimed_fee_x_amount: int
    total_claimed_fee_y_amount: int
    total_claimed_rewards: list[int]
    reserved: list[int]

    @classmethod
    async def fetch(
            cls,
            conn: AsyncClient,
            address: Pubkey,
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["Position"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
            cls,
            conn: AsyncClient,
            addresses: list[Pubkey],
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["Position"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["Position"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "Position":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = Position.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            lb_pair=dec.lb_pair,
            owner=dec.owner,
            liquidity_shares=dec.liquidity_shares,
            reward_infos=list(
                map(
                    lambda item: types.user_reward_info.UserRewardInfo.from_decoded(
                        item
                    ),
                    dec.reward_infos,
                )
            ),
            fee_infos=list(
                map(
                    lambda item: types.fee_info.FeeInfo.from_decoded(item),
                    dec.fee_infos,
                )
            ),
            lower_bin_id=dec.lower_bin_id,
            upper_bin_id=dec.upper_bin_id,
            last_updated_at=dec.last_updated_at,
            total_claimed_fee_x_amount=dec.total_claimed_fee_x_amount,
            total_claimed_fee_y_amount=dec.total_claimed_fee_y_amount,
            total_claimed_rewards=dec.total_claimed_rewards,
            reserved=dec.reserved,
        )

    def to_json(self) -> PositionJSON:
        return {
            "lb_pair": str(self.lb_pair),
            "owner": str(self.owner),
            "liquidity_shares": self.liquidity_shares,
            "reward_infos": list(map(lambda item: item.to_json(), self.reward_infos)),
            "fee_infos": list(map(lambda item: item.to_json(), self.fee_infos)),
            "lower_bin_id": self.lower_bin_id,
            "upper_bin_id": self.upper_bin_id,
            "last_updated_at": self.last_updated_at,
            "total_claimed_fee_x_amount": self.total_claimed_fee_x_amount,
            "total_claimed_fee_y_amount": self.total_claimed_fee_y_amount,
            "total_claimed_rewards": self.total_claimed_rewards,
            "reserved": self.reserved,
        }

    @classmethod
    def from_json(cls, obj: PositionJSON) -> "Position":
        return cls(
            lb_pair=Pubkey.from_string(obj["lb_pair"]),
            owner=Pubkey.from_string(obj["owner"]),
            liquidity_shares=obj["liquidity_shares"],
            reward_infos=list(
                map(
                    lambda item: types.user_reward_info.UserRewardInfo.from_json(item),
                    obj["reward_infos"],
                )
            ),
            fee_infos=list(
                map(
                    lambda item: types.fee_info.FeeInfo.from_json(item),
                    obj["fee_infos"],
                )
            ),
            lower_bin_id=obj["lower_bin_id"],
            upper_bin_id=obj["upper_bin_id"],
            last_updated_at=obj["last_updated_at"],
            total_claimed_fee_x_amount=obj["total_claimed_fee_x_amount"],
            total_claimed_fee_y_amount=obj["total_claimed_fee_y_amount"],
            total_claimed_rewards=obj["total_claimed_rewards"],
            reserved=obj["reserved"],
        )
