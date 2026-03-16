from __future__ import annotations
from typing import List, Tuple
from urllib.parse import urlparse

from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage
from pages.streamer_page import StreamerPage


class SearchPage(BasePage):
    """Search / Browse page for interacting with Twitch search results."""

    # Search input field - CONFIRMED WORKING from mobile DOM analysis
    SEARCH_INPUT: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "input[data-a-target='tw-input']",
    )
    SEARCH_INPUT_FALLBACK: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "input[placeholder='Search']",
    )

    # The container holding actual search results layout (avoids bottom nav items)
    # Twitch mobile uses tw-core-scrollable-area or a general main wrapper.
    # Fallback to a wrapper but scrollable-area is common on mobile Twitch
    RESULTS_CONTAINER: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "div[data-a-target='tw-core-scrollable-area'], div.scrollable-area, main",
    )

    # Target links for actual streamer/video results - Mobile optimized
    CHANNEL_LINKS: Tuple[str, str] = (
        By.CSS_SELECTOR,
        "a[href*='/videos/'], button[aria-label*='Live with'], article a[href^='/']",
    )

    def search_for(self, query: str) -> SearchPage:
        """Type a query into the search input and press Enter."""
        from components.modal_handler import ModalHandler
        ModalHandler(self.driver, self.wait).dismiss_all()

        try:
            element = self.wait.wait_for_visible(self.SEARCH_INPUT)
        except Exception:
            element = self.wait.wait_for_visible(self.SEARCH_INPUT_FALLBACK)

        element.clear()
        element.send_keys(query)

        # Re-find the element to avoid stale reference after send_keys
        try:
            element = self.wait.wait_for_visible(self.SEARCH_INPUT)
        except Exception:
            element = self.wait.wait_for_visible(self.SEARCH_INPUT_FALLBACK)

        # Twitch Mobile SPA is highly sensitive to navigation and Keys.ENTER.
        # The most reliable way to submit a search is clicking the autocomplete suggestion.
        suggestion_locator = (By.CSS_SELECTOR, "div[data-a-target='search-result']")
        try:
            suggestion = self.wait.wait_for_clickable(suggestion_locator, timeout=5)
            self._js_click(suggestion)
        except Exception:
            # Fallback to Enter key if autocomplete fails to load
            try:
                # Re-find element again before sending ENTER
                try:
                    element = self.wait.wait_for_clickable(self.SEARCH_INPUT, timeout=3)
                except Exception:
                    element = self.wait.wait_for_clickable(self.SEARCH_INPUT_FALLBACK, timeout=3)
                element.send_keys(Keys.ENTER)
            except Exception:
                pass

        try:
            # Check specifically for the query parameter, because the base search overlay is already at "/search"
            self.wait.wait_for_url_contains("?term=")
        except Exception:
            pass

        # Now wait for the "Video" tab and click it, as per user request
        videos_tab_locator = (By.CSS_SELECTOR, "a[href*='type=videos']")
        try:
            videos_tab = self.wait.wait_for_clickable(videos_tab_locator, timeout=5)
            self._js_click(videos_tab)
            # Wait for tab switch to complete
            self.wait._resolve_wait(2).until(lambda d: d.execute_script("return document.readyState") == "complete")
        except Exception:
            # Fallback to finding by text if href match fails
            try:
                # Twitch mobile uses "Video" (singular) in the tab text
                videos_tab_text = self.driver.find_element(By.XPATH, "//*[self::a or self::span][contains(text(), 'Video')]")
                self._js_click(videos_tab_text)
                # Wait for tab switch to complete
                self.wait._resolve_wait(2).until(lambda d: d.execute_script("return document.readyState") == "complete")
            except Exception:
                pass


        # Wait for the results container to load AND actual results to appear
        self.wait.wait_for_element(self.RESULTS_CONTAINER)
        
        # Wait for actual search results to load (streamer cards or video thumbnails)
        try:
            self.wait._resolve_wait(10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "article, div.streamCard, div[data-a-target*='card'], img[src*='preview']")) > 0
            )
        except Exception:
            # If no results load, continue anyway - might be no results for this query
            pass
        
        return self

    def scroll_results(self, times: int) -> SearchPage:
        """Scroll down the search results list using element-based scrolling for infinite scroll."""
        try:
            # Twitch mobile uses a scrollable div. Scrolling the `window` can trigger
            # pull-to-refresh or close the search overlay, redirecting back to `/directory`.
            container = self.wait.wait_for_element(self.RESULTS_CONTAINER)
            
            # Find all video/streamer cards to scroll to the last one
            for i in range(times):
                # Get current video cards
                video_cards = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/videos/'], button[aria-label*='Live with']")
                
                if video_cards:
                    # Scroll to the last card to trigger infinite scroll
                    last_card = video_cards[-1]
                    self.wait.scroll_into_view(last_card)
                else:
                    # Fallback to container scroll if no cards found
                    self.driver.execute_script(
                        "arguments[0].scrollTop += arguments[0].clientHeight;", container
                    )
                
                # Wait for new content to load
                self.wait._resolve_wait(2).until(lambda d: d.execute_script("return document.readyState") == "complete")
                
        except Exception:
            self._scroll_down(times) # Fallback to window scroll
            
        return self

    def _find_live_channel_cards(self) -> List[WebElement]:
        """Find clickable channel links scoped strictly inside the search results container."""
        # We query strictly inside the scrollable/results area, dodging the bottom nav
        all_links: List[WebElement] = self.driver.find_elements(*self.CHANNEL_LINKS)
        channel_links: List[WebElement] = []

        for link in all_links:
            href = link.get_attribute("href") or ""
            aria_label = link.get_attribute("aria-label") or ""
            
            # For button elements (mobile streamer cards), check aria-label
            if not href and aria_label and "Live with" in aria_label:
                channel_links.append(link)
                continue
            
            # For regular links, filter by href patterns
            try:
                path = urlparse(href).path.rstrip("/")
            except Exception:
                continue

            if not path or path == "/":
                continue

            # Skip navigation and search links
            if any(skip in path for skip in ['/directory', '/search', '/categories']):
                continue

            # Allow single-segment paths (channels: /esl_sc2) OR /videos/ paths  
            segments = [s for s in path.split("/") if s]
            
            # If it's a video link, it starts with 'videos' and has channel name
            if len(segments) > 1 and segments[0] == "videos":
                channel_links.append(link)
                continue
                
            # If it's a single segment and not navigation, it's a channel link
            if len(segments) == 1 and segments[0] not in ['directory', 'search']:
                channel_links.append(link)

        return channel_links

    def select_first_live_streamer(self) -> StreamerPage:
        """Click the first live streamer result and handle possible new tab."""
        cards = self._find_live_channel_cards()

        if not cards:
            raise ValueError("No live streamer cards found in search results.")

        first_card = cards[0]
        self.wait.scroll_into_view(first_card)
        try:
            first_card.click()
        except ElementClickInterceptedException:
            self._js_click(first_card)

        # Handle potential new tab
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])

        return StreamerPage(self.driver, self.wait)
