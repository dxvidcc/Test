# Kleinteile-Automat — Mechanik-Konzept

Ausgabeautomat für Schrauben, Muttern und Unterlegscheiben. Bedienung über ein
Panel ("7x M3x10"), Ausgabe stückgenau in eine Schale, wie der Münzauswurf an
einer Supermarktkasse.

Das Gerät besteht aus zwei mechanisch getrennten Modulen an einem gemeinsamen
Panel:

- **Teil I — Trockenmodul**: Schrauben, Muttern, Scheiben (Abschnitte 1–16)
- **Teil II — Nassmodul**: 2K-Epoxid mit Verdicker, dosiert und gerührt in einen
  Mischbecher (Abschnitte N1–N12)

Dieses Dokument behandelt **ausschließlich die Mechanik**: Bevorratung,
Vereinzelung, Dosierung, Auswurf, Zählung und Fertigung. Steuerungsplattform
(ESP32 / Pi / Arduino) ist bewusst offen gelassen; alle Schnittstellen sind so
beschrieben, dass jede Plattform sie bedienen kann.

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
- **Befüllen aus der Tüte, nicht von Hand orientiert.** Ein Schüttguttrichter
  mit **Hubschieber** über der Hängeschiene orientiert die Schrauben selbst
  (Abschnitt 4.3): hineinkippen, der Schieber fischt sie hängend heraus, falsch
  liegende Teile fallen zurück und werden erneut angeboten. Das ist die
  eigentliche Antwort auf den Betriebsaufwand.
- **Zweites Modul: 2K-Epoxid** (Teil II). Harz, Härter und Verdicker werden
  **nach Gewicht** in einen Einweg-Mischbecher dosiert und automatisch gerührt.
  Dasselbe Grundprinzip wie beim Zählen: gemessen wird das Ergebnis, nicht die
  Ansteuerung.
- **Untergrenze M2.** M1/M1.6 sind bewusst nicht im Sortiment — die
  Schlitztoleranzen wären im Druck nicht beherrschbar.

---

# Teil I — Trockenmodul

## 1. Anforderungen

| # | Anforderung | Zielwert |
|---|---|---|
| A1 | Teilespektrum Schrauben | M2 – M8, Länge 4 – 40 mm, Zylinder-/Linsen-/Senkkopf |
| A2 | Teilespektrum Muttern | M2 – M8, ISO 4032 / 4033, Stoppmuttern optional |
| A3 | Teilespektrum Scheiben | M2 – M8, ISO 7089/7090, Federringe als Sonderfall |
| A4 | Stückgenauigkeit | 100 % — die ausgegebene Menge muss der bestellten entsprechen |
| A5 | Durchsatz | ≥ 1 Teil/s pro Fach (7 Stück ≈ 7 s sind akzeptabel) |
| A6 | Fachanzahl Zielausbau | 24 – 48 Sorten |
| A7 | Füllmenge je Fach | ≥ 100 Teile (bei M3-Scheiben deutlich mehr) |
| A8 | Nachfüllen | im laufenden Betrieb, ohne Werkzeug, ohne Demontage |
| A9 | Fehlerrate | < 1 Blockade pro 1000 Ausgaben, kein stiller Fehlauswurf |
| A10 | Geräusch | kein metallisches Prellen im Ausgabeschacht |
| A11 | Nachfüllen Schrauben | unorientiert aus der Vorratstüte, ohne Einzelteil-Handhabung |
| A12 | Epoxid-Ansatz (Teil II) | 15 – 150 g, Mischungsverhältnis-Fehler < 2 % der Härtermasse |

**Abgrenzung:** keine Gemischtausgabe mehrerer Sorten in einem Vorgang in der
ersten Ausbaustufe; keine Federringe ohne Auffädeldorn; keine Faserfüllstoffe im
Nassmodul (Abschnitt N6).

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

### 4.3 Befüllen: das Orientierungsproblem und seine Lösung

Die Hängeschiene erzwingt eine definierte Lage — das ist ihre Stärke bei der
Ausgabe und ihre Schwäche beim Befüllen. Naiv müsste jede Schraube von Hand
eingehängt werden; bei 150 Teilen pro Kartusche ist das der Grund, aus dem so
ein Gerät am Ende ungenutzt in der Ecke steht.

**Grundsatz: nicht der Mensch orientiert die Schrauben, sondern die Mechanik.**
Drei Ausbaustufen, aufsteigend nach Aufwand:

#### Stufe 1 — Ladewanne (ein Werkzeug für das ganze Gerät)

