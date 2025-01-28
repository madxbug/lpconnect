import hashlib
from dataclasses import dataclass, fields
from enum import Enum
from typing import List, Dict, Type, TypeVar, Any

import base58
from construct import Struct, Int16sl, Int32sl, Int64ul, Bytes, Flag, Array, BytesInteger


class EventType(Enum):
    CompositionFee = "CompositionFee"
    AddLiquidity = "AddLiquidity"
    RemoveLiquidity = "RemoveLiquidity"
    Swap = "Swap"
    ClaimReward = "ClaimReward"
    FundReward = "FundReward"
    InitializeReward = "InitializeReward"
    UpdateRewardDuration = "UpdateRewardDuration"
    UpdateRewardFunder = "UpdateRewardFunder"
    PositionClose = "PositionClose"
    ClaimFee = "ClaimFee"
    LbPairCreate = "LbPairCreate"
    PositionCreate = "PositionCreate"
    FeeParameterUpdate = "FeeParameterUpdate"
    IncreaseObservation = "IncreaseObservation"
    WithdrawIneligibleReward = "WithdrawIneligibleReward"
    UpdatePositionOperator = "UpdatePositionOperator"
    UpdatePositionLockReleaseSlot = "UpdatePositionLockReleaseSlot"
    GoToABin = "GoToABin"


event_structures = {
    EventType.CompositionFee: Struct(
        "owner" / Bytes(32),
        "binId" / Int16sl,
        "tokenXFeeAmount" / Int64ul,
        "tokenYFeeAmount" / Int64ul,
        "protocolTokenXFeeAmount" / Int64ul,
        "protocolTokenYFeeAmount" / Int64ul
    ),
    EventType.AddLiquidity: Struct(
        "lbPair" / Bytes(32),
        "owner" / Bytes(32),
        "position" / Bytes(32),
        "amounts" / Array(2, Int64ul),
        "activeBinId" / Int32sl
    ),
    EventType.RemoveLiquidity: Struct(
        "lbPair" / Bytes(32),
        "owner" / Bytes(32),
        "position" / Bytes(32),
        "amounts" / Array(2, Int64ul),
        "activeBinId" / Int32sl
    ),
    EventType.Swap: Struct(
        "lbPair" / Bytes(32),
        "owner" / Bytes(32),
        "startBinId" / Int32sl,
        "endBinId" / Int32sl,
        "amountIn" / Int64ul,
        "amountOut" / Int64ul,
        "swapForY" / Flag,
        "fee" / Int64ul,
        "protocolFee" / Int64ul,
        "feeBps" / BytesInteger(16, swapped=True),
        "hostFee" / Int64ul
    ),
    EventType.ClaimReward: Struct(
        "lbPair" / Bytes(32),
        "position" / Bytes(32),
        "owner" / Bytes(32),
        "rewardIndex" / Int64ul,
        "totalReward" / Int64ul
    ),
    EventType.FundReward: Struct(
        "lbPair" / Bytes(32),
        "funder" / Bytes(32),
        "rewardIndex" / Int64ul,
        "amount" / Int64ul
    ),
    EventType.InitializeReward: Struct(
        "lbPair" / Bytes(32),
        "rewardMint" / Bytes(32),
        "funder" / Bytes(32),
        "rewardIndex" / Int64ul,
        "rewardDuration" / Int64ul
    ),
    EventType.UpdateRewardDuration: Struct(
        "lbPair" / Bytes(32),
        "rewardIndex" / Int64ul,
        "oldRewardDuration" / Int64ul,
        "newRewardDuration" / Int64ul
    ),
    EventType.UpdateRewardFunder: Struct(
        "lbPair" / Bytes(32),
        "rewardIndex" / Int64ul,
        "oldFunder" / Bytes(32),
        "newFunder" / Bytes(32)
    ),
    EventType.PositionClose: Struct(
        "position" / Bytes(32),
        "owner" / Bytes(32)
    ),
    EventType.ClaimFee: Struct(
        "lbPair" / Bytes(32),
        "position" / Bytes(32),
        "owner" / Bytes(32),
        "feeX" / Int64ul,
        "feeY" / Int64ul
    ),
    EventType.LbPairCreate: Struct(
        "lbPair" / Bytes(32),
        "binStep" / Int16sl,
        "tokenX" / Bytes(32),
        "tokenY" / Bytes(32)
    ),
    EventType.PositionCreate: Struct(
        "lbPair" / Bytes(32),
        "position" / Bytes(32),
        "owner" / Bytes(32)
    ),
    EventType.FeeParameterUpdate: Struct(
        "lbPair" / Bytes(32),
        "protocolShare" / Int16sl,
        "baseFactor" / Int16sl
    ),
    EventType.IncreaseObservation: Struct(
        "oracle" / Bytes(32),
        "newObservationLength" / Int64ul
    ),
    EventType.WithdrawIneligibleReward: Struct(
        "lbPair" / Bytes(32),
        "rewardMint" / Bytes(32),
        "amount" / Int64ul
    ),
    EventType.UpdatePositionOperator: Struct(
        "position" / Bytes(32),
        "oldOperator" / Bytes(32),
        "newOperator" / Bytes(32)
    ),
    EventType.UpdatePositionLockReleaseSlot: Struct(
        "position" / Bytes(32),
        "currentSlot" / Int64ul,
        "newLockReleaseSlot" / Int64ul,
        "oldLockReleaseSlot" / Int64ul,
        "sender" / Bytes(32)
    ),
    EventType.GoToABin: Struct(
        "lbPair" / Bytes(32),
        "fromBinId" / Int32sl,
        "toBinId" / Int32sl
    )
}


