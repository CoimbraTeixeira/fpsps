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


def promo_hash(promotions: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(promotions)).encode()).hexdigest()[:16]


def main():
    state = load_state()
    alerts = []

    for scraper in get_all_scrapers():
        print(f"Checking {scraper.name}...", flush=True)
        try:
            result = scraper.scrape()
            promotions = result["promotions"]
            new_hash = promo_hash(promotions)

            prev = state.get(scraper.name, {})
            prev_hash = prev.get("promo_hash")

            if prev_hash is None:
                print(f"  First run — baseline: {len(promotions)} promotion(s) found", flush=True)
            elif new_hash != prev_hash and promotions:
                print(f"  NEW PROMOTION(S) DETECTED: {len(promotions)}", flush=True)
                alerts.append({
                    "airline": scraper.name,
                    "url": scraper.url,
                    "promotions": promotions,
                })
            elif new_hash != prev_hash:
                print(f"  Page changed but no promotions detected — skipping", flush=True)
            else:
                print(f"  No new promotions", flush=True)

            state[scraper.name] = {
                "promo_hash": new_hash,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "promotions": promotions,
            }

        except Exception as exc:
            print(f"  ERROR: {exc}", flush=True)

    save_state(state)

    if alerts:
        send_notification(alerts)
        print(f"\nAlert sent for: {', '.join(a['airline'] for a in alerts)}", flush=True)
    else:
        print("\nNo new promotions detected.", flush=True)


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