Eine flache Wanne mit geschlitztem Boden, Neigung ca. 10°. Eine Handvoll
Schrauben hineinkippen, kurz schütteln oder mit einem 5-€-Vibrationsmotor
rütteln: die Schrauben fallen in die Schlitze und hängen am Kopf, die restlichen
rutschen zur Seite. Die Wanne wird an die Kartusche angedockt, der Schlitz
fluchtet, ein Schieber streift die Reihe hinüber.

- Kosten: ein Druckteil plus Vibrationsmotor, **einmal für alle Kartuschen**.
- Aufwand: ca. 1 Minute pro Kartuschenfüllung statt ca. 10 Minuten Einzelhandhabung.
- Keinerlei Änderung an der Kartusche nötig — funktioniert auch nachgerüstet.

#### Stufe 2 — Schüttguttrichter mit Hubschieber (Empfehlung für den Endausbau)

Das Prinzip kommt aus kommerziellen Schraubenzuführungen und ist der eigentliche
Gewinn: der Trichter sitzt direkt auf der Kartusche, befüllt wird durch simples
Hineinkippen aus der Vorratstüte.

```
        ┌──────────────────────┐
        │  o  o   o  o  o   o  │  ← Schüttgut, unorientiert
        │    o  o   o  o   o   │
        │  o   o  ┌─┐ o   o    │
        │    o  o │▓│  o   o   │   ┌─┐  Hubschieber, Oberkante
        │  o   o  │▓│o   o     │   │▓│  angeschrägt, mit Schlitz
        └─────────┤▓├──────────┘   └─┘
                  │▓│  ▲ Schieber fährt durch die Schüttung nach oben
                  │▓│  │
             ═════╪═╪══╪═══  Übergabe oben auf die Hängeschiene
                  ▼ ▼
              Schiene (Puffer)  ──►  Escapement  ──►  Fallschacht
```

Funktion eines Hubes:
1. Der Schieber fährt durch die Schüttung nach oben. Seine Oberkante ist
   angeschrägt und trägt denselben Schlitz wie die Schiene.
2. Schrauben, die zufällig mit dem Schaft in den Schlitz fallen, bleiben hängen.
   Alle anderen rutschen über die Schräge in den Trichter zurück — **falsch
   orientierte Teile werden automatisch aussortiert und erneut angeboten.**
3. Oben fluchtet der Schieberschlitz mit dem Schienenschlitz; die hängenden
   Schrauben rutschen auf die Schiene.

Ein Hub fördert 0 bis n Teile — das ist unkritisch, weil die Schiene nur noch
**Puffer** ist. Gezählt wird weiterhin unten am Escapement und im Fallschacht
(Abschnitt 8). Die Steuerung fährt einfach so lange Hübe, bis der Füllstands-
sensor der Schiene meldet "voll genug".

**Antrieb ohne zweiten Motor:** Die Kartuschenwelle bekommt zwei Freiläufe
(Klemmkörper- oder gedruckte Klinkenfreiläufe), die gegenläufig wirken:

| Drehrichtung | wirkt auf | Funktion |
|---|---|---|
| vorwärts | Nockenwelle des Escapements | ein Teil ausgeben |
| rückwärts | Kurbel des Hubschiebers | einen Förderhub fahren |

Damit bleibt die Schnittstelle aus Abschnitt 7 unverändert — ein Motor, eine
Welle, zwei Drehrichtungen. Das Gerät muss nicht einmal wissen, ob die gesteckte
Kartusche einen Trichter hat: es dreht rückwärts, wenn die Schiene leer meldet.

Nachteile, klar benannt:
- Die Kartusche wird deutlich höher (Trichtervolumen) und beansprucht mehr
  Bauraum in der Matrix.
- Zwei Freiläufe im Druckteil sind der anspruchsvollste Teil der ganzen Mechanik.
  Fällt der Nachweis in P2b durch, ist der Rückfall ein kleiner zweiter Motor
  je Fach — teurer, aber trivial.
- Bei sehr kurzen Schrauben (L/d < 2) sinkt die Ausbeute je Hub; das kostet nur
  Zeit, keine Funktion.

#### Stufe 3 — Klasse A: der selbstorientierende Flachschlitz-Trichter

Für Scheiben und Muttern ist das Problem viel kleiner und mit reiner Geometrie
lösbar: ein Trichter, dessen Auslaufschlitz nur **eine Teiledicke** hoch und so
breit wie das Teil ist. Eine Scheibe passt dort nur flach hindurch, hochkant
niemals. Scheiben aus der Tüte einfüllen, kurz rütteln, fertig — die Teile
ordnen sich beim Durchtritt von selbst.

Muttern brauchen zusätzlich die Verdrehsicherung des Sechskantrohres
(Abschnitt 4.1) und einen etwas höheren Schlitz; ihr Orientierungsproblem ist
auf "liegend statt stehend" reduziert und damit ebenfalls geometrisch erledigt.

