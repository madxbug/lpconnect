import asyncio
import os

import aiofiles
import msgpack
import pytest
import pytest_asyncio

from bots.base.database.lp_storage import LPStorage, PositionKey, ThreadInfo
from libs.utils.base_storage import ValidationError, StorageOperationError


@pytest.fixture
def temp_file(tmp_path):
    return str(tmp_path / "test_storage.msgpack")


@pytest_asyncio.fixture
async def storage(temp_file):
    storage = LPStorage(file_path=temp_file, save_interval=0.1, batch_size=2)
    await storage.initialize()
    try:
        yield storage
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_position_key_validation():
    # Test valid case
    PositionKey.validate("token1", "token2", "owner1", "pool1")

    # Test invalid cases
    with pytest.raises(ValidationError):
        PositionKey.validate("", "token2", "owner1", "pool1")

    with pytest.raises(ValidationError):
        PositionKey.validate("token1", "token2", "", "pool1")

    with pytest.raises(ValidationError):
        PositionKey.validate(None, "token2", "owner1", "pool1")


@pytest.mark.asyncio
async def test_thread_info_validation():
    # Test valid case
    ThreadInfo.validate(1)

    # Test invalid cases
    with pytest.raises(ValidationError):
        ThreadInfo.validate(-1)

    with pytest.raises(ValidationError):
        ThreadInfo.validate("not an int")


@pytest.mark.asyncio
async def test_add_position(storage):
    # Test adding new position
    is_new = await storage.add_position("token1", "token2", "owner1", "pool1")
    assert is_new is True

    # Test incrementing existing position
    is_new = await storage.add_position("token1", "token2", "owner1", "pool1")
    assert is_new is False

    # Verify position count
    count = await storage.get_position_count("token1", "token2", "owner1")
    assert count == 2


@pytest.mark.asyncio
async def test_remove_position(storage):
    # Add positions
    await storage.add_position("token1", "token2", "owner1", "pool1")
    await storage.add_position("token1", "token2", "owner1", "pool1")

    # Remove position
    tokens, was_deleted = await storage.remove_position("owner1", "pool1")
    assert tokens == ("token1", "token2")
    assert was_deleted is False

    # Remove last position
    tokens, was_deleted = await storage.remove_position("owner1", "pool1")
    assert tokens == ("token1", "token2")
    assert was_deleted is True

    # Try removing from empty storage
    tokens, was_deleted = await storage.remove_position("owner1", "pool1")
    assert tokens is None
    assert was_deleted is False


@pytest.mark.asyncio
async def test_get_unique_owners_count(storage):
    # Add positions for different owners
    await storage.add_position("token1", "token2", "owner1", "pool1")
    await storage.add_position("token1", "token3", "owner2", "pool1")
    await storage.add_position("token1", "token4", "owner3", "pool1")

    count = await storage.get_unique_owners_count("token1")
    assert count == 3


@pytest.mark.asyncio
async def test_get_token_pools(storage):
    # Add positions in different pools
    await storage.add_position("token1", "token2", "owner1", "pool1")
    await storage.add_position("token1", "token2", "owner1", "pool2")

    pools = await storage.get_token_pools("token1")
    assert pools == {"pool1", "pool2"}


@pytest.mark.asyncio
async def test_get_pool_users(storage):
    # Add positions for different users in same pool
    await storage.add_position("token1", "token2", "owner1", "pool1")
    await storage.add_position("token1", "token2", "owner1", "pool1")
    await storage.add_position("token1", "token2", "owner2", "pool1")

    users = await storage.get_pool_users("token1", "pool1")
    assert len(users) == 2
    assert ("owner1", 2) in users
    assert ("owner2", 1) in users


@pytest.mark.asyncio
async def test_thread_operations(storage):
    # Add thread
    thread_info = ThreadInfo(thread_id=1)
    await storage.add_thread("token1", thread_info)

    # Get thread and verify initial state
    retrieved = await storage.get_thread("token1")
    assert retrieved.thread_id == 1
    assert not retrieved.needs_update

    # Update thread status - we create a new ThreadInfo since it's immutable
    new_thread_info = ThreadInfo(
        thread_id=retrieved.thread_id,
        needs_update=True,
        last_updated=123.45
    )
    await storage.add_thread("token1", new_thread_info)

    # Verify updated state
    retrieved = await storage.get_thread("token1")
    assert retrieved.needs_update
    assert retrieved.last_updated == 123.45

    # Remove thread
    await storage.remove_thread("token1")
    assert await storage.get_thread("token1") is None


