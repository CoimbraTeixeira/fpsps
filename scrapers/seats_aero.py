import json
import os
import urllib.request
import urllib.parse

# European programs available on seats.aero
SOURCES = [
    "flyingblue",
    "lufthansa",
    "sas",
    "virginatlantic",
    "finnair",
    "turkish",
]

# Cabin codes used in the seats.aero API and their display labels
CABINS = [
    ("business", "J", "Business"),
    ("first", "F", "First"),
]

# Minimum remaining seats to include in highlights
MIN_SEATS = 1


class SeatsAeroScraper:
    name = "seats.aero (Europe Award Availability)"
    url = "https://seats.aero"

    def __init__(self):
        self.api_key = os.environ.get("SEATS_AERO_API_KEY", "")

    def scrape(self) -> dict:
        if not self.api_key:
            print("  seats.aero: SEATS_AERO_API_KEY not set — skipping", flush=True)
            return {"content": "skipped:no_api_key", "promotions": []}

        highlights = []
        for source in SOURCES:
            for cabin_param, cabin_code, cabin_label in CABINS:
                try:
                    rows = self._fetch(source, cabin_param)
                    highlights.extend(
                        self._extract(rows, source, cabin_code, cabin_label)
                    )
                except Exception as exc:
                    print(f"  seats.aero {source}/{cabin_param}: {exc}", flush=True)

        # Sort for stable hashing
        highlights.sort()
        return {
            "content": json.dumps(highlights),
            "promotions": highlights[:15],
        }

    def _fetch(self, source: str, cabin: str) -> list:
        params = urllib.parse.urlencode(
            {
                "source": source,
                "cabin": cabin,
                "origin_region": "Europe",
                "take": 200,
            }
        )
        req = urllib.request.Request(
            f"https://seats.aero/partnerapi/availability?{params}",
            headers={
                "Partner-Authorization": self.api_key,
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read()).get("data", [])

    def _extract(
        self, rows: list, source: str, cabin_code: str, cabin_label: str
    ) -> list[str]:
        results = []
        for item in rows:
            avail_key = f"{cabin_code}Available"
            mileage_key = f"{cabin_code}MileageCost"
            if not item.get(avail_key):
                continue
            remaining = item.get(f"{cabin_code}RemainingSeats", 0) or 0
            if remaining < MIN_SEATS:
                continue
            origin = item.get("OriginAirport", "?")
            dest = item.get("DestinationAirport", "?")
            date = item.get("Date", "?")[:10]
            mileage = item.get(mileage_key, 0) or 0
            results.append(
                f"{source.upper()} {cabin_label}: {origin}→{dest} "
                f"{date} — {remaining} seat(s), {mileage:,} miles"
            )
        return results
