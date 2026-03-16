"""Test Twitch mobile search functionality."""

import pytest
from tests.base_test import BaseTwitchTest


@pytest.mark.smoke
class TestTwitchStarCraftSearch(BaseTwitchTest):
    """Test suite for Twitch mobile search functionality."""

    def test_search_and_open_streamer(self, driver, wait, screenshot):
        """Test searching for StarCraft II and opening first streamer."""
        # Use the common search flow from base class
        channel_name = self.search_and_validate_streamer(driver, wait, "StarCraft II")
        
        # Validate we got a real channel name
        assert channel_name.strip() != "", "Failed to extract a valid channel name."
        assert len(channel_name) > 2, "Channel name seems too short."
