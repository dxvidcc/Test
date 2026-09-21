# Kleinteile-Automat — Mechanik-Konzept

Ausgabeautomat für Schrauben, Muttern und Unterlegscheiben. Bedienung über ein
Panel ("7x M3x10"), Ausgabe stückgenau in eine Schale, wie der Münzauswurf an
einer Supermarktkasse.

Dieses Dokument behandelt **ausschließlich die Mechanik**: Bevorratung,
Vereinzelung, Auswurf, Zählung und Fertigung. Steuerungsplattform (ESP32 / Pi /
Arduino) ist bewusst offen gelassen; alle Schnittstellen sind so beschrieben,
dass jede Plattform sie bedienen kann.

---

## 0. Kurzfassung

- **Ein Fach pro Sorte**, als austauschbare **Kartusche**. Die Kartusche bringt
  die sortenspezifische Geometrie mit (Rohrmaß, Taschentiefe, Schlitzbreite),
  der Antrieb bleibt im Gerät. Eine neue Schraubensorte = ein neues Druckteil,
  keine neue Elektronik.
- **Zwei Magazin-Bauformen** decken das gesamte Sortiment ab:
  - **Klasse A — Stapelrohr** für flache, rotationssymmetrische Teile
    (Unterlegscheiben, Muttern). Echter "Münzstapel".
  - **Klasse B — Hängeschiene (Schlitzrohr)** für Schrauben: der Schaft hängt
    im Schlitz, der Kopf liegt auf den Schlitzkanten auf. Das erzwingt eine
    definierte Lage und macht die Vereinzelung überhaupt erst berechenbar.
- **Vereinzelung**: Klasse A über ein **Taschenrad**, Klasse B über ein
  **Doppelfinger-Escapement**. Beide haben dieselbe Antriebsschnittstelle:
  *eine Wellenumdrehung = genau ein Teil*.
- **Zählen nur nach Hüben ist nicht zulässig.** Jeder Auswurf wird im Fallschacht
  einzeln verifiziert (induktiver Sensor oder Lichtschranke). Fehlt ein Teil,
  schiebt die Steuerung nach; nach N Fehlversuchen: Abbruch mit Störmeldung.
- **Kritischer Grenzfall M1**: unterhalb M2 ist die Hängeschiene nicht mehr
  zuverlässig. Für M1/M1.6 siehe Anhang B — dort wird ein Lochscheiben-Magazin
  mit Gewichtsverifikation empfohlen.

---

## 1. Anforderungen

| # | Anforderung | Zielwert |
|---|---|---|
| A1 | Teilespektrum Schrauben | M1 – M8, Länge 4 – 40 mm, Zylinder-/Linsen-/Senkkopf |
| A2 | Teilespektrum Muttern | M2 – M8, ISO 4032 / 4033, Stoppmuttern optional |
| A3 | Teilespektrum Scheiben | M2 – M8, ISO 7089/7090, Federringe als Sonderfall |
| A4 | Stückgenauigkeit | 100 % — die ausgegebene Menge muss der bestellten entsprechen |
| A5 | Durchsatz | ≥ 1 Teil/s pro Fach (7 Stück ≈ 7 s sind akzeptabel) |
| A6 | Fachanzahl Zielausbau | 24 – 48 Sorten |
| A7 | Füllmenge je Fach | ≥ 100 Teile (bei M3-Scheiben deutlich mehr) |
| A8 | Nachfüllen | im laufenden Betrieb, ohne Werkzeug, ohne Demontage |
| A9 | Fehlerrate | < 1 Blockade pro 1000 Ausgaben, kein stiller Fehlauswurf |
| A10 | Geräusch | kein metallisches Prellen im Ausgabeschacht |

**Abgrenzung:** kein Schüttgut-Handling im Gerät (siehe Abschnitt 4.3), keine
Gemischtausgabe mehrerer Sorten in einem Vorgang in der ersten Ausbaustufe.

---

## 2. Warum Kleinteile keine Münzen sind

Der Münzautomat als Vorbild trägt weiter, als man denkt — aber nicht überall.
Die Unterschiede bestimmen das gesamte Konzept:

1. **Münzen sind flach und symmetrisch.** Eine Scheibe oder Mutter auch. Eine
   Schraube ist es nicht: sie hat Kopf und Schaft, also eine Vorzugslage. Im
   glatten Rohr kippt sie, verkeilt sich quer oder stapelt sich Kopf-auf-Kopf.
   → Schrauben brauchen ein Magazin, das die Lage **erzwingt**, nicht nur führt.
2. **Münzen sind trocken und gleich dick.** Verzinkte oder geölte Schrauben
   kleben aneinander; ein Ölfilm zwischen zwei Scheiben hält zwei Teile
   zusammen, die als eines gezählt würden. → Die Vereinzelung muss geometrisch
   trennen (Tasche mit definierter Tiefe), nicht über Reibung.
