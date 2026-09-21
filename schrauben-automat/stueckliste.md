# Stückliste

Ergänzung zu `mechanik-konzept.md`. Alle Preise sind **Richtwerte** (Stand der
Planung, europäischer Versandhandel) und dienen der Größenordnung, nicht der
Beschaffung. Die Steuerungsplattform ist bewusst noch offen — sie steht als
Platzhalter in Abschnitt 4.

---

## 1. Prototyp — der erste Nachmittag (P0 + W0)

Das Minimum, um die beiden Fragen zu beantworten, an denen das ganze Projekt
hängt: Gibt das Escapement wirklich genau ein Teil frei, und fließt zähes Harz
per Schwerkraft schnell genug?

| Pos | Teil | Menge | Richtpreis | Anmerkung |
|---|---|---|---|---|
| 1.1 | PETG-Filament | 1 kg | 20 € | reicht für alle Prototypteile |
| 1.2 | M3-Schrauben als Testware | 200 Stk | 8 € | Zylinderkopf, eine Länge |
| 1.3 | Messschieber (digital) | 1 | 15 € | Pflicht — Taschentiefe wird gemessen, nicht geschätzt |
| 1.4 | Silikonschlauch 8 × 12 mm | 1 m | 6 € | für W0 |
| 1.5 | Schlauchklemme (Handbetrieb) | 1 | 2 € | Quetschventil von Hand |
| 1.6 | Feinwaage 0,01 g / 500 g | 1 | 15 € | später durch Wägezelle ersetzt |
| 1.7 | Epoxid-Set klein (Harz + Härter) | 300 g | 20 € | Datenblatt mitnehmen! |
| | **Summe P0 + W0** | | **ca. 85 €** | kein Motor, keine Elektronik |

---

## 2. Ein motorisiertes Fach (P1) — je Kartusche

Diese Position wird im Vollausbau mit der Fachzahl multipliziert.

| Pos | Teil | Menge | Richtpreis | Anmerkung |
|---|---|---|---|---|
| 2.1 | Getriebemotor N20, 6 V, ca. 100 min⁻¹ | 1 | 4,00 € | Drehmoment > 0,3 Nm an der Welle |
| 2.2 | Motortreiber-Kanal (DRV8833 / TB6612, 2 Kanäle je Platine) | 0,5 | 0,75 € | Reversieren zwingend nötig |
| 2.3 | Hall-Sensor A3144 + Magnet 3 × 2 mm | 1 | 0,50 € | Index: eine Umdrehung = ein Teil |
| 2.4 | Gabel-/Reflexkoppler (z. B. ITR9608) | 1 | 0,50 € | Füllstand der Schiene |
| 2.5 | Kartusche, gedruckt (PETG, ca. 60 g) | 1 | 1,50 € | Magazin + Vereinzelung + Kupplung |
| 2.6 | Einwegkupplung HF0612 (Freilauf) | 2 | 3,00 € | nur bei Trichter-Kartuschen (Abschnitt 4.3, Stufe 2) |
| 2.7 | Kleinteile (Wellenstummel 4 mm, Federdraht, Buchsen) | — | 1,00 € | |
| | **Summe je Fach** | | **ca. 11 €** | ohne Trichter: ca. 8 € |

---

## 3. Trockenmodul zentral (einmalig, unabhängig von der Fachzahl)

| Pos | Teil | Menge | Richtpreis | Anmerkung |
|---|---|---|---|---|
| 3.1 | Induktiver Näherungssensor LJ12A3-4-Z/BX | 1 | 5,00 € | zählt in der Hauptrutsche; erkennt nur Metall |
| 3.2 | Wägezelle 500 g + HX711 | 1 | 5,00 € | Plausibilitätsprüfung der Ausgabeschale (optional) |
| 3.3 | I/O-Erweiterung MCP23017 (16 Kanäle) | 2 | 6,00 € | bei 24 Fächern |
| 3.4 | Netzteil 12 V / 5 A | 1 | 15,00 € | plus Step-down auf 6 V für die Motoren |
| 3.5 | Alu-Profil 20 × 20 mm + Winkel | ca. 6 m | 35,00 € | Rahmen |
| 3.6 | Gehäuseplatten (Acryl 4 mm oder Sperrholz 6 mm) | ca. 1 m² | 25,00 € | Front transparent |
| 3.7 | TPU-Filament (Rutschenauskleidung) | 250 g | 8,00 € | Geräuschdämpfung, Anforderung A10 |
| 3.8 | Kabel, JST-XH-Steckverbinder, Schrumpfschlauch | — | 20,00 € | |
| 3.9 | Ladewanne mit Vibrationsmotor (Befüllhilfe Stufe 1) | 1 | 10,00 € | ein Werkzeug für alle Kartuschen |
| | **Summe zentral** | | **ca. 130 €** | |

