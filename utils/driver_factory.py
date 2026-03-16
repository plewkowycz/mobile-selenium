from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import Settings


class DriverFactory:
    """Factory class to create and configure WebDriver instances.

    Uses Chrome DevTools Protocol mobile emulation, which injects the full
    device profile (viewport dimensions, devicePixelRatio, and user-agent
    string) at the browser level — no manual window resizing is required.
    """

    @staticmethod
    def create_driver(settings: Settings) -> webdriver.Chrome:
        """Create and return a configured Chrome WebDriver instance."""
        options = Options()

        # ── Mobile Emulation via DevTools ──────────────────────────
        # "deviceName" maps to a built-in Chrome DevTools profile that
        # sets viewport width/height, deviceScaleFactor, and the
        # mobile user-agent automatically — forcing the Mobile Web
        # Manifest of any site (e.g. m.twitch.tv).
        mobile_emulation: dict[str, str] = {"deviceName": settings.MOBILE_DEVICE}
        options.add_experimental_option("mobileEmulation", mobile_emulation)

        # ── Anti-Detection Hardening ─────────────────────────────────────
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # ── Stability flags ────────────────────────────────────────
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # ── Headless mode (CI only) ───────────────────────────────────
        import os

        if os.getenv("CI") or settings.HEADLESS:
            options.add_argument("--headless=new")

        # ── Driver binary management ──────────────────────────────
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # ── Post-init anti-detection ─────────────────────────────────
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return driver
