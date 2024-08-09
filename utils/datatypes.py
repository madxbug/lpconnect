import json
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Any

from solders.pubkey import Pubkey

from meteora.bin_array import PositionBinData
from meteora.get_positions import PositionInfo
from meteora.idl.meteora_dllm.accounts import LbPair


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


@dataclass
class ProcessedPosition:
    info: PositionInfo
    lb_pair_info: LbPair
    total_x_amount: Decimal
    total_y_amount: Decimal
    position_bin_data: List[PositionBinData]

    def to_json(self):
        return json.dumps({
            'info': self.info.to_json(),
            'lb_pair_info': self.lb_pair_info.to_json(),
            'total_x_amount': str(self.total_x_amount),
            'total_y_amount': str(self.total_y_amount),
            'position_bin_data': [data.to_json() for data in self.position_bin_data]
        }, cls=CustomJSONEncoder, indent=4)


@dataclass
class CachedPositionInfo:
    lb_pair: Pubkey
    last_updated_at: int

    def to_json(self) -> Dict[str, Any]:
        return {
            "lb_pair": str(self.lb_pair),
            "last_updated_at": self.last_updated_at
        }

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'CachedPositionInfo':
        return cls(
            lb_pair=Pubkey.from_string(json_data['lb_pair']),
            last_updated_at=json_data['last_updated_at']
        )
