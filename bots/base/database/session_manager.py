from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Self

import discord

from config.constants import LPCONNECT
from libs.utils.base_storage import (
    BaseStorage, StorageConfig, StorageError,
    ValidationError, StorageOperationError, MsgPackable
)

logger = logging.getLogger(LPCONNECT)


@dataclass(frozen=True, slots=True)
class SessionKey:
    lb_pair: str
    owner: str

    @classmethod
    def validate(cls, lb_pair: str, owner: str) -> None:
        """Validate session key components"""
        if not all(isinstance(x, str) for x in [lb_pair, owner]):
            raise ValidationError("All session key components must be strings")
        if not all(x.strip() for x in [lb_pair, owner]):
            raise ValidationError("All session key components must be non-empty strings")

    def to_key_string(self) -> str:
        """Convert to string representation for serialization"""
        return f"{self.lb_pair}:{self.owner}"

    @classmethod
    def from_key_string(cls, key_str: str) -> Self:
        """Create from string representation"""
        try:
            lb_pair, owner = key_str.split(":", 1)
            return cls(lb_pair=lb_pair, owner=owner)
        except ValueError as e:
            raise ValidationError(f"Invalid session key format: {e}")


@dataclass
class ThreadInfo:
    thread_id: int
    count: int = 1
    last_closed: Optional[float] = None
    main_message_id: Optional[int] = None
    placeholder_message_id: Optional[int] = None


@dataclass
class StorageState(MsgPackable):
    """State container implementing MsgPackable protocol"""
    VERSION: int = 1

    version: int = VERSION
    sessions: Dict[SessionKey, ThreadInfo] = field(default_factory=dict)
    lb_pair_sessions: Dict[str, Set[SessionKey]] = field(default_factory=lambda: {})
    owner_sessions: Dict[str, Set[SessionKey]] = field(default_factory=lambda: {})

    def to_msgpack(self) -> dict:
        """Serialize to msgpack format"""
        return {
            'version': self.version,
            'sessions': {
                key.to_key_string(): {
                    'thread_id': info.thread_id,
                    'count': info.count,
                    'last_closed': info.last_closed,
                    'main_message_id': info.main_message_id,
                    'placeholder_message_id': info.placeholder_message_id
                }
                for key, info in self.sessions.items()
            }
        }

    @classmethod
    def from_msgpack(cls, data: dict) -> Self:
        try:
            state = cls()
            state.version = data.get('version', cls.VERSION)

            # Rebuild sessions
            for session_key, info in data.get('sessions', {}).items():
                key = SessionKey.from_key_string(session_key)
                thread_info = ThreadInfo(
                    thread_id=info['thread_id'],
                    count=info['count'],
                    last_closed=info['last_closed'],
                    main_message_id=info['main_message_id'],
                    placeholder_message_id=info['placeholder_message_id']
                )
                state.sessions[key] = thread_info

                # Rebuild derived indices
                if key.lb_pair not in state.lb_pair_sessions:
                    state.lb_pair_sessions[key.lb_pair] = set()
                state.lb_pair_sessions[key.lb_pair].add(key)

                if key.owner not in state.owner_sessions:
                    state.owner_sessions[key.owner] = set()
                state.owner_sessions[key.owner].add(key)

            return state

        except Exception as e:
            raise StorageError(f"Failed to deserialize storage state: {e}")


