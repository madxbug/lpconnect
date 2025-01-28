import asyncio
import time
from typing import Optional, Callable

import discord

from libs.meteora.idl.meteora_dllm.events.decoder import PositionCloseEvent


class CloseEventQueue:
    """Manages a queue of close position events with controlled processing."""

    def __init__(self, handler_fn: Callable, max_workers: int = 10):
        """Initialize the queue with a maximum number of concurrent workers."""
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.handler_fn = handler_fn

    async def add_event(self, event: PositionCloseEvent,
                        discord_channel: discord.TextChannel,
                        is_anonymous: bool) -> None:
        """Add a close position event to the queue and start processing if needed."""
        await self.queue.put((event, discord_channel, is_anonymous, time.time()))
        if self.processing_task is None or self.processing_task.done():
            self.processing_task = asyncio.create_task(self.process_queue())

    async def process_queue(self) -> None:
        """Process events in the queue, waiting if necessary before processing each event."""
        while not self.queue.empty():
            event, discord_channel, is_anonymous, arrival_time = await self.queue.get()
            current_time = time.time()
            wait_time = max(60 - (current_time - arrival_time), 0)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            await self.process_event(event, discord_channel, is_anonymous)

    async def process_event(self, event: PositionCloseEvent,
                            discord_channel: discord.TextChannel,
                            is_anonymous: bool) -> None:
        """Process a single close position event, using a semaphore to limit concurrent processing."""
        async with self.semaphore:
            await self.handler_fn(event, discord_channel, is_anonymous)
