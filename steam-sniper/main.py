#!/usr/bin/env python3
"""
Steam CS:GO Skin Sniper — Cookie-basierte Authentifizierung
Kein SDA, keine 2FA-Secrets nötig.

Setup:
  1. cp config.example.json config.json
  2. Cookies aus dem Browser eintragen (Anleitung in README)
  3. pip install -r requirements.txt
  4. python main.py
"""

import json
import sys
import time
from pathlib import Path

import schedule
from colorama import Fore, Style, init

from market import SteamMarket
from sniper import SkinSniper

init(autoreset=True)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"{Fore.RED}config.json nicht gefunden!{Style.RESET_ALL}")
        print("Kopiere config.example.json → config.json und trage deine Cookies ein.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


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
  Auto-Kauf   : {'JA' if auto else 'NEIN (Testmodus)'}
""")
    print(f"{Fore.YELLOW}Überwachte Skins:{Style.RESET_ALL}")
    for s in config["skins"]:
        print(f"  • {s}")
    print()


def main() -> None:
    config = load_config()
    print_banner(config)

    cookies = config.get("cookies", {})
    if not cookies.get("sessionid") or not cookies.get("steamLoginSecure"):
        print(f"{Fore.RED}Cookies fehlen in config.json! Bitte sessionid und steamLoginSecure eintragen.{Style.RESET_ALL}")
        sys.exit(1)

    market = SteamMarket(cookies, currency=config.get("currency", 3))

    print(f"{Fore.CYAN}Prüfe Steam-Login …{Style.RESET_ALL}")
    if not market.test_login():
        print(f"{Fore.RED}Login fehlgeschlagen — Cookies abgelaufen oder ungültig!{Style.RESET_ALL}")
        print("Bitte neue Cookies aus dem Browser kopieren und in config.json eintragen.")
        sys.exit(1)
    print(f"{Fore.GREEN}Login erfolgreich!{Style.RESET_ALL}\n")

    sniper = SkinSniper(market, config)
    interval = config.get("check_interval_seconds", 30)

    def job() -> None:
        remaining = sniper.remaining_targets()
        if not remaining:
            print(f"{Fore.GREEN}Alle Skins gekauft! Bot wird beendet.{Style.RESET_ALL}")
            sys.exit(0)
        print(f"{Fore.CYAN}--- Scan läuft ({len(remaining)} Skin(s) im Visier) ---{Style.RESET_ALL}")
        sniper.run_once()

    job()
    schedule.every(interval).seconds.do(job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot gestoppt.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