#### Vergleich

| Verfahren | Aufwand je Füllung | Kosten | Änderung an der Kartusche |
|---|---|---|---|
| Von Hand einhängen | ~10 min | 0 € | keine |
| Ladewanne (Stufe 1) | ~1 min | ~10 € einmalig | keine |
| Hubschieber-Trichter (Stufe 2) | **~10 s (Tüte auskippen)** | ~5 € je Kartusche | Trichter + 2 Freiläufe |
| Flachschlitz-Trichter (Stufe 3, Klasse A) | ~15 s | ~2 € je Kartusche | Trichteraufsatz |

**Empfehlung:** Stufe 1 sofort bauen (sie funktioniert ab P0 und kostet fast
nichts), Stufe 2 in P2b nachweisen und danach für die Vielverbrauchs-Sorten
(M3, M4) umsetzen. Stufe 3 gehört von Anfang an auf jede Klasse-A-Kartusche.

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
Gesamtausgabe. Eine hochauflösende Wägezelle braucht Teil II ohnehin
(Abschnitt N5), die Bauteilauswahl ist damit bereits geklärt.

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
- **Nachfüllvorgang**: siehe Abschnitt 4.3 — entweder Kartusche ziehen und an
  der Ladewanne füllen, oder bei Trichter-Kartuschen direkt aus der Tüte in den
  Trichter kippen, ohne die Kartusche zu entnehmen.
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
| F11 | Hubschieber fördert nichts | Trichter fast leer, Schüttung entmischt | weitere Hübe (max. 10), dann Meldung "nachfüllen"; Trichterwände steiler als der Schüttwinkel |
| F12 | Schraube fällt bei der Übergabe zurück | Schieberschlitz und Schienenschlitz fluchten nicht | Endanschlag statt Zeitsteuerung, Übergabe mit Überdeckung ausführen |

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
| **P2b** | Hubschieber-Trichter auf die M3-Kartusche aufsetzen | Befüllen aus der Tüte statt orientiertes Einlegen (A11) |
| **P3** | 4er-Modul mit Sammelrutsche und Schale | Layout, Akustik, serielle Ausgabe |
| **P4** | Vollausbau 24 Fächer, Panel, Bestandsführung | Steuerungsplattform wird hier erstmals relevant |

**P0 ist bewusst antriebslos.** Wenn die Vereinzelung von Hand nicht 50-mal
hintereinander genau ein Teil liefert, hilft kein Motor — er verdeckt das
Problem nur. Erst wenn P0 steht, lohnt sich alles Weitere.

---

## 16. Offene Entscheidungen

| # | Frage | Auswirkung |
|---|---|---|
| O1 | Externe Ladewanne (ein Werkzeug fürs ganze Gerät) oder integrierter Hubschieber je Kartusche? | Siehe Vergleich in 4.3 — entscheidet über Kartuschenhöhe und Antriebsaufwand |
| O2 | Bekommt jede Kartusche einen Trichter, oder nur die Vielverbrauchs-Sorten (M3/M4)? | Mischbestückung ist möglich, da die Antriebsschnittstelle gleich bleibt |
| O3 | Sind Federringe/Stoppmuttern im Sortiment? | Federringe brauchen Auffädeldorn, Stoppmuttern sind höher als Standardmuttern |
| O4 | Ein zentraler Zählsensor (serielle Ausgabe) oder einer je Fach? | Kosten gegen Durchsatz; serielle Ausgabe reicht für A5 |
| O5 | Wägezelle im Trockenmodul Pflicht oder Option? | Option — im Nassmodul dagegen zwingend |
| O6 | Fachraster und maximale Kartuschenbreite | Legt das Gehäuse fest und ist später teuer zu ändern |
| O7 | Nassmodul: welches Harzsystem wird fest hinterlegt? | Mischungsverhältnis und Topfzeit sind systemspezifisch und gehören ins Behälterprofil |
| O8 | Verdicker: nur pyrogene Kieselsäure oder auch Glass Bubbles als zweite Sorte? | Zweite Sorte = zweiter Trichter und zweite Schnecke; Fasern bleiben ausgeschlossen |

---

# Teil II — Nassmodul: 2K-Epoxid mit Verdicker

## N1. Aufgabe

Drei Vorratsbehälter am selben Gerät, bedient über dasselbe Panel:

| Behälter | Inhalt | Aggregatzustand |
|---|---|---|
| B1 | Epoxidharz | flüssig, zäh (Richtwert 700 – 1500 mPa·s bei 20 °C) |
| B2 | Härter | flüssig, dünner (Richtwert 50 – 500 mPa·s) |
| B3 | Verdicker (pyrogene Kieselsäure, alternativ Glass Bubbles) | **Pulver**, sehr leicht (Schüttdichte ca. 0,05 – 0,1 g/cm³) — Schnecke statt Ventil, siehe N6 |

