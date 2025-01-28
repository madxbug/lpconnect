from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Self

from config.constants import LPCONNECT
from libs.utils.base_storage import (
    BaseStorage, StorageConfig, StorageError,
    ValidationError, StorageOperationError, MsgPackable
)

logger = logging.getLogger(LPCONNECT)


@dataclass(frozen=True, slots=True)
class IndexKey:
    lb_pair: str
    user: str
    position: str

    @classmethod
    def validate(cls, lb_pair: str, user: str, position: str) -> None:
        """Validate index key components"""
        if not all(isinstance(x, str) for x in [lb_pair, user, position]):
            raise ValidationError("All index key components must be strings")
        if not all(x.strip() for x in [lb_pair, user, position]):
            raise ValidationError("All index key components must be non-empty strings")

    def to_key_string(self) -> str:
        """Convert to string representation for serialization"""
        return f"{self.lb_pair}:{self.user}:{self.position}"

    @classmethod
    def from_key_string(cls, key_str: str) -> Self:
        """Create from string representation"""
        try:
            lb_pair, user, position = key_str.split(":")
            return cls(lb_pair=lb_pair, user=user, position=position)
        except ValueError as e:
            raise ValidationError(f"Invalid index key format: {e}")


@dataclass
class StorageState(MsgPackable):
    """State container implementing MsgPackable protocol"""
    VERSION: int = 1

    version: int = VERSION
    indices: Dict[IndexKey, int] = field(default_factory=dict)
    lb_pair_users: Dict[str, Dict[str, Set[IndexKey]]] = field(
        default_factory=lambda: {}
    )
    max_indices: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: {}
    )

    def to_msgpack(self) -> dict:
        """Serialize to msgpack format"""
        return {
            'version': self.version,
            'indices': {
                key.to_key_string(): index
                for key, index in self.indices.items()
            },
            'max_indices': {
                lb_pair: {
                    user: max_idx
                    for user, max_idx in user_indices.items()
                }
                for lb_pair, user_indices in self.max_indices.items()
            }
        }

    @classmethod
    def from_msgpack(cls, data: dict) -> Self:
        try:
            state = cls()
            state.version = data.get('version', cls.VERSION)

            # Rebuild indices
            for idx_key, index in data.get('indices', {}).items():
                key = IndexKey.from_key_string(idx_key)
                state.indices[key] = index

                # Rebuild derived indices
                if key.lb_pair not in state.lb_pair_users:
                    state.lb_pair_users[key.lb_pair] = {}
                if key.user not in state.lb_pair_users[key.lb_pair]:
                    state.lb_pair_users[key.lb_pair][key.user] = set()
                state.lb_pair_users[key.lb_pair][key.user].add(key)

            # Rebuild max indices
            state.max_indices = data.get('max_indices', {})

            return state

        except Exception as e:
            raise StorageError(f"Failed to deserialize storage state: {e}")


class PositionIndexStorage(BaseStorage[StorageState]):
    """Position index storage using improved base storage"""

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

    async def get_position_index(self, lb_pair: str, user: str, position: str) -> Optional[int]:
        """Get index for a position"""
        try:
            IndexKey.validate(lb_pair, user, position)
            key = IndexKey(lb_pair, user, position)
            return self.state.indices.get(key)
        except Exception as e:
            logger.error(f"Error getting position index: {e}")
            return None

    async def create_position_index(self, lb_pair: str, user: str, position: str) -> int:
        """Create a new index for a position"""
        try:
            IndexKey.validate(lb_pair, user, position)

            async with self._lock:
                key = IndexKey(lb_pair, user, position)

                # Check if position already exists
                if key in self.state.indices:
                    logger.warning(f"Found existing position index for {key}")
                    return self.state.indices[key]

                # Get next available index
                if lb_pair not in self.state.max_indices:
                    self.state.max_indices[lb_pair] = {}
                if user not in self.state.max_indices[lb_pair]:
                    self.state.max_indices[lb_pair][user] = -1

                new_index = self.state.max_indices[lb_pair][user] + 1
                self.state.indices[key] = new_index
                self.state.max_indices[lb_pair][user] = new_index

                # Update user indices
                if lb_pair not in self.state.lb_pair_users:
                    self.state.lb_pair_users[lb_pair] = {}
                if user not in self.state.lb_pair_users[lb_pair]:
                    self.state.lb_pair_users[lb_pair][user] = set()
                self.state.lb_pair_users[lb_pair][user].add(key)

                self._mark_modified()
                return new_index

        except Exception as e:
            raise StorageOperationError(f"Failed to create position index: {e}")

    async def cleanup_lb_pair_positions(self, lb_pair: str, user: str) -> None:
        """Remove all positions for a lb_pair and user"""
        async with self._lock:
            try:
                if lb_pair in self.state.lb_pair_users and user in self.state.lb_pair_users[lb_pair]:
                    keys = self.state.lb_pair_users[lb_pair][user].copy()
                    for key in keys:
                        del self.state.indices[key]
                    del self.state.lb_pair_users[lb_pair][user]
                    if lb_pair in self.state.max_indices:
                        self.state.max_indices[lb_pair].pop(user, None)
                    if not self.state.lb_pair_users[lb_pair]:
                        del self.state.lb_pair_users[lb_pair]

                    if lb_pair in self.state.max_indices and not self.state.max_indices[lb_pair]:
                        del self.state.max_indices[lb_pair]

                    self._mark_modified()

            except Exception as e:
                raise StorageOperationError(f"Failed to cleanup positions: {e}")
