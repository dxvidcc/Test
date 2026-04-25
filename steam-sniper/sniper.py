import time
from datetime import datetime
from colorama import Fore, Style

from market import SteamMarket


class SkinSniper:
    def __init__(self, market: SteamMarket, config: dict):
        self.market = market
        self.skins: list[str] = config["skins"]
        self.min_cents: int = config["price_range"]["min_cents"]
        self.max_cents: int = config["price_range"]["max_cents"]
        self.auto_buy: bool = config.get("auto_buy", False)
        self.max_buy_per_skin: int = config.get("max_buy_per_skin", 1)
        self.bought_count: dict[str, int] = {skin: 0 for skin in self.skins}

    def _log(self, msg: str, color: str = Style.RESET_ALL) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.CYAN}[{ts}]{Style.RESET_ALL} {color}{msg}{Style.RESET_ALL}")

    def check_skin(self, skin_name: str) -> None:
        if self.bought_count.get(skin_name, 0) >= self.max_buy_per_skin:
            return

        listings = self.market.get_listings(skin_name, count=5)
        if not listings:
            self._log(f"Keine Listings gefunden: {skin_name}", Fore.YELLOW)
            return

        cheapest = listings[0]
        price = cheapest["price_cents"]

        if self.min_cents <= price <= self.max_cents:
            self._log(
                f"SNIPE! '{skin_name}' für {price / 100:.2f} ct "
                f"(Ziel: {self.min_cents}–{self.max_cents} ct)",
                Fore.GREEN,
            )
            if self.auto_buy:
                self._buy(skin_name, cheapest)
            else:
                self._log("auto_buy=false → kein automatischer Kauf.", Fore.YELLOW)
        else:
            self._log(f"'{skin_name}' → {price / 100:.2f} ct — außerhalb des Bereichs")

    def _buy(self, skin_name: str, listing: dict) -> None:
        self._log(f"Kaufe '{skin_name}' für {listing['price_cents'] / 100:.2f} ct …", Fore.MAGENTA)
        if self.market.buy_listing(listing, skin_name):
            self.bought_count[skin_name] = self.bought_count.get(skin_name, 0) + 1
            self._log(f"Kauf erfolgreich! '{skin_name}' ist jetzt in deinem Inventar.", Fore.GREEN)
        else:
            self._log("Kauf fehlgeschlagen — Listing evtl. schon weg.", Fore.RED)

    def run_once(self) -> None:
        for skin in self.skins:
            self.check_skin(skin)
            time.sleep(1.5)

    def remaining_targets(self) -> list[str]:
        return [s for s in self.skins if self.bought_count.get(s, 0) < self.max_buy_per_skin]
