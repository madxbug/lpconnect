import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Self

import numpy as np

from config.constants import LPCONNECT
from libs.utils.base_storage import BaseStorage, StorageConfig, StorageError, ValidationError, MsgPackable

logger = logging.getLogger(LPCONNECT)

REWARD_PERIOD = 20
MAX_TIME_TO_VOTE = 120


@dataclass(frozen=True, slots=True)
class VoteKey:
    message_id: int
    user_id: int

    @classmethod
    def validate(cls, message_id: int, user_id: int) -> None:
        if not all(isinstance(x, int) for x in [message_id, user_id]):
            raise ValidationError("Vote key components must be integers")
        if not all(x > 0 for x in [message_id, user_id]):
            raise ValidationError("Vote key components must be positive integers")

    def to_key_string(self) -> str:
        return f"{self.message_id}:{self.user_id}"

    @classmethod
    def from_key_string(cls, key_str: str) -> Self:
        try:
            message_id, user_id = map(int, key_str.split(":"))
            return cls(message_id=message_id, user_id=user_id)
        except ValueError as e:
            raise ValidationError(f"Invalid vote key format: {e}")


@dataclass
class VoteInfo:
    vote: str
    timestamp: float
    weight: float
    points: Optional[float] = None


@dataclass
class MessageInfo:
    start_time: float
    is_votable: bool
    owner_id: int
    actual_outcome: Optional[str] = None
    is_final: bool = False
    points_calculated: bool = False


@dataclass
class UserStats:
    total_points: float = 0.0
    correct_votes: int = 0
    incorrect_votes: int = 0
    last_updated: Optional[float] = None


@dataclass
class StorageState(MsgPackable):
    VERSION: int = 1

    version: int = VERSION
    votes: Dict[VoteKey, VoteInfo] = field(default_factory=dict)
    messages: Dict[int, MessageInfo] = field(default_factory=dict)
    user_stats: Dict[int, UserStats] = field(default_factory=dict)

    # Index mappings
    message_votes: Dict[int, Set[VoteKey]] = field(default_factory=lambda: {})
    user_votes: Dict[int, Set[VoteKey]] = field(default_factory=lambda: {})

    def to_msgpack(self) -> dict:
        return {
            'version': self.version,
            'votes': {
                key.to_key_string(): {
                    'vote': info.vote,
                    'timestamp': info.timestamp,
                    'weight': info.weight,
                    'points': info.points
                }
                for key, info in self.votes.items()
            },
            'messages': {
                str(msg_id): {
                    'start_time': info.start_time,
                    'is_votable': info.is_votable,
                    'owner_id': info.owner_id,
                    'actual_outcome': info.actual_outcome,
                    'is_final': info.is_final,
                    'points_calculated': info.points_calculated
                }
                for msg_id, info in self.messages.items()
            },
            'user_stats': {
                str(user_id): {
                    'total_points': stats.total_points,
                    'correct_votes': stats.correct_votes,
                    'incorrect_votes': stats.incorrect_votes,
                    'last_updated': stats.last_updated
                }
                for user_id, stats in self.user_stats.items()
            }
        }

    @classmethod
    def from_msgpack(cls, data: dict) -> Self:
        try:
            state = cls()
            state.version = data.get('version', cls.VERSION)

            # Rebuild votes
            for vote_key_str, info in data.get('votes', {}).items():
                key = VoteKey.from_key_string(vote_key_str)
                vote_info = VoteInfo(
                    vote=info['vote'],
                    timestamp=info['timestamp'],
                    weight=info['weight'],
                    points=info['points']
                )
                state.votes[key] = vote_info

                # Rebuild indices
                if key.message_id not in state.message_votes:
                    state.message_votes[key.message_id] = set()
                state.message_votes[key.message_id].add(key)

                if key.user_id not in state.user_votes:
                    state.user_votes[key.user_id] = set()
                state.user_votes[key.user_id].add(key)

            # Rebuild messages
            for msg_id_str, info in data.get('messages', {}).items():
                msg_id = int(msg_id_str)
                state.messages[msg_id] = MessageInfo(
                    start_time=info['start_time'],
                    is_votable=info['is_votable'],
                    owner_id=info['owner_id'],
                    actual_outcome=info['actual_outcome'],
                    is_final=info['is_final'],
                    points_calculated=info['points_calculated']
                )

            # Rebuild user stats
            for user_id_str, stats in data.get('user_stats', {}).items():
                user_id = int(user_id_str)
                state.user_stats[user_id] = UserStats(
                    total_points=stats['total_points'],
                    correct_votes=stats['correct_votes'],
                    incorrect_votes=stats['incorrect_votes'],
                    last_updated=stats['last_updated']
                )

            return state
        except Exception as e:
            raise StorageError(f"Failed to deserialize storage state: {e}")


