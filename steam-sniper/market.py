import time
import requests
from colorama import Fore, Style

APPID_CSGO = 730
MARKET_BASE = "https://steamcommunity.com/market"

CURRENCY_NAMES = {
    1: "USD",
    3: "EUR",
    5: "GBP",
}


class SteamMarket:
    def __init__(self, session: requests.Session, currency: int = 3):
        self.session = session
        self.currency = currency

    def get_listings(self, market_hash_name: str, count: int = 10) -> list[dict]:
        url = f"{MARKET_BASE}/listings/{APPID_CSGO}/{requests.utils.quote(market_hash_name)}/render/"
        params = {
            "start": 0,
            "count": count,
            "currency": self.currency,
            "language": "english",
            "format": "json",
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Listings fetch failed for '{market_hash_name}': {e}{Style.RESET_ALL}")
            return []

        listings = []
        raw_listings = data.get("listinginfo", {})
        assets = data.get("assets", {}).get(str(APPID_CSGO), {}).get("2", {})

        for listing_id, info in raw_listings.items():
            converted = info.get("converted_price", 0)
            converted_fee = info.get("converted_fee", 0)
            total_cents = converted + converted_fee

            asset_id = info.get("asset", {}).get("id", "")
            asset = assets.get(asset_id, {})

            listings.append({
                "listing_id": listing_id,
                "price_cents": total_cents,
                "asset_id": asset_id,
                "name": asset.get("market_hash_name", market_hash_name),
            })

        listings.sort(key=lambda x: x["price_cents"])
        return listings

    def get_lowest_price(self, market_hash_name: str) -> int | None:
        url = f"{MARKET_BASE}/priceoverview/"
        params = {
            "appid": APPID_CSGO,
            "currency": self.currency,
            "market_hash_name": market_hash_name,
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                return None
            # Steam liefert den Preis als String z.B. "0,05€"
            lowest_str = data.get("lowest_price", "")
            return _parse_price_string(lowest_str)
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Price overview failed for '{market_hash_name}': {e}{Style.RESET_ALL}")
            return None


def _parse_price_string(price_str: str) -> int | None:
    """Wandelt Steam-Preisstrings wie '0,21€' oder '$0.21' in Cent um."""
    import re
    digits = re.sub(r"[^\d]", "", price_str)
    if digits:
        return int(digits)
    return None
