import pytest
import sys
from pathlib import Path
import requests
from urllib.parse import urlparse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

sys.path.append(str(Path(__file__).parent.parent))  # Adds the parent directory to sys.path

from page_objects.base_page import BasePage, LandingPage


@pytest.mark.smoke
class TestDtexMainPage:
    def test_dtex_main_page_flow(self, driver):
        dtex_main_page = LandingPage(driver)
        dtex_main_page.set_url("https://www.dtexsystems.com/")
        dtex_main_page.set_page_title("DTEX Systems | The Trusted Leader for Insider Risk Management")
        dtex_main_page.open()
        assert dtex_main_page.page_title_is_correct(), "DTEX Main Page title is not correct"

        assert len(dtex_main_page.check_page_for_errors())>0, f"DTEX Main Page has errors {dtex_main_page.check_page_for_errors()}"
        assert len(dtex_main_page.check_page_links())>1, f"DTEX Main Page has broken links {dtex_main_page.check_page_links()}"