---

## 4. Steuerung und Panel — Platzhalter (Entscheidung offen)

| Variante | Teile | Richtpreis |
|---|---|---|
| ESP32-S3 mit 7"-Touchdisplay | Board + Display als Einheit | 45 – 70 € |
| Raspberry Pi 4/5 + 7"-Touchscreen | Pi, Netzteil, Display, SD | 120 – 160 € |
| Arduino Mega + Nextion-Display | Board + Display | 60 – 80 € |

Die Mechanik ist von dieser Wahl nicht betroffen: sie braucht je Fach zwei
digitale Ausgänge (Motorrichtung) und zwei digitale Eingänge (Index, Füllstand),
dazu zentral einen Zähleingang und einen I²C-Bus für die Wägezellen.

---

## 5. Nassmodul (2K-Epoxid mit Verdicker)

| Pos | Teil | Menge | Richtpreis | Anmerkung |
|---|---|---|---|---|
| 5.1 | Servo MG90S + gedruckte Quetschbacke | 2 | 6,00 € | Quetschventil Harz und Härter |
| 5.2 | Silikonschlauch 8 × 12 mm | 2 m | 12,00 € | Verschleißteil, benetzt |
| 5.3 | Wägezelle 300 g (Einpunkt) + HX711 | 1 | 10,00 € | Mischbecher; siehe Hinweis unten |
| 5.4 | Schrittmotor 28BYJ-48 + Treiber | 1 | 5,00 € | Dosierschnecke Pulver |
| 5.5 | Getriebemotor 12 V, ca. 30 min⁻¹ | 1 | 5,00 € | Brückenbrecher im Pulvertrichter |
| 5.6 | Getriebemotor 12 V, ca. 300 min⁻¹ | 1 | 8,00 € | Rührteller |
| 5.7 | Edelstahlrohr Ø 6 mm, 150 mm | 1 | 3,00 € | Pulverauslauf, geerdet gegen Statik |
| 5.8 | Vorratsflaschen PE 1 l / 0,5 l + gedruckte Adapterdeckel | 3 | 12,00 € | Harz, Härter, Pulver |
| 5.9 | Auffangwanne PP | 1 | 5,00 € | chemikalienfest, herausnehmbar |
| 5.10 | Einweg-Mischbecher PP 200 ml | 100 Stk | 12,00 € | ab 250 ml bei Glass Bubbles |
| 5.11 | Holzspatel als Rührpaddel | 100 Stk | 4,00 € | Einwegteil, wird mit dem Becher entsorgt |
| 5.12 | Nitrilhandschuhe | 100 Stk | 8,00 € | Härter ist hautsensibilisierend |
| | **Summe Nassmodul** | | **ca. 90 €** | ohne Verbrauchsmaterial |

**Verbrauchsmaterial (nicht Teil des Geräts):** Epoxidharz + Härter ca. 1 kg
(30 – 50 €), pyrogene Kieselsäure 250 g (15 – 25 €).

> **Hinweis zu 5.3:** Die im Konzept genannte Auflösung von 0,01 g ist mit einer
> 10-€-Wägezelle nur unter guten Bedingungen erreichbar (Abschirmung,
> Mittelwertbildung, keine Zugluft, konstante Temperatur). Test W1/W2 klärt das.
> Wird nur 0,05 g stabil erreicht, steigt der Mindestansatz von 15 g auf 25 g —
> die Mechanik ändert sich dadurch nicht.

---

## 6. Gesamtkosten Vollausbau (24 Fächer + Nassmodul)

| Block | Rechnung | Summe |
|---|---|---|
| Fächer | 24 × 11 € | 264 € |
| Trockenmodul zentral | | 130 € |
| Steuerung/Panel | mittlere Variante | 70 € |
| Nassmodul | | 90 € |
| Filament gesamt | ca. 2 kg PETG + TPU | 45 € |
| Reserve 15 % | | 90 € |
| | **Gesamt** | **ca. 690 €** |

Der Einstieg kostet davon ca. 85 € (Abschnitt 1). Erst wenn P0 und W0 bestanden
sind, lohnt die Beschaffung der Positionen 2 bis 5 — vorher ist jede Bestellung
eine Wette auf eine unbewiesene Mechanik.
