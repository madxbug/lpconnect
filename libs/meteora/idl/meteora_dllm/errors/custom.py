import typing

from anchorpy.error import ProgramError


class InvalidStartBinIndex(ProgramError):
    def __init__(self) -> None:
        super().__init__(6000, "Invalid start bin index")

    code = 6000
    name = "InvalidStartBinIndex"
    msg = "Invalid start bin index"


class InvalidBinId(ProgramError):
    def __init__(self) -> None:
        super().__init__(6001, "Invalid bin id")

    code = 6001
    name = "InvalidBinId"
    msg = "Invalid bin id"


class InvalidInput(ProgramError):
    def __init__(self) -> None:
        super().__init__(6002, "Invalid input data")

    code = 6002
    name = "InvalidInput"
    msg = "Invalid input data"


class ExceededAmountSlippageTolerance(ProgramError):
    def __init__(self) -> None:
        super().__init__(6003, "Exceeded amount slippage tolerance")

    code = 6003
    name = "ExceededAmountSlippageTolerance"
    msg = "Exceeded amount slippage tolerance"


class ExceededBinSlippageTolerance(ProgramError):
    def __init__(self) -> None:
        super().__init__(6004, "Exceeded bin slippage tolerance")

    code = 6004
    name = "ExceededBinSlippageTolerance"
    msg = "Exceeded bin slippage tolerance"


class CompositionFactorFlawed(ProgramError):
    def __init__(self) -> None:
        super().__init__(6005, "Composition factor flawed")

    code = 6005
    name = "CompositionFactorFlawed"
    msg = "Composition factor flawed"


class NonPresetBinStep(ProgramError):
    def __init__(self) -> None:
        super().__init__(6006, "Non preset bin step")

    code = 6006
    name = "NonPresetBinStep"
    msg = "Non preset bin step"


class ZeroLiquidity(ProgramError):
    def __init__(self) -> None:
        super().__init__(6007, "Zero liquidity")

    code = 6007
    name = "ZeroLiquidity"
    msg = "Zero liquidity"


class InvalidPosition(ProgramError):
    def __init__(self) -> None:
        super().__init__(6008, "Invalid position")

    code = 6008
    name = "InvalidPosition"
    msg = "Invalid position"


class BinArrayNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6009, "Bin array not found")

    code = 6009
    name = "BinArrayNotFound"
    msg = "Bin array not found"


class InvalidTokenMint(ProgramError):
    def __init__(self) -> None:
        super().__init__(6010, "Invalid token mint")

    code = 6010
    name = "InvalidTokenMint"
    msg = "Invalid token mint"


class InvalidAccountForSingleDeposit(ProgramError):
    def __init__(self) -> None:
        super().__init__(6011, "Invalid account for single deposit")

    code = 6011
    name = "InvalidAccountForSingleDeposit"
    msg = "Invalid account for single deposit"


class PairInsufficientLiquidity(ProgramError):
    def __init__(self) -> None:
        super().__init__(6012, "Pair insufficient liquidity")

    code = 6012
    name = "PairInsufficientLiquidity"
    msg = "Pair insufficient liquidity"


class InvalidFeeOwner(ProgramError):
    def __init__(self) -> None:
        super().__init__(6013, "Invalid fee owner")

    code = 6013
    name = "InvalidFeeOwner"
    msg = "Invalid fee owner"


class InvalidFeeWithdrawAmount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6014, "Invalid fee withdraw amount")

    code = 6014
    name = "InvalidFeeWithdrawAmount"
    msg = "Invalid fee withdraw amount"


class InvalidAdmin(ProgramError):
    def __init__(self) -> None:
        super().__init__(6015, "Invalid admin")

    code = 6015
    name = "InvalidAdmin"
    msg = "Invalid admin"


class IdenticalFeeOwner(ProgramError):
    def __init__(self) -> None:
        super().__init__(6016, "Identical fee owner")

    code = 6016
    name = "IdenticalFeeOwner"
    msg = "Identical fee owner"


class InvalidBps(ProgramError):
    def __init__(self) -> None:
        super().__init__(6017, "Invalid basis point")

    code = 6017
    name = "InvalidBps"
    msg = "Invalid basis point"


class MathOverflow(ProgramError):
    def __init__(self) -> None:
        super().__init__(6018, "Math operation overflow")

    code = 6018
    name = "MathOverflow"
    msg = "Math operation overflow"


class TypeCastFailed(ProgramError):
    def __init__(self) -> None:
        super().__init__(6019, "Type cast error")

    code = 6019
    name = "TypeCastFailed"
    msg = "Type cast error"


