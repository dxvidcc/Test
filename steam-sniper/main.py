#!/usr/bin/env python3
"""
Steam CS:GO Skin Sniper
Überwacht den Steam-Markt auf Skins innerhalb einer Preisspanne
und kauft sie automatisch (wenn auto_buy=true).

Setup:
  1. cp config.example.json config.json
  2. Trage deine Steam-Zugangsdaten + 2FA-Secrets ein
  3. pip install -r requirements.txt
  4. python main.py
"""

import json
import sys
import time
from pathlib import Path

import schedule
from colorama import Fore, Style, init
from steampy.client import SteamClient

from market import SteamMarket
from sniper import SkinSniper

init(autoreset=True)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"{Fore.RED}config.json nicht gefunden.{Style.RESET_ALL}")
        print(f"Kopiere config.example.json → config.json und fülle deine Daten ein.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def build_client(config: dict) -> SteamClient:
    client = SteamClient(config["api_key"])
    client.login(
        username=config["username"],
        password=config["password"],
        steam_guard=json.dumps({
            "shared_secret": config["shared_secret"],
            "identity_secret": config["identity_secret"],
        }),
    )
    return client


def print_banner(config: dict) -> None:
    mn = config["price_range"]["min_cents"]
    mx = config["price_range"]["max_cents"]
    interval = config.get("check_interval_seconds", 30)
    auto = config.get("auto_buy", False)

    print(f"""
{Fore.CYAN}╔══════════════════════════════════════╗
║      Steam CS:GO Skin Sniper         ║
╚══════════════════════════════════════╝{Style.RESET_ALL}
  Preisspanne : {mn} – {mx} Cent
  Skins       : {len(config['skins'])}
  Interval    : {interval}s
  Auto-Kauf   : {'JA' if auto else 'NEIN'}
""")
    print(f"{Fore.YELLOW}Überwachte Skins:{Style.RESET_ALL}")
    for s in config["skins"]:
        print(f"  • {s}")
    print()


def main() -> None:
    config = load_config()
    print_banner(config)

    print(f"{Fore.CYAN}Melde bei Steam an …{Style.RESET_ALL}")
    client = build_client(config)
    print(f"{Fore.GREEN}Anmeldung erfolgreich!{Style.RESET_ALL}\n")

    market = SteamMarket(client._session, currency=config.get("currency", 3))
    sniper = SkinSniper(client, market, config)

    interval = config.get("check_interval_seconds", 30)

    def job():
        remaining = sniper.remaining_targets()
        if not remaining:
            print(f"{Fore.GREEN}Alle Skins wurden gekauft. Bot wird beendet.{Style.RESET_ALL}")
            sys.exit(0)
        print(f"{Fore.CYAN}--- Scan läuft ({len(remaining)} Skin(s) im Visier) ---{Style.RESET_ALL}")
        sniper.run_once()

    job()  # Sofort beim Start einmal prüfen
    schedule.every(interval).seconds.do(job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot gestoppt.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