@dataclass
class DLMMEvent:
    block_time: int
    tx: str


@dataclass
class CompositionFeeEvent(DLMMEvent):
    owner: str
    binId: int
    tokenXFeeAmount: int
    tokenYFeeAmount: int
    protocolTokenXFeeAmount: int
    protocolTokenYFeeAmount: int


@dataclass
class AddLiquidityEvent(DLMMEvent):
    lbPair: str
    owner: str
    position: str
    amounts: List[int]
    activeBinId: int


@dataclass
class RemoveLiquidityEvent(DLMMEvent):
    lbPair: str
    owner: str
    position: str
    amounts: List[int]
    activeBinId: int


@dataclass
class SwapEvent(DLMMEvent):
    lbPair: str
    owner: str
    startBinId: int
    endBinId: int
    amountIn: int
    amountOut: int
    swapForY: bool
    fee: int
    protocolFee: int
    feeBps: int
    hostFee: int


@dataclass
class ClaimRewardEvent(DLMMEvent):
    lbPair: str
    position: str
    owner: str
    rewardIndex: int
    totalReward: int


@dataclass
class FundRewardEvent(DLMMEvent):
    lbPair: str
    funder: str
    rewardIndex: int
    amount: int


@dataclass
class InitializeRewardEvent(DLMMEvent):
    lbPair: str
    rewardMint: str
    funder: str
    rewardIndex: int
    rewardDuration: int


@dataclass
class UpdateRewardDurationEvent(DLMMEvent):
    lbPair: str
    rewardIndex: int
    oldRewardDuration: int
    newRewardDuration: int


@dataclass
class UpdateRewardFunderEvent(DLMMEvent):
    lbPair: str
    rewardIndex: int
    oldFunder: str
    newFunder: str


@dataclass
class PositionCloseEvent(DLMMEvent):
    position: str
    owner: str


@dataclass
class ClaimFeeEvent(DLMMEvent):
    lbPair: str
    position: str
    owner: str
    feeX: int
    feeY: int


@dataclass
class LbPairCreateEvent(DLMMEvent):
    lbPair: str
    binStep: int
    tokenX: str
    tokenY: str


@dataclass
class PositionCreateEvent(DLMMEvent):
    lbPair: str
    position: str
    owner: str


@dataclass
class FeeParameterUpdateEvent(DLMMEvent):
    lbPair: str
    protocolShare: int
    baseFactor: int


@dataclass
class IncreaseObservationEvent(DLMMEvent):
    oracle: str
    newObservationLength: int


@dataclass
class WithdrawIneligibleRewardEvent(DLMMEvent):
    lbPair: str
    rewardMint: str
    amount: int