class InvalidRewardIndex(ProgramError):
    def __init__(self) -> None:
        super().__init__(6020, "Invalid reward index")

    code = 6020
    name = "InvalidRewardIndex"
    msg = "Invalid reward index"


class InvalidRewardDuration(ProgramError):
    def __init__(self) -> None:
        super().__init__(6021, "Invalid reward duration")

    code = 6021
    name = "InvalidRewardDuration"
    msg = "Invalid reward duration"


class RewardInitialized(ProgramError):
    def __init__(self) -> None:
        super().__init__(6022, "Reward already initialized")

    code = 6022
    name = "RewardInitialized"
    msg = "Reward already initialized"


class RewardUninitialized(ProgramError):
    def __init__(self) -> None:
        super().__init__(6023, "Reward not initialized")

    code = 6023
    name = "RewardUninitialized"
    msg = "Reward not initialized"


class IdenticalFunder(ProgramError):
    def __init__(self) -> None:
        super().__init__(6024, "Identical funder")

    code = 6024
    name = "IdenticalFunder"
    msg = "Identical funder"


class RewardCampaignInProgress(ProgramError):
    def __init__(self) -> None:
        super().__init__(6025, "Reward campaign in progress")

    code = 6025
    name = "RewardCampaignInProgress"
    msg = "Reward campaign in progress"


class IdenticalRewardDuration(ProgramError):
    def __init__(self) -> None:
        super().__init__(6026, "Reward duration is the same")

    code = 6026
    name = "IdenticalRewardDuration"
    msg = "Reward duration is the same"


class InvalidBinArray(ProgramError):
    def __init__(self) -> None:
        super().__init__(6027, "Invalid bin array")

    code = 6027
    name = "InvalidBinArray"
    msg = "Invalid bin array"


class NonContinuousBinArrays(ProgramError):
    def __init__(self) -> None:
        super().__init__(6028, "Bin arrays must be continuous")

    code = 6028
    name = "NonContinuousBinArrays"
    msg = "Bin arrays must be continuous"


class InvalidRewardVault(ProgramError):
    def __init__(self) -> None:
        super().__init__(6029, "Invalid reward vault")

    code = 6029
    name = "InvalidRewardVault"
    msg = "Invalid reward vault"


class NonEmptyPosition(ProgramError):
    def __init__(self) -> None:
        super().__init__(6030, "Position is not empty")

    code = 6030
    name = "NonEmptyPosition"
    msg = "Position is not empty"


class UnauthorizedAccess(ProgramError):
    def __init__(self) -> None:
        super().__init__(6031, "Unauthorized access")

    code = 6031
    name = "UnauthorizedAccess"
    msg = "Unauthorized access"


class InvalidFeeParameter(ProgramError):
    def __init__(self) -> None:
        super().__init__(6032, "Invalid fee parameter")

    code = 6032
    name = "InvalidFeeParameter"
    msg = "Invalid fee parameter"


class MissingOracle(ProgramError):
    def __init__(self) -> None:
        super().__init__(6033, "Missing oracle account")

    code = 6033
    name = "MissingOracle"
    msg = "Missing oracle account"


class InsufficientSample(ProgramError):
    def __init__(self) -> None:
        super().__init__(6034, "Insufficient observation sample")

    code = 6034
    name = "InsufficientSample"
    msg = "Insufficient observation sample"


class InvalidLookupTimestamp(ProgramError):
    def __init__(self) -> None:
        super().__init__(6035, "Invalid lookup timestamp")

    code = 6035
    name = "InvalidLookupTimestamp"
    msg = "Invalid lookup timestamp"


class BitmapExtensionAccountIsNotProvided(ProgramError):
    def __init__(self) -> None:
        super().__init__(6036, "Bitmap extension account is not provided")

    code = 6036
    name = "BitmapExtensionAccountIsNotProvided"
    msg = "Bitmap extension account is not provided"


class CannotFindNonZeroLiquidityBinArrayId(ProgramError):
    def __init__(self) -> None:
        super().__init__(6037, "Cannot find non-zero liquidity binArrayId")

    code = 6037
    name = "CannotFindNonZeroLiquidityBinArrayId"
    msg = "Cannot find non-zero liquidity binArrayId"


class BinIdOutOfBound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6038, "Bin id out of bound")

    code = 6038
    name = "BinIdOutOfBound"
    msg = "Bin id out of bound"


class InsufficientOutAmount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6039, "Insufficient amount in for minimum out")

    code = 6039
    name = "InsufficientOutAmount"
    msg = "Insufficient amount in for minimum out"