Bedienablauf: Einwegbecher einsetzen → am Panel Menge wählen (z. B. 40 g) und
Konsistenz (dünnflüssig / Gel / Paste) → Start. Das Gerät dosiert Harz und
Härter im richtigen Verhältnis, rührt, rieselt den Verdicker ein, rührt erneut
und meldet die verbleibende Topfzeit.

## N2. Warum das kein Getränkeautomat ist

Fünf Randbedingungen bestimmen die gesamte Konstruktion:

1. **Das Mischungsverhältnis ist nicht verhandelbar.** Epoxid härtet
   stöchiometrisch; zu viel oder zu wenig Härter ergibt keine "etwas andere"
   Mischung, sondern eine dauerhaft weiche, klebrige Masse, die nicht
   nachhärtet. Der Fehler ist irreversibel und am Ergebnis erst nach Stunden
   sichtbar. Typische Verhältnisse liegen je System zwischen 100:50 und 100:30
   nach Gewicht — **der Wert kommt aus dem Datenblatt des konkreten Systems,
   niemals aus einer Tabelle wie dieser.**
2. **Volumendosierung scheidet damit aus.** Harz und Härter haben
   unterschiedliche Dichten und stark unterschiedliche Viskositäten, und die
   Viskosität ändert sich grob um den Faktor 2 je 10 K Temperaturänderung. Eine
   Steuerung über Pumpenlaufzeit wäre im Winter falsch und im Sommer auch.
   → **Dosiert wird nach Gewicht, mit Waage im Regelkreis.** Exakt dasselbe
   Prinzip wie beim Schraubenzählen: gemessen wird das Ergebnis.
3. **Topfzeit.** Ab dem Moment des Mischens läuft eine Uhr (je System typisch
   10 – 45 min). Im Gerät darf nie etwas Gemischtes stehen bleiben.
4. **Aushärtung im Gerät ist ein Totalschaden.** Jedes Bauteil, das Harz *und*
   Härter sieht, muss ein Wegwerfteil sein. Das ist die zentrale Entwurfsregel
   des Nassmoduls.
5. **Chemie.** Aminische Härter sind hautsensibilisierend und ätzend, greifen
   Kupfer und Messing an und reagieren an Luft mit Feuchtigkeit und CO₂
   ("Amin-Blush"). Benetzte Teile daher aus PP, PE, PTFE, Silikon oder
   Edelstahl; Behälter dicht.

## N3. Architektur

```
     ┌──────┐   ┌──────┐        ┌──────────┐
     │  B1  │   │  B2  │        │    B3    │  Pulver
     │ Harz │   │Härter│        │ Verdicker│
     └───┬──┘   └───┬──┘        └────┬─────┘
         │          │            ┌───┴───┐
      ═══╪══      ══╪══          │Schnecke│ + Brückenbrecher
      Quetsch-    Quetsch-       └───┬───┘
      ventil      ventil             │
         │          │                │
         ▼          ▼                ▼
        ╲__        __╱          ╲___╱      ← getrennte Düsen, Abrisskante
          ╲________╱  ╲________╱
              ╭──────────────╮
              │ Einwegbecher │ ◄── Rührpaddel (Einwegteil) von oben
              ╰──────┬───────╯
              ┌──────┴───────┐
              │  Wägezelle   │ 0,01 g / 500 g
              └──────────────┘
              ┌──────────────┐
              │ Auffangwanne │ PP, chemikalienfest
              └──────────────┘
```

## N4. Dosierung der Flüssigkeiten

| Variante | Viskositätstauglich | Reinigung | Kosten | Bewertung |
|---|---|---|---|---|
| **Schwerkraft + Quetschventil** | gut (Bohrung groß wählen) | Schlauch = Wegwerfteil | sehr niedrig | **Empfehlung** |
| Schlauchpumpe (peristaltisch) | mittel (pulsiert, saugt zäh) | Schlauch = Wegwerfteil | niedrig | Rückfallebene, wenn der Behälter nicht oben stehen kann |
| Zahnradpumpe | sehr gut | nur mit Lösemittel | hoch | benetzte Lager, Reinigungsproblem |
| Spritzenpumpe | sehr gut | Spritze = Wegwerfteil | mittel | sehr genau, aber Nachfüllhub und begrenztes Volumen |
| Druckbehälter + Zeitventil | gut | mittel | mittel | Druckluft nötig, Genauigkeit nur mit Waage |