3. **Münzen haben enge Toleranzen.** Ein Schraubenkopf variiert im Zehntel,
   Federringe sind aufgebogen und verhaken ineinander. → Spiel großzügiger
   auslegen und dafür die Lage mechanisch zwangsführen.
4. **Der Stapel drückt.** 200 M5-Schrauben sind ca. 400 g. Trägt der Auswurf-
   Finger diese Last, klemmt er. → Die Stapellast wird von einem separaten
   Rückhalteelement getragen, der Auswerfer arbeitet lastfrei (Abschnitt 6.2).

Daraus folgt die Zweiteilung des Sortiments in Klasse A und Klasse B.

---

## 3. Systemarchitektur: das Kartuschenprinzip

```
        ┌──────── Kartusche (je Sorte, 3D-Druck, ~2 €) ────────┐
        │  Magazin (Rohr / Hängeschiene)                        │
        │  Rückhalteelement                                     │
        │  Vereinzelungsorgan (Taschenrad bzw. Escapement)      │
        │  Kupplungsstummel  ◄── sortenunabhängige Schnittstelle│
        │  Datenmatrix-Code / Kerbcodierung (Sorte + Stückzahl) │
        └───────────────────────────────────────────────────────┘
                      │  Teil fällt nach unten
        ┌─────────────▼─────────────────────────────────────────┐
        │  Gerät (einmalig, ~40 € je Fach)                      │
        │  Getriebemotor + Index-Sensor                         │
        │  Fallschacht mit Zählsensor                           │
        │  Sammelrutsche  →  Ausgabeschale                      │
        └───────────────────────────────────────────────────────┘
```

**Die zentrale Entwurfsentscheidung:** Alles, was von der Schraubensorte abhängt,
sitzt in einem billigen Druckteil. Alles, was Geld kostet (Motor, Sensorik,
Verkabelung), ist sortenunabhängig und bleibt im Gerät. Neue Sorte = Kartusche
drucken, Parameter in die Steuerung eintragen, einstecken.

Nebeneffekte, die diese Aufteilung mitbringt:
- Nachfüllen heißt Kartusche tauschen — die volle wird in Ruhe am Tisch
  befüllt, der Automat steht nicht still.
- Eine klemmende Kartusche wird gezogen und ausgeräumt, ohne das Gerät zu öffnen.
- Die Kartusche trägt ihre Identität selbst (Code am Griff), die Steuerung kann
  eine falsch eingesteckte Kartusche erkennen, statt M4 statt M3 auszugeben.

---

## 4. Magazin-Bauformen

### 4.1 Klasse A — Stapelrohr (Scheiben, Muttern)

Senkrechtes Rohr, Teile liegen flach aufeinander. Funktioniert genau wie ein
Münzrohr.

```
        Schnitt (Seite)
        ┌─┬─────────┬─┐
        │ │ ▭▭▭▭▭▭▭ │ │   ← Scheiben, flach gestapelt
        │ │ ▭▭▭▭▭▭▭ │ │
        │ │ ▭▭▭▭▭▭▭ │ │
        │ │ ▭▭▭▭▭▭▭ │ │
        └─┴────┬────┴─┘
          ╔════╧════╗
          ║ Taschenrad ║      ← Tasche = 1 Teildicke, dreht 1 Teil heraus
          ╚════╤════╝
               ▼ Fallschacht
```

- Innenmaß = Außenmaß des Teils + Spiel (Richtwert 0,4 – 0,6 mm bei Scheiben,
  0,3 – 0,5 mm über Schlüsselweite bei Muttern).
- **Muttern:** sechskantiges Rohrprofil statt rundem. Ein rundes Rohr lässt die
  Mutter frei rotieren und verkanten; das Sechskantprofil hält sie in Lage und
  macht die Taschentiefe reproduzierbar.
- **Sonderfall Federringe:** verhaken sich ineinander (Schraubenlinie). Sie
  brauchen einen Dorn in der Rohrmitte, auf den sie aufgefädelt werden — dann
  verhalten sie sich wie Scheiben. Ohne Dorn ist die Ausgabe nicht sicher
  vereinzelbar; im Zweifel Federringe aus dem Sortiment nehmen.

### 4.2 Klasse B — Hängeschiene / Schlitzrohr (Schrauben)

Die Schraube hängt am Kopf: der Schaft steckt im Schlitz, der Kopf liegt auf den
beiden Schlitzkanten auf. Damit ist die Lage aller Teile in der Schiene
identisch — das ist die Voraussetzung für eine sichere Vereinzelung.

