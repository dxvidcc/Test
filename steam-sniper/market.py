import requests
from colorama import Fore, Style

APPID_CSGO = 730
MARKET_BASE = "https://steamcommunity.com/market"


class SteamMarket:
    def __init__(self, cookies: dict, currency: int = 3):
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9",
        })
        self.currency = currency
        self.sessionid = cookies.get("sessionid", "")

    def test_login(self) -> bool:
        try:
            resp = self.session.get(
                f"{MARKET_BASE}/getwalletbalance/",
                timeout=10,
            )
            return resp.json().get("success") == 1
        except Exception:
            return False

    def get_listings(self, market_hash_name: str, count: int = 5) -> list[dict]:
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
            print(f"{Fore.RED}[FEHLER] Listings für '{market_hash_name}': {e}{Style.RESET_ALL}")
            return []

        listings = []
        raw_listings = data.get("listinginfo", {})
        assets = data.get("assets", {}).get(str(APPID_CSGO), {}).get("2", {})

        for listing_id, info in raw_listings.items():
            subtotal = info.get("converted_price", 0)
            fee = info.get("converted_fee", 0)
            asset_id = info.get("asset", {}).get("id", "")
            asset = assets.get(asset_id, {})

            listings.append({
                "listing_id": listing_id,
                "subtotal": subtotal,
                "fee": fee,
                "price_cents": subtotal + fee,
                "name": asset.get("market_hash_name", market_hash_name),
            })

        listings.sort(key=lambda x: x["price_cents"])
        return listings

    def buy_listing(self, listing: dict, market_hash_name: str) -> bool:
        url = f"{MARKET_BASE}/buylisting/{listing['listing_id']}"
        data = {
            "sessionid": self.sessionid,
            "currency": self.currency,
            "subtotal": listing["subtotal"],
            "fee": listing["fee"],
            "total": listing["price_cents"],
            "quantity": 1,
        }
        headers = {
            "Referer": f"{MARKET_BASE}/listings/{APPID_CSGO}/{requests.utils.quote(market_hash_name)}",
            "Origin": "https://steamcommunity.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            resp = self.session.post(url, data=data, headers=headers, timeout=15)
            result = resp.json()
            return result.get("wallet_info") is not None or result.get("purchaseid") is not None
        except Exception as e:
            print(f"{Fore.RED}[FEHLER] Kauf: {e}{Style.RESET_ALL}")
            return False
