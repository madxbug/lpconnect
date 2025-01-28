import os
from decimal import Decimal
from enum import Enum
from typing import List, Tuple, Dict, Any

import httpx

from libs.utils.datatypes import PricePoint

BASE_URL = 'https://public-api.birdeye.so/defi/history_price'
REQUIRED_PARAMS = ['address', 'address_type', 'type', 'time_from', 'time_to']

MAX_DATA_POINTS = 999
SECONDS_PER_MINUTE = 60


class AddressType(Enum):
    PAIR = 'pair'
    TOKEN = 'token'


class TimeInterval(Enum):
    ONE_MINUTE = ('1m', 60)
    THREE_MINUTES = ('3m', 180)
    FIVE_MINUTES = ('5m', 300)
    FIFTEEN_MINUTES = ('15m', 900)
    THIRTY_MINUTES = ('30m', 1800)
    ONE_HOUR = ('1H', 3600)
    TWO_HOURS = ('2H', 7200)
    FOUR_HOURS = ('4H', 14400)
    SIX_HOURS = ('6H', 21600)
    EIGHT_HOURS = ('8H', 28800)
    TWELVE_HOURS = ('12H', 43200)
    ONE_DAY = ('1D', 86400)
    THREE_DAYS = ('3D', 259200)
    ONE_WEEK = ('1W', 604800)
    ONE_MONTH = ('1M', 2592000)  # Approximation: 30 days

    def __init__(self, code, seconds):
        self.code = code
        self.seconds = seconds

    @classmethod
    def from_code(cls, code):
        for interval in cls:
            if interval.code == code:
                return interval
        raise ValueError(f"No TimeInterval found for code: {code}")

    def __str__(self):
        return self.code


class ValidationError(Exception):
    pass


class FetchError(Exception):
    pass


async def fetch_with_retry(url: str, headers: Dict[str, str], max_retries: int = 3) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        for _ in range(max_retries):
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError:
                if _ == max_retries - 1:
                    raise FetchError(f"HTTP error! status: {response.status_code}")
            except httpx.RequestError:
                if _ == max_retries - 1:
                    raise FetchError("Failed to fetch data")


def validate_params(params: Dict[str, str]) -> None:
    missing_params = [param for param in REQUIRED_PARAMS if param not in params]
    if missing_params:
        raise ValidationError(f"Missing required parameters: {', '.join(missing_params)}")


def build_url(params: Dict[str, str]) -> str:
    return f"{BASE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"


async def get_historical_price(
        address: str,
        address_type: AddressType,
        interval: TimeInterval,
        from_block_time: int,
        to_block_time: int
) -> List[PricePoint]:
    to_block_time += interval.seconds  # birdeye will return empty list if to-from<interval

    params = {
        'address': address,
        'address_type': address_type.value,
        'type': interval.code,
        'time_from': str(from_block_time),
        'time_to': str(to_block_time)
    }

    try:
        validate_params(params)
        url = build_url(params)
        headers = {
            'x-chain': 'solana',
            'x-api-key': os.getenv('BIRDEYE_API_KEY', '')
        }
        data = await fetch_with_retry(url, headers)
        values = [PricePoint(Decimal(point.get('value', 0)), point.get('unixTime', 0)) for point in
                  data.get("data", {}).get("items", [])]
        return values
    except ValidationError as e:
        raise ValidationError(str(e))
    except FetchError as e:
        raise FetchError(str(e))


def determine_optimal_time_interval(from_block_time: int, to_block_time: int) -> TimeInterval:
    total_duration_minutes = (to_block_time - from_block_time) / SECONDS_PER_MINUTE
    target_interval_minutes = int((total_duration_minutes / MAX_DATA_POINTS) + 0.5)

    available_intervals: List[Tuple[int, TimeInterval]] = [
        (1, TimeInterval.ONE_MINUTE),
        (3, TimeInterval.THREE_MINUTES),
        (5, TimeInterval.FIVE_MINUTES),
        (15, TimeInterval.FIFTEEN_MINUTES),
        (30, TimeInterval.THIRTY_MINUTES),
        (60, TimeInterval.ONE_HOUR),
        (120, TimeInterval.TWO_HOURS),
        (240, TimeInterval.FOUR_HOURS),
        (360, TimeInterval.SIX_HOURS),
        (480, TimeInterval.EIGHT_HOURS),
        (720, TimeInterval.TWELVE_HOURS),
        (1440, TimeInterval.ONE_DAY),
        (4320, TimeInterval.THREE_DAYS),
        (10080, TimeInterval.ONE_WEEK),
        (43200, TimeInterval.ONE_MONTH)
    ]

    for minutes, interval in available_intervals:
        if minutes >= target_interval_minutes:
            return interval

    return TimeInterval.ONE_MONTH


def determine_interval_index(init_block_time: int, interval: TimeInterval, target_block_time: int) -> int:
    time_difference = target_block_time - init_block_time
    index = time_difference // interval.seconds
    return max(0, index)