```
        Schnitt quer (A-A)              Ansicht längs, Neigung ~35°
        ┌──────────────────┐             ▬▬▬O                       
        │  ▬▬▬▬▬  ← Kopf   │              ▬▬▬O                      
        │────┐    ┌────────│               ▬▬▬O   ← rutschen nach
        │    │ ▌  │        │                ▬▬▬O
        │    └────┘        │                 ▬▬▬O
        │      ↑ Schaft im │                   ▬▬▬O ← vorderste Schraube
        │        Schlitz   │                      ╫  Escapement
        └──────────────────┘                      ▼
```

- Schlitzbreite = Schaft-Nenndurchmesser + 0,3 … 0,5 mm (muss über das Gewinde
  passen, nicht über den Kerndurchmesser).
- Kanalbreite oben = Kopfdurchmesser + 0,5 mm, Höhe = Kopfhöhe + 0,5 mm,
  damit sich der Kopf nicht querstellen kann.
- Neigung 30 – 45°, damit die Teile allein durch Schwerkraft nachrutschen. Bei
  kurzen Schrauben (L/d < 3) eher steiler, bei langen flacher — lange Schrauben
  schwingen sonst und rasten nicht sauber ins Escapement.
- **Längenunabhängig innerhalb einer Sorte:** die Schiene führt über Kopf und
  Schaft, nicht über die Länge. Eine M3-Schiene nimmt M3x8 bis M3x30 — die
  Kartusche bleibt dieselbe, nur der Inhalt ändert sich. Das reduziert die Zahl
  der Kartuschentypen erheblich.
- **Senkkopf** braucht eine eigene Schienenvariante: der konische Kopf zentriert
  sich in den Schlitz hinein und klemmt, wenn die Auflagekante scharf ist. Lösung:
  Auflagekante mit 90°-Fase, damit der Kopf definiert aufsitzt statt sich zu
  verkeilen.

### 4.3 Klasse C — Schüttgut (bewusst zurückgestellt)

Ein Trichter mit Wendelrad oder Rüttler wäre bedienfreundlicher (Schrauben aus
der Tüte hineinkippen), erkauft das aber mit Rückführung, Lagenerkennung und
deutlich höherer Komplexität — praktisch ein Miniatur-Wendelförderer pro Fach.

**Konsequenz für den Betrieb, ehrlich benannt:** Klasse B heißt, dass die
Schrauben beim Befüllen **orientiert** eingelegt werden müssen. Das ist der
eigentliche Aufwand im Betrieb, nicht die Ausgabe. Abmilderung:
- Befüll-Kamm: ein Werkzeug, in das eine Handvoll Schrauben gekippt und
  gerüttelt wird, bis sie in Schlitzen hängen; der Kamm wird dann an die
  Kartusche angedockt und die Reihe hinübergeschoben.
- Eine Kartusche fasst 100 – 200 Teile; bei Heimwerker-/Laborgebrauch ist das
  Befüllen dann eine Aufgabe pro Quartal, nicht pro Woche.

Siehe Abschnitt 16, offene Entscheidung O1.

---

## 5. Vereinzelung: Varianten und Bewertung

| Variante | Prinzip | Stückgenauigkeit | Klemmneigung | Teilespektrum | Kosten | Bewertung |
|---|---|---|---|---|---|---|
| **V1 Schieber** | Linearer Schieber mit Tasche, Hubmagnet | hoch | mittel (Stapellast auf Schieber) | A + B | niedrig | laut, Magnet zieht Strom, Hub nicht geregelt |
| **V2 Taschenrad** | Drehscheibe mit Tasche = 1 Teildicke | **sehr hoch** | niedrig | **A** | niedrig | **Empfehlung Klasse A** |
| **V3 Doppelfinger-Escapement** | 2 Finger, 180° versetzt auf Nockenwelle | **sehr hoch** | **sehr niedrig** | **B** | mittel | **Empfehlung Klasse B** |
| **V4 Schnecke / Auger** | Förderschnecke, Steigung = 1 Teil | mittel | niedrig | B, kurze Teile | mittel | Teil kann in Windung springen → nicht stückgenau genug für A4 |
| **V5 Wendelförderer** | Vibrationstopf | hoch | niedrig | alle | **sehr hoch** | pro Sorte ein Topf — für 24 Fächer utopisch |
| **V6 Zellenrad quer** | Trommel mit Längsnut | hoch | mittel | B | mittel | gute Alternative zu V3, aber Trommel muss je Länge angepasst werden |

**Entscheidung: V2 für Klasse A, V3 für Klasse B.** Beide werden auf dieselbe
Schnittstelle gebracht (eine Umdrehung = ein Teil, Abschnitt 7), sodass das Gerät
nicht wissen muss, welcher Typ steckt.

V1 wird verworfen, obwohl es die naheliegendste Lösung ist: der Schieber trägt
im Moment des Auswerfens die volle Stapellast, und genau dort entstehen die
Blockaden, die A9 verbietet.

---

## 6. Empfohlene Vereinzelung im Detail

