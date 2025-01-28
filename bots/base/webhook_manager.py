import asyncio
import datetime
import logging
import traceback
from collections import deque
from typing import Dict, Any, Protocol, runtime_checkable

from config.constants import LPCONNECT

logger = logging.getLogger(LPCONNECT)


@runtime_checkable
class TransactionProcessor(Protocol):
    async def process_transaction(self, transaction: Dict[str, Any]) -> None:
        """Process transaction"""


class WebhookManager:
    def __init__(self,
                 transaction_processor: TransactionProcessor,
                 max_queue_size: int = 10000,
                 num_workers: int = 5):
        """Initialize the WebhookManager."""
        self.incoming_queue = asyncio.Queue(maxsize=max_queue_size)
        self.processing_queue = asyncio.Queue()
        self.num_workers = num_workers
        self.workers = []
        self.is_running = False
        self.position_service = transaction_processor
        self.stats = {
            "received": 0,
            "processed": 0,
            "failed": 0,
            "queue_size": 0
        }
        self.recent_failures = deque(maxlen=100)

    async def start(self):
        """Start the webhook manager and create worker tasks."""
        logger.info("Starting WebhookManager...")
        self.is_running = True

        # Start worker tasks
        self.workers = [
            asyncio.create_task(self._process_queue(f"worker-{i}"))
            for i in range(self.num_workers)
        ]

        # Start queue manager
        self.queue_manager = asyncio.create_task(self._manage_queues())
        logger.info(f"Started {self.num_workers} workers")

    async def stop(self):
        """Gracefully stop the webhook manager."""
        logger.info("Stopping WebhookManager...")
        self.is_running = False

        # Wait for queues to empty
        await self.incoming_queue.join()
        await self.processing_queue.join()

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        self.queue_manager.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("WebhookManager stopped")

    async def add_webhook(self, content: Dict[str, Any]) -> bool:
        """Add a webhook to the processing queue."""
        try:
            self.stats["received"] += 1

            await asyncio.wait_for(
                self.incoming_queue.put(content),
                timeout=1.0
            )
            self.stats["queue_size"] = self.incoming_queue.qsize()
            return True
        except asyncio.TimeoutError:
            self.stats["failed"] += 1
            self.recent_failures.append({
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "reason": "Queue full",
                "queue_size": self.incoming_queue.qsize()
            })
            return False

    async def _manage_queues(self):
        """Move items from incoming queue to processing queue."""
        while self.is_running:
            try:
                content = await self.incoming_queue.get()
                await self.processing_queue.put(content)
                self.incoming_queue.task_done()
            except Exception as e:
                logger.error(f"Queue management error: {e}")
                await asyncio.sleep(1)

    async def _process_webhook(self, content: Any, worker_id: str):
        """Process webhook content."""
        try:
            if isinstance(content, dict):
                content = [content]
            elif not isinstance(content, list):
                logger.error(f"Unexpected content type: {type(content)}")
                return False

            tasks = [self.position_service.process_transaction(transaction)
                     for transaction in content]
            await asyncio.gather(*tasks)
            return True

        except Exception as e:
            logger.error(f"Worker {worker_id}: Error processing webhook: {e}")
            logger.error(traceback.format_exc())
            self.recent_failures.append({
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "reason": str(e),
                "worker": worker_id
            })
            return False

    async def _process_queue(self, worker_id: str):
        """Process items from the queue."""
        logger.info(f"Worker {worker_id} started")
        while self.is_running:
            try:
                content = await self.processing_queue.get()
                success = await self._process_webhook(content, worker_id)
                if success:
                    self.stats["processed"] += 1
                else:
                    self.stats["failed"] += 1
                self.processing_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id}: Processing error: {e}")
                await asyncio.sleep(1)
        logger.info(f"Worker {worker_id} stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current status and statistics."""
        return {
            "stats": self.stats,
            "is_running": self.is_running,
            "recent_failures": list(self.recent_failures),
            "incoming_queue_size": self.incoming_queue.qsize(),
            "processing_queue_size": self.processing_queue.qsize()
        }