class InvalidPositionWidth(ProgramError):
    def __init__(self) -> None:
        super().__init__(6040, "Invalid position width")

    code = 6040
    name = "InvalidPositionWidth"
    msg = "Invalid position width"


class ExcessiveFeeUpdate(ProgramError):
    def __init__(self) -> None:
        super().__init__(6041, "Excessive fee update")

    code = 6041
    name = "ExcessiveFeeUpdate"
    msg = "Excessive fee update"


class PoolDisabled(ProgramError):
    def __init__(self) -> None:
        super().__init__(6042, "Pool disabled")

    code = 6042
    name = "PoolDisabled"
    msg = "Pool disabled"


class InvalidPoolType(ProgramError):
    def __init__(self) -> None:
        super().__init__(6043, "Invalid pool type")

    code = 6043
    name = "InvalidPoolType"
    msg = "Invalid pool type"


class ExceedMaxWhitelist(ProgramError):
    def __init__(self) -> None:
        super().__init__(6044, "Whitelist for wallet is full")

    code = 6044
    name = "ExceedMaxWhitelist"
    msg = "Whitelist for wallet is full"


class InvalidIndex(ProgramError):
    def __init__(self) -> None:
        super().__init__(6045, "Invalid index")

    code = 6045
    name = "InvalidIndex"
    msg = "Invalid index"


class RewardNotEnded(ProgramError):
    def __init__(self) -> None:
        super().__init__(6046, "Reward not ended")

    code = 6046
    name = "RewardNotEnded"
    msg = "Reward not ended"


class MustWithdrawnIneligibleReward(ProgramError):
    def __init__(self) -> None:
        super().__init__(6047, "Must withdraw ineligible reward")

    code = 6047
    name = "MustWithdrawnIneligibleReward"
    msg = "Must withdraw ineligible reward"


class UnauthorizedAddress(ProgramError):
    def __init__(self) -> None:
        super().__init__(6048, "Unauthorized address")

    code = 6048
    name = "UnauthorizedAddress"
    msg = "Unauthorized address"


class OperatorsAreTheSame(ProgramError):
    def __init__(self) -> None:
        super().__init__(6049, "Cannot update because operators are the same")

    code = 6049
    name = "OperatorsAreTheSame"
    msg = "Cannot update because operators are the same"


class WithdrawToWrongTokenAccount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6050, "Withdraw to wrong token account")

    code = 6050
    name = "WithdrawToWrongTokenAccount"
    msg = "Withdraw to wrong token account"


class WrongRentReceiver(ProgramError):
    def __init__(self) -> None:
        super().__init__(6051, "Wrong rent receiver")

    code = 6051
    name = "WrongRentReceiver"
    msg = "Wrong rent receiver"


class AlreadyPassActivationSlot(ProgramError):
    def __init__(self) -> None:
        super().__init__(6052, "Already activated")

    code = 6052
    name = "AlreadyPassActivationSlot"
    msg = "Already activated"


class LastSlotCannotBeSmallerThanActivateSlot(ProgramError):
    def __init__(self) -> None:
        super().__init__(6053, "Last slot cannot be smaller than activate slot")

    code = 6053
    name = "LastSlotCannotBeSmallerThanActivateSlot"
    msg = "Last slot cannot be smaller than activate slot"


class ExceedMaxSwappedAmount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6054, "Swapped amount is exceeded max swapped amount")

    code = 6054
    name = "ExceedMaxSwappedAmount"
    msg = "Swapped amount is exceeded max swapped amount"


class InvalidStrategyParameters(ProgramError):
    def __init__(self) -> None:
        super().__init__(6055, "Invalid strategy parameters")

    code = 6055
    name = "InvalidStrategyParameters"
    msg = "Invalid strategy parameters"


class LiquidityLocked(ProgramError):
    def __init__(self) -> None:
        super().__init__(6056, "Liquidity locked")

    code = 6056
    name = "LiquidityLocked"
    msg = "Liquidity locked"


class InvalidLockReleaseSlot(ProgramError):
    def __init__(self) -> None:
        super().__init__(6057, "Invalid lock release slot")

    code = 6057
    name = "InvalidLockReleaseSlot"
    msg = "Invalid lock release slot"


class BinRangeIsNotEmpty(ProgramError):
    def __init__(self) -> None:
        super().__init__(6058, "Bin range is not empty")

    code = 6058
    name = "BinRangeIsNotEmpty"
    msg = "Bin range is not empty"