### 6.1 Klasse A — Taschenrad

```
        Draufsicht Taschenrad            Schnitt
         ╭───────────────╮               Stapel ▼
        ╱                 ╲             ┌───────┐
       │      ╭─────╮      │            │ ▭▭▭▭▭ │
       │      │Tasche│     │   →        ├───────┤ ← Deckplatte
       │      ╰─────╯      │            │ ▭ ░░░ │ ← Rad, Tasche mit 1 Teil
        ╲                 ╱             ├──┬────┤ ← Bodenplatte mit Loch
         ╰───────────────╯                 ▼
```

- **Taschentiefe = Nenndicke des Teils + 0,15 mm.** Zu tief: zwei Teile fallen.
  Zu flach: das Teil schleift an der Deckplatte und wird verkantet mitgerissen.
  Dies ist das kritischste Maß der ganzen Baugruppe und muss je Sorte am realen
  Teil ausgemessen werden, nicht aus der Norm übernommen.
- Die Deckplatte über dem Rad wirkt als **Abstreifer**: ein zweites, anhaftendes
  Teil (Ölfilm) wird beim Weiterdrehen abgestreift, statt mitzufahren. Die
  Abstreifkante ist scharf auszuführen (kein Radius, keine Fase).
- Die Stapellast drückt auf die Radoberseite, nicht auf eine Auswurfkante. Das
  erzeugt Reibmoment (vom Motor aufzubringen), aber keine Blockade.
- Radmaterial mit guten Gleiteigenschaften (POM-Einleger oder PETG mit
  gleitmodifizierter Oberfläche), da hier die Dauerreibung auftritt.

### 6.2 Klasse B — Doppelfinger-Escapement

Das Kernstück des Konzepts. Zwei Finger sitzen auf einer gemeinsamen Nockenwelle,
um 180° versetzt, und arbeiten **immer gegenläufig**:

```
        Zustand 1 (Ruhe)          Zustand 2 (Auswurf)
        ═══O═O═O═O═O              ═══O═O═O═O╢O
                  ╢  ← Finger 2 zu           ╢ ← Finger 2 offen
                 ╫   ← Finger 1 offen       ╫  ← Finger 1 zu (hält Säule)
                                              ▼ ein Teil fällt
```

Ablauf einer Umdrehung:
1. **Finger 1 (Rückhalt, oben)** fährt ein und hält die gesamte Säule — ab
   jetzt ist der Bereich darunter lastfrei.
2. **Finger 2 (Auswurf, unten)** fährt aus und gibt genau die eine Schraube
   frei, die zwischen den Fingern steht. Sie fällt.
3. Finger 2 fährt wieder ein, Finger 1 öffnet, die Säule rutscht um eine
   Teilung nach.

Warum das die Blockaden löst: Der Auswurffinger bewegt sich **nie unter Last**.
Der Abstand der beiden Finger definiert geometrisch, dass genau ein Teil im
Zwischenraum steht — es gibt keinen Zustand, in dem zwei Teile durchrutschen
können. Der Abstand der Fingerebenen ist sortenabhängig (Kopfdurchmesser +
Spiel) und damit Teil der Kartuschengeometrie.

- Fingerform: keilförmig angeschrägt, damit ein Finger, der auf einen Kopf
  trifft, die Säule zurückschiebt statt zu klemmen.
- Nockenwelle mit Index-Markierung, damit die Steuerung die Ruhelage kennt und
  nicht in Zustand 2 stehen bleibt (sonst läuft die Kartusche leer).

---

## 7. Antriebsschnittstelle

Eine einzige mechanische Schnittstelle für beide Klassen:

| Merkmal | Festlegung |
|---|---|
| Kupplung | Vierkant- oder Oldham-Kupplung, Mitnahme mit Winkelspiel ≤ 5° |
| Definition | **1 Umdrehung der Kartuschenwelle = 1 ausgegebenes Teil** |
| Drehrichtung | eine Richtung im Normalbetrieb, Reversierbarkeit zwingend (Entklemmen) |
| Drehmoment | Auslegung auf 0,3 Nm an der Kartuschenwelle, Abschaltung bei Überlast |
| Drehzahl | 60 – 90 min⁻¹ → 1 – 1,5 Teile/s, erfüllt A5 |
| Lageerkennung | Index je Umdrehung (Hall/Mikroschalter) **im Gerät**, nicht in der Kartusche |

Antriebsoptionen im Gerät, ohne Vorentscheidung für eine Steuerungsplattform:

- **Getriebemotor (N20-Klasse) + Index-Sensor** — günstig, leise, laufruhig;
  die Umdrehung wird über den Index beendet, nicht über die Zeit. Empfohlen.
- **Schrittmotor (28BYJ-48-Klasse)** — Position ohne Sensor, aber langsamer und
  bei Blockade unbemerkt Schrittverlust. Nur mit Index-Rückmeldung akzeptabel.
