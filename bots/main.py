#!/usr/bin/env python3
"""
LP Bot Manager

A command-line tool for managing and running Liquidity Pool bots.
Each bot can be configured via a .env file.

Supported bots:
- lpfeed: LP Feed Bot for LP pairs and pools sharing
- lparena: LP Arena Bot for LP strategies sharing

Usage:
    ./main.py lpfeed [--env PATH_TO_ENV] [--log-dir PATH_TO_LOGS]
    ./main.py lparena [--env PATH_TO_ENV] [--log-dir PATH_TO_LOGS]
"""

import argparse
import asyncio
import os
import sys
import traceback
from pathlib import Path
from typing import Any

from bots.base.bot_config import BotConfig
from bots.lparena.lparena import LPArenaBot
from bots.lparena.lparena_config import LPArenaConfig
from bots.lpfeed.lpfeed import LPFeedBot
from libs.utils.utils import setup_logger


def validate_path(path: str, should_exist: bool = True) -> str:
    """
    Validate that a path exists and is accessible.

    Args:
        path: Path to validate
        should_exist: Whether the path should already exist

    Returns:
        str: Validated path

    Raises:
        argparse.ArgumentTypeError: If path validation fails
    """
    try:
        path_obj = Path(path)
        if should_exist:
            if not path_obj.exists():
                raise argparse.ArgumentTypeError(f"Path not found: {path}")
            if not os.access(path, os.R_OK):
                raise argparse.ArgumentTypeError(f"Path is not accessible: {path}")
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        return str(path_obj)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid path {path}: {str(e)}")


def validate_env_path(path: str) -> str:
    """Validate .env file path."""
    path = validate_path(path)
    if not Path(path).is_file():
        raise argparse.ArgumentTypeError(f"Not a file: {path}")
    return path


def validate_log_dir(path: str) -> str:
    """Validate and create log directory if needed."""
    return validate_path(path, should_exist=False)


def parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(
        description='LP Bot Manager - Manage and run Liquidity Pool bots',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'bot',
        choices=['lpfeed', 'lparena'],
        help='Bot type to run'
    )

    parser.add_argument(
        '--env', '-e',
        type=validate_env_path,
        default=None,  # We'll set the default dynamically after parsing
        help='Path to .env configuration file (default: ./.env.{bot_type})'
    )

    parser.add_argument(
        '--log-dir', '-l',
        type=validate_log_dir,
        default='./logs',
        help='Directory for log files (default: ./logs)'
    )

    # Parse args first
    args = parser.parse_args()

    # Set default env path if not provided
    if args.env is None:
        default_env = f'./.env.{args.bot}'
        args.env = validate_env_path(default_env)

    return args


async def create_bot(bot_type: str, env_path: str) -> Any:
    """
    Create a bot instance based on type.

    Args:
        bot_type: Type of bot to create
        config: Bot configuration

    Returns:
        Bot instance

    Raises:
        ValueError: If bot_type is invalid
    """
    match bot_type:
        case 'lpfeed':
            return LPFeedBot(BotConfig.from_env(env_path))
        case 'lparena':
            return LPArenaBot(LPArenaConfig.from_env(env_path))
        case _:
            raise ValueError(f"Unsupported bot type: {bot_type}")


async def start_bot(bot_type: str, env_path: str, log_dir: str) -> None:
    """
    Initialize and start the specified bot.

    Args:
        bot_type: Type of bot to run
        env_path: Path to .env configuration file
        log_dir: Directory for log files

    Raises:
        Exception: If bot initialization or startup fails
    """
    logger = setup_logger(log_dir=log_dir, bot_type=bot_type)

    try:
        logger.info(f"Loading configuration from {env_path}")

        logger.info(f"Initializing {bot_type} bot")
        bot = await create_bot(bot_type, env_path)

        logger.info(f"Starting {bot_type} bot")
        await bot.start()

    except Exception as e:
        logger.error(f"Bot startup failed: {str(e)}")
        logger.debug(f"Detailed error: {traceback.format_exc()}")
        raise


async def main() -> None:
    """Main entry point - parse args and start bot."""
    args = parse_args()
    await start_bot(args.bot, args.env, args.log_dir)


def run() -> None:
    """Script entry point with error handling."""
    try:
        if sys.version_info < (3, 12):
            print("Error: Python 3.12+ is required", file=sys.stderr)
            sys.exit(1)

        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nShutdown requested by user", file=sys.stderr)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    run()
