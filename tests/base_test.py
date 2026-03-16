"""Base test class for Twitch mobile tests."""

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from config.settings import Settings
from utils.screenshot_helper import ScreenshotHelper
from utils.wait_helper import WaitHelper


class BaseTwitchTest:
    """Base class for Twitch mobile tests with common setup."""

    @pytest.fixture(autouse=True)
    def setup_test_screenshot(self, screenshot: ScreenshotHelper):
        """Take a screenshot before each test."""
        screenshot.take_screenshot("test_start")

    @pytest.fixture(autouse=True)
    def cleanup_test_screenshot(self, screenshot: ScreenshotHelper, request):
        """Take a screenshot after each test."""
        yield
        screenshot.take_screenshot(f"{request.node.name}_completed")

    def search_and_validate_streamer(
        self, driver: WebDriver, wait: WaitHelper, query: str = "StarCraft II"
    ) -> str:
        """Common flow to search for a streamer and return channel name."""
        from pages.home_page import HomePage
        from pages.search_page import SearchPage
        from pages.streamer_page import StreamerPage

        # Search flow
        home_page = HomePage(driver, wait).open(Settings().BASE_URL)
        search_page = home_page.click_search()
        search_page.search_for(query)
        search_page.scroll_results(2)

        # Get first streamer
        streamer_page = search_page.select_first_live_streamer()
        streamer_page.handle_modal_if_present()
        streamer_page.wait_for_page_load()

        # Return channel name for validation
        return streamer_page.get_channel_name()