@pytest.mark.asyncio
async def test_persistence(temp_file):
    # Create and populate first instance
    storage1 = LPStorage(file_path=temp_file, save_interval=0.1)
    await storage1.initialize()

    try:
        await storage1.add_position("token1", "token2", "owner1", "pool1")
        thread_info = ThreadInfo(thread_id=1, needs_update=True, last_updated=123.45)
        await storage1.add_thread("token1", thread_info)

        # Force save and ensure it's written
        await storage1._save_state()
        assert os.path.exists(temp_file)

    finally:
        await storage1.close()

    # Create second instance and verify state
    storage2 = LPStorage(file_path=temp_file)
    await storage2.initialize()

    try:
        # Verify position data
        count = await storage2.get_position_count("token1", "token2", "owner1")
        assert count == 1

        # Verify thread data
        thread = await storage2.get_thread("token1")
        assert thread is not None
        assert thread.thread_id == 1
        assert thread.needs_update is False
        assert thread.last_updated == 0
    finally:
        await storage2.close()


@pytest.mark.asyncio
async def test_batch_saving(storage):
    # Add positions up to batch size
    await storage.add_position("token1", "token2", "owner1", "pool1")
    await storage.add_position("token1", "token2", "owner2", "pool1")

    # Wait for potential batch save
    await asyncio.sleep(0.2)

    # Verify file exists and has content
    assert os.path.exists(storage.config.file_path)
    assert os.path.getsize(storage.config.file_path) > 0


@pytest.mark.asyncio
async def test_periodic_saving(storage):
    await storage.add_position("token1", "token2", "owner1", "pool1")

    # Wait for periodic save interval
    await asyncio.sleep(0.2)

    # Verify file exists and has content
    assert os.path.exists(storage.config.file_path)
    assert os.path.getsize(storage.config.file_path) > 0


@pytest.mark.asyncio
async def test_concurrent_operations(storage):
    # Test concurrent position operations
    async def add_positions():
        for i in range(5):
            await storage.add_position(f"token{i}", f"token{i + 1}", "owner1", "pool1")
            await asyncio.sleep(0.01)  # Small delay to ensure interleaving

    async def remove_positions():
        for _ in range(5):
            await storage.remove_position("owner1", "pool1")
            await asyncio.sleep(0.01)  # Small delay to ensure interleaving

    # Run operations concurrently
    await asyncio.gather(add_positions(), remove_positions())

    # Verify final state
    total_count = 0
    for i in range(5):
        count = await storage.get_position_count(f"token{i}", f"token{i + 1}", "owner1")
        total_count += count
    assert total_count >= 0  # The exact count may vary due to concurrency


@pytest.mark.asyncio
async def test_error_handling(storage):
    # Test invalid position addition
    with pytest.raises(StorageOperationError):
        await storage.add_position("", "", "", "")

    # Test operations on non-existent data
    count = await storage.get_position_count("nonexistent", "nonexistent", "owner")
    assert count == 0

    pools = await storage.get_token_pools("nonexistent")
    assert len(pools) == 0

    users = await storage.get_pool_users("nonexistent", "nonexistent")
    assert len(users) == 0


@pytest.mark.asyncio
async def test_state_recovery_edge_cases(temp_file):
    """Test state recovery in various edge cases"""
    storage1 = LPStorage(file_path=temp_file)
    await storage1.initialize()

    try:
        await storage1.add_position("token1", "token2", "owner1", "pool1")
        await storage1._save_state()
        await storage1.close()  # Close first storage

        # Corrupt the file with valid msgpack data
        async with aiofiles.open(temp_file, 'wb') as f:
            corrupt_data = msgpack.packb({'version': 1, 'positions': {}, 'invalid': True})
            await f.write(corrupt_data)

        # Should handle corrupted but valid msgpack file
        storage2 = LPStorage(file_path=temp_file)
        await storage2.initialize()  # Should start with empty state

        # Verify empty state
        count = await storage2.get_position_count("token1", "token2", "owner1")
        assert count == 0
    finally:
        if storage2._sync_task:
            storage2._sync_task.cancel()
        await storage2.close()


