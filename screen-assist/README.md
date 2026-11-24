# Screen-Assist

Eine Kamera filmt den Bildschirm von **PC 1** (dem gesicherten Rechner, auf dem
keine Software laufen darf). Das Bild läuft auf **PC 2**, wird dort gerade
gerechnet und auf einem Monitor angezeigt. Eine KI legt live Hinweise darüber:
Markierungen „Hier klicken" / „Das eintippen" genau auf der richtigen Stelle,
plus ein Seitenpanel mit Erklärung und Code.

PC 1 wird dabei **nicht angefasst** – keine Software, kein USB, kein Kabel.
Es ist nur „ein Foto vom Bildschirm", so wie es die IT freigegeben hat, nur
automatisiert.

> **Wichtig:** Dieses Projekt bildet genau den von der IT erlaubten Weg nach
> (Bildschirmfoto → KI). Dauerhaftes Streamen ist mehr als ein Einzelfoto –
> lass dir das von der IT einmal ausdrücklich bestätigen.

## Aufbau

```
Kamera (am Monitor-Arm)  ──►  PC 2  ──►  Entzerrung  ──►  KI (Claude)
                                             │                │
                                             ▼                ▼
                                    Monitor an PC 2:  Spiegelbild + Overlay
                                    „Hier klicken", Code im Seitenpanel
```

## Installation (auf PC 2)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="dein-schluessel"      # Windows: set ANTHROPIC_API_KEY=...
```

## 1. Kalibrieren (einmalig)

Kamera anschließen, dann:

```bash
python calibrate.py
```

Die vier Ecken des Bildschirms von PC 1 anklicken → `s` zum Speichern.
Danach ist die genaue Kameraposition fast egal – Hauptsache alle vier Ecken
sind im Bild.

## 2. Starten

```bash
python main.py
```

| Taste | Funktion |
|-------|----------|
| **Leertaste** | Frage stellen (tippen, **Enter** sendet das aktuelle Bild + Frage) |
| **Tab** | Seitenpanel ein/aus |
| **C** | Hinweis zum Neu-Kalibrieren |
| **Esc** | Beenden |

## Zum Ausprobieren ohne Kamera

In `config.json` unter `source` den Typ auf `test_image` stellen und ein
`test_screen.png` (einfach ein Screenshot) ins Verzeichnis legen. Dann läuft
alles mit dem Standbild – ideal zum Testen von Entzerrung, Overlay und KI,
bevor die Kamera hängt.

## Konfiguration (`config.json`)

| Feld | Bedeutung |
|------|-----------|
| `source.type` | `camera` oder `test_image` |
| `source.camera_index` | 0, 1, … je nach Kamera |
| `dewarp.output_width/height` | Auflösung des geraden Bildschirm-Ausschnitts |
| `display.monitor_index` | auf welchem Monitor an PC 2 angezeigt wird |
| `display.fullscreen` | Vollbild an/aus |
| `ai.model` | **Claude-Modell – auf ein für deinen Account verfügbares Modell setzen** |
| `ai.language` | `de` oder `en` |

## Eingangs-unabhängig

Die Software bekommt intern immer nur „ein Bild". Falls die IT später einen
**HDMI-Splitter/Capture-Stick** erlaubt, muss nur in `source.py` eine weitere
Quelle ergänzt werden – Entzerrung, KI und Overlay bleiben unverändert.
