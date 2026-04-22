import html
import re
import urllib.request
from abc import ABC
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

PROMO_KEYWORDS = [
    "bonus", "promotion", "promo", "special offer", "limited time",
    "% off", "% bonus", "discount", "sale", "extra miles", "buy miles",
    "purchase miles", "earn more", "miles sale", "points sale",
]

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class BaseScraper(ABC):
    name: str
    url: str

    def scrape(self) -> dict:
        try:
            text = self._fetch_playwright()
        except (PlaywrightTimeout, PlaywrightError) as exc:
            print(f"  Playwright failed ({exc!s:.80}), falling back to HTTP request", flush=True)
            text = self._fetch_urllib()

        return {
            "content": text,
            "promotions": self._find_promotions(text),
        }

    # --- Playwright path ---

    def _fetch_playwright(self) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=_UA,
                locale="en-GB",
                viewport={"width": 1280, "height": 800},
                timezone_id="Europe/London",
            )
            page = context.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            try:
                try:
                    page.goto(self.url, wait_until="networkidle", timeout=30000)
                except (PlaywrightTimeout, PlaywrightError):
                    page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                self._wait_for_content(page)
                return self._extract_text(page)
            finally:
                browser.close()

    def _wait_for_content(self, page):
        pass

    def _extract_text(self, page) -> str:
        return page.inner_text("body")

    # --- urllib fallback path ---

    def _fetch_urllib(self) -> str:
        req = urllib.request.Request(self.url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return self._html_to_text(raw)

    def _html_to_text(self, raw: str) -> str:
        raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = html.unescape(raw)
        return re.sub(r"\s+", " ", raw).strip()

    # --- shared ---

    def _find_promotions(self, text: str) -> list[str]:
        lines = text.split("\n")
        found = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or len(stripped) < 15:
                continue
            if any(kw in stripped.lower() for kw in PROMO_KEYWORDS):
                start = max(0, i - 1)
                end = min(len(lines), i + 3)
                block = " ".join(l.strip() for l in lines[start:end] if l.strip())
                if block:
                    found.append(block[:400])
        seen = set()
        result = []
        for item in found:
            if item not in seen:
                seen.add(item)
                result.append(item)
            if len(result) >= 10:
                break
        return result
