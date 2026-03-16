from __future__ import annotations
from typing import Tuple

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from pages.search_page import SearchPage
from components.modal_handler import ModalHandler


class HomePage(BasePage):
    """Twitch Home Page object for mobile emulation."""

    # Bottom navigation "Browse" link (magnifying glass icon) - CONFIRMED WORKING
    BROWSE_BUTTON: Tuple[str, str] = (By.CSS_SELECTOR, "a[href='/directory']")

    def open(self, base_url: str) -> HomePage:
        """Navigate to the base URL and return the HomePage instance."""
        self.driver.get(base_url)
        
        # Dismiss cookie/consent banners before interacting with the page
        ModalHandler(self.driver, self.wait).dismiss_all()
        
        # Wait for Browse button to be available
        self._get_element(self.BROWSE_BUTTON)
        
        return self

    def click_search(self) -> SearchPage:
        """Click the Browse button in the bottom nav to reach the search/directory page."""
        self._click(self.BROWSE_BUTTON)
        return SearchPage(self.driver, self.wait)
