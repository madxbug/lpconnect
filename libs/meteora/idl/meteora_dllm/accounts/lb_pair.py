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
from ..types import ProtocolFeeJSON, ProtocolFee, protocol_fee


class LbPairJSON(typing.TypedDict):
    parameters: types.static_parameters.StaticParametersJSON
    v_parameters: types.variable_parameters.VariableParametersJSON
    bump_seed: list[int]
    bin_step_seed: list[int]
    pair_type: int
    active_id: int
    bin_step: int
    status: int
    require_base_factor_seed: int
    base_factor_seed: list[int]
    padding1: list[int]
    token_x_mint: str
    token_y_mint: str
    reserve_x: str
    reserve_y: str
    protocol_fee: ProtocolFeeJSON
    fee_owner: str
    reward_infos: list[types.reward_info.RewardInfoJSON]
    oracle: str
    bin_array_bitmap: list[int]
    last_updated_at: int
    whitelisted_wallet: str
    pre_activation_swap_address: str
    base_key: str
    activation_slot: int
    pre_activation_slot_duration: int
    padding2: list[int]
    lock_durations_in_slot: int
    creator: str
    reserved: list[int]


@dataclass
class LbPair:
    parameters: types.static_parameters.StaticParameters
    v_parameters: types.variable_parameters.VariableParameters
    bump_seed: list[int]
    bin_step_seed: list[int]
    pair_type: int
    active_id: int
    bin_step: int
    status: int
    require_base_factor_seed: int
    base_factor_seed: list[int]
    padding1: list[int]
    token_x_mint: Pubkey
    token_y_mint: Pubkey
    reserve_x: Pubkey
    reserve_y: Pubkey
    protocol_fee: ProtocolFee
    fee_owner: Pubkey
    reward_infos: list[types.reward_info.RewardInfo]
    oracle: Pubkey
    bin_array_bitmap: list[int]
    last_updated_at: int
    whitelisted_wallet: Pubkey
    pre_activation_swap_address: Pubkey
    base_key: Pubkey
    activation_slot: int
    pre_activation_slot_duration: int
    padding2: list[int]
    lock_durations_in_slot: int
    creator: Pubkey
    reserved: list[int]

    discriminator: typing.ClassVar = b"!\x0b1b\xb5e\xb1\r"
    layout: typing.ClassVar = borsh.CStruct(
        "parameters" / types.static_parameters.StaticParameters.layout,
        "v_parameters" / types.variable_parameters.VariableParameters.layout,
        "bump_seed" / borsh.U8[1],
        "bin_step_seed" / borsh.U8[2],
        "pair_type" / borsh.U8,
        "active_id" / borsh.I32,
        "bin_step" / borsh.U16,
        "status" / borsh.U8,
        "require_base_factor_seed" / borsh.U8,
        "base_factor_seed" / borsh.U8[2],
        "padding1" / borsh.U8[2],
        "token_x_mint" / BorshPubkey,
        "token_y_mint" / BorshPubkey,
        "reserve_x" / BorshPubkey,
        "reserve_y" / BorshPubkey,
        "protocol_fee" / ProtocolFee.layout,
        "fee_owner" / BorshPubkey,
        "reward_infos" / types.reward_info.RewardInfo.layout[2],
        "oracle" / BorshPubkey,
        "bin_array_bitmap" / borsh.U64[16],
        "last_updated_at" / borsh.I64,
        "whitelisted_wallet" / BorshPubkey,
        "pre_activation_swap_address" / BorshPubkey,
        "base_key" / BorshPubkey,
        "activation_slot" / borsh.U64,
        "pre_activation_slot_duration" / borsh.U64,
        "padding2" / borsh.U8[8],
        "lock_durations_in_slot" / borsh.U64,
        "creator" / BorshPubkey,
        "reserved" / borsh.U8[24],
    )

    @classmethod
    async def fetch(
            cls,
            conn: AsyncClient,
            address: Pubkey,
            commitment: typing.Optional[Commitment] = None,
            program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["LbPair"]:
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
    ) -> typing.List[typing.Optional["LbPair"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["LbPair"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "LbPair":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = LbPair.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            parameters=types.static_parameters.StaticParameters.from_decoded(
                dec.parameters
            ),
            v_parameters=types.variable_parameters.VariableParameters.from_decoded(
                dec.v_parameters
            ),
            bump_seed=dec.bump_seed,
            bin_step_seed=dec.bin_step_seed,
            pair_type=dec.pair_type,
            active_id=dec.active_id,
            bin_step=dec.bin_step,
            status=dec.status,
            require_base_factor_seed=dec.require_base_factor_seed,
            base_factor_seed=dec.base_factor_seed,
            padding1=dec.padding1,
            token_x_mint=dec.token_x_mint,
            token_y_mint=dec.token_y_mint,
            reserve_x=dec.reserve_x,
            reserve_y=dec.reserve_y,
            protocol_fee=protocol_fee.ProtocolFee.from_decoded(dec.protocol_fee),
            fee_owner=dec.fee_owner,
            reward_infos=list(
                map(
                    lambda item: types.reward_info.RewardInfo.from_decoded(item),
                    dec.reward_infos,
                )
            ),
            oracle=dec.oracle,
            bin_array_bitmap=dec.bin_array_bitmap,
            last_updated_at=dec.last_updated_at,
            whitelisted_wallet=dec.whitelisted_wallet,
            pre_activation_swap_address=dec.pre_activation_swap_address,
            base_key=dec.base_key,
            activation_slot=dec.activation_slot,
            pre_activation_slot_duration=dec.pre_activation_slot_duration,
            padding2=dec.padding2,
            lock_durations_in_slot=dec.lock_durations_in_slot,
            creator=dec.creator,
            reserved=dec.reserved,
        )

    def to_json(self) -> LbPairJSON:
        return {
            "parameters": self.parameters.to_json(),
            "v_parameters": self.v_parameters.to_json(),
            "bump_seed": self.bump_seed,
            "bin_step_seed": self.bin_step_seed,
            "pair_type": self.pair_type,
            "active_id": self.active_id,
            "bin_step": self.bin_step,
            "status": self.status,
            "require_base_factor_seed": self.require_base_factor_seed,
            "base_factor_seed": self.base_factor_seed,
            "padding1": self.padding1,
            "token_x_mint": str(self.token_x_mint),
            "token_y_mint": str(self.token_y_mint),
            "reserve_x": str(self.reserve_x),
            "reserve_y": str(self.reserve_y),
            "protocol_fee": self.protocol_fee.to_json(),
            "fee_owner": str(self.fee_owner),
            "reward_infos": list(map(lambda item: item.to_json(), self.reward_infos)),
            "oracle": str(self.oracle),
            "bin_array_bitmap": self.bin_array_bitmap,
            "last_updated_at": self.last_updated_at,
            "whitelisted_wallet": str(self.whitelisted_wallet),
            "pre_activation_swap_address": str(self.pre_activation_swap_address),
            "base_key": str(self.base_key),
            "activation_slot": self.activation_slot,
            "pre_activation_slot_duration": self.pre_activation_slot_duration,
            "padding2": self.padding2,
            "lock_durations_in_slot": self.lock_durations_in_slot,
            "creator": str(self.creator),
            "reserved": self.reserved,
        }

    @classmethod
    def from_json(cls, obj: LbPairJSON) -> "LbPair":
        return cls(
            parameters=types.static_parameters.StaticParameters.from_json(
                obj["parameters"]
            ),
            v_parameters=types.variable_parameters.VariableParameters.from_json(
                obj["v_parameters"]
            ),
            bump_seed=obj["bump_seed"],
            bin_step_seed=obj["bin_step_seed"],
            pair_type=obj["pair_type"],
            active_id=obj["active_id"],
            bin_step=obj["bin_step"],
            status=obj["status"],
            require_base_factor_seed=obj["require_base_factor_seed"],
            base_factor_seed=obj["base_factor_seed"],
            padding1=obj["padding1"],
            token_x_mint=Pubkey.from_string(obj["token_x_mint"]),
            token_y_mint=Pubkey.from_string(obj["token_y_mint"]),
            reserve_x=Pubkey.from_string(obj["reserve_x"]),
            reserve_y=Pubkey.from_string(obj["reserve_y"]),
            protocol_fee=protocol_fee.ProtocolFee.from_json(obj["protocol_fee"]),
            fee_owner=Pubkey.from_string(obj["fee_owner"]),
            reward_infos=list(
                map(
                    lambda item: types.reward_info.RewardInfo.from_json(item),
                    obj["reward_infos"],
                )
            ),
            oracle=Pubkey.from_string(obj["oracle"]),
            bin_array_bitmap=obj["bin_array_bitmap"],
            last_updated_at=obj["last_updated_at"],
            whitelisted_wallet=Pubkey.from_string(obj["whitelisted_wallet"]),
            pre_activation_swap_address=Pubkey.from_string(
                obj["pre_activation_swap_address"]
            ),
            base_key=Pubkey.from_string(obj["base_key"]),
            activation_slot=obj["activation_slot"],
            pre_activation_slot_duration=obj["pre_activation_slot_duration"],
            padding2=obj["padding2"],
            lock_durations_in_slot=obj["lock_durations_in_slot"],
            creator=Pubkey.from_string(obj["creator"]),
            reserved=obj["reserved"],
        )
