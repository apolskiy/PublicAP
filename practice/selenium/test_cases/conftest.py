import pytest
from selenium import webdriver
import json
import os
from pathlib import Path


from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.safari.service import Service as SafariService

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions


def _load_config() -> dict:
    """Load config/config.json if present; return {} if missing/invalid."""
    cfg_path = Path(__file__).parent / "config" / "config.json"
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {cfg_path}: {e}") from e


def _resolve_browser(pytest_ui_browser: str | None, cfg: dict) -> str:
    """
    Precedence:
      1) CLI: --ui-browser
      2) ENV: BROWSER
      3) config/config.json: {"browser": "..."}
      4) default: "chrome"
    """
    if pytest_ui_browser:
        return pytest_ui_browser.strip().lower()
    env_browser = os.getenv("BROWSER")
    if env_browser:
        return env_browser.strip().lower()
    cfg_browser = (cfg.get("browser") or "").strip().lower()
    return cfg_browser if cfg_browser else "chrome"


@pytest.fixture()
def driver(request):
    """Provides a Selenium WebDriver instance for UI tests."""
    cfg = _load_config()
    browser = _resolve_browser(request.config.getoption("--ui-browser"), cfg)
    try:
        headless = request.config.getoption("--headless")
    except ValueError:
        headless = False
    print(f"[conftest] Creating driver for: {browser} (headless={headless})")

    if browser == "edge":
        opts = EdgeOptions()
        if headless:
            opts.add_argument("--headless=new")
        drv = webdriver.Edge(
            service=EdgeService(EdgeChromiumDriverManager().install()),
            options=opts,
        )

    elif browser == "firefox":
        opts = FirefoxOptions()
        if headless:
            opts.add_argument("-headless")
        drv = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=opts,
        )

    elif browser == "chrome":

        opts = ChromeOptions()
        #opts.add_argument("--headless=new")
        if headless:
            opts.add_argument("--headless=new")
        drv = webdriver.Chrome(options=opts)
        #drv = webdriver.Chrome(
            #service=ChromeService(ChromeDriverManager().install()),
            #options=opts,
        #)

    else:
        raise TypeError(f"Browser '{browser}' not supported. Choose from: edge, chrome, firefox")

    drv.implicitly_wait(10)
    yield drv
    print(f"[conftest] Quitting driver for: {browser}")
    #drv.get("http://www.google.com")
    drv.quit()


def pytest_addoption(parser):
    """Adds UI test options to pytest."""
    group = parser.getgroup("ui", "UI test options")
    group.addoption(
        "--ui-browser",
        action="store",
        default=None,  # let config/env decide the default
        help="Browser for UI tests: edge, chrome, firefox",
    )
    """group.addoption(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )"""