**Gewählt: Schwerkraft + Quetschventil.** Die Begründung ist die Entwurfsregel
aus N2.4 — das einzige benetzte Bauteil ist ein Stück Silikonschlauch, und das
ist ein Cent-Artikel. Epoxid haftet auf Silikon kaum (derselbe Grund, aus dem
Silikon als Formenmaterial dient); ausgehärtete Reste lassen sich ausdrücken.
Ein Quetschventil (Servo oder Hubmagnet, der den Schlauch abklemmt) berührt das
Medium überhaupt nicht.

**Der Schlauchquerschnitt entscheidet über den Durchsatz** — er geht in vierter
Potenz ein (Hagen-Poiseuille). Überschlag für Harz mit 1000 mPa·s bei 300 mm
Höhenunterschied und 250 mm Schlauchlänge:

| Schlauch-Innen-Ø | Volumenstrom | 30 g Harz in |
|---|---|---|
| 6 mm | ca. 0,4 ml/s | ca. 70 s |
| 8 mm | ca. 1,3 ml/s | ca. 22 s |

→ **mindestens 8 mm Innendurchmesser**, kurze Wege, Behälter hoch aufstellen.
Optional die Harzflasche auf 25 – 30 °C temperieren: halbe Viskosität,
doppelter Durchsatz. Den Härter nicht mitheizen — die Topfzeit sinkt mit der
Temperatur des Ansatzes.

## N5. Waage und Dosierstrategie

Die Waage ist im Nassmodul kein Zusatzsensor, sondern das führende Messmittel.

1. **Tarieren** mit eingesetztem Becher. Kein Becher erkannt (Gewicht unter
   Schwelle) → keine Dosierung. Rückstände im Becher → Tara darauf, aber
   Warnung, dass der Becher nicht leer ist.
2. **Harz dosieren**, zweistufig: Grobstrom bis kurz vor Ziel, dann Ventil
   takten (Tropfenmodus).
3. **Nachlaufkompensation:** Nach dem Schließen läuft der Schlauchinhalt noch
   nach. Das Gerät schließt deshalb vor dem Zielwert und misst die tatsächliche
   Nachlaufmasse — dieser Wert wird pro Ansatz nachgeführt (lernender Offset).
   Ohne diese Kompensation ist der kleine Ansatz (15 g) nicht zu halten.
4. **Härter auf das tatsächlich ausgegebene Harzgewicht berechnen**, nicht auf
   den Sollwert. Wurden statt 30,0 g eben 30,7 g Harz dosiert, wird das
   Verhältnis auf 30,7 g bezogen. **Damit ist eine Überdosierung des Harzes
   völlig harmlos** — nur das Verhältnis zählt, nicht die Absolutmenge. Das ist
   der Kniff, der das ganze Modul robust macht.
5. **Rühren erst danach**, und zwar mit von der Waage entkoppeltem Becher: das
   Rührwerk erzeugt Kräfte, die jede Messung unbrauchbar machen. Entweder hebt
   ein kleiner Hub den Becher während des Rührens von der Waage ab, oder das
   Rührwerk hängt an einem eigenen Rahmen und wird nur zwischen den Wägungen
   betrieben. **Nicht wiegen und rühren gleichzeitig.**

**Mindestansatz 15 g.** Darunter dominiert der Nachlauf die Genauigkeit; A12
(< 2 % Verhältnisfehler) wäre nicht mehr nachweisbar. Der Mindestansatz gehört
als harte Grenze in die Steuerung.

## N6. Verdicker (Pulver)

Pyrogene Kieselsäure ist mechanisch der unangenehmste Stoff im ganzen Gerät:
Schüttdichte in der Größenordnung von 50 g/l, extrem fein, neigt zu
Brückenbildung und lädt sich elektrostatisch auf. Sie fließt nicht.

- **Förderorgan: Dosierschnecke** mit geringer Steigung, darüber ein langsam
  laufender **Brückenbrecher** (Rührflügel an der Trichterwand). Schwerkraft
  allein funktioniert hier garantiert nicht.
- Trichterwände deutlich steiler als der Schüttwinkel, innen glatt; Ecken und
  Radien vermeiden.
- **Dosierung ebenfalls nach Gewicht.** Die Zugabemenge liegt bei Kieselsäure in
  der Größenordnung weniger Gewichtsprozent, bei Glass Bubbles deutlich höher —
  die Konsistenzstufen am Panel sind hinterlegte Rezepte je Verdickersorte.
- **Reihenfolge ist Verfahrenstechnik, nicht Geschmackssache:** erst Harz und
  Härter vollständig mischen, dann den Verdicker **langsam in den laufenden
  Rührer einrieseln**. Wird der Verdicker vorher zugegeben, lässt sich der
  Härter nicht mehr sauber einarbeiten, und es entstehen Klumpen.