class SessionStorage(BaseStorage[StorageState]):
    """Session storage using improved base storage"""

    def __init__(self, file_path: str | Path,
                 cleanup_timeout: int,
                 cleanup_manager=None,
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
        self.cleanup_manager = cleanup_manager
        self.cleanup_timeout = cleanup_timeout

    async def initialize(self, cleanup_manager=None) -> None:
        self.cleanup_manager = cleanup_manager
        await super().initialize()

    def create_empty_state(self) -> StorageState:
        """Create an empty storage state"""
        return StorageState()

    def state_from_msgpack(self, data: dict) -> StorageState:
        """Create state from msgpack data"""
        return StorageState.from_msgpack(data)

    async def get_thread(self, lb_pair: str, owner: str, discord_channel) -> Optional[discord.Thread]:
        """Get thread for a given lb_pair and owner"""
        try:
            SessionKey.validate(lb_pair, owner)
            key = SessionKey(lb_pair, owner)

            if key in self.state.sessions:
                thread_info = self.state.sessions[key]
                thread = discord_channel.get_thread(thread_info.thread_id)
                if thread:
                    return thread
            return None

        except Exception as e:
            logger.error(f"Failed to get thread: {e}")
            return None

    async def create_thread(self, lb_pair: str, owner: str, discord_channel, title: str,
                            main_message_id: Optional[int] = None,
                            placeholder_message_id: Optional[int] = None) -> discord.Thread:
        """Create a new thread"""
        try:
            SessionKey.validate(lb_pair, owner)

            async with self._lock:
                thread = await discord_channel.create_thread(
                    name=title,
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=10080  # 7 days
                )

                key = SessionKey(lb_pair, owner)
                thread_info = ThreadInfo(
                    thread_id=thread.id,
                    main_message_id=main_message_id,
                    placeholder_message_id=placeholder_message_id
                )

                self.state.sessions[key] = thread_info

                if lb_pair not in self.state.lb_pair_sessions:
                    self.state.lb_pair_sessions[lb_pair] = set()
                self.state.lb_pair_sessions[lb_pair].add(key)

                if owner not in self.state.owner_sessions:
                    self.state.owner_sessions[owner] = set()
                self.state.owner_sessions[owner].add(key)

                self._mark_modified()
                return thread

        except Exception as e:
            raise StorageOperationError(f"Failed to create thread: {e}")

    async def open_position(self, lb_pair: str, owner: str) -> None:
        """Increment position count for a session"""
        async with self._lock:
            key = SessionKey(lb_pair, owner)
            if key in self.state.sessions:
                self.state.sessions[key].count += 1
                self._mark_modified()
            else:
                logger.warning(f"Attempted to increment count for non-existent thread: {lb_pair}, {owner}")

    async def close_position(self, lb_pair: str, owner: str) -> None:
        """Decrement position count for a session"""
        async with self._lock:
            key = SessionKey(lb_pair, owner)
            if key in self.state.sessions:
                thread_info = self.state.sessions[key]
                if thread_info.count > 0:
                    thread_info.count -= 1
                    if thread_info.count == 0:
                        thread_info.last_closed = asyncio.get_running_loop().time()
                    self._mark_modified()
                else:
                    logger.warning(f"Attempting to close a position with count 0 for {lb_pair}, {owner}")
            else:
                logger.warning(f"No record found for {lb_pair}, {owner}")

    async def set_session_message_ids(self, lb_pair: str, owner: str,
                                      main_message_id: int,
                                      placeholder_message_id: int) -> None:
        """Update message IDs for a session"""
        async with self._lock:
            key = SessionKey(lb_pair, owner)
            if key in self.state.sessions:
                thread_info = self.state.sessions[key]
                thread_info.main_message_id = main_message_id
                thread_info.placeholder_message_id = placeholder_message_id
                self._mark_modified()
            else:
                logger.warning(f"Attempted to set message IDs for non-existent thread: {lb_pair}, {owner}")

    async def cleanup_old_sessions(self, discord_channel) -> None:
        """Clean up old sessions"""
        if not self.cleanup_manager:
            logger.warning("Cleanup manager not initialized")
            return

        async with self._lock:
            current_time = asyncio.get_running_loop().time()
            to_delete = []

            for key, thread_info in self.state.sessions.items():
                if (thread_info.count == 0 and
                        thread_info.last_closed is not None and
                        current_time - thread_info.last_closed > self.cleanup_timeout):

                    thread = discord_channel.get_thread(thread_info.thread_id)
                    if not thread:
                        logger.error(f"Could not find thread {thread_info.thread_id} for cleanup")
                        continue

                    await self.cleanup_manager.cleanup_session(
                        discord_channel,
                        thread_info.thread_id,
                        key.lb_pair,
                        key.owner,
                        thread_info.main_message_id,
                        thread_info.placeholder_message_id
                    )
                    to_delete.append(key)

            for key in to_delete:
                del self.state.sessions[key]
                self.state.lb_pair_sessions[key.lb_pair].discard(key)
                self.state.owner_sessions[key.owner].discard(key)

            if to_delete:
                self._mark_modified()
