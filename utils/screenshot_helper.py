from datetime import datetime
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver


class ScreenshotHelper:
    """Helper class for taking screenshots."""

    def __init__(self, driver: WebDriver, screenshot_dir: Path):
        self._driver = driver
        self._screenshot_dir = screenshot_dir

    def take_screenshot(self, name: str) -> Path:
        """Take a screenshot and save it to the screenshot directory."""
        # Create the directory if it does not exist
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{name}.png"
        file_path = self._screenshot_dir / filename

        self._driver.save_screenshot(str(file_path))
        return file_path