- **Modellbau-Servo** — nur für Schieberlösungen sinnvoll, nicht für die
  Dauerdrehung des Taschenrads.
- **Hubmagnet** — verworfen (laut, keine Rückmeldung, hoher Spitzenstrom).

**Wichtig:** Der Index-Sensor gehört ins Gerät, nicht in die Kartusche. Sonst
wandert Elektronik ins Verschleißteil und das Kartuschenprinzip ist dahin.

**Reversierstrategie:** Erkennt die Steuerung Überlast (Motorstrom) oder
ausbleibenden Index, fährt sie 1/4 Umdrehung zurück und erneut vor — bis zu
drei Versuche. Das löst die weitaus meisten Verklemmungen ohne Eingriff.

---

## 8. Zählung und Verifikation

**Grundsatz: gezählt wird, was unten ankommt — nicht, was oben angesteuert
wurde.** Ein Hubzähler ist eine Absichtserklärung, keine Messung. Anforderung A4
ist nur mit einem geschlossenen Regelkreis erfüllbar:

```
   Soll: 7 Stück
     ├─► Umdrehung auslösen
     │      └─► Sensor im Fallschacht meldet Teil?
     │             ja  → Zähler +1
     │             nein → Wiederholung (max. 3), sonst Störung
     └─◄ bis Zähler = Soll
```

Sensorvarianten für den Fallschacht:

| Sensor | Eignung | Anmerkung |
|---|---|---|
| **Induktiver Näherungssensor** | **empfohlen** | reagiert nur auf Metall, unempfindlich gegen Staub, Öl, Späne; erkennt auch kleine Teile sicher |
| Gabellichtschranke | gut ab M2 | verschmutzt mit der Zeit, braucht engen Schacht |
| Reflexlichtschranke | schwach | glänzende verzinkte Teile streuen unzuverlässig |
| Wägezelle in der Schale | Ergänzung | prüft die Gesamtmenge über das bekannte Stückgewicht — fängt genau den Fall ab, den der Schachtsensor nicht sieht: zwei aneinanderklebende Teile |

**Empfohlene Kombination:** induktiver Sensor je Fach (oder je Sammelrutsche,
wenn immer nur ein Fach gleichzeitig läuft — das spart erheblich Sensorik) plus
**eine** Wägezelle unter der Ausgabeschale als Plausibilitätsprüfung über die
Gesamtausgabe. Bei M1-Teilen ist die Wägezelle nicht Ergänzung, sondern das
führende Messmittel (Anhang B).

Der Schachtsensor braucht eine Entprellung in Hardware oder Software: ein
fallendes Teil kann an der Schachtwand abprallen und zwei Flanken erzeugen.
Sperrzeit nach einer erkannten Flanke: ca. 50 ms.

---

## 9. Füllstand und Nachfüllen

- **Füllstand "leer"**: Reflex- oder Gabellichtschranke unmittelbar über dem
  Vereinzelungsorgan. Meldet zuverlässig den Zustand, der den Betrieb stoppt.
- **Füllstand "niedrig"**: Sensor auf ca. 20 % Höhe der Schiene/des Rohrs, für
  die Nachbestell-/Nachfüllmeldung.
- **Rechnerischer Bestand**: die Steuerung führt den Zählerstand je Kartusche
  mit. Das ist für die Anzeige gut genug, ersetzt aber nie den Leer-Sensor —
  fehlerhafte Zählungen und Handentnahmen driften auseinander.
- **Kartuschentausch**: Code am Kartuschengriff (Datamatrix oder mechanische
  Kerbcodierung) identifiziert Sorte und Sollfüllung. Steckt eine unerwartete
  Kartusche im Schacht, verweigert die Steuerung die Ausgabe, statt die falsche
  Schraube auszugeben.
- Kartuschen sind **transparent** auszuführen (klares PETG-Fenster oder
  Acrylrohr): der sichtbare Füllstand ist die beste Bedienerinformation und
  kostet nichts.

---

## 10. Sammelschacht, Ausgabeschale, Akustik

```
   Fach 1   Fach 2   Fach 3   ...
     │        │        │
     ▼        ▼        ▼
   ╲ ╲ ╲ ╲ ╲ ╲ ╲ ╲ ╲ ╲ ╲        ← Sammelrutsche, ca. 40° geneigt,
    ╲   ╲   ╲   ╲   ╲   ╲         mit TPU/Filz ausgekleidet
     ╲___╲___╲___╲___╲___╲
              │ Zählsensor (wenn zentral)
              ▼
         ╭──────────╮
         │  Schale  │ ← auf Wägezelle, vorn offen, hinten hoch
         ╰──────────╯
```

