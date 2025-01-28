from __future__ import annotations

import abc
import asyncio
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar, Optional, Set, Final
from typing import Protocol, runtime_checkable

import aiofiles
import msgpack

from config.constants import LPCONNECT

logger = logging.getLogger(LPCONNECT)


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class ValidationError(StorageError):
    """Validation related errors"""
    pass


class StorageOperationError(StorageError):
    """Operation related errors"""
    pass


@runtime_checkable
class MsgPackable(Protocol):
    """Protocol for objects that can be serialized to msgpack"""

    def to_msgpack(self) -> dict: ...

    @classmethod
    def from_msgpack(cls, data: dict) -> MsgPackable: ...


StateT = TypeVar('StateT', bound=MsgPackable)  # Ensure state type implements MsgPackable protocol


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Configuration for storage behavior with validation"""
    file_path: Path
    save_interval: float = field(default=5.0)
    batch_size: int = field(default=1000)
    max_retries: int = field(default=3)
    retry_delay: float = field(default=0.1)
    temp_dir: Optional[Path] = field(default=None)
    save_retry_count: int = field(default=3)
    save_retry_delay: float = field(default=0.5)

    def __post_init__(self) -> None:
        if self.save_interval <= 0:
            raise ValidationError("save_interval must be positive")
        if self.batch_size <= 0:
            raise ValidationError("batch_size must be positive")
        if self.max_retries <= 0:
            raise ValidationError("max_retries must be positive")
        if self.retry_delay <= 0:
            raise ValidationError("retry_delay must be positive")


class BaseStorage(Generic[StateT], abc.ABC):
    """Base class for persistent storage implementations with improved safety"""

    # Class constants
    TEMP_PREFIX: Final[str] = 'storage_'
    TEMP_SUFFIX: Final[str] = '.tmp'

    def __init__(self, config: StorageConfig | str | Path) -> None:
        """Initialize storage with either a config object or a file path"""
        self.config = (StorageConfig(Path(config)) if isinstance(config, (str, Path))
                       else config)
        self._lock: asyncio.Lock = asyncio.Lock()
        self._sync_task: Optional[asyncio.Task] = None
        self._modified: bool = False
        self._last_save: float = 0.0
        self._changes_since_save: int = 0
        self._shutdown: bool = False
        self._pending_tasks: Set[asyncio.Task] = set()
        self.state: Optional[StateT] = None

    async def __aenter__(self) -> BaseStorage[StateT]:
        """Async context manager support"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure proper cleanup on context exit"""
        await self.close()

    @abc.abstractmethod
    def create_empty_state(self) -> StateT:
        """Create and return an empty state object"""
        ...

    async def initialize(self) -> None:
        """Initialize storage and start background save task"""
        try:
            await self._load_state()
            self._sync_task = asyncio.create_task(
                self._periodic_save(),
                name=f"periodic_save_{self.config.file_path.name}"
            )
        except Exception as e:
            raise StorageError(f"Failed to initialize storage: {e}") from e

    async def close(self) -> None:
        """Safely close storage and ensure final state save"""
        self._shutdown = True

        # Cancel and wait for sync task
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        # Wait for pending tasks with timeout
        if self._pending_tasks:
            done, pending = await asyncio.wait(
                self._pending_tasks,
                timeout=self.config.save_interval
            )
            for task in pending:
                task.cancel()

        # Final save
        try:
            async with self._lock:
                await self._save_state()
        except Exception as e:
            logger.error(f"Error during final save: {e}")
            raise

    async def _load_state(self) -> None:
        """Load state from file with improved error handling"""
        try:
            if not self.config.file_path.exists():
                self.state = self.create_empty_state()
                return

            async with asyncio.timeout(self.config.save_interval):
                async with aiofiles.open(self.config.file_path, 'rb') as f:
                    data = msgpack.unpackb(await f.read())
                    if not isinstance(data, dict):
                        raise ValidationError("Invalid state format")
                    self.state = self.state_from_msgpack(data)

        except (asyncio.TimeoutError, ValidationError) as e:
            logger.error(f"Error loading state: {e}")
            self.state = self.create_empty_state()
        except Exception as e:
            logger.error(f"Critical error loading state: {e}")
            raise StorageError(f"Failed to load state: {e}") from e

    async def _save_state(self) -> None:
        """Save state using temporary file with improved safety and retry logic"""
        if not self._modified or not self.state:
            return

        data = self.state_to_msgpack(self.state)
        packed_data = msgpack.packb(data)

        temp_dir = self.config.temp_dir or self.config.file_path.parent
        tmp_path = None

        for attempt in range(self.config.save_retry_count):
            try:
                # Use tempfile for atomic writes
                with tempfile.NamedTemporaryFile(
                        mode='wb',
                        prefix=self.TEMP_PREFIX,
                        suffix=self.TEMP_SUFFIX,
                        dir=temp_dir,
                        delete=False
                ) as tmp:
                    tmp_path = Path(tmp.name)
                    await asyncio.to_thread(tmp.write, packed_data)  # Write in a non-blocking way

                # Atomic rename with retries for Windows
                try:
                    tmp_path.replace(self.config.file_path)
                except PermissionError:
                    # On Windows, retry replace operation
                    await asyncio.sleep(self.config.save_retry_delay)
                    tmp_path.replace(self.config.file_path)

                self._modified = False
                self._changes_since_save = 0
                self._last_save = asyncio.get_running_loop().time()
                return

            except (IOError, OSError) as e:
                logger.warning(f"Save attempt {attempt + 1} failed: {e}")
                if attempt < self.config.save_retry_count - 1:
                    await asyncio.sleep(self.config.save_retry_delay)
                else:
                    raise StorageError(f"Failed to save state after {self.config.save_retry_count} attempts") from e
            finally:
                if tmp_path:
                    tmp_path.unlink(missing_ok=True)

    async def _periodic_save(self) -> None:
        """Periodically save state with improved error handling"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.config.save_interval)
                async with self._lock:
                    await self._save_state()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic save: {e}")
                await asyncio.sleep(1.0)  # Backoff on error

    def _mark_modified(self) -> None:
        """Mark state as modified and handle batch saves"""
        self._modified = True
        self._changes_since_save += 1

        if self._changes_since_save >= self.config.batch_size:
            task = asyncio.create_task(self._save_state())
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)

    async def acquire_lock(self) -> asyncio.Lock:
        """Acquire storage lock"""
        await self._lock.acquire()
        return self._lock

    def release_lock(self) -> None:
        """Release storage lock"""
        self._lock.release()

    def state_to_msgpack(self, state: StateT) -> dict:
        """Convert state to msgpack format"""
        return state.to_msgpack()

    @abc.abstractmethod
    def state_from_msgpack(self, data: dict) -> StateT:
        """Create state from msgpack data"""
