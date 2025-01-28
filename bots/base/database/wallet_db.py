from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Self

from config.constants import LPCONNECT
from libs.utils.base_storage import (
    BaseStorage, StorageConfig, StorageError,
    ValidationError, StorageOperationError, MsgPackable
)

logger = logging.getLogger(LPCONNECT)


@dataclass(frozen=True, slots=True)
class WalletKey:
    discord_id: str
    wallet_address: str

    @classmethod
    def validate(cls, discord_id: str, wallet_address: str) -> None:
        """Validate wallet key components"""
        if not all(isinstance(x, str) for x in [discord_id, wallet_address]):
            raise ValidationError("All wallet key components must be strings")
        if not all(x.strip() for x in [discord_id, wallet_address]):
            raise ValidationError("All wallet key components must be non-empty strings")

    def to_key_string(self) -> str:
        """Convert to string representation for serialization"""
        return f"{self.discord_id}:{self.wallet_address}"

    @classmethod
    def from_key_string(cls, key_str: str) -> Self:
        """Create from string representation"""
        try:
            discord_id, wallet_address = key_str.split(":", 1)
            return cls(discord_id=discord_id, wallet_address=wallet_address)
        except ValueError as e:
            raise ValidationError(f"Invalid wallet key format: {e}")


@dataclass
class StorageState(MsgPackable):
    """State container implementing MsgPackable protocol"""
    VERSION: int = 1

    version: int = VERSION
    wallets: Dict[WalletKey, bool] = field(default_factory=dict)  # bool represents is_anonymous
    discord_wallets: Dict[str, Set[WalletKey]] = field(default_factory=lambda: {})
    wallet_discord: Dict[str, str] = field(default_factory=dict)

    def to_msgpack(self) -> dict:
        """Serialize to msgpack format"""
        return {
            'version': self.version,
            'wallets': {
                key.to_key_string(): value
                for key, value in self.wallets.items()
            }
        }

    @classmethod
    def from_msgpack(cls, data: dict) -> Self:
        try:
            state = cls()
            state.version = data.get('version', cls.VERSION)

            # Rebuild wallets
            for wallet_key, is_anonymous in data.get('wallets', {}).items():
                key = WalletKey.from_key_string(wallet_key)
                state.wallets[key] = is_anonymous

                # Rebuild derived indices
                if key.discord_id not in state.discord_wallets:
                    state.discord_wallets[key.discord_id] = set()
                state.discord_wallets[key.discord_id].add(key)
                state.wallet_discord[key.wallet_address] = key.discord_id

            return state

        except Exception as e:
            raise StorageError(f"Failed to deserialize storage state: {e}")


class WalletStorage(BaseStorage[StorageState]):
    """Wallet storage using improved base storage"""

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

    async def add_wallet(self, discord_id: str, wallet_address: str, is_anonymous: bool = False) -> bool:
        """Add a wallet address for a discord user"""
        try:
            WalletKey.validate(discord_id, wallet_address)

            async with self._lock:
                key = WalletKey(discord_id, wallet_address)
                is_new = key not in self.state.wallets

                if is_new:
                    self.state.wallets[key] = is_anonymous

                    if discord_id not in self.state.discord_wallets:
                        self.state.discord_wallets[discord_id] = set()
                    self.state.discord_wallets[discord_id].add(key)

                    self.state.wallet_discord[wallet_address] = discord_id
                    self._mark_modified()

                return is_new

        except Exception as e:
            raise StorageOperationError(f"Failed to add wallet: {e}")

    async def remove_wallet(self, discord_id: str, wallet_address: str) -> bool:
        """Remove a wallet address for a discord user"""
        async with self._lock:
            key = WalletKey(discord_id, wallet_address)
            if key in self.state.wallets:
                del self.state.wallets[key]
                self.state.discord_wallets[discord_id].discard(key)
                del self.state.wallet_discord[wallet_address]
                self._mark_modified()
                return True
            return False

    async def get_user_wallets(self, discord_id: str) -> List[str]:
        """Get all wallet addresses for a discord user"""
        wallets = self.state.discord_wallets.get(discord_id, set())
        return [key.wallet_address for key in wallets]

    async def get_discord_id_by_wallet(self, wallet_address: str, default_value=None) -> Optional[str]:
        """Get discord ID associated with a wallet address"""
        return self.state.wallet_discord.get(wallet_address, default_value)

    async def wallet_exists(self, wallet_address: str) -> bool:
        """Check if a wallet address exists in storage"""
        return wallet_address in self.state.wallet_discord

    async def get_all_wallets(self) -> List[str]:
        """Get all unique wallet addresses"""
        return list(self.state.wallet_discord.keys())

    async def is_wallet_anonymous(self, wallet_address: str) -> bool:
        """Check if a wallet is set to anonymous mode"""
        discord_id = await self.get_discord_id_by_wallet(wallet_address)
        if discord_id:
            key = WalletKey(discord_id, wallet_address)
            return self.state.wallets.get(key, False)
        return False