- **Staub:** Auslauf tief in den Becher führen, kurze Fallstrecke, kein
  Luftzug, Trichter dicht mit Trockenmittel-Belüftung. Amorphe Kieselsäure ist
  kein Quarzstaub, aber feiner Staub hat in der Lunge trotzdem nichts zu suchen
  — die Pulverstrecke wird eingehaust.
- **Faserfüllstoffe** (Baumwollflocken, Glasfaserschnitzel) blockieren jede
  Schnecke zuverlässig. Sie bleiben aus dem Automaten heraus und werden von Hand
  zugegeben; das ist eine bewusste Abgrenzung, keine offene Baustelle.

### N6.1 Was "Pulver" konkret bedeutet: Volumen statt Masse

Die Mengen klingen nach nichts — 2 oder 3 Gramm — aber pyrogene Kieselsäure ist
so leicht, dass die Masse die falsche Größe zum Nachdenken ist. Überschlag für
einen 40-g-Ansatz mit Pastenkonsistenz:

| Größe | Wert |
|---|---|
| Harz + Härter, 40 g bei ca. 1,1 g/cm³ | ca. 36 ml |
| Kieselsäure 3 g bei Schüttdichte ca. 0,05 g/cm³ | **ca. 60 ml** |
| Glass Bubbles 8 g bei Schüttdichte ca. 0,1 g/cm³ | **ca. 80 ml** |

**Das Pulver hat mehr Volumen als die Flüssigkeit, in die es hinein soll.**
Daraus folgen vier Festlegungen, die sonst erst am Prototyp auffallen:

1. **Bechergröße nach dem Schüttzustand wählen, nicht nach dem Endzustand.**
   Kieselsäure fällt beim Benetzen praktisch vollständig in sich zusammen (echte
   Dichte ca. 2,2 g/cm³, der Rest ist Luft) — der Ansatz hat am Ende wieder
   ca. 38 ml. Aber dazwischen türmt sich das Pulver auf. Für 40 g Ansatz daher
   **Becher ab 200 ml**, bei Glass Bubbles (die als Hohlkugeln erhalten bleiben
   und das Volumen dauerhaft vergrößern) ab 250 ml.
2. **Zugabe zwingend portionsweise in den laufenden Rührer.** Nicht nur wegen
   der Klumpen: die Schüttung passt gar nicht auf einmal in den Becher. Das
   Einrieseln über 30 – 60 s ist keine Vorsichtsmaßnahme, sondern
   Volumenbedingung.
3. **Schneckenauslegung folgt daraus direkt.** Eine Schnecke Ø 12 mm mit 10 mm
   Steigung fördert je Umdrehung ca. 0,8 ml geometrisch, realistisch bei halber
   Füllung ca. 0,4 ml. Für 60 ml sind das rund 150 Umdrehungen — bei 120 min⁻¹
   etwa 75 s. Das passt genau zur geforderten Einrieselzeit: **die langsame
   Schnecke ist hier keine Schwäche, sondern die gewünschte Betriebsart.** Eine
   schnelle Schnecke müsste künstlich gedrosselt werden.
4. **Statik ernst nehmen.** Feines Pulver lädt sich beim Fördern auf und bleibt
   an Becherwand, Düse und allem in Reichweite kleben — Material, das an der
   Wand oberhalb des Harzspiegels hängt, ist dosiert, aber nicht im Ansatz, und
   verfälscht das Rezept. Gegenmaßnahmen: Auslaufrohr aus geerdetem Edelstahl,
   Fallstrecke unter 30 mm, Auslauf dicht über dem Harzspiegel statt am
   Becherrand, und das Paddel so geformt, dass es die Wand oberhalb des Spiegels
   mit erfasst.

Die Waage ist von all dem unbeeindruckt — sie wiegt die 3 g so genau wie 30 g.
Die Auflösung ist also **nicht** die Herausforderung bei der Pulverdosierung;
Förderstetigkeit und Statik sind es.

## N7. Rührwerk

**Zentrale Entscheidung: Becher und Rührpaddel sind Einwegteile.** Damit
entfällt die Reinigung vollständig — und mit ihr das Problem, an dem solche
Geräte sonst scheitern.

- Paddel in einer Federklemme oder einem Bajonett am Antrieb; nach dem Ansatz
  wird es mit dem Becher zusammen entnommen und entsorgt.
- Einfachste Bauform: **Becher dreht auf einem Teller, Paddel steht fest und
  exzentrisch.** Der Antrieb sitzt unten, über dem Becher hängt nur ein
  passives Teil — das ist mechanisch deutlich einfacher als ein abgesenkter
  Rührmotor.
