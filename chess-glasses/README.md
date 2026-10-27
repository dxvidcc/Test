# chess-glasses

Sagt dir über die Meta-Brille (ohne Display) per Sprache den besten Schachzug an.
Die Brille überträgt ihr Kamerabild per WhatsApp-Videoanruf an deinen Mac, das Script
liest das Brett, rechnet mit Stockfish und spricht den Zug zurück in den Anruf – du
hörst ihn in den Brillen-Lautsprechern.

```
Brille ──WhatsApp-Videoanruf──▶ Mac (WhatsApp-App)
                                  │ Screenshot ~1×/s
                                  ▼
                       lokaler Check (unscharf? keine Änderung? → überspringen)
                                  ▼
                       Claude liest das Brett (Stellung als 8 Reihen)
                                  ▼
                       python-chess: welcher legale Zug passt? (2 Frames müssen übereinstimmen)
                                  ▼
                       Stockfish (0,5 s) → "Springer g1 nach f3"
                                  ▼
                       say → BlackHole 2ch = Mikrofon von WhatsApp → Ohr
```

## Einrichtung (macOS)

1. `brew install stockfish blackhole-2ch`
2. `pip install -r requirements.txt`
3. `export ANTHROPIC_API_KEY=...`
4. Zweites WhatsApp-Konto auf dem Mac (oder ein Freund) – die Brille startet über dein
   Handy einen Videoanruf an dieses Konto. Auf der Brille: „Hey Meta, starte einen
   Videoanruf mit …“ bzw. im Anruf auf die Brillenkamera umschalten.
5. WhatsApp-Desktop → Einstellungen → Anrufe: **Mikrofon = BlackHole 2ch**.
6. Mac: Systemeinstellungen → Datenschutz → **Bildschirmaufnahme** für das Terminal erlauben.
7. Optional deutsche Stimme: Systemeinstellungen → Bedienungshilfen → Gesprochene Inhalte → „Anna“.

## Start

```bash
python chesscoach.py --color white          # du spielst Weiß
python chesscoach.py --color black --announce-opponent
```

Nützliche Optionen:

| Option | Bedeutung |
|---|---|
| `--think 0.5` | Stockfish-Bedenkzeit pro Zug in Sekunden |
| `--region x,y,w,h` | Bildschirmbereich, falls das WhatsApp-Fenster nicht gefunden wird |
| `--device ''` | über die Mac-Lautsprecher statt BlackHole sprechen (zum Testen) |
| `--lang en` | Ansagen auf Englisch |
| `--fen "<FEN>"` | mitten in einer Partie einsteigen |
| `--announce-opponent` | auch den erkannten Gegnerzug ansagen (gut zum Prüfen) |
| `CHESSCOACH_MODEL=...` | anderes Claude-Modell (Standard `claude-opus-5-5`) |

Tipps: Brett möglichst komplett und von oben im Bild halten, Hand nach dem Zug kurz
wegnehmen. Wenn ein Zug falsch erkannt wurde, mit `Strg+C` beenden (die aktuelle FEN wird
ausgegeben) und mit korrigiertem `--fen` neu starten.

**Fair Play:** In Turnieren, Vereins- oder gewerteten Partien ist das Betrug
(FIDE-Regeln, Ausschluss). Nur für Spaß-, Trainings- oder Analysepartien verwenden, bei
denen der Gegner Bescheid weiß.