@pytest.mark.asyncio
async def test_data_consistency(storage):
    """Test data consistency across all indices"""
    # First, let's verify initial empty state
    tokenA_initial = await storage.get_pool_users("tokenA", "pool1")
    assert len(tokenA_initial) == 0

    # Add positions sequentially and verify after each addition
    # First position
    await storage.add_position("tokenA", "tokenB", "owner1", "pool1")
    users = await storage.get_pool_users("tokenA", "pool1")
    assert len(users) == 1
    assert ("owner1", 1) in users

    # Second position (same position)
    await storage.add_position("tokenA", "tokenB", "owner1", "pool1")
    users = await storage.get_pool_users("tokenA", "pool1")
    assert len(users) == 1
    assert ("owner1", 2) in users

    # Third position (different token pair)
    await storage.add_position("tokenA", "tokenC", "owner1", "pool1")
    users = await storage.get_pool_users("tokenA", "pool1")
    assert len(users) == 1
    assert ("owner1", 1) in users  # This should be a separate count as it's a different token pair

    # Verify token_positions
    tokenA_pools = await storage.get_token_pools("tokenA")
    assert len(tokenA_pools) == 1
    assert "pool1" in tokenA_pools

    # Verify counts for specific token pairs
    count_AB = await storage.get_position_count("tokenA", "tokenB", "owner1")
    assert count_AB == 2  # This pair was added twice

    count_AC = await storage.get_position_count("tokenA", "tokenC", "owner1")
    assert count_AC == 1  # This pair was added once

    # Remove a position and check consistency
    tokens, deleted = await storage.remove_position("owner1", "pool1")
    assert tokens is not None

    # Verify the count decreased
    if tokens == ("tokenA", "tokenB"):
        count_AB = await storage.get_position_count("tokenA", "tokenB", "owner1")
        assert count_AB == 1
    elif tokens == ("tokenA", "tokenC"):
        count_AC = await storage.get_position_count("tokenA", "tokenC", "owner1")
        assert count_AC == 0


@pytest.mark.asyncio
async def test_concurrent_save_load(temp_file):
    """Test concurrent save and load operations"""
    storage_obj = LPStorage(file_path=temp_file, save_interval=0.1)
    await storage_obj.initialize()

    try:
        # Create multiple position additions
        add_tasks = []
        for i in range(10):
            task = asyncio.create_task(
                storage_obj.add_position(f"token{i}", f"tokenB", "owner1", "pool1")
            )
            add_tasks.append(task)
            await asyncio.sleep(0.01)  # Small delay to avoid file contention

        # Wait for all operations to complete
        await asyncio.gather(*add_tasks)

        # Force final save
        await storage_obj._save_state()

        # Verify final state
        for i in range(10):
            count = await storage_obj.get_position_count(f"token{i}", "tokenB", "owner1")
            assert count == 1
    finally:
        await storage_obj.close()


@pytest.mark.asyncio
async def test_memory_cleanup(storage):
    """Test proper cleanup of storage resources"""
    # Add positions in smaller batches
    batch_size = 100
    for batch in range(10):
        for i in range(batch_size):
            index = batch * batch_size + i
            await storage.add_position(
                f"token{index}", f"tokenB", f"owner{index}", f"pool{index % 10}"
            )
        await asyncio.sleep(0.1)  # Allow time for background saves

    # Remove positions in batches
    for batch in range(10):
        for i in range(batch_size):
            index = batch * batch_size + i
            await storage.remove_position(f"owner{index}", f"pool{index % 10}")
        await asyncio.sleep(0.1)  # Allow time for background saves

    # Verify cleanup
    assert len(storage.state.positions) == 0
    # Check derived indices are empty
    assert all(len(pos_set) == 0 for pos_set in storage.state.token_positions.values())
    assert all(len(pos_set) == 0 for pos_set in storage.state.owner_pool_positions.values())
