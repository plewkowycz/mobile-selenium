from typing import Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.wait_helper import WaitHelper


class ModalHandler:
    """Component handling Twitch overlays, modals, consent gates, and
    app-redirect interstitials.

    Each locator is attempted with a short, independent timeout.  If the
    element is absent the timeout is silently swallowed — normal test flow
    is never interrupted.
    """

    # Cookie consent banner — "Accept" button.
    # Twitch wraps text inside nested <span> elements, so we match
    # descendant text nodes.
    COOKIE_CONSENT_ACCEPT_BUTTON: Tuple[str, str] = (
        By.XPATH,
        "//button[.//text()[normalize-space()='Accept']]",
    )

    # Mature content / age gate
    MATURE_CONTENT_ACCEPT_BUTTON: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "button[data-a-target='player-overlay-mature-accept']",
    )

    # Content classification gate
    START_WATCHING_BUTTON: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "button[data-a-target='content-classification-gate-overlay-start-watching-button']",
    )

    # "Open in App" / "Keep using web" bottom sheet or modal
    KEEP_USING_WEB_BUTTON: Tuple[str, str] = (
        By.XPATH,
        (
            "//*[self::button or self::a or @role='button' or self::div][normalize-space()='Keep using web']"
            " | //*[self::button or self::a or @role='button' or self::div][.//text()[normalize-space()='Keep using web']]"
            " | //div[contains(@class, 'ScCoreButton')]//*[text()='Keep using web']"
            " | //button[contains(., 'Keep using web')]"
        ),
    )

    # "Open App for …" interstitial — full-page redirect prompt.
    # Detected by the presence of the "Open App" CTA button on this page.
    OPEN_APP_INTERSTITIAL_BUTTON: Tuple[str, str] = (
        By.XPATH,
        "//button[.//text()[normalize-space()='Open App']]",
    )

    _CLICK_MODALS = [
        COOKIE_CONSENT_ACCEPT_BUTTON,
        MATURE_CONTENT_ACCEPT_BUTTON,
        START_WATCHING_BUTTON,
        KEEP_USING_WEB_BUTTON,
    ]

    def __init__(self, driver: WebDriver, wait: WaitHelper) -> None:
        self.driver = driver
        self.wait = wait

    def dismiss_all(self) -> None:
        """Attempt to close every known modal / interstitial.

        Optimized for mobile: Uses fast JS-based text matching first, then
        sequential locator attempts with a very short timeout.
        """
        # 1. Proactive JS Dismissal (By-passes element-clickable checks, works on blockers)
        self.driver.execute_script("""
            const texts = ['Keep using web', 'Accept', 'Start Watching', 'Accept Cookies', 'Accept all'];
            const elements = document.querySelectorAll('button, a, div[role="button"], span');
            elements.forEach(el => {
                const txt = el.innerText || el.textContent;
                if (texts.some(t => txt && txt.includes(t))) {
                    try { el.click(); } catch(e) {}
                }
            });
        """)

        # Give JS a moment to take effect
        from utils.wait_helper import WaitHelper

        temp_wait = WaitHelper(self.driver, 1)
        temp_wait._resolve_wait(1).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        short_wait = WebDriverWait(
            self.driver, 1
        )  # Reduced from 3s to prevent test starvation

        # 2. Handle "Open App for …" interstitial by going back
        self._dismiss_open_app_interstitial(short_wait)

        # 3. Click-dismiss standard modals via explicit locators
        for locator in self._CLICK_MODALS:
            try:
                element = short_wait.until(EC.element_to_be_clickable(locator))
                self.driver.execute_script("arguments[0].click();", element)
            except TimeoutException:
                pass

    def _dismiss_open_app_interstitial(self, short_wait: WebDriverWait) -> None:
        """If the browser landed on an "Open App for …" interstitial page,
        navigate back to return to the previous content page."""
        try:
            short_wait.until(
                EC.presence_of_element_located(self.OPEN_APP_INTERSTITIAL_BUTTON)
            )
            # This is a full-page interstitial — going back is the safest
            # way to return to the test flow without opening the native app.
            self.driver.back()
            from utils.wait_helper import WaitHelper

            temp_wait = WaitHelper(self.driver, 1)
            temp_wait._resolve_wait(1).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            pass
