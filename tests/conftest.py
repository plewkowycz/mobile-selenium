import pytest
from typing import Generator

from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings, settings as global_settings
from utils.driver_factory import DriverFactory
from utils.screenshot_helper import ScreenshotHelper
from utils.wait_helper import WaitHelper


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Fixture providing the global settings instance."""
    return global_settings


@pytest.fixture(scope="function")
def driver(settings: Settings) -> Generator[WebDriver, None, None]:
    """Fixture to create and quit the WebDriver."""
    driver_instance = DriverFactory.create_driver(settings)
    try:
        yield driver_instance
    finally:
        driver_instance.quit()


@pytest.fixture(scope="function")
def wait(driver: WebDriver, settings: Settings) -> WaitHelper:
    """Fixture providing a WaitHelper instance."""
    return WaitHelper(driver, settings.DEFAULT_TIMEOUT)


@pytest.fixture(scope="function")
def screenshot(driver: WebDriver, settings: Settings) -> ScreenshotHelper:
    """Fixture providing a ScreenshotHelper instance."""
    return ScreenshotHelper(driver, settings.SCREENSHOT_DIR)


# ── Hooks ─────────────────────────────────────────────────────────


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item) -> Generator[None, None, None]:
    """Capture a screenshot on test failure and attach it to the HTML report."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        driver: WebDriver | None = item.funcargs.get("driver")
        if driver is None:
            return

        settings_instance: Settings = item.funcargs.get("settings", global_settings)
        helper = ScreenshotHelper(driver, settings_instance.SCREENSHOT_DIR)
        screenshot_path = helper.take_screenshot(item.name)

        # Attach the screenshot to the pytest-html report if available
        if hasattr(report, "extras"):
            import pytest_html

            report.extras.append(pytest_html.extras.image(str(screenshot_path)))