- **Fallhöhe begrenzen und brechen.** Ein M3-Teil aus 300 mm Höhe auf ABS
  springt aus der Schale. Gegenmaßnahme: die Rutsche in zwei Stufen brechen und
  die Lauffläche mit TPU (3D-gedruckt, 2 mm) oder Filz auskleiden. Das löst
  gleichzeitig A10.
- **Schale hinten hoch, vorn flach** — genau die Geometrie des Münzauswurfs:
  Teile können nicht herausspringen, aber mit der Handkante herausgewischt
  werden. Innen eine Mulde, damit auch die letzte M2-Scheibe greifbar bleibt.
- **Schale entnehmbar** (Magnethalter), damit man sie direkt über das Werkstück
  ausschütten kann und zum Reinigen abnehmen kann.
- **Keine Klappe** in der ersten Ausbaustufe: sie verhindert nichts, was hier
  verhindert werden müsste, kostet aber Mechanik und ist eine Fehlerquelle.
- Die Wägezelle unter der Schale braucht eine Tara-Nullung vor jeder Ausgabe;
  liegt noch Material vom letzten Vorgang darin, wird darauf tariert.

---

## 11. Gesamtlayout

Vorschlag Ausbaustufe 1: **Matrix 4 Reihen × 6 Fächer = 24 Sorten**.

```
   ┌──────────────────────────────────────────┐
   │  ▤ ▤ ▤ ▤ ▤ ▤   ← Kartuschen von vorn     │
   │  ▤ ▤ ▤ ▤ ▤ ▤      steckbar               │
   │  ▤ ▤ ▤ ▤ ▤ ▤                             │
   │  ▤ ▤ ▤ ▤ ▤ ▤                             │
   │ ┌──────────────┐                          │
   │ │   Panel      │   ╭─────────╮            │
   │ └──────────────┘   │  Schale │            │
   └────────────────────┴─────────┴────────────┘
```

- Kartuschen von **vorn** steckbar; die Antriebe sitzen auf einer rückseitigen
  Backplane. Ein Servicefall betrifft immer nur eine Kartusche.
- Je Reihe eine Sammelrutsche, die Reihenrutschen münden in eine gemeinsame
  Hauptrutsche. Bei "immer nur ein Fach gleichzeitig" genügt **ein** zentraler
  Zählsensor in der Hauptrutsche — das ist die mit Abstand wirtschaftlichste
  Sensorikvariante und bestimmt die Betriebsart: Ausgaben laufen seriell.
- Geräterahmen: Aluminium-Profil 20×20 oder 6-mm-Sperrholz/Acryl-Gehäuse; die
  Genauigkeit sitzt in den Druckteilen, nicht im Rahmen.
- Einbaumaß je Fach als Raster festlegen (z. B. 40 mm Teilung), damit breite
  Kartuschen (M8) zwei Rasterplätze belegen können, statt das Raster zu sprengen.

---

## 12. Fertigung, Material, Toleranzen

| Bauteil | Material | Hinweis |
|---|---|---|
| Kartuschenkörper | PETG | zäh, maßhaltig, transparent verfügbar; kein PLA (kriecht unter Stapellast) |
| Hängeschiene | PETG oder PA12 (SLS) | Schlitzkanten sind Verschleißflächen |
| Taschenrad | POM-Einleger, sonst PETG | Dauerreibung unter Stapellast |
| Escapement-Finger | PA12 / PETG | Keilflanke sauber, ohne Stufen |
| Deck-/Abstreifplatte | Metall (0,5 mm Blech) | die Abstreifkante muss scharf bleiben |
| Rutschenauskleidung | TPU 2 mm oder Filz | Geräusch und Prellen |

Druckhinweise:
- **Schichtrichtung**: Schlitzkanten und Fingerflanken so orientieren, dass die
  Belastung **quer** zur Schichtebene wirkt, nicht als Schälbelastung.
- **Spaltmaße**: bewegliche Passungen mit 0,2 mm Spiel je Seite beginnen und
  am Prototyp einschleifen. Taschentiefen dagegen **nicht** pauschal, sondern je
  Sorte am realen Teil ermitteln (Abschnitt 6.1).
- **Elefantenfuß** an der ersten Schicht ruiniert genau die Maße, auf die es
  ankommt: kritische Flächen nie auf das Druckbett legen.
- Parametrisches CAD verwenden (Fusion/OpenSCAD/FreeCAD mit Variablentabelle):
  eine neue Sorte soll ein Zeilen-Eintrag sein, keine Neukonstruktion.

---

## 13. Fehlerfälle und Gegenmaßnahmen

