"""Centralized runtime configuration.

Every environment-dependent value (target URL, credentials, browser
behaviour) is resolved here exactly once. No other module reads
``os.environ`` directly, so there is a single place to look when a run
behaves unexpectedly.

Resolution order: real environment variables win, then a local ``.env``
file, then the documented defaults below.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    """Read an environment variable as a boolean flag."""
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of the configuration for one test run."""

    base_url: str
    username: str
    password: str
    browser_name: str
    headless: bool
    slow_mo_ms: int

    @classmethod
    def from_env(cls) -> "Settings":
        """Build a Settings instance from the environment / .env file."""
        return cls(
            base_url=os.getenv("BASE_URL", "https://www.saucedemo.com/"),
            username=os.getenv("TEST_USERNAME", "standard_user"),
            password=os.getenv("TEST_PASSWORD", "secret_sauce"),
            browser_name=os.getenv("BROWSER", "chromium"),
            headless=_env_bool("HEADLESS", True),
            slow_mo_ms=int(os.getenv("SLOW_MO", "0")),
        )


settings = Settings.from_env()