- Drehzahl 200 – 400 min⁻¹. Schneller rühren zieht Luft ein; Blasen im Harz
  sind ein Qualitätsfehler, kein Schönheitsfehler.
- Paddelgeometrie mit ca. 1 mm Wandabstand und einem Bodenräumer. Unvermischtes
  Material an Wand und Boden ist der klassische Fehler beim Handmischen und
  beim automatischen genauso.
- Rührprogramm: ca. 60 s Harz + Härter → Verdicker über 30 – 60 s einrieseln →
  60 – 90 s nachrühren.
- **Ehrlicher Hinweis fürs Panel:** Kein automatisches Rührwerk erreicht die
  Sicherheit des Umtopfens in einen zweiten Becher. Für kritische Verklebungen
  bleibt "kurz von Hand nachmischen und umtopfen" die richtige Empfehlung — das
  Gerät nimmt das Abwiegen ab, nicht die Verantwortung.

## N8. Düsen, Tropfen, Kreuzkontamination

- **Getrennte Düsen mit Abstand.** Ein einziger Tropfen Härter, der in die
  Harzdüse gelangt, härtet dort aus und setzt sie dauerhaft zu. Die Härterdüse
  steht deshalb nie über der Harzdüse oder über dem Harzbehälter.
- Düsenspitze mit scharfer **Abrisskante**, damit der Tropfen abreißt statt am
  Werkstoff entlangzukriechen.
- **Parkposition** mit Silikonkappe oder über einem eigenen Abtropfnapf je Düse.
- Schlauch und Düse sind definierte Verschleißteile mit Wechselintervall; sie
  kosten wenige Cent und werden vorsorglich getauscht, nicht bei Störung.

## N9. Sicherheit und Betriebsschutz

- **Becher-Erkennung** über die Waage: ohne Becher keine Dosierung. Kein Becher
  unter der Düse ist der einzige Fehler, der das Gerät selbst versaut.
- **Auffangwanne** aus PP unter der gesamten Station, herausnehmbar.
- **Überfüllschutz**: Zielmasse plus Toleranz überschritten → Ventil zu,
  Ansatz als "verworfen" markieren statt Härter nachzukippen.
- **Topfzeit-Anzeige** nach jedem Ansatz, mit Ablaufwarnung.
- **Zugangssicherung** für das Nassmodul (PIN oder Schlüsselschalter): der
  Härter ist ätzend, das Trockenmodul darf ruhig für alle offen sein, das
  Nassmodul nicht.
- Handschuh-Hinweis am Panel; Behälterwechsel nur als **ganze Flasche mit
  Adapterdeckel**, nicht durch Umfüllen.
- Belüfteter Aufstellort, insbesondere während der Pulverdosierung.

## N10. Integration ins Gesamtgerät

- **Mechanisch strikt getrennt** vom Trockenmodul: eigener Rahmenabschnitt,
  eigene Waage, eigene Ausgabestelle. Keine gemeinsame Sammelrutsche.
- Der Grund ist banal und teuer: ein Harztropfen in der Schraubenrutsche
  verklebt Kartuschenausgänge dauerhaft, und Metallspäne im Harzansatz ruinieren
  die Verklebung.
- **Gemeinsam bleiben Panel, Rahmen und Stromversorgung** — für den Benutzer ist
  es ein Gerät, mechanisch sind es zwei.
- Anordnung: Nassmodul unten (schwere Flaschen tief, kurze Fallwege, Auffangwanne
  am Boden), Trockenmodul darüber.

## N11. Teststand und Abnahme (Nassmodul)

| Test | Umfang | Kriterium |
|---|---|---|
| W1 Dosiergenauigkeit | 20 Ansätze à 30 g | Verhältnisfehler < 2 % der Härtermasse (A12) |
| W2 Kleinstansatz | 20 Ansätze à 15 g | dito — hier entscheidet die Nachlaufkompensation |
| W3 Nachlauf | 20 Ventilschließungen | Nachlaufmasse < 0,2 g und reproduzierbar |
| W4 Temperaturgang | Ansätze bei 15 °C und 30 °C | gleiche Genauigkeit, nur andere Dauer |
| W5 Mischgüte | Ansatz aushärten, aufschneiden | keine weichen Zonen, keine Schlieren an Wand und Boden |
| W6 Verdicker | Konsistenzstufen Gel und Paste | keine Klumpen, reproduzierbare Konsistenz |
| W6b Pulverförderung | 20 Dosierungen à 3 g | Streuung < 5 %, kein Abriss durch Brückenbildung, Becher fasst die Schüttung |
| W7 Aushärtung | Shore-Härte nach 24 h gegen Handansatz | kein messbarer Unterschied |
| W8 Dauerstand | 50 Ansätze ohne Reinigung | keine Düsenverstopfung, kein Tropfverlust |

