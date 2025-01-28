from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PricePoint:
    price: Decimal
    block_time: int
