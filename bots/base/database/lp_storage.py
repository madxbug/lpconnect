from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, List, Final, Self

from config.constants import LPCONNECT
from libs.utils.base_storage import (
    BaseStorage, StorageConfig, StorageError,
    ValidationError, StorageOperationError, MsgPackable
)

logger = logging.getLogger(LPCONNECT)


@dataclass(frozen=True, slots=True)
class PositionKey:
    token_x: str
    token_y: str
    owner: str
    pool: str

    @classmethod
    def validate(cls, token_x: str, token_y: str, owner: str, pool: str) -> None:
        """Validate position key components"""
        if not all(isinstance(x, str) for x in [token_x, token_y, owner, pool]):
            raise ValidationError("All position key components must be strings")
        if not all(x.strip() for x in [token_x, token_y, owner, pool]):
            raise ValidationError("All position key components must be non-empty strings")

    def to_key_string(self) -> str:
        """Convert to string representation for serialization"""
        return f"{self.token_x}:{self.token_y}:{self.owner}:{self.pool}"

    @classmethod
    def from_key_string(cls, key_str: str) -> Self:
        """Create from string representation"""
        try:
            token_x, token_y, owner, pool = key_str.split(":")
            return cls(token_x=token_x, token_y=token_y, owner=owner, pool=pool)
        except ValueError as e:
            raise ValidationError(f"Invalid position key format: {e}")


@dataclass(slots=True)
class ThreadInfo:
    thread_id: int
    needs_update: bool = False
    last_updated: float = 0.0

    @classmethod
    def validate(cls, thread_id: int) -> None:
        if not isinstance(thread_id, int) or thread_id < 0:
            raise ValidationError("Thread ID must be a non-negative integer")


@dataclass
class StorageState(MsgPackable):
    """State container implementing MsgPackable protocol"""
    VERSION: Final[int] = 1

    version: int = VERSION
    positions: Dict[PositionKey, int] = field(default_factory=dict)
    owner_pool_positions: Dict[Tuple[str, str], Set[PositionKey]] = field(
        default_factory=lambda: defaultdict(set)
    )
    token_positions: Dict[str, Set[PositionKey]] = field(
        default_factory=lambda: defaultdict(set)
    )
    token_pool_owners: Dict[Tuple[str, str], Dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int))
    )
    threads_info: Dict[str, ThreadInfo] = field(default_factory=dict)

    def to_msgpack(self) -> dict:
        """Serialize to msgpack format"""
        return {
            'version': self.version,
            'positions': {
                key.to_key_string(): value
                for key, value in self.positions.items()
            },
            'threads': {
                token: thread_info.thread_id
                for token, thread_info in self.threads_info.items()
            }
        }

    @classmethod
    def from_msgpack(cls, data: dict) -> Self:
        try:
            state = cls()
            state.version = data.get('version', cls.VERSION)

            # Rebuild positions
            for pos_key, count in data.get('positions', {}).items():
                key = PositionKey.from_key_string(pos_key)
                state.positions[key] = count
                # Rebuild derived indices
                state.owner_pool_positions[(key.owner, key.pool)].add(key)
                state.token_positions[key.token_x].add(key)
                state.token_positions[key.token_y].add(key)
                state.token_pool_owners[(key.token_x, key.pool)][key.owner] = count
                state.token_pool_owners[(key.token_y, key.pool)][key.owner] = count

            # Rebuild threads
            state.threads_info = {
                k: ThreadInfo(thread_id=v)
                for k, v in data.get('threads', {}).items()
            }

            return state

        except Exception as e:
            raise StorageError(f"Failed to deserialize storage state: {e}")


