import asyncio
import json
from typing import Dict, List

import aiofiles
from solders.pubkey import Pubkey

from .datatypes import ProcessedPosition, CachedPositionInfo


class PositionStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = asyncio.Lock()
        self._positions: Dict[Pubkey, Dict[Pubkey, CachedPositionInfo]] = {}

    async def load_positions(self):
        try:
            async with aiofiles.open(self.file_path, mode='r') as f:
                content = await f.read()
                string_dict = json.loads(content) if content else {}
                self._positions = {
                    Pubkey.from_string(k): {Pubkey.from_string(inner_k): CachedPositionInfo.from_json(v) for inner_k, v
                                            in inner_v.items()}
                    for k, inner_v in string_dict.items()
                }
        except FileNotFoundError:
            self._positions = {}

    async def _save_positions(self):
        string_dict = {
            str(k): {str(inner_k): v.to_json() for inner_k, v in inner_v.items()}
            for k, inner_v in self._positions.items()
        }
        async with aiofiles.open(self.file_path, mode='w') as f:
            await f.write(json.dumps(string_dict, indent=4))

    async def update(self, wallet: Pubkey, positions: List[ProcessedPosition]):
        async with self.lock:
            if wallet not in self._positions:
                self._positions[wallet] = {}
            for position in positions:
                self._positions[wallet][position.info.public_key] = CachedPositionInfo(
                    position.info.position.lb_pair, position.info.position.last_updated_at)
            await self._save_positions()

    async def get(self, wallet: Pubkey) -> Dict[Pubkey, CachedPositionInfo]:
        async with self.lock:
            return self._positions.get(wallet, {})

    async def delete(self, wallet: Pubkey, positions: List[Pubkey]):
        async with self.lock:
            for position in positions:
                del self._positions[wallet][position]
            await self._save_positions()
