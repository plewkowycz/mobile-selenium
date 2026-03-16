import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configuration settings for the Twitch Selenium framework."""

    BASE_URL: str = os.environ.get("BASE_URL", "https://m.twitch.tv")
    MOBILE_DEVICE: str = os.environ.get("MOBILE_DEVICE", "Pixel 7")
    BROWSER: str = os.environ.get("BROWSER", "chrome")
    IMPLICIT_WAIT: int = int(os.environ.get("IMPLICIT_WAIT", "0"))
    DEFAULT_TIMEOUT: int = int(os.environ.get("DEFAULT_TIMEOUT", "15"))
    SCREENSHOT_DIR: Path = Path(os.environ.get("SCREENSHOT_DIR", "screenshots"))
    HEADLESS: bool = os.environ.get("HEADLESS", "false").lower() in (
        "true",
        "1",
        "yes",
        "t",
    )


settings = Settings()