| # | Fehlerfall | Ursache | Gegenmaßnahme |
|---|---|---|---|
| F1 | Zwei Teile auf einmal | Taschentiefe zu groß, Ölfilm | Tasche nachmessen, Abstreifkante scharf, Wägezelle als Fangnetz |
| F2 | Kein Teil trotz Umdrehung | Brücke im Magazin, leer | Reversieren (3 Versuche), Leer-Sensor abfragen, dann Störung |
| F3 | Teil verklemmt im Escapement | Kopftoleranz, Grat am Teil | Reversieren; Fingerkeil flacher; Kartusche ziehbar für Handeingriff |
| F4 | Schraube springt aus der Schale | Fallhöhe | Rutsche abstufen, TPU-Auskleidung, Schale hinten hoch |
| F5 | Falsche Sorte ausgegeben | Kartusche falsch gesteckt | Codierung an der Kartusche, Abgleich vor jeder Ausgabe |
| F6 | Sensor zählt einen Prellvorgang doppelt | Abprall an der Schachtwand | 50 ms Sperrzeit, Schacht innen weich auskleiden |
| F7 | Federringe verhaken | Schraubenlinie | Auffädeldorn im Rohr, sonst Sorte ausschließen |
| F8 | Zählerstand driftet | Handentnahme, Fehlzählung | Leer-/Low-Sensor führt, Zähler ist nur Anzeige |
| F9 | Kurze Schraube kippt in der Schiene | L/d < 2 | Schiene steiler, Schlitzführung verlängern, Grenzwert dokumentieren |
| F10 | Motor blockiert dauerhaft | Fremdkörper, Span | Strommessung → Abschaltung, Fach sperren, Meldung |

---

## 14. Teststand und Abnahmekriterien

Der Teststand ist **eine einzelne Kartusche** auf einer Grundplatte mit Motor,
Index-Sensor und Zählsensor — kein komplettes Gerät. Alle mechanischen Fragen
lassen sich daran klären, und zwar bevor Gehäuse und Verkabelung existieren.

Prüfprogramm je Kartuschentyp:

| Test | Umfang | Kriterium |
|---|---|---|
| T1 Dauerlauf | 1000 Auswürfe | < 1 Blockade, 0 Doppelausgaben |
| T2 Restentleerung | von voll bis leer | Ausgabe bis zum letzten Teil oder definierte Restmenge |
| T3 Volllast | volle Kartusche, erste 50 Teile | kein erhöhtes Moment, kein Klemmen |
| T4 Ölfilm | Teile mit Korrosionsschutzöl benetzt | 0 Doppelausgaben |
| T5 Längenspektrum | kürzeste und längste Schraube der Sorte | beide Grenzfälle sicher |
| T6 Entklemmung | absichtlich verklemmen | Reversierstrategie löst in ≥ 90 % der Fälle |
| T7 Geräusch | subjektiv + Messung | kein Prellen hörbar, Ausgabe unter 60 dB(A) |

T1 und T4 sind die entscheidenden Tests — sie adressieren direkt A4 und A9.
Ein Kartuschentyp gilt erst nach T1–T6 als freigegeben und darf erst dann
vervielfältigt werden.

---

## 15. Roadmap

| Stufe | Inhalt | Ziel |
|---|---|---|
| **P0** | Eine Klasse-B-Kartusche (M3), Handkurbel, kein Motor, kein Sensor | Beweis, dass das Escapement genau ein Teil freigibt |
| **P1** | P0 + Getriebemotor + Index + Zählsensor auf Testplatte | Regelkreis aus Abschnitt 8 nachweisen, T1–T6 fahren |
| **P2** | Zweite Bauform: Klasse-A-Kartusche (M3-Scheiben, M3-Muttern) | Nachweis, dass eine Antriebsschnittstelle beide Klassen bedient |
| **P3** | 4er-Modul mit Sammelrutsche und Schale | Layout, Akustik, serielle Ausgabe |
| **P4** | Vollausbau 24 Fächer, Panel, Bestandsführung | Steuerungsplattform wird hier erstmals relevant |

**P0 ist bewusst antriebslos.** Wenn die Vereinzelung von Hand nicht 50-mal
hintereinander genau ein Teil liefert, hilft kein Motor — er verdeckt das
Problem nur. Erst wenn P0 steht, lohnt sich alles Weitere.

---

## 16. Offene Entscheidungen

| # | Frage | Auswirkung |
|---|---|---|
| O1 | Orientiertes Befüllen (Klasse B) akzeptabel, oder Schüttgut-Trichter nötig? | Bestimmt, ob Klasse C entwickelt werden muss — größter Einzelposten im Projekt |
| O2 | Sortiment: ist M1 wirklich nötig, oder reicht ab M2? | M1 erzwingt die Sonderlösung aus Anhang B |
| O3 | Sind Federringe/Stoppmuttern im Sortiment? | Federringe brauchen Auffädeldorn, Stoppmuttern sind höher als Standardmuttern |
| O4 | Ein zentraler Zählsensor (serielle Ausgabe) oder einer je Fach? | Kosten gegen Durchsatz; serielle Ausgabe reicht für A5 |
| O5 | Wägezelle als Pflicht oder Option? | Pflicht, sobald M1/M1.6 im Sortiment sind |
| O6 | Fachraster und maximale Kartuschenbreite | Legt das Gehäuse fest und ist später teuer zu ändern |

