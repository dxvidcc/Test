# chess-glasses

Sagt dir über die Meta-Brille (ohne Display) per Sprache den besten Schachzug an.
Die Brille überträgt ihr Kamerabild per WhatsApp-Videoanruf an deinen PC, das Script
liest das Brett, rechnet mit Stockfish und spricht den Zug zurück in den Anruf – du
hörst ihn in den Brillen-Lautsprechern. Läuft auf **Windows** und macOS.

```
Brille ──WhatsApp-Videoanruf──▶ PC (WhatsApp-App)
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
                       Sprachausgabe → virtuelles Kabel = Mikrofon von WhatsApp → Ohr
```

## Einrichtung (Windows)

1. **Python** installieren (python.org, beim Installieren „Add python.exe to PATH“ anhaken).
2. **VB-CABLE** installieren (vb-audio.com/Cable, als Administrator), danach neu starten.
   Das ist das virtuelle Kabel: was auf „CABLE Input“ abgespielt wird, kommt bei
   „CABLE Output“ als Mikrofon wieder heraus.
3. **Stockfish** für Windows laden (stockfishchess.org), entpacken und die `.exe` als
   `stockfish.exe` in diesen Ordner legen.
4. **WhatsApp** aus dem Microsoft Store installieren und mit dem zweiten Konto anmelden.
5. In diesem Ordner eine Eingabeaufforderung öffnen und einmalig:
   ```
   pip install -r requirements.txt
   setx ANTHROPIC_API_KEY "sk-ant-..."
   ```
   Danach das Fenster schließen und neu öffnen (sonst kennt es den Key noch nicht).
6. Optional deutsche Stimme: Einstellungen → Zeit und Sprache → Sprache → Deutsch →
   Sprachausgabe.

## Spielen (Windows)

1. Mit der Brille den PC per WhatsApp-**Video** anrufen, am PC annehmen.
2. Im Anruf als **Mikrofon „CABLE Output“** wählen. Das Anruffenster sichtbar lassen
   (nicht minimieren).
3. Doppelklick auf **`Schach.bat`**, `w` oder `s` eingeben – fertig.

Ton prüfen, während der Anruf läuft: `python chesscoach.py --test-voice` – du solltest
„Test. Springer f3.“ in der Brille hören.

## Einrichtung (macOS)

`brew install stockfish blackhole-2ch`, `pip install -r requirements.txt`,
`export ANTHROPIC_API_KEY=...`, Terminal die Bildschirmaufnahme erlauben, dann
`python chesscoach.py --color white`. Mikrofon in WhatsApp: BlackHole 2ch.

## Optionen

| Option | Bedeutung |
|---|---|
| `--think 0.5` | Stockfish-Bedenkzeit pro Zug in Sekunden |
| `--region x,y,w,h` | festen Bildschirmbereich nehmen statt das WhatsApp-Fenster zu suchen |
| `--device ''` | über die Lautsprecher statt ins virtuelle Kabel sprechen (zum Testen) |
| `--stockfish PFAD` | Stockfish liegt woanders |
| `--lang en` | Ansagen auf Englisch |
| `--fen "<FEN>"` | mitten in einer Partie einsteigen |
| `--announce-opponent` | auch den erkannten Gegnerzug ansagen (gut zum Prüfen) |
| `--test-voice` | nur einen Testsatz in den Anruf sprechen |
| `CHESSCOACH_MODEL=...` | anderes Claude-Modell (Standard `claude-opus-5-5`) |

Tipps: Brett möglichst komplett und von oben im Bild halten, Hand nach dem Zug kurz
wegnehmen. Wenn ein Zug falsch erkannt wurde, beenden (`Strg+C`, die aktuelle FEN wird
ausgegeben) und mit korrigiertem `--fen` neu starten.

**Fair Play:** In Turnieren, Vereins- oder gewerteten Partien ist das Betrug
(FIDE-Regeln, Ausschluss). Nur für Spaß-, Trainings- oder Analysepartien verwenden, bei
denen der Gegner Bescheid weiß.
