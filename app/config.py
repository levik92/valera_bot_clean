"""Configuration for the Valera bot.

This module reads environment variables via `python-dotenv` to configure the bot.
You can set variables in a `.env` file or directly in the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv


# Load variables from a .env file if present
load_dotenv()


@dataclass
class Settings:
    """Simple settings container using environment variables with sensible defaults."""

    bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    openai_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    start_bonus: int = field(default_factory=lambda: int(os.getenv("START_BONUS", "10")))
    ref_bonus: int = field(default_factory=lambda: int(os.getenv("REF_BONUS", "10")))
    generate_cost: int = field(default_factory=lambda: int(os.getenv("GENERATE_COST", "1")))
    cooldown_seconds: int = field(default_factory=lambda: int(os.getenv("COOLDOWN_SECONDS", "5")))
    allowed_user_ids: List[int] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        # Parse comma-separated user IDs into a list of ints
        ids_raw = os.getenv("ALLOWED_USER_IDS", "")
        if ids_raw:
            ids_list = []
            for part in ids_raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    ids_list.append(int(part))
                except ValueError:
                    # ignore invalid entries silently
                    continue
            self.allowed_user_ids = ids_list
        else:
            self.allowed_user_ids = []


def get_settings() -> Settings:
    """Return a singleton Settings instance.

    Using a function allows for lazy instantiation and easier mocking/testing.
    """
    return Settings()
