from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional, Self

from config.constants import LPCONNECT
from libs.utils.base_storage import (
    BaseStorage, StorageConfig, StorageError,
    ValidationError, StorageOperationError, MsgPackable
)

logger = logging.getLogger(LPCONNECT)


@dataclass(frozen=True, slots=True)
class PerformanceKey:
    user: str
    session: int
    lb_pair: str
    position: str

    @classmethod
    def validate(cls, user: str, session: int, lb_pair: str, position: str) -> None:
        """Validate performance key components"""
        if not all(isinstance(x, str) for x in [user, lb_pair, position]):
            raise ValidationError("user, lb_pair, position performance key components must be strings")
        if not all(x.strip() for x in [user, lb_pair, position]):
            raise ValidationError("user, lb_pair, position performance key components must be non-empty strings")
        if not isinstance(session, int):
            raise ValidationError("session performance key components must be integer")

    def to_key_string(self) -> str:
        """Convert to string representation for serialization"""
        return f"{self.user}:{self.session}:{self.lb_pair}:{self.position}"

    @classmethod
    def from_key_string(cls, key_str: str) -> Self:
        """Create from string representation"""
        try:
            user, session, lb_pair, position = key_str.split(":")
            return cls(user=user, session=int(session), lb_pair=lb_pair, position=position)
        except ValueError as e:
            raise ValidationError(f"Invalid performance key format: {e}")


@dataclass
class TokenBalance:
    amount_x: Decimal = field(default_factory=lambda: Decimal('0'))
    amount_y: Decimal = field(default_factory=lambda: Decimal('0'))
    value_in_y: Decimal = field(default_factory=lambda: Decimal('0'))

    def to_dict(self) -> dict:
        return {
            'amount_x': str(self.amount_x),
            'amount_y': str(self.amount_y),
            'value_in_y': str(self.value_in_y)
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            amount_x=Decimal(data['amount_x']),
            amount_y=Decimal(data['amount_y']),
            value_in_y=Decimal(data['value_in_y'])
        )


@dataclass
class PositionPerformance:
    deposits: TokenBalance = field(default_factory=TokenBalance)
    withdrawals: TokenBalance = field(default_factory=TokenBalance)
    fees_earned: TokenBalance = field(default_factory=TokenBalance)

    def to_dict(self) -> dict:
        return {
            'deposits': self.deposits.to_dict(),
            'withdrawals': self.withdrawals.to_dict(),
            'fees_earned': self.fees_earned.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            deposits=TokenBalance.from_dict(data['deposits']),
            withdrawals=TokenBalance.from_dict(data['withdrawals']),
            fees_earned=TokenBalance.from_dict(data['fees_earned'])
        )

    def aggregate(self, other: 'PositionPerformance') -> None:
        """Aggregate another performance into this one"""
        self.deposits.amount_x += other.deposits.amount_x
        self.deposits.amount_y += other.deposits.amount_y
        self.deposits.value_in_y += other.deposits.value_in_y

        self.withdrawals.amount_x += other.withdrawals.amount_x
        self.withdrawals.amount_y += other.withdrawals.amount_y
        self.withdrawals.value_in_y += other.withdrawals.value_in_y

        self.fees_earned.amount_x += other.fees_earned.amount_x
        self.fees_earned.amount_y += other.fees_earned.amount_y
        self.fees_earned.value_in_y += other.fees_earned.value_in_y


@dataclass
class StorageState(MsgPackable):
    """State container implementing MsgPackable protocol"""
    VERSION: int = 1

    version: int = VERSION
    performances: Dict[PerformanceKey, PositionPerformance] = field(default_factory=dict)
    user_sessions: Dict[str, Dict[int, set[PerformanceKey]]] = field(
        default_factory=lambda: {}
    )
    session_pairs: Dict[int, Dict[str, set[PerformanceKey]]] = field(
        default_factory=lambda: {}
    )

    def to_msgpack(self) -> dict:
        """Serialize to msgpack format"""
        return {
            'version': self.version,
            'performances': {
                key.to_key_string(): perf.to_dict()
                for key, perf in self.performances.items()
            }
        }

    @classmethod
    def from_msgpack(cls, data: dict) -> Self:
        try:
            state = cls()
            state.version = data.get('version', cls.VERSION)

            # Rebuild performances
            for perf_key, perf_data in data.get('performances', {}).items():
                key = PerformanceKey.from_key_string(perf_key)
                performance = PositionPerformance.from_dict(perf_data)
                state.performances[key] = performance

                # Rebuild derived indices
                if key.user not in state.user_sessions:
                    state.user_sessions[key.user] = {}
                if key.session not in state.user_sessions[key.user]:
                    state.user_sessions[key.user][key.session] = set()
                state.user_sessions[key.user][key.session].add(key)

                if key.session not in state.session_pairs:
                    state.session_pairs[key.session] = {}
                if key.lb_pair not in state.session_pairs[key.session]:
                    state.session_pairs[key.session][key.lb_pair] = set()
                state.session_pairs[key.session][key.lb_pair].add(key)

            return state

        except Exception as e:
            raise StorageError(f"Failed to deserialize storage state: {e}")