---

## Anhang A — Richtmaße für die Kartuschenauslegung

> **Diese Werte sind Richtwerte zur Erstauslegung.** Kopfdurchmesser variieren je
> Kopfform und Hersteller erheblich. Vor dem Druck einer Kartusche gilt:
> **am realen Teil mit dem Messschieber nachmessen** — insbesondere Kopfhöhe,
> Kopfdurchmesser und Teiledicke, denn diese drei Maße bestimmen Taschentiefe und
> Fingerabstand.

Schrauben, Innensechskant-Zylinderkopf (ISO 4762), Richtwerte:

| Größe | Schaft d | Kopf-Ø ca. | Kopfhöhe ca. | Schlitzbreite = d+0,4 | Kanalbreite = Kopf+0,5 |
|---|---|---|---|---|---|
| M2 | 2,0 | 3,8 | 2,0 | 2,4 | 4,3 |
| M2,5 | 2,5 | 4,5 | 2,5 | 2,9 | 5,0 |
| M3 | 3,0 | 5,5 | 3,0 | 3,4 | 6,0 |
| M4 | 4,0 | 7,0 | 4,0 | 4,4 | 7,5 |
| M5 | 5,0 | 8,5 | 5,0 | 5,4 | 9,0 |
| M6 | 6,0 | 10,0 | 6,0 | 6,4 | 10,5 |
| M8 | 8,0 | 13,0 | 8,0 | 8,4 | 13,5 |

Muttern (ISO 4032) und Scheiben (ISO 7089), Richtwerte:

| Größe | Mutter SW | Mutter Höhe | Scheibe Außen-Ø | Scheibe Dicke |
|---|---|---|---|---|
| M3 | 5,5 | 2,4 | 7 | 0,5 |
| M4 | 7,0 | 3,2 | 9 | 0,8 |
| M5 | 8,0 | 4,7 | 10 | 1,0 |
| M6 | 10,0 | 5,2 | 12 | 1,6 |
| M8 | 13,0 | 6,8 | 16 | 1,6 |

Ableitungsregeln:
- Taschentiefe Klasse A = gemessene Teiledicke + 0,15 mm
- Rohrinnenmaß Scheiben = Außen-Ø + 0,5 mm
- Sechskant-Rohrinnenmaß Muttern = SW + 0,4 mm
- Fingerabstand Escapement = Kopf-Ø + 0,6 mm

---

## Anhang B — Grenzfall M1 / M1.6

M1 ist im Sortiment der kritischste Fall und sollte separat entschieden werden
(O2). Die Zahlen erklären, warum:

- Kopfdurchmesser ca. 2 mm, Schaft 1 mm, Masse einer M1x4 unter 0,05 g.
- Ein Schlitz von 1,4 mm mit 0,2 mm Fertigungstoleranz hat 14 % Maßabweichung —
  im FDM-Druck ist das nicht sicher beherrschbar. Die Hängeschiene aus Abschnitt
  4.2 verliert hier ihre Zuverlässigkeit.
- Das Teil ist so leicht, dass Reibung und statische Aufladung die Schwerkraft
  überwiegen können: es rutscht nicht zuverlässig nach.
- Ein induktiver Sensor erkennt die Masse im Fallschacht nur noch grenzwertig.

Empfehlung für M1/M1.6, falls im Sortiment:
1. **Lochscheiben-Magazin statt Hängeschiene**: eine Scheibe mit Bohrungen
   (Ø Schaft + 0,3 mm), in denen die Schrauben hängen wie in einem Setzkasten,
   wird schrittweise über die Auswurföffnung gedreht. Die Geometrie ist eine
   Bohrung statt eines Schlitzes — Bohrungen sind im Druck (oder gebohrt in
   Acryl) deutlich maßhaltiger als schmale Schlitze.
2. **Fertigung dieser Kartusche nicht im FDM-Druck**, sondern aus Acryl gebohrt
   oder als SLS-Teil.
3. **Wägezelle als führendes Zählmittel**: 7 Stück à 0,05 g = 0,35 g; eine
   Wägezelle mit 0,01-g-Auflösung unterscheidet 6 von 7 Teilen sicher, wo ein
   Schachtsensor versagt. Die Schale muss dann windgeschützt stehen.
4. Alternativ, und deutlich billiger: **M1 aus dem Automaten herausnehmen** und
   als Streifenware im Fach daneben lagern. Das sollte ernsthaft geprüft werden,
   bevor für eine selten gebrauchte Größe eine Sonderbauform entwickelt wird.