W5 und W7 sind die eigentlichen Abnahmetests: sie prüfen nicht die Mechanik,
sondern ob am Ende brauchbares Epoxid herauskommt.

## N12. Roadmap Nassmodul

| Stufe | Inhalt | Ziel |
|---|---|---|
| **W0** | Schlauch, Quetschventil, Küchenwaage, Handbetrieb | Durchfluss und Nachlauf real messen (N4/N5) |
| **W1** | Eine Flüssigkeit, Waage im Regelkreis | Zielmasse ± 0,1 g automatisch treffen |
| **W2** | Zweite Flüssigkeit, Verhältnisrechnung auf Istmasse | W1/W2-Tests bestehen |
| **W3** | Rührwerk mit Einwegbecher und -paddel | Mischgüte W5 |
| **W4** | Verdickerschnecke mit Brückenbrecher | W6 |
| **W5** | Einhausung, Auffangwanne, Zugangssicherung, Panel-Anbindung | Betriebsreife |

**W0 ist wie P0 bewusst primitiv**: ein Schlauch, eine Klemme und eine
Küchenwaage beantworten die einzige Frage, an der das Konzept scheitern könnte —
ob zähes Harz per Schwerkraft schnell genug und reproduzierbar genug fließt.
Diese Messung kostet einen Nachmittag und entscheidet über den ganzen Rest.

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

## Anhang B — Auslegungsdaten Nassmodul

> Alle Stoffwerte sind **Richtwerte zur Auslegung**. Mischungsverhältnis,
> Topfzeit und Verarbeitungstemperatur des konkret verwendeten Systems stehen im
> technischen Datenblatt des Herstellers und nirgends sonst. Sie gehören als
> Behälterprofil in die Steuerung und werden beim Flaschenwechsel mitgetauscht.

**Stoffwerte (Größenordnungen, 20 °C)**

| Größe | Harz | Härter | Verdicker (pyrogene Kieselsäure) |
|---|---|---|---|
| Viskosität | 700 – 1500 mPa·s | 50 – 500 mPa·s | Pulver |
| Dichte | ca. 1,1 g/cm³ | ca. 0,95 – 1,0 g/cm³ | Schüttdichte ca. 0,05 g/cm³ |
| Temperaturgang Viskosität | ca. Faktor 2 je 10 K | ca. Faktor 2 je 10 K | — |
| Werkstoffverträglichkeit | PP, PE, PTFE, Silikon, Edelstahl | dito, **kein Kupfer/Messing** | — |

**Durchflussabschätzung Schwerkraftdosierung** (laminar, Hagen-Poiseuille;
η = 1 Pa·s, Höhe 300 mm, Schlauchlänge 250 mm, ρ = 1,1 g/cm³):

| Innen-Ø | Volumenstrom | Massenstrom | 30 g in |
|---|---|---|---|
| 4 mm | ca. 0,08 ml/s | ca. 0,09 g/s | ca. 5,5 min — unbrauchbar |
| 6 mm | ca. 0,4 ml/s | ca. 0,45 g/s | ca. 70 s |
| 8 mm | ca. 1,3 ml/s | ca. 1,4 g/s | ca. 22 s |
| 10 mm | ca. 3,2 ml/s | ca. 3,5 g/s | ca. 9 s |

Die vierte Potenz des Radius ist hier die ganze Botschaft: von 6 auf 8 mm
verdreifacht sich der Durchsatz. Umgekehrt macht ein zu dünner Schlauch das
Konzept unbrauchbar, lange bevor die Genauigkeit ein Thema wird.

**Anforderung an die Wägeauflösung** (Verhältnis 100:50, Grenze A12 = 2 % der
Härtermasse):

| Ansatz | Harz | Härter | zulässige Abweichung | nötige Auflösung |
|---|---|---|---|---|
| 15 g | 10 g | 5 g | ± 0,10 g | 0,01 g |
| 40 g | 27 g | 13 g | ± 0,27 g | 0,01 – 0,05 g |
| 150 g | 100 g | 50 g | ± 1,0 g | 0,1 g |

→ Eine Wägezelle mit 0,01 g Auflösung und 500 g Bereich deckt das gesamte
Spektrum ab. Der **Mindestansatz von 15 g ergibt sich nicht aus der Waage,
sondern aus dem Nachlauf** (Test W3): solange die Nachlaufmasse unter 0,2 g
liegt und reproduzierbar ist, trägt die Kompensation aus N5.3 den kleinen
Ansatz.