class PositionPerformanceStorage(BaseStorage[StorageState]):
    """Position performance storage using improved base storage"""

    def __init__(self, file_path: str | Path,
                 save_interval: float = 5.0,
                 batch_size: int = 1000,
                 **kwargs):
        config = StorageConfig(
            file_path=Path(file_path),
            save_interval=save_interval,
            batch_size=batch_size,
            **kwargs
        )
        super().__init__(config)

    def create_empty_state(self) -> StorageState:
        """Create an empty storage state"""
        return StorageState()

    def state_from_msgpack(self, data: dict) -> StorageState:
        """Create state from msgpack data"""
        return StorageState.from_msgpack(data)

    async def update_position_performance(self, user: str, session: int, lb_pair: str,
                                          position: str, performance: PositionPerformance) -> None:
        """Update performance for a position"""
        try:
            PerformanceKey.validate(user, session, lb_pair, position)

            async with self._lock:
                key = PerformanceKey(user, session, lb_pair, position)
                self.state.performances[key] = performance

                # Update indices
                if user not in self.state.user_sessions:
                    self.state.user_sessions[user] = {}
                if session not in self.state.user_sessions[user]:
                    self.state.user_sessions[user][session] = set()
                self.state.user_sessions[user][session].add(key)

                if session not in self.state.session_pairs:
                    self.state.session_pairs[session] = {}
                if lb_pair not in self.state.session_pairs[session]:
                    self.state.session_pairs[session][lb_pair] = set()
                self.state.session_pairs[session][lb_pair].add(key)

                self._mark_modified()

        except Exception as e:
            raise StorageOperationError(f"Failed to update position performance: {e}")

    async def get_user_performance(self, user: str, session: Optional[int] = None) -> Dict[
        int, Dict[str, Dict[str, PositionPerformance]]]:
        """Get all performance data for a user, optionally filtered by session"""
        try:
            result = {}

            if session:
                sessions = {session: self.state.user_sessions.get(user, {}).get(session, set())}
            else:
                sessions = self.state.user_sessions.get(user, {})

            for sess, keys in sessions.items():
                result[sess] = {}
                for key in keys:
                    if key.lb_pair not in result[sess]:
                        result[sess][key.lb_pair] = {}
                    result[sess][key.lb_pair][key.position] = self.state.performances[key]

            return result

        except Exception as e:
            logger.error(f"Error getting user performance: {e}")
            return {}

    async def get_user_lbpair_performance(self, user: str, session: int, lb_pair: str) -> Dict[
        str, PositionPerformance]:
        """Get performance data for a specific user, session, and lb_pair"""
        try:
            result = {}
            keys = self.state.session_pairs.get(session, {}).get(lb_pair, set())

            for key in keys:
                if key.user == user:
                    result[key.position] = self.state.performances[key]

            return result

        except Exception as e:
            logger.error(f"Error getting user lb_pair performance: {e}")
            return {}

    async def get_aggregated_user_lbpair_performance(self, user: str, session: int,
                                                     lb_pair: str) -> PositionPerformance:
        """Get aggregated performance data for a specific user, session, and lb_pair"""
        try:
            positions_performance = await self.get_user_lbpair_performance(user, session, lb_pair)

            aggregated = PositionPerformance()
            for performance in positions_performance.values():
                aggregated.aggregate(performance)

            return aggregated

        except Exception as e:
            logger.error(f"Error getting aggregated performance: {e}")
            return PositionPerformance()

    async def cleanup_user_positions(self, user: str, session: Optional[int] = None) -> None:
        """Remove all positions for a user, optionally filtered by session"""
        async with self._lock:
            try:
                if session:
                    keys = self.state.user_sessions.get(user, {}).get(session, set()).copy()
                    for key in keys:
                        del self.state.performances[key]
                        self.state.user_sessions[user][session].discard(key)
                        self.state.session_pairs[session][key.lb_pair].discard(key)
                    if not self.state.session_pairs[session][key.lb_pair]:
                        del self.state.session_pairs[session][key.lb_pair]
                    if not self.state.user_sessions[user][session]:
                        del self.state.user_sessions[user][session]
                else:
                    sessions = self.state.user_sessions.get(user, {}).copy()
                    for sess, keys in sessions.items():
                        for key in keys:
                            del self.state.performances[key]
                            self.state.session_pairs[sess][key.lb_pair].discard(key)
                        if not self.state.session_pairs[sess][key.lb_pair]:
                            del self.state.session_pairs[sess][key.lb_pair]
                        del self.state.user_sessions[user][sess]
                    if user in self.state.user_sessions:
                        del self.state.user_sessions[user]

                self._mark_modified()

            except Exception as e:
                raise StorageOperationError(f"Failed to cleanup user positions: {e}")
