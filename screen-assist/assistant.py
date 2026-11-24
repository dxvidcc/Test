"""KI-Anbindung: schickt den entzerrten Bildschirm-Ausschnitt + deine Frage
an Claude und bekommt strukturierte Hinweise zurueck.

Die KI antwortet als JSON mit normalisierten Koordinaten (0..1), bezogen auf
das gerade Bildschirm-Rechteck. Dadurch lassen sich Markierungen pixelgenau
auf das Spiegelbild legen -- egal wie gross das Anzeigefenster ist.

Benoetigt die Umgebungsvariable ANTHROPIC_API_KEY.
"""

import base64
import json
import os
import re

import cv2

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


SYSTEM_PROMPT = """Du bist ein Assistent, der einem Nutzer live hilft, der an
einem Computer (PC 1) arbeitet. Du siehst ein Foto/Abbild seines Bildschirms.
Der Nutzer stellt eine Frage oder hat ein Problem.

Antworte AUSSCHLIESSLICH als JSON in genau dieser Struktur:
{
  "summary": "kurze Erklaerung, was zu tun ist (1-3 Saetze)",
  "annotations": [
    {
      "type": "click | type | look | warning",
      "x": 0.0,              // horizontale Position auf dem Bildschirm, 0=links 1=rechts
      "y": 0.0,              // vertikale Position, 0=oben 1=unten
      "label": "sehr kurzer Text fuer die Sprechblase, z.B. 'Hier klicken'",
      "detail": "optional laengerer Text fuer das Seitenpanel",
      "code": "optional Code, der eingetippt werden soll"
    }
  ]
}

Regeln:
- x und y beziehen sich auf die sichtbare Stelle auf dem Bildschirm im Bild.
- Schaetze die Koordinaten so genau wie moeglich anhand dessen, was du siehst.
- Hoechstens 5 annotations. Nur das Noetige markieren.
- 'click' = anklicken, 'type' = hier etwas eintippen (nutze dann 'code'),
  'look' = hier hinschauen/lesen, 'warning' = Warnung.
- Kein Text ausserhalb des JSON. Antworte auf {lang}.
"""


class Assistant:
    def __init__(self, config: dict):
        if anthropic is None:
            raise RuntimeError("Paket 'anthropic' fehlt. pip install anthropic")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY ist nicht gesetzt. "
                "Setze deinen API-Schluessel als Umgebungsvariable."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = config["ai"]["model"]
        self.max_tokens = int(config["ai"]["max_tokens"])
        lang = {"de": "Deutsch", "en": "Englisch"}.get(
            config["ai"].get("language", "de"), "Deutsch"
        )
        self.system = SYSTEM_PROMPT.replace("{lang}", lang)

    @staticmethod
    def _encode(frame) -> str:
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            raise RuntimeError("Bild konnte nicht kodiert werden.")
        return base64.b64encode(buf.tobytes()).decode("ascii")

    def ask(self, frame, question: str) -> dict:
        """frame: entzerrter Bildschirm (BGR). question: Frage des Nutzers.
        Rueckgabe: dict mit 'summary' und 'annotations'."""
        img_b64 = self._encode(frame)
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": question or "Was soll ich hier als Naechstes tun?",
                        },
                    ],
                }
            ],
        )
        text = "".join(
            block.text for block in message.content if block.type == "text"
        )
        return self._parse(text)

    @staticmethod
    def _parse(text: str) -> dict:
        # JSON aus der Antwort herausschneiden (robust gegen Rahmen-Text).
        match = re.search(r"\{.*\}", text, re.DOTALL)
        raw = match.group(0) if match else text
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {"summary": text.strip()[:500], "annotations": []}
        data.setdefault("summary", "")
        data.setdefault("annotations", [])
        # Koordinaten absichern.
        clean = []
        for a in data["annotations"]:
            try:
                a["x"] = max(0.0, min(1.0, float(a.get("x", 0.5))))
                a["y"] = max(0.0, min(1.0, float(a.get("y", 0.5))))
            except (TypeError, ValueError):
                a["x"], a["y"] = 0.5, 0.5
            a.setdefault("type", "look")
            a.setdefault("label", "")
            clean.append(a)
        data["annotations"] = clean
        return data
