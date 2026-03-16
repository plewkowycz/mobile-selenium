from typing import Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    ElementClickInterceptedException,
)
from utils.wait_helper import WaitHelper


class BasePage:
    """Base class providing common actions across all Page Objects."""

    def __init__(self, driver: WebDriver, wait: WaitHelper):
        self.driver = driver
        self.wait = wait

    def _click(self, locator: Tuple[str, str]) -> None:
        """Wait for an element to be clickable and click it. Falls back to JS click if intercepted."""
        element = self.wait.wait_for_clickable(locator)
        try:
            element.click()
        except ElementClickInterceptedException:
            self._js_click(element)

    def _js_click(self, element: WebElement) -> None:
        """Click an element via JavaScript to bypass overlay interception."""
        self.driver.execute_script("arguments[0].click();", element)

    def _type(self, locator: Tuple[str, str], text: str) -> None:
        """Wait for an element to be visible, clear it, and send keys."""
        element = self.wait.wait_for_visible(locator)
        element.clear()
        element.send_keys(text)

    def _get_element(self, locator: Tuple[str, str]) -> WebElement:
        """Wait for an element to be present and return it."""
        return self.wait.wait_for_element(locator)

    def _scroll_down(self, times: int = 1) -> None:
        """Scroll down the page a specified number of times."""
        for _ in range(times):
            current_offset = self.driver.execute_script("return window.pageYOffset;")
            self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
            # Wait for scroll to complete using JS check instead of sleep
            self.wait._resolve_wait(1).until(
                lambda driver: (
                    driver.execute_script("return window.pageYOffset;")
                    != current_offset
                )
            )

    def _is_element_present(self, locator: Tuple[str, str]) -> bool:
        """Check if an element is present in the DOM without waiting."""
        # By finding elements directly on the driver without WebDriverWait,
        # we check the DOM state immediately (0s timeout since IMPLICIT_WAIT is 0).
        elements = self.driver.find_elements(locator[0], locator[1])
        return len(elements) > 0
