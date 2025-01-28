from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Self

from config.constants import LPCONNECT
from libs.utils.base_storage import (
    BaseStorage, StorageConfig, StorageError,
    ValidationError, StorageOperationError, MsgPackable
)

logger = logging.getLogger(LPCONNECT)


@dataclass(frozen=True, slots=True)
class TokenPair:
    token_x: str
    token_y: str


@dataclass
class StorageState(MsgPackable):
    """State container implementing MsgPackable protocol"""
    VERSION: int = 1

    version: int = VERSION
    pairs: Dict[str, TokenPair] = field(default_factory=dict)  # lb_pair -> TokenPair
    token_pairs: Dict[str, Set[str]] = field(default_factory=lambda: {})  # token -> lb_pairs

    def to_msgpack(self) -> dict:
        """Serialize to msgpack format"""
        return {
            'version': self.version,
            'pairs': {
                lb_pair: {
                    'token_x': pair.token_x,
                    'token_y': pair.token_y
                }
                for lb_pair, pair in self.pairs.items()
            }
        }

    @classmethod
    def from_msgpack(cls, data: dict) -> Self:
        try:
            state = cls()
            state.version = data.get('version', cls.VERSION)

            # Rebuild pairs
            for lb_pair, pair_data in data.get('pairs', {}).items():
                token_x = pair_data['token_x']
                token_y = pair_data['token_y']
                pair = TokenPair(token_x=token_x, token_y=token_y)
                state.pairs[lb_pair] = pair

                # Rebuild derived indices
                for token in [token_x, token_y]:
                    if token not in state.token_pairs:
                        state.token_pairs[token] = set()
                    state.token_pairs[token].add(lb_pair)

            return state

        except Exception as e:
            raise StorageError(f"Failed to deserialize storage state: {e}")


class LBPairTokenStorage(BaseStorage[StorageState]):
    """LBPair token storage using improved base storage"""

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

    async def set_tokens(self, lb_pair: str, token_x: str, token_y: str) -> None:
        """Set token pair for an LB pair"""
        try:
            async with self._lock:
                if lb_pair in self.state.pairs:
                    old_pair = self.state.pairs[lb_pair]
                    self.state.token_pairs[old_pair.token_x].discard(lb_pair)
                    self.state.token_pairs[old_pair.token_y].discard(lb_pair)

                # Add new token pair
                new_pair = TokenPair(token_x=token_x, token_y=token_y)
                self.state.pairs[lb_pair] = new_pair

                # Update token indices
                for token in [token_x, token_y]:
                    if token not in self.state.token_pairs:
                        self.state.token_pairs[token] = set()
                    self.state.token_pairs[token].add(lb_pair)

                self._mark_modified()

        except Exception as e:
            raise StorageOperationError(f"Failed to set tokens: {e}")

    async def get_tokens(self, lb_pair: str) -> Tuple[Optional[str], Optional[str]]:
        """Get token pair for an LB pair"""
        try:
            if not lb_pair.strip():
                raise ValidationError("LB pair must be a non-empty string")

            pair = self.state.pairs.get(lb_pair)
            return (pair.token_x, pair.token_y) if pair else (None, None)

        except Exception as e:
            logger.error(f"Error getting tokens: {e}")
            return None, None

    async def get_pairs_by_token(self, token: str) -> Set[str]:
        """Get all LB pairs containing a token"""
        try:
            if not token.strip():
                raise ValidationError("Token must be a non-empty string")

            return self.state.token_pairs.get(token, set()).copy()

        except Exception as e:
            logger.error(f"Error getting pairs by token: {e}")
            return set()

    async def remove_pair(self, lb_pair: str) -> bool:
        """Remove an LB pair from storage"""
        try:
            if not lb_pair.strip():
                raise ValidationError("LB pair must be a non-empty string")

            async with self._lock:
                if lb_pair in self.state.pairs:
                    pair = self.state.pairs[lb_pair]
                    del self.state.pairs[lb_pair]

                    # Remove from token indices and cleanup empty sets
                    self.state.token_pairs[pair.token_x].discard(lb_pair)
                    self.state.token_pairs[pair.token_y].discard(lb_pair)

                    # Clean up empty token sets
                    if not self.state.token_pairs[pair.token_x]:
                        del self.state.token_pairs[pair.token_x]
                    if not self.state.token_pairs[pair.token_y]:
                        del self.state.token_pairs[pair.token_y]

                    self._mark_modified()
                    return True
                return False

        except Exception as e:
            logger.error(f"Error removing pair: {e}")
            return False
