from __future__ import annotations
from typing import Tuple

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from components.modal_handler import ModalHandler


class StreamerPage(BasePage):
    """Streamer/Channel Page object representing the viewing experience."""

    # Video player container
    VIDEO_PLAYER: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "div[data-a-target='video-player']",
    )

    # Fallback: the actual <video> tag inside the player
    VIDEO_ELEMENT: Tuple[str, str] = (By.CSS_SELECTOR, "video")

    # Channel/streamer name — button that opens channel metadata
    CHANNEL_NAME_BUTTON: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "button[aria-label*='Open channel metadata']",
    )

    # Fallback channel name selector
    CHANNEL_NAME_HEADING: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "h1[data-a-target='stream-title']",
    )

    def wait_for_page_load(self) -> StreamerPage:
        """Wait until the page is loaded and ready for interaction."""
        # Wait for URL to contain a streamer path (not just /videos/)
        try:
            self.wait.wait_for_url_contains("/videos/")
        except Exception:
            # If not /videos/, wait for any channel path (single segment)
            current_url = self.driver.current_url
            # Give a moment for navigation to complete
            self.wait._resolve_wait(2).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

        # Wait for page to be fully ready
        self.wait._resolve_wait(5).until(
            lambda driver: (
                driver.execute_script("return document.readyState") == "complete"
            )
        )

        # Try to find any meaningful element that indicates we're on a stream page
        try:
            self.wait.wait_for_element(self.VIDEO_PLAYER, timeout=5)
        except Exception:
            try:
                self.wait.wait_for_element(self.VIDEO_ELEMENT, timeout=5)
            except Exception:
                try:
                    self.wait.wait_for_element(self.CHANNEL_NAME_HEADING, timeout=5)
                except Exception:
                    # If none of the expected elements are found, just wait for URL to stabilize
                    current_url = self.driver.current_url
                    self.wait._resolve_wait(3).until(
                        lambda driver: driver.current_url == current_url
                    )

        return self

    def get_channel_name(self) -> str:
        """Extract the channel/streamer name from the page."""
        try:
            element = self.wait.wait_for_visible(self.CHANNEL_NAME_BUTTON)
            # The aria-label is "Open channel metadata for <ChannelName>"
            aria_label = element.get_attribute("aria-label") or ""
            name = aria_label.replace("Open channel metadata for ", "").strip()
            if name:
                return name
            return element.text.strip()
        except Exception:
            # Fallback: try to get channel name from heading
            try:
                element = self.wait.wait_for_visible(self.CHANNEL_NAME_HEADING)
                return element.text.strip()
            except Exception:
                # Additional fallbacks for different mobile layouts
                try:
                    # Try to find any h1 or title element that might contain the channel name
                    title_element = self.driver.find_element(By.TAG_NAME, "h1")
                    return title_element.text.strip()
                except Exception:
                    try:
                        # Try to get channel name from URL as last resort
                        url = self.driver.current_url
                        if "/videos/" in url:
                            # Extract channel name from URL like /channel/videos/
                            path_parts = [
                                p for p in url.split("/") if p and p != "videos"
                            ]
                            if path_parts:
                                return path_parts[-1].replace("-", " ").title()
                        return "Unknown Channel"
                    except Exception:
                        return "Unknown Channel"

    def handle_modal_if_present(self) -> StreamerPage:
        """Dismiss common modals/gates on stream load using the ModalHandler."""
        handler = ModalHandler(self.driver, self.wait)
        handler.dismiss_all()
        return self
