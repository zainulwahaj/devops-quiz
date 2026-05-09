from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from html import unescape
from time import sleep
from urllib.parse import quote_plus, urldefrag, urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SOURCE_HOME = "https://www.theatlantic.com/"
SEARCH_URL = "https://www.theatlantic.com/search/?q={query}"
ARTICLE_PATH_RE = re.compile(r"/(?:[^/]+/)?archive/\d{4}/", re.IGNORECASE)


@dataclass(frozen=True)
class ArticleResult:
    url: str
    text: str


def fetch_first_article(keyword: str) -> ArticleResult:
    driver = _create_driver()
    try:
        article_url = _find_first_article_url(driver, keyword)
        if not article_url:
            return ArticleResult(url="", text="")

        driver.get(article_url)
        _wait_for_page(driver)
        article_text = _extract_article_text(driver)
        return ArticleResult(url=article_url, text=article_text)
    except WebDriverException as exc:
        return ArticleResult(url="", text=f"Selenium could not fetch an article: {exc.msg}")
    finally:
        driver.quit()


def _create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1365,1000")
    options.add_argument("--lang=en-US")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    chrome_binary = _first_available(
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    )
    if chrome_binary:
        options.binary_location = chrome_binary

    chromedriver = shutil.which("chromedriver")
    service = Service(executable_path=chromedriver) if chromedriver else Service()
    return webdriver.Chrome(service=service, options=options)


def _find_first_article_url(driver: webdriver.Chrome, keyword: str) -> str:
    driver.get(SEARCH_URL.format(query=quote_plus(keyword)))
    _wait_for_page(driver)
    sleep(1)

    links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
    candidates: list[str] = []
    for link in links:
        href = link.get_attribute("href") or ""
        clean_url = _normalize_url(href)
        if clean_url and _is_article_url(clean_url) and clean_url not in candidates:
            candidates.append(clean_url)

    if candidates:
        return candidates[0]

    return _fallback_from_homepage(driver, keyword)


def _fallback_from_homepage(driver: webdriver.Chrome, keyword: str) -> str:
    driver.get(SOURCE_HOME)
    _wait_for_page(driver)
    keyword_lower = keyword.lower()

    links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
    for link in links:
        href = _normalize_url(link.get_attribute("href") or "")
        text = (link.text or "").strip().lower()
        if href and _is_article_url(href) and keyword_lower in text:
            return href

    for link in links:
        href = _normalize_url(link.get_attribute("href") or "")
        if href and _is_article_url(href):
            return href

    return ""


def _extract_article_text(driver: webdriver.Chrome) -> str:
    script = """
    const parts = [];
    const title = document.querySelector('h1')?.innerText || document.title || '';
    const description = document.querySelector('meta[name="description"]')?.content
      || document.querySelector('meta[property="og:description"]')?.content
      || '';

    if (title.trim()) parts.push(title.trim());
    if (description.trim()) parts.push(description.trim());

    const selectors = [
      'article p',
      'main p',
      '[data-testid*="article"] p',
      '[class*="Article"] p',
      '[class*="article"] p'
    ];

    const seen = new Set();
    for (const selector of selectors) {
      for (const node of document.querySelectorAll(selector)) {
        const text = (node.innerText || '').replace(/\\s+/g, ' ').trim();
        if (text.length >= 45 && !seen.has(text)) {
          seen.add(text);
          parts.push(text);
        }
      }
    }

    if (parts.length <= 2) {
      const bodyText = (document.body?.innerText || '').replace(/\\s+/g, ' ').trim();
      if (bodyText) parts.push(bodyText);
    }

    return parts.join('\\n\\n');
    """
    text = driver.execute_script(script)
    return _clean_text(str(text or ""))


def _wait_for_page(driver: webdriver.Chrome) -> None:
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except TimeoutException:
        pass


def _normalize_url(url: str) -> str:
    if not url:
        return ""

    url, _fragment = urldefrag(url)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ""
    if parsed.netloc not in {"www.theatlantic.com", "theatlantic.com"}:
        return ""
    return f"https://www.theatlantic.com{parsed.path}"


def _is_article_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != "www.theatlantic.com":
        return False
    if any(part in parsed.path for part in ("/search/", "/newsletters/", "/podcasts/")):
        return False
    return bool(ARTICLE_PATH_RE.search(parsed.path))


def _first_available(*names: str) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return ""


def _clean_text(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
