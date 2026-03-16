"""Base test class for Twitch mobile tests."""

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from config.settings import Settings
from utils.screenshot_helper import ScreenshotHelper
from utils.wait_helper import WaitHelper


class BaseTwitchTest:
    """Base class for Twitch mobile tests with common setup and retry logic."""
    
    @pytest.fixture(autouse=True)
    def setup_test_screenshot(self, screenshot: ScreenshotHelper):
        """Take a screenshot before each test."""
        screenshot.take_screenshot("test_start")
    
    @pytest.fixture(autouse=True)
    def cleanup_test_screenshot(self, screenshot: ScreenshotHelper, request):
        """Take a screenshot after each test."""
        yield
        screenshot.take_screenshot(f"{request.node.name}_completed")
    
    def retry_action(self, func, max_attempts: int = 3, timeout: int = 10):
        """Retry mechanism using Selenium's built-in WebDriverWait with retry logic."""
        for attempt in range(max_attempts):
            try:
                return func()
            except (StaleElementReferenceException, TimeoutException) as e:
                if attempt == max_attempts - 1:
                    # Last attempt, re-raise the exception
                    raise
                print(f"Attempt {attempt + 1}/{max_attempts} failed: {type(e).__name__}: {str(e)}")
                # Wait a moment before retrying
                WebDriverWait(WebDriver(None), 2).until(
                    lambda d: True  # Simple wait for 2 seconds
                )
    
    def search_and_validate_streamer(
        self, 
        driver: WebDriver, 
        wait: WaitHelper, 
        query: str = "StarCraft II"
    ) -> str:
        """Common flow to search for a streamer and return channel name with retry logic."""
        from pages.home_page import HomePage
        from pages.search_page import SearchPage
        from pages.streamer_page import StreamerPage
        
        def perform_search():
            # Search flow
            home_page = HomePage(driver, wait).open(Settings().BASE_URL)
            search_page = home_page.click_search()
            search_page.search_for(query)
            search_page.scroll_results(2)
            
            # Get first streamer with retry
            streamer_page = self.retry_action(
                lambda: search_page.select_first_live_streamer(),
                max_attempts=3,
                timeout=10
            )
            
            streamer_page.handle_modal_if_present()
            streamer_page.wait_for_page_load()
            
            # Return channel name for validation
            return streamer_page.get_channel_name()
        
        return perform_search()
