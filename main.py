import json
import hashlib
import os
import sys
from datetime import datetime, timezone

from scrapers import get_all_scrapers
from notifier import send_notification

STATE_FILE = "state.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def main():
    state = load_state()
    alerts = []

    for scraper in get_all_scrapers():
        print(f"Checking {scraper.name}...", flush=True)
        try:
            result = scraper.scrape()
            new_hash = content_hash(result["content"])

            prev = state.get(scraper.name, {})
            prev_hash = prev.get("hash")

            if prev_hash is None:
                print(f"  First run — recording baseline", flush=True)
            elif prev_hash != new_hash:
                print(f"  CHANGE DETECTED", flush=True)
                alerts.append({
                    "airline": scraper.name,
                    "url": scraper.url,
                    "promotions": result["promotions"],
                })
            else:
                print(f"  No change", flush=True)

            state[scraper.name] = {
                "hash": new_hash,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "promotions": result["promotions"],
            }

        except Exception as exc:
            print(f"  ERROR: {exc}", flush=True)

    save_state(state)

    if alerts:
        send_notification(alerts)
        print(f"\nAlert sent for: {', '.join(a['airline'] for a in alerts)}", flush=True)
    else:
        print("\nNo changes detected.", flush=True)


def test_email():
    print("Sending test email...", flush=True)
    send_notification([{
        "airline": "Test Airline",
        "url": "https://example.com",
        "promotions": ["This is a test notification from fpsps — email delivery is working."],
    }])
    print("Test email sent.", flush=True)


if __name__ == "__main__":
    if "--test-email" in sys.argv:
        test_email()
    else:
        main()