def _calculate_vote_weight(vote_time: float, start_time: float) -> float:
    time_diff = abs(vote_time - start_time)

    if time_diff < REWARD_PERIOD:
        return 1.0

    threshold_point = 0.3
    log_drop_end = MAX_TIME_TO_VOTE / 4

    if time_diff <= log_drop_end:
        weight = 1 - np.log(time_diff / log_drop_end + 1)
        weight = max(weight, threshold_point)
    else:
        weight = threshold_point - (time_diff - log_drop_end) / (MAX_TIME_TO_VOTE - log_drop_end) * threshold_point
        weight = max(weight, 0.0001)

    return weight


class VoteStorage(BaseStorage[StorageState]):
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
        return StorageState()

    def state_from_msgpack(self, data: dict) -> StorageState:
        return StorageState.from_msgpack(data)

    async def add_vote(self, message_id: int, user_id: int, vote: str) -> bool:
        async with self._lock:
            VoteKey.validate(message_id, user_id)
            key = VoteKey(message_id, user_id)

            # Check if message exists and is votable
            if message_id not in self.state.messages:
                return False

            message_info = self.state.messages[message_id]
            if not message_info.is_votable:
                return False

            # Check voting timeframe
            current_time = datetime.now().timestamp()
            if current_time - message_info.start_time > MAX_TIME_TO_VOTE:
                return False

            # Check if user already voted
            if key in self.state.votes:
                return False

            # Add vote
            weight = _calculate_vote_weight(current_time, message_info.start_time)
            vote_info = VoteInfo(vote=vote, timestamp=current_time, weight=weight)
            self.state.votes[key] = vote_info

            # Update indices
            if message_id not in self.state.message_votes:
                self.state.message_votes[message_id] = set()
            self.state.message_votes[message_id].add(key)

            if user_id not in self.state.user_votes:
                self.state.user_votes[user_id] = set()
            self.state.user_votes[user_id].add(key)

            self._mark_modified()
            return True

    async def record_votable_message(self, message_id: int, owner_id: int):
        async with self._lock:
            self.state.messages[message_id] = MessageInfo(
                start_time=datetime.now().timestamp(),
                is_votable=True,
                owner_id=owner_id
            )
            self._mark_modified()

    async def set_vote_result(self, message_id: int, actual_outcome: str, is_final: bool = True) -> bool:
        async with self._lock:
            if message_id not in self.state.messages:
                return False

            message_info = self.state.messages[message_id]
            if message_info.is_final and message_info.points_calculated:
                return False

            message_info.actual_outcome = actual_outcome
            message_info.is_final = is_final

            if is_final:
                await self._calculate_points(message_id)
                message_info.points_calculated = True

            self._mark_modified()
            return True

    async def _calculate_points(self, message_id: int):
        if message_id not in self.state.message_votes:
            return

        vote_keys = self.state.message_votes[message_id]
        message_info = self.state.messages[message_id]
        actual_outcome = message_info.actual_outcome

        # Separate correct and incorrect votes
        correct_votes = []
        incorrect_votes = []

        for key in vote_keys:
            vote_info = self.state.votes[key]
            if vote_info.vote == actual_outcome:
                correct_votes.append((key, vote_info))
            else:
                incorrect_votes.append((key, vote_info))

        total_correct_weight = sum(info.weight for _, info in correct_votes)
        total_incorrect_weight = sum(info.weight for _, info in incorrect_votes)

        points_per_correct_vote = len(vote_keys)
        points_per_incorrect_vote = -(points_per_correct_vote / 2)

        # Calculate and update points
        current_time = datetime.now().timestamp()

        for key, vote_info in correct_votes:
            normalized_weight = vote_info.weight / total_correct_weight if total_correct_weight > 0 else 0
            points = normalized_weight * points_per_correct_vote
            vote_info.points = points

            if key.user_id not in self.state.user_stats:
                self.state.user_stats[key.user_id] = UserStats()

            user_stats = self.state.user_stats[key.user_id]
            user_stats.total_points += points
            user_stats.correct_votes += 1
            user_stats.last_updated = current_time

        for key, vote_info in incorrect_votes:
            normalized_weight = vote_info.weight / total_incorrect_weight if total_incorrect_weight > 0 else 0
            points = normalized_weight * points_per_incorrect_vote
            vote_info.points = points

            if key.user_id not in self.state.user_stats:
                self.state.user_stats[key.user_id] = UserStats()

            user_stats = self.state.user_stats[key.user_id]
            user_stats.total_points += points
            user_stats.incorrect_votes += 1
            user_stats.last_updated = current_time

    async def get_user_stats(self, user_id: int) -> dict:
        stats = self.state.user_stats.get(user_id, UserStats())
        total_votes = stats.correct_votes + stats.incorrect_votes

        return {
            'total_points': stats.total_points,
            'correct_votes': stats.correct_votes,
            'incorrect_votes': stats.incorrect_votes,
            'last_updated': datetime.fromtimestamp(stats.last_updated) if stats.last_updated else None,
            'accuracy': stats.correct_votes / total_votes if total_votes > 0 else 0
        }

    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        sorted_stats = sorted(
            self.state.user_stats.items(),
            key=lambda x: x[1].total_points,
            reverse=True
        )[:limit]

        return [{
            'user_id': user_id,
            'total_points': stats.total_points,
            'correct_votes': stats.correct_votes,
            'incorrect_votes': stats.incorrect_votes,
            'accuracy': stats.correct_votes / (stats.correct_votes + stats.incorrect_votes)
            if (stats.correct_votes + stats.incorrect_votes) > 0 else 0
        } for user_id, stats in sorted_stats]

    async def get_vote_details(self, message_id: int) -> List[Dict]:
        """Get detailed vote information including points for a specific message"""
        if message_id not in self.state.message_votes:
            return []

        vote_keys = self.state.message_votes[message_id]
        message_info = self.state.messages[message_id]

        return [{
            'user_id': key.user_id,
            'vote': info.vote,
            'weight': info.weight,
            'points': info.points,
            'timestamp': info.timestamp,
            'is_correct': info.vote == message_info.actual_outcome if message_info.actual_outcome else None
        } for key, info in (
            (key, self.state.votes[key]) for key in vote_keys
        )]

    async def get_user_voting_stats(self, user_id: int) -> Dict:
        """Get detailed voting statistics for a specific user"""
        created_messages = [
            msg_id for msg_id, info in self.state.messages.items()
            if info.owner_id == user_id
        ]

        resolved_votes = len([
            msg_id for msg_id in created_messages
            if self.state.messages[msg_id].points_calculated
        ])

        user_vote_keys = self.state.user_votes.get(user_id, set())
        user_votes = [self.state.votes[key] for key in user_vote_keys]

        # Calculate voting statistics
        total_votes = len(user_votes)
        avg_weight = sum(vote.weight for vote in user_votes) / total_votes if total_votes > 0 else 0
        avg_points = sum(vote.points or 0 for vote in user_votes) / total_votes if total_votes > 0 else 0
        positive_votes = sum(1 for vote in user_votes if vote.points and vote.points > 0)
        negative_votes = sum(1 for vote in user_votes if vote.points and vote.points < 0)

        # Calculate response times
        response_times = []
        for key in user_vote_keys:
            if key.message_id in self.state.messages:
                vote_info = self.state.votes[key]
                message_info = self.state.messages[key.message_id]
                response_time = vote_info.timestamp - message_info.start_time
                response_times.append(response_time)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Get first and last vote timestamps
        vote_timestamps = [vote.timestamp for vote in user_votes]
        first_vote = min(vote_timestamps) if vote_timestamps else None
        last_vote = max(vote_timestamps) if vote_timestamps else None

        return {
            'created_votes': {
                'total': len(created_messages),
                'resolved': resolved_votes
            },
            'voting_activity': {
                'total_votes': total_votes,
                'average_weight': avg_weight,
                'average_points': avg_points,
                'positive_votes': positive_votes,
                'negative_votes': negative_votes,
                'first_vote': datetime.fromtimestamp(first_vote) if first_vote else None,
                'last_vote': datetime.fromtimestamp(last_vote) if last_vote else None,
                'average_response_time': avg_response_time
            }
        }

    async def cleanup_old_votes(self, days: int = 30):
        """Remove votes older than specified number of days"""
        async with self._lock:
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()

            # Find old messages
            old_message_ids = [
                msg_id for msg_id, info in self.state.messages.items()
                if info.start_time < cutoff_time
            ]

            # Remove old votes and update indices
            for msg_id in old_message_ids:
                if msg_id in self.state.message_votes:
                    vote_keys = self.state.message_votes[msg_id]

                    # Update user vote indices
                    for key in vote_keys:
                        if key.user_id in self.state.user_votes:
                            self.state.user_votes[key.user_id].discard(key)
                            if not self.state.user_votes[key.user_id]:
                                del self.state.user_votes[key.user_id]

                        # Remove vote
                        if key in self.state.votes:
                            del self.state.votes[key]

                    # Remove message votes
                    del self.state.message_votes[msg_id]

                # Remove message
                del self.state.messages[msg_id]

            self._mark_modified()

    async def get_message_stats(self, message_id: int) -> Optional[Dict]:
        """Get statistics for a specific message/position"""
        if message_id not in self.state.messages:
            return None

        message_info = self.state.messages[message_id]
        vote_keys = self.state.message_votes.get(message_id, set())
        votes = [self.state.votes[key] for key in vote_keys]

        if not votes:
            return {
                'total_votes': 0,
                'status': 'open' if message_info.is_votable else 'closed',
                'outcome': message_info.actual_outcome,
                'is_final': message_info.is_final,
                'vote_distribution': {}
            }

        vote_distribution = {}
        for vote in votes:
            if vote.vote not in vote_distribution:
                vote_distribution[vote.vote] = 0
            vote_distribution[vote.vote] += 1

        return {
            'total_votes': len(votes),
            'status': 'open' if message_info.is_votable else 'closed',
            'outcome': message_info.actual_outcome,
            'is_final': message_info.is_final,
            'vote_distribution': vote_distribution,
            'average_weight': sum(v.weight for v in votes) / len(votes),
            'total_points_awarded': sum(v.points or 0 for v in votes)
        }