class LPStorage(BaseStorage[StorageState]):
    """Liquidity position storage using improved base storage"""

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

    # Position operations
    async def add_position(self, token_x: str, token_y: str, owner: str, pool: str) -> bool:
        """Add or increment a position"""
        try:
            PositionKey.validate(token_x, token_y, owner, pool)

            async with self._lock:
                key = PositionKey(token_x, token_y, owner, pool)
                is_new = key not in self.state.positions

                self.state.positions[key] = self.state.positions.get(key, 0) + 1
                count = self.state.positions[key]

                self.state.owner_pool_positions[(owner, pool)].add(key)
                self.state.token_positions[token_x].add(key)
                self.state.token_positions[token_y].add(key)
                self.state.token_pool_owners[(token_x, pool)][owner] = count
                self.state.token_pool_owners[(token_y, pool)][owner] = count

                self._mark_modified()
                return is_new

        except Exception as e:
            raise StorageOperationError(f"Failed to add position: {e}")

    async def remove_position(self, owner: str, pool: str) -> Tuple[Optional[Tuple[str, str]], bool]:
        """Remove or decrement a position"""
        async with self._lock:
            positions = self.state.owner_pool_positions.get((owner, pool), set())
            if not positions:
                return None, False

            for key in positions:
                if self.state.positions[key] > 0:
                    count = self.state.positions[key]
                    new_count = count - 1
                    self.state.positions[key] = new_count

                    was_deleted = new_count <= 0
                    if was_deleted:
                        del self.state.positions[key]
                        positions.remove(key)
                        self.state.token_positions[key.token_x].discard(key)
                        self.state.token_positions[key.token_y].discard(key)
                        del self.state.token_pool_owners[(key.token_x, pool)][owner]
                        del self.state.token_pool_owners[(key.token_y, pool)][owner]
                    else:
                        self.state.token_pool_owners[(key.token_x, pool)][owner] = new_count
                        self.state.token_pool_owners[(key.token_y, pool)][owner] = new_count

                    self._mark_modified()
                    return (key.token_x, key.token_y), was_deleted

            return None, False

    async def get_position_count(self, token_x: str, token_y: str, owner: str) -> int:
        """Get total position count for given tokens and owner"""
        try:
            return sum(
                count for key, count in self.state.positions.items()
                if key.token_x == token_x and key.token_y == token_y and key.owner == owner
            )
        except Exception as e:
            logger.error(f"Error getting position count: {e}")
            return 0

    async def get_unique_owners_count(self, token: str) -> int:
        """Get count of unique owners for a token"""
        try:
            return len({
                key.owner for key in self.state.token_positions[token]
                if self.state.positions.get(key, 0) > 0
            })
        except Exception as e:
            logger.error(f"Error getting unique owners count: {e}")
            return 0

    async def get_token_pools(self, token: str) -> Set[str]:
        """Get all pools for a token"""
        try:
            return {
                key.pool for key in self.state.token_positions[token]
                if self.state.positions.get(key, 0) > 0
            }
        except Exception as e:
            logger.error(f"Error getting token pools: {e}")
            return set()

    async def get_pool_users(self, token: str, pool: str) -> List[Tuple[str, int]]:
        """Get all users and their position counts for a token in a pool"""
        try:
            owners_dict = self.state.token_pool_owners[(token, pool)]
            return [
                (owner, count) for owner, count in sorted(owners_dict.items())
                if count > 0
            ]
        except Exception as e:
            logger.error(f"Error getting pool users: {e}")
            return []

    # Thread operations
    async def add_thread(self, token: str, thread_info: ThreadInfo) -> None:
        """Add or update a thread"""
        async with self._lock:
            self.state.threads_info[token] = thread_info
            self._mark_modified()

    async def remove_thread(self, token: str) -> None:
        """Remove a thread"""
        async with self._lock:
            if token in self.state.threads_info:
                del self.state.threads_info[token]
                self._mark_modified()

    async def get_thread(self, token: str) -> Optional[ThreadInfo]:
        """Get thread information"""
        return self.state.threads_info.get(token)

    async def update_thread_status(
            self, token: str, needs_update: bool, last_updated: float = None
    ) -> None:
        """Update thread status"""
        async with self._lock:
            if token in self.state.threads_info:
                self.state.threads_info[token].needs_update = needs_update
                if last_updated is not None:
                    self.state.threads_info[token].last_updated = last_updated
                self._mark_modified()

    async def get_all_threads(self) -> Dict[str, ThreadInfo]:
        """Get all threads"""
        return self.state.threads_info.copy()
