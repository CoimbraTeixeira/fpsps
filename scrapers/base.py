from abc import ABC
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

PROMO_KEYWORDS = [
    "bonus", "promotion", "promo", "special offer", "limited time",
    "% off", "% bonus", "discount", "sale", "extra miles", "buy miles",
    "purchase miles", "earn more", "miles sale", "points sale",
]


class BaseScraper(ABC):
    name: str
    url: str

    def scrape(self) -> dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-GB",
                viewport={"width": 1280, "height": 800},
                timezone_id="Europe/London",
            )
            page = context.new_page()
            # hide the webdriver flag that sites use to detect automation
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            try:
                self._goto(page, self.url)
                self._wait_for_content(page)
                text = self._extract_text(page)
            finally:
                browser.close()

        return {
            "content": text,
            "promotions": self._find_promotions(text),
        }

    def _goto(self, page, url: str):
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except (PlaywrightTimeout, PlaywrightError):
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

    def _wait_for_content(self, page):
        pass

    def _extract_text(self, page) -> str:
        return page.inner_text("body")

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
