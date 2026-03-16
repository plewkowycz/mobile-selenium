from typing import Tuple

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WaitHelper:
    """Explicit-wait abstraction.

    Every method uses ``WebDriverWait`` — the framework never calls
    ``time.sleep()`` for element synchronisation.

    ``StaleElementReferenceException`` is added to the list of ignored
    exceptions so that lazy-loaded DOM mutations (common on Twitch after
    scrolling) do not immediately blow up a wait — the condition is simply
    re-evaluated on the next poll cycle.
    """

    _IGNORED_EXCEPTIONS = (StaleElementReferenceException,)

    def __init__(self, driver: WebDriver, timeout: int) -> None:
        self._driver = driver
        self._timeout = timeout
        self._wait = WebDriverWait(
            driver,
            timeout,
            ignored_exceptions=self._IGNORED_EXCEPTIONS,
        )

    def wait_for_element(
        self, locator: Tuple[str, str], *, timeout: int | None = None
    ) -> WebElement:
        """Wait for an element to be present in the DOM."""
        return self._resolve_wait(timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_clickable(
        self, locator: Tuple[str, str], *, timeout: int | None = None
    ) -> WebElement:
        """Wait for an element to be clickable."""
        return self._resolve_wait(timeout).until(EC.element_to_be_clickable(locator))

    def wait_for_visible(
        self, locator: Tuple[str, str], *, timeout: int | None = None
    ) -> WebElement:
        """Wait for an element to be visible on the page."""
        return self._resolve_wait(timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_for_url_contains(self, partial_url: str) -> bool:
        """Wait for the URL to contain a specific string."""
        return self._wait.until(EC.url_contains(partial_url))

    def scroll_into_view(self, element: WebElement) -> None:
        """Execute JavaScript to scroll the element into view."""
        self._driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )

    # ── private helpers ────────────────────────────────────────────

    def _resolve_wait(self, timeout: int | None) -> WebDriverWait:
        """Return the default wait or build a one-off wait with a custom timeout."""
        if timeout is None:
            return self._wait
        return WebDriverWait(
            self._driver,
            timeout,
            ignored_exceptions=self._IGNORED_EXCEPTIONS,
        )