CustomError = typing.Union[
    InvalidStartBinIndex,
    InvalidBinId,
    InvalidInput,
    ExceededAmountSlippageTolerance,
    ExceededBinSlippageTolerance,
    CompositionFactorFlawed,
    NonPresetBinStep,
    ZeroLiquidity,
    InvalidPosition,
    BinArrayNotFound,
    InvalidTokenMint,
    InvalidAccountForSingleDeposit,
    PairInsufficientLiquidity,
    InvalidFeeOwner,
    InvalidFeeWithdrawAmount,
    InvalidAdmin,
    IdenticalFeeOwner,
    InvalidBps,
    MathOverflow,
    TypeCastFailed,
    InvalidRewardIndex,
    InvalidRewardDuration,
    RewardInitialized,
    RewardUninitialized,
    IdenticalFunder,
    RewardCampaignInProgress,
    IdenticalRewardDuration,
    InvalidBinArray,
    NonContinuousBinArrays,
    InvalidRewardVault,
    NonEmptyPosition,
    UnauthorizedAccess,
    InvalidFeeParameter,
    MissingOracle,
    InsufficientSample,
    InvalidLookupTimestamp,
    BitmapExtensionAccountIsNotProvided,
    CannotFindNonZeroLiquidityBinArrayId,
    BinIdOutOfBound,
    InsufficientOutAmount,
    InvalidPositionWidth,
    ExcessiveFeeUpdate,
    PoolDisabled,
    InvalidPoolType,
    ExceedMaxWhitelist,
    InvalidIndex,
    RewardNotEnded,
    MustWithdrawnIneligibleReward,
    UnauthorizedAddress,
    OperatorsAreTheSame,
    WithdrawToWrongTokenAccount,
    WrongRentReceiver,
    AlreadyPassActivationSlot,
    LastSlotCannotBeSmallerThanActivateSlot,
    ExceedMaxSwappedAmount,
    InvalidStrategyParameters,
    LiquidityLocked,
    InvalidLockReleaseSlot,
    BinRangeIsNotEmpty,
]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    6000: InvalidStartBinIndex(),
    6001: InvalidBinId(),
    6002: InvalidInput(),
    6003: ExceededAmountSlippageTolerance(),
    6004: ExceededBinSlippageTolerance(),
    6005: CompositionFactorFlawed(),
    6006: NonPresetBinStep(),
    6007: ZeroLiquidity(),
    6008: InvalidPosition(),
    6009: BinArrayNotFound(),
    6010: InvalidTokenMint(),
    6011: InvalidAccountForSingleDeposit(),
    6012: PairInsufficientLiquidity(),
    6013: InvalidFeeOwner(),
    6014: InvalidFeeWithdrawAmount(),
    6015: InvalidAdmin(),
    6016: IdenticalFeeOwner(),
    6017: InvalidBps(),
    6018: MathOverflow(),
    6019: TypeCastFailed(),
    6020: InvalidRewardIndex(),
    6021: InvalidRewardDuration(),
    6022: RewardInitialized(),
    6023: RewardUninitialized(),
    6024: IdenticalFunder(),
    6025: RewardCampaignInProgress(),
    6026: IdenticalRewardDuration(),
    6027: InvalidBinArray(),
    6028: NonContinuousBinArrays(),
    6029: InvalidRewardVault(),
    6030: NonEmptyPosition(),
    6031: UnauthorizedAccess(),
    6032: InvalidFeeParameter(),
    6033: MissingOracle(),
    6034: InsufficientSample(),
    6035: InvalidLookupTimestamp(),
    6036: BitmapExtensionAccountIsNotProvided(),
    6037: CannotFindNonZeroLiquidityBinArrayId(),
    6038: BinIdOutOfBound(),
    6039: InsufficientOutAmount(),
    6040: InvalidPositionWidth(),
    6041: ExcessiveFeeUpdate(),
    6042: PoolDisabled(),
    6043: InvalidPoolType(),
    6044: ExceedMaxWhitelist(),
    6045: InvalidIndex(),
    6046: RewardNotEnded(),
    6047: MustWithdrawnIneligibleReward(),
    6048: UnauthorizedAddress(),
    6049: OperatorsAreTheSame(),
    6050: WithdrawToWrongTokenAccount(),
    6051: WrongRentReceiver(),
    6052: AlreadyPassActivationSlot(),
    6053: LastSlotCannotBeSmallerThanActivateSlot(),
    6054: ExceedMaxSwappedAmount(),
    6055: InvalidStrategyParameters(),
    6056: LiquidityLocked(),
    6057: InvalidLockReleaseSlot(),
    6058: BinRangeIsNotEmpty(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