@dataclass
class UpdatePositionOperatorEvent(DLMMEvent):
    position: str
    oldOperator: str
    newOperator: str


@dataclass
class UpdatePositionLockReleaseSlotEvent(DLMMEvent):
    position: str
    currentSlot: int
    newLockReleaseSlot: int
    oldLockReleaseSlot: int
    sender: str


@dataclass
class GoToABinEvent(DLMMEvent):
    lbPair: str
    fromBinId: int
    toBinId: int


event_dataclasses: Dict[EventType, Type[DLMMEvent]] = {
    EventType.CompositionFee: CompositionFeeEvent,
    EventType.AddLiquidity: AddLiquidityEvent,
    EventType.RemoveLiquidity: RemoveLiquidityEvent,
    EventType.Swap: SwapEvent,
    EventType.ClaimReward: ClaimRewardEvent,
    EventType.FundReward: FundRewardEvent,
    EventType.InitializeReward: InitializeRewardEvent,
    EventType.UpdateRewardDuration: UpdateRewardDurationEvent,
    EventType.UpdateRewardFunder: UpdateRewardFunderEvent,
    EventType.PositionClose: PositionCloseEvent,
    EventType.ClaimFee: ClaimFeeEvent,
    EventType.LbPairCreate: LbPairCreateEvent,
    EventType.PositionCreate: PositionCreateEvent,
    EventType.FeeParameterUpdate: FeeParameterUpdateEvent,
    EventType.IncreaseObservation: IncreaseObservationEvent,
    EventType.WithdrawIneligibleReward: WithdrawIneligibleRewardEvent,
    EventType.UpdatePositionOperator: UpdatePositionOperatorEvent,
    EventType.UpdatePositionLockReleaseSlot: UpdatePositionLockReleaseSlotEvent,
    EventType.GoToABin: GoToABinEvent
}


def get_discriminator(event_name):
    discriminator_input = f"event:{event_name}".encode('utf-8')
    return hashlib.sha256(discriminator_input).digest()[:8]


T = TypeVar('T', bound=DLMMEvent)


def create_event_instance(event_class: Type[T],
                          block_time: int, tx: str,
                          decoded_event: Dict[str, Any]) -> T:
    field_mapping = {}
    for field_info in fields(event_class):
        field_name = field_info.name
        if field_name in ['block_time', 'tx']:
            continue
        field_mapping[field_name] = field_name

    constructor_args = {field_mapping.get(k, k): v for k, v in decoded_event.items()}

    missing_fields = set(field_mapping.values()) - set(constructor_args.keys())
    if missing_fields:
        raise ValueError(f"Missing fields for {event_class.__name__}: {missing_fields}")

    event_instance = event_class(block_time=block_time, tx=tx, **constructor_args)
    return event_instance


class EventDecoder:
    event_discriminators = {get_discriminator(event.value): event for event in event_structures.keys()}

    @classmethod
    def decode_event(cls, event_data, block_time: int, tx: str) -> DLMMEvent:
        if len(event_data) < 8:
            raise ValueError("Event data is too short to contain a discriminator.")

        discriminator = event_data[:8]
        event_type = cls.event_discriminators.get(discriminator)
        if not event_type:
            raise ValueError(f"Unknown event discriminator: {discriminator.hex()}")

        event_body = event_data[8:]
        structure = event_structures[event_type]
        parsed_event = structure.parse(event_body)

        decoded_event = {}
        for field, value in parsed_event.items():
            if field == '_io':
                continue
            if isinstance(value, bytes) and len(value) == 32:
                decoded_event[field] = base58.b58encode(value).decode('utf-8')
            elif isinstance(value, list):
                decoded_event[field] = [int(v) for v in value]
            elif isinstance(value, bytes):
                decoded_event[field] = value.decode('utf-8')
            elif isinstance(value, int):
                decoded_event[field] = int(value)
            elif isinstance(value, bool):
                decoded_event[field] = bool(value)
            else:
                decoded_event[field] = value

        event_class = event_dataclasses.get(event_type)
        if event_class is None:
            raise ValueError(f"No data class defined for event type {event_type}")
        event_instance = create_event_instance(event_class, block_time, tx, decoded_event)

        return event_instance
