# Technisches Konzept: Modulares, batteriebetriebenes Erkennungssystem

**Version:** 1.0  
**Datum:** 2026-06-05  
**Status:** Entwurf

---

## Inhaltsverzeichnis

1. [Geeignete Technologien zur Erkennung von Menschen und großen Lebewesen](#1-geeignete-technologien)
2. [Warum reine Bewegungsmelder ungeeignet sind](#2-warum-reine-bewegungsmelder-ungeeignet-sind)
3. [Technologievergleich](#3-technologievergleich)
4. [Empfohlene Systemarchitektur](#4-empfohlene-systemarchitektur)
5. [Kommunikation ohne WLAN](#5-kommunikation-ohne-wlan)
6. [Rolle von Gateways und Repeatern](#6-rolle-von-gateways-und-repeatern)
7. [Aufbau eines Sensorknotens](#7-aufbau-eines-sensorknotens)
8. [Energieversorgung und Batterielaufzeit](#8-energieversorgung-und-batterielaufzeit)
9. [Zentrale Einheit, Server und Dashboard](#9-zentrale-einheit-server-und-dashboard)
10. [Datenfluss vom Sensor bis zur Anzeige](#10-datenfluss-vom-sensor-bis-zur-anzeige)
11. [Menschenerkennung ohne Videoüberwachung](#11-menschenerkennung-ohne-videoüberwachung)
12. [Erkennung von Hunden und großen Tieren](#12-erkennung-von-hunden-und-großen-tieren)
13. [Strategien zur Reduktion von Fehlalarmen](#13-strategien-zur-reduktion-von-fehlalarmen)
14. [Sicherheitsaspekte und Verschlüsselung](#14-sicherheitsaspekte-und-verschlüsselung)
15. [Grober Prototyp mit realistischen Komponenten](#15-grober-prototyp-mit-realistischen-komponenten)
16. [Skalierbarkeit](#16-skalierbarkeit)
17. [Technische Risiken und Grenzen](#17-technische-risiken-und-grenzen)
18. [Empfehlung für den ersten Prototyp](#18-empfehlung-für-den-ersten-prototyp)

---

## 1. Geeignete Technologien zur Erkennung von Menschen und großen Lebewesen

Die Erkennung von Menschen und großen Tieren ist deutlich anspruchsvoller als einfache Bewegungserkennung. Der Kern des Problems liegt in der Unterscheidung zwischen relevanten Objekten (Mensch, Hund) und irrelevanten Störquellen (Wind, Regen, Vögel, Insekten, Blätter).

### 1.1 Physikalische Grundlage der Unterscheidung

Menschen und große Tiere unterscheiden sich von Störquellen durch mehrere messbare Eigenschaften:

| Eigenschaft           | Mensch/Hund           | Störquelle (Blatt, Vogel) |
|-----------------------|-----------------------|---------------------------|
| Wärmeabstrahlung      | 36–38 °C, großflächig | gering oder nicht vorhanden |
| Radarquerschnitt      | 0,5–1,0 m² (Mensch)   | < 0,01 m²                 |
| Bewegungsmuster       | rhythmisch, zielgerichtet | chaotisch, unregelmäßig |
| Körpergröße           | > 50 cm Höhe          | < 20 cm                   |
| Doppler-Signatur      | charakteristische Extremitätenbewegung | breitbandiges Rauschen |

### 1.2 Technologiekombinationen nach Eignung

**Klasse A – Hochgenauigkeit (empfohlen für zuverlässige Erkennung):**
- **mmWave-Radar + PIR-Sensor:** Radar erkennt Bewegung und Körpergröße, PIR bestätigt Wärmesignatur. Sehr geringe Fehlalarmrate.
- **Thermalkamera + einfaches KI-Modell:** Silouette-basierte Klassifikation im Wärmebildbereich, datenschutzkonform, wetterfest.

**Klasse B – Mittlere Genauigkeit (für einfachere Szenarien):**
- **PIR + Mikrowellen-Radar (Dual-Tech):** Klassischer Doppelmelder, günstig, aber keine Klassifikation.
- **Time-of-Flight + PIR:** Ermöglicht grobe Größenabschätzung.

**Klasse C – Nur als Ergänzung:**
- **Einzel-PIR:** Zu viele Fehlalarme in der Outdoor-Umgebung.
- **Ultraschall:** Kurze Reichweite, wetterempfindlich.

---

## 2. Warum reine Bewegungsmelder ungeeignet sind

Handelsübliche PIR-Bewegungsmelder (Passive Infrared) sind für den beschriebenen Anwendungsfall aus mehreren Gründen allein unzureichend:

### 2.1 Funktionsprinzip und Einschränkungen

Ein PIR-Sensor misst lediglich die **Änderung der Infrarotstrahlung** in seinem Erfassungsbereich. Er ist blind für:

- **Art des Objekts:** Er unterscheidet nicht zwischen Mensch, Vogel oder flatterndem Blatt.
- **Größe des Objekts:** Ein Vogel, der 30 cm vor dem Sensor vorbeifliegt, erzeugt dasselbe Signal wie ein Mensch in 5 m Entfernung.
- **Temperaturänderungen durch Umwelt:** Sonneneinstrahlung, die einen Ast aufwärmt und der Wind dann bewegt, kann einen PIR-Alarm auslösen.

### 2.2 Typische Fehlalarmquellen im Outdoor-Betrieb

```
Typische Falsch-Positiv-Rate reiner PIR-Sensoren (Outdoor):
- Sonnenstrahlung + Windbewegte Vegetation: 40–60 % aller Auslösungen
- Vögel und größere Insekten:               10–20 %
- Regen und Wetterphänomene:                 5–15 %
- Kleine Säugetiere (Mäuse, Ratten):         5–10 %
→ Nur ~15–35 % der Auslösungen sind tatsächlich Menschen oder große Tiere
```

### 2.3 Fazit

Reine Bewegungsmelder sind als **Vorfilter** sinnvoll, um den Sensorknoten aus dem Tiefschlaf zu wecken. Für die eigentliche Klassifikation (Mensch vs. Störung) sind sie nicht ausreichend. Sie müssen durch eine zweite Technologie oder KI-gestützte Nachverarbeitung ergänzt werden.

---

## 3. Technologievergleich

### 3.1 Übersichtstabelle

| Technologie       | Reichweite   | Wetterfest | Klassif. | Stromverbrauch | Kosten (Modul) | Privatsphäre |
|-------------------|--------------|------------|----------|----------------|----------------|--------------|
| PIR               | 5–15 m       | Bedingt    | Keine    | Sehr niedrig   | 1–5 €          | Hoch         |
| Mikrowellen-Radar | 5–20 m       | Ja         | Gering   | Niedrig        | 3–15 €         | Hoch         |
| mmWave-Radar (60 GHz) | 3–10 m  | Ja         | Mittel–Hoch | Mittel      | 15–40 €        | Hoch         |
| Thermalkamera (Low-Res) | 5–15 m | Ja       | Hoch     | Mittel         | 30–150 €       | Sehr hoch    |
| RGB-Kamera + KI   | 3–30 m       | Bedingt    | Sehr hoch | Hoch           | 10–60 €        | Niedrig      |
| LiDAR (1D/2D)     | 1–40 m       | Bedingt    | Mittel   | Mittel–Hoch    | 20–200 €       | Hoch         |
| Time-of-Flight    | 0,1–5 m      | Bedingt    | Gering   | Niedrig        | 3–15 €         | Hoch         |

### 3.2 Detailbewertung der wichtigsten Technologien

#### mmWave-Radar (z. B. Texas Instruments IWR6843, Acconeer XM125)

**Funktionsprinzip:** Millimeterwellen (60–77 GHz) werden ausgesendet und reflektierte Echos analysiert. Aus Laufzeit, Frequenzverschiebung (Doppler) und Phasenlage lassen sich Entfernung, Geschwindigkeit und grobe Kontur extrahieren.

**Vorteile:**
- Erkennt Atmung und Herzschlag (Micro-Doppler) – eindeutige Signatur für Lebewesen
- Funktioniert durch dünne Materialien (Kunststoffgehäuse, Vegetation)
- Unabhängig von Lichtverhältnissen und weitgehend wetterunabhängig
- Keine Erfassung visuell identifizierbarer Bilder → datenschutzkonform

**Nachteile:**
- Moderate Reichweite (3–10 m effektiv für Menschenerkennung)
- Metallische Objekte können starke Reflexionen verursachen (Fehlalarme)
- Höherer Stromverbrauch als PIR (typisch 150–500 mW im Betrieb)
- Programmierung/Konfiguration komplex

**Stromverbrauch (Beispiel TI IWR6843AOP):**
- Aktivbetrieb: ~350–600 mW
- Sleep: ~1–5 mW

#### PIR-Sensor (z. B. HC-SR501, BISS0001-basiert)

**Vorteile:** Extrem günstig, sehr geringer Stromverbrauch (< 1 mW im Betrieb), einfache Integration, breite Verfügbarkeit.

**Nachteile:** Keine Klassifikation, sehr hohe Fehlalarmrate outdoor, temperaturempfindlich, blind bei langsamer Bewegung.

**Empfehlung:** Ausschließlich als Wake-Up-Trigger verwenden, nicht als primärer Klassifikationssensor.

#### Thermalkamera (z. B. FLIR Lepton 3.5, MLX90640, Heimann HTPA)

**Funktionsprinzip:** Messung der Infrarotstrahlung im Bereich 8–14 µm. Lebewesen mit Körpertemperatur erscheinen deutlich heller als Umgebungstemperatur.

**Vorteile:**
- Erkennt Lebewesen zuverlässig durch Wärmekontrast
- Datenschutzkonform (kein erkennbares Gesicht bei niedriger Auflösung)
- Funktioniert bei totaler Dunkelheit
- Mit einfachem KI-Modell: Klassifikation Mensch vs. Tier vs. Hintergrund möglich

**Nachteile:**
- Teure Module (Lepton 3.5: ~120–200 €; MLX90640: ~30–50 €)
- Niedrige Auflösung (MLX90640: 32×24 Pixel) schränkt Klassifikationsqualität ein
- Im Sommer bei hohen Umgebungstemperaturen sinkt der Wärmekontrast
- Verarbeitung der Thermaldaten erfordert Mikrocontroller mit ausreichend RAM

**Niedrig-Auflösung als Feature:** Bei 32×24 Pixeln ist keine personenbezogene Identifikation möglich. Dies ist ein Datenschutzvorteil und vereinfacht die lokale KI-Verarbeitung erheblich.

#### Kamera mit lokaler KI (z. B. Sony IMX500, Raspberry Pi Camera + Coral TPU)

**Vorteile:**
- Höchste Klassifikationsgenauigkeit (YOLO, MobileNet: >90 % Personenerkennung)
- Gleichzeitig optionales Bildbeweismittel

**Nachteile:**
- Datenschutzrechtlich problematisch (DSGVO)
- Hoher Stromverbrauch (ESP32-CAM: ~300 mW; Pi Zero + Coral: ~1–2 W)
- Schlechte Performance bei Dunkelheit ohne IR-Beleuchtung
- Regen, Schmutz und Kondenswasser beeinflussen Linse

**Sonderfall Sony IMX500:** Kamera-SoC mit eingebetteter KI-Inferenz. Gibt nur Metadaten (Bounding Box, Klasse, Konfidenz) aus, kein Rohbild. Technisch interessant, aber teuer (~30–80 €) und derzeit nur begrenzte Ökosystem-Unterstützung.

#### LiDAR (z. B. Benewake TF-Luna, RPLIDAR A1)

**Vorteile:** Präzise Entfernungsmessung, funktioniert bei Tag und Nacht.

**Nachteile:** Punktmessung (1D) kaum ausreichend für Klassifikation; 2D-LiDAR (360°) zu groß und zu stromhungrig für Batteriebetrieb; Regen, Nebel und Staub stören erheblich.

**Empfehlung:** Nur für spezielle Szenarien (z. B. Eingangstor-Lichtschranke), nicht als primäre Erkennungstechnologie.

### 3.3 Sensorfusion: Warum die Kombination besser ist

```
Einzelsensor-Zuverlässigkeit (Outdoor):
  PIR allein:                ~40 % Präzision
  mmWave allein:             ~70 % Präzision
  Thermalkamera allein:      ~75 % Präzision

Sensorfusion:
  PIR (Wake-Up) + mmWave:              ~80 % Präzision
  PIR (Wake-Up) + Thermalkamera:       ~85 % Präzision
  PIR + mmWave + Thermalkamera:        ~92 % Präzision
  (Schätzwerte, stark umgebungsabhängig)
```

Die Kombination aus **PIR als Aufweck-Trigger** und **mmWave oder Thermalkamera als Klassifikationssensor** bietet das beste Verhältnis aus Zuverlässigkeit, Stromverbrauch und Kosten.

---

## 4. Empfohlene Systemarchitektur

### 4.1 Systemübersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        ÜBERWACHUNGSBEREICH                       │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │Knoten #1 │    │Knoten #2 │    │Knoten #3 │    │Knoten #N │  │
│  │(PIR+mmW) │    │(PIR+mmW) │    │(PIR+Thm) │    │(PIR+mmW) │  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘  │
│       │ LoRa          │ LoRa          │ LoRa          │ LoRa   │
│       └───────────────┴───────────────┴───────────────┘        │
│                               │                                  │
│                      ┌────────▼────────┐                        │
│                      │   Gateway/      │                        │
│                      │   Repeater      │  (optional, bei        │
│                      │   (falls nötig) │   großer Entfernung)  │
│                      └────────┬────────┘                        │
└───────────────────────────────┼─────────────────────────────────┘
                                │ LoRa / LoRaWAN / kabelgebunden
                       ┌────────▼────────┐
                       │  Zentraleinheit  │
                       │  (Gateway-Node   │
                       │   + Raspberry Pi │
                       │   oder Server)   │
                       └────────┬────────┘
                                │ LAN / Internet (optional)
                       ┌────────▼────────┐
                       │    Dashboard     │
                       │  (Web-UI, App,   │
                       │   Benachricht.)  │
                       └─────────────────┘
```

### 4.2 Schichtenmodell

**Schicht 1 – Sensorknoten (Edge-Gerät):**
- Sensorerfassung und lokale Vorverarbeitung
- Klassifikation auf dem Mikrocontroller
- Schlafmodus-Management
- Ereignisbasierte Funk-Übertragung

**Schicht 2 – Kommunikationsnetz:**
- LoRa-Punkt-zu-Punkt oder LoRaWAN-Netzwerk
- Optional Mesh-Routing bei komplexen Topologien
- Gateway/Repeater bei Bedarf

**Schicht 3 – Zentraleinheit:**
- Empfang aller Ereignismeldungen
- Datenbankpersistenz
- Regelwerk für Alarme
- Dashboard-Backend (REST API / MQTT Broker)

**Schicht 4 – Benutzerschnittstelle:**
- Web-Dashboard (Browser-basiert)
- Push-Benachrichtigungen (App, E-Mail, Webhook)
- Konfigurationsoberfläche

### 4.3 Datenmodell eines Ereignisses

Ein Sensorknoten sendet bei Erkennung ein kompaktes Paket (~15–30 Byte):

```
Ereignis-Paket (Binärformat):
Byte 0-1:   Knoten-ID (16-bit)
Byte 2:     Ereignistyp: 0x01=Mensch, 0x02=Tier, 0x03=Unklar, 0x04=Heartbeat
Byte 3:     Konfidenz (0–100)
Byte 4-5:   Batterispannung (mV, 16-bit)
Byte 6:     RSSI des letzten Empfangs (dBm + Offset)
Byte 7:     Temperatur (°C + Offset, 8-bit)
Byte 8-11:  Unix-Zeitstempel (32-bit, falls RTC vorhanden)
Byte 12-13: CRC16-Prüfsumme
```

Gesamtgröße: 14 Byte – gut geeignet für LoRa-Übertragung mit niedriger Datenrate.

---

## 5. Kommunikation ohne WLAN

### 5.1 Vergleich verfügbarer Funktechnologien

| Technologie    | Reichweite (Freifeld) | Bandbreite | Stromverbrauch TX | Mesh | Lizenz | Typische Latenz |
|----------------|-----------------------|------------|-------------------|------|--------|-----------------|
| LoRa (868 MHz) | 2–15 km               | 0,3–27 kbps | 20–120 mA        | Nein (LoRaWAN) | Frei (EU 868) | 1–5 s |
| LoRa Mesh (Meshtastic) | 2–10 km       | ~1–5 kbps  | 20–120 mA        | Ja   | Frei   | 2–30 s |
| Zigbee (2,4 GHz) | 10–100 m            | 250 kbps   | 20–40 mA         | Ja   | Frei   | 10–100 ms |
| Thread         | 10–100 m              | 250 kbps   | 20–40 mA         | Ja   | Frei   | < 100 ms |
| Sub-GHz (868/915 MHz, proprietär) | 300 m – 2 km | 1–500 kbps | 10–100 mA | Nein/Ja | Frei | < 500 ms |
| Bluetooth 5 Mesh | 10–100 m           | 1 Mbps     | 5–15 mA          | Ja   | Frei   | 50–200 ms |
| 433 MHz (OOK/FSK) | 100 m – 2 km      | 1–100 kbps | 10–50 mA         | Nein | Frei   | 50–500 ms |

### 5.2 Empfehlung: LoRa (868 MHz in EU)

**LoRa** ist die am besten geeignete Technologie für dieses System:

**Gründe:**
1. **Große Reichweite:** Im Freifeld 2–15 km, in bebautem Gelände 300 m – 2 km. Deckt die meisten Outdoor-Szenarien ab.
2. **Extrem niedriger Stromverbrauch:** Ein Sendevorgang dauert 20–500 ms und verbraucht ~50–100 mA. Bei einem Ereignis pro Stunde ergibt sich ein sehr geringer Durchschnittsverbrauch.
3. **Penetration durch Vegetation:** 868 MHz durchdringt Wald und Buschwerk deutlich besser als 2,4 GHz.
4. **Lizenzfreiheit in EU (868 MHz, SRD-Band):** Keine Genehmigung erforderlich, jedoch Duty-Cycle-Beschränkung von 1 % (36 s/h).
5. **Günstige Module:** LoRa-Module (z. B. LLCC68, SX1276, E32-868T20D) kosten 3–15 €.

**Einschränkungen:**
- Duty-Cycle-Beschränkung: Max. 36 Sekunden Sendezeit pro Stunde im 868-MHz-Band.
- Keine garantierte Empfangsbestätigung ohne ACK-Mechanismus.
- Bandbreite zu gering für Bild- oder Audiodaten.

**LoRaWAN vs. Direktübertragung:**
- **Direktübertragung (P2P-LoRa):** Einfacher, kein separates Netzwerk nötig, aber kein Routing-Protokoll.
- **LoRaWAN:** Standardprotokoll mit Geräteauthentifizierung (OTAA/ABP), Verschlüsselung (AES-128), und mehreren Gateways. Empfohlen für größere Deployments.

### 5.3 Zigbee / Thread als Alternative

Für Szenarien mit kurzen Distanzen (Haus, Hofgelände < 200 m):
- **Zigbee:** Weit verbreitet, günstige Module (CC2530, CC2652), Mesh-Routing vorhanden.
- **Thread:** Moderner, IPv6-basiert, kompatibel mit Matter-Ökosystem.
- **Nachteil beider:** 2,4 GHz hat deutlich schlechtere Durchdringung von Vegetation und Wänden.

### 5.4 Sub-GHz (z. B. Semtech SX1231, TI CC1101, SPIRIT1)

Proprietäre Sub-GHz-Protokolle bei 868 MHz oder 433 MHz:
- Einfachere Implementierung als LoRa
- Geringere Reichweite als LoRa (durch fehlendes Spread-Spectrum)
- Gut für einfache Punkt-zu-Punkt-Systeme

---

## 6. Rolle von Gateways und Repeatern

### 6.1 Wann sind Gateways/Repeater nötig?

Ein LoRa-Gateway ist erforderlich, wenn:
- Der Bereich zu groß ist für direkte Verbindung (> 500 m in bebautem Gelände)
- Natürliche Hindernisse (Hügel, Gebäude) die Funkstrecke blockieren
- Mehr als ~20–30 Knoten verwaltet werden (LoRaWAN-Gateway effizienter)

### 6.2 Repeater-Konzept (P2P-LoRa)

```
Knoten A ──[LoRa]──► Repeater ──[LoRa]──► Zentrale

Repeater-Logik:
  - Empfangt LoRa-Paket
  - Prüft Paket-ID (Duplikat-Schutz)
  - Sendet das Paket mit kurzer Verzögerung weiter (Store & Forward)
  - Stromversorgung: idealer Kandidat für Solarenergie (da stationär)
```

**Einschränkung:** Repeater müssen im selben LoRa-Kanal und mit kompatibler Konfiguration betrieben werden. Sie erhöhen die Übertragungslatenz um ~1–5 Sekunden.

### 6.3 LoRaWAN-Gateway

Ein LoRaWAN-Gateway (z. B. RAK7268, Dragino LPS8, Heltec HT-M01) empfängt Pakete von bis zu hunderten Knoten gleichzeitig über alle Spreading Factors.

**Hardware-Anforderungen eines Gateways:**
- LoRaWAN-Concentrator-Chip (SX1301/SX1302/SX1303)
- Ethernet oder LTE/4G-Backhaul
- Stromversorgung (kein Batteriebetrieb sinnvoll – daher Solar oder Netz)
- Kostenpunkt: 100–300 € für fertige Gateways

---

## 7. Aufbau eines Sensorknotens

### 7.1 Blockschaltbild

```
┌─────────────────────────────────────────────────────────────┐
│                        SENSORKNOTEN                          │
│                                                              │
│  ┌──────────┐   Interrupt    ┌──────────────────────────┐   │
│  │PIR-Sensor│──────────────►│                          │   │
│  └──────────┘                │   Mikrocontroller        │   │
│                               │   (ESP32-S3 / nRF52840 / │   │
│  ┌──────────┐   SPI/I2C      │    STM32L4)              │   │
│  │mmWave    │◄──────────────►│                          │   │
│  │Radar     │                │   - Schlafmodus-Mgmt.    │   │
│  └──────────┘                │   - Klassifikations-     │   │
│                               │     logik                │   │
│  ┌──────────┐   I2C          │   - Verschlüsselung      │   │
│  │Temp/     │◄──────────────►│   - Paketvorbereitung    │   │
│  │Feuchte   │                │                          │   │
│  │(optional)│                └──────────┬───────────────┘   │
│  └──────────┘                           │ SPI                │
│                                         ▼                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LoRa-Modul (SX1276 / LLCC68)            │   │
│  │              (868 MHz, 20–100 mW TX)                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Stromversorgung                             │   │
│  │  LiPo 3,7V / 2–5 Ah   ──►  LDO / Buck-Boost         │   │
│  │  (optional Solar MPPT)       3,3V für MCU/Sensoren    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Empfohlene Komponenten (Prototyp-Variante)

#### Mikrocontroller

**Option A: ESP32-S3 (Espressif)**
- Vorteile: Bekannte Plattform, ULP-Coprozessor für Sleep, integriertes WLAN/BT (kann deaktiviert werden), gute Bibliotheken
- Stromverbrauch im Deep Sleep: ~10–20 µA
- Stromverbrauch aktiv: ~80–150 mA (bei 240 MHz)
- Preis: 3–8 € (Modul)

**Option B: nRF52840 (Nordic Semiconductor)**
- Vorteile: Extrem sparsam, BLE5 + Zigbee/Thread, sehr aktive Community (Zephyr RTOS)
- Stromverbrauch im Deep Sleep: ~1,5–3 µA
- Stromverbrauch aktiv: ~4–8 mA (CPU), ~15–20 mA (bei BLE TX)
- Preis: 3–10 € (Modul, z. B. Seeed XIAO nRF52840)

**Option C: STM32L476 / STM32L562 (STMicroelectronics)**
- Vorteile: Industrie-Standard, extrem niedriger Stromverbrauch, gute Hardware-Security-Funktionen
- Stromverbrauch im Standby: ~0,4–2 µA
- Preis: 3–12 €

**Empfehlung für Prototyp:** ESP32-S3 (Verfügbarkeit, Bibliotheken, Community); für Produktion: nRF52840 (Effizienz) oder STM32L4 (Robustheit).

#### Primärsensor: mmWave-Radar

**Acconeer XM125 (60 GHz, Pulsed Coherent Radar):**
- Reichweite: 0,1–20 m (Presence Detection bis ~5–7 m zuverlässig)
- Erkennung: Presence, Movement, Distance
- Schnittstelle: SPI/UART, I2C
- Stromverbrauch: ~80–200 mW aktiv, ~2 mW Standby
- Preis: ~10–20 € (EVK-Board ca. 60 €, Bare-Modul geplant)
- Besonderheit: SDK mit Presence-Detection-Algorithmus verfügbar

**Texas Instruments IWR6843AOP (60 GHz FMCW):**
- Sehr leistungsfähig, People Counting, Vitalsignale
- Komplex in der Konfiguration, höherer Preis (~30–60 €)
- Eher für Phase 2 / Produktionsversion geeignet

**DFRobot SEN0395 (24 GHz):**
- Günstiger Einstieg (~25 €), UART-Interface, fertige Firmware
- Weniger Klassifikationstiefe als 60-GHz-Systeme
- Gut für schnellen Prototyp

#### Aufweck-Trigger: PIR

**AM312 (miniaturisiert, 3,3V direkt):**
- Maße: 7×5 mm
- Verbrauch im Betrieb: ~20 µA
- Preis: < 1 €
- Ideal als reiner Aufweck-Interrupt

**HC-SR501:**
- Günstig, justierbare Empfindlichkeit und Haltezeit
- Größer, benötigt 5V (mit 3,3V-Interface-Lösung)

#### LoRa-Modul

**EBYTE E22-900M22S (SX1262, 868/915 MHz):**
- TX-Leistung: bis 22 dBm (160 mW)
- Empfindlichkeit: –148 dBm
- SPI-Interface
- Preis: 5–12 €

**Heltec HT-RA62 (SX1262):**
- SMD-Modul, kompakt
- Preis: 4–10 €

**RAK4631 (nRF52840 + SX1262 in einem Modul):**
- Kombiniertes Modul, sehr kompakt
- Preis: 15–25 €
- Exzellent für Produktionsvariante

#### Umgebungssensoren (optional)

- **BME280 (Bosch):** Temperatur, Luftfeuchte, Luftdruck – 2 € – I2C
- **DS18B20:** Temperatur, wasserdicht – 1–2 €
- **LIS3DH:** 3-Achsen-Beschleunigung (Manipulationsschutz) – 1–3 €

#### Gehäuse und Mechanik

- **Spelsberg TG PC 1208-6-o:** IP65, Polycarbonat, 120×80×60 mm – ~15 €
- **Hammond 1554 Series:** IP67, verschiedene Größen – 10–30 €
- Kabelverschraubungen M16/M20 für Antennendurchführung
- Haltebügel aus Edelstahl oder Aluminium für Pfahlmontage

### 7.3 Firmware-Ablaufdiagramm

```
┌────────────────────────────────────────────────────────┐
│                   POWER-ON / WAKEUP                     │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────┐
          │ PIR-Interrupt?   │──Nein──► Deep Sleep (Warte auf PIR)
          └────────┬─────────┘
                   │ Ja
                   ▼
          ┌──────────────────────────────┐
          │ mmWave-Radar aktivieren      │
          │ Warte 200–500 ms für Messung │
          └────────┬─────────────────────┘
                   │
                   ▼
          ┌──────────────────────────────────────────────┐
          │ Klassifikation:                               │
          │  - Presence Score (mmWave) > Schwellwert?     │
          │  - Bewegungscharakteristik (Mensch/Tier/None) │
          └────────┬──────────────────────────────────────┘
                   │
          ┌────────┴──────────┐
          │                   │
          ▼                   ▼
    Kein relevantes      Relevant (Mensch/Tier)
    Objekt erkannt       erkannt
          │                   │
          ▼                   ▼
    Zurück zu            ┌──────────────────────┐
    Deep Sleep           │ Paket erstellen       │
                         │ (Typ, Konfidenz,      │
                         │  Batterie, Temp.)     │
                         └──────────┬────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ LoRa senden           │
                         │ (verschlüsselt, ACK   │
                         │  optional)            │
                         └──────────┬────────────┘
                                    │
                                    ▼
                         Cooldown (5–30 s)
                         dann Deep Sleep
```

---

## 8. Energieversorgung und Batterielaufzeit

### 8.1 Energiebilanz-Analyse

Die Batterielaufzeit hängt entscheidend von drei Faktoren ab:
1. **Ruhestrom** (Zeit im Deep Sleep)
2. **Aktivierungshäufigkeit** (wie oft löst der PIR aus)
3. **Verbrauch bei Klassifikation + Funk**

#### Beispielrechnung: Normalbetrieb (20 Auslösungen/Tag)

```
Ziel-Hardware: ESP32-S3 + mmWave (SEN0395) + LoRa (SX1262) + PIR (AM312)
Akku: LiPo 18650, 3000 mAh, 3,7 V nominal = 11,1 Wh

─── Deep Sleep ───────────────────────────────────────────────
ESP32-S3 Deep Sleep:     15 µA
AM312 PIR (dauernd an):  20 µA
LoRa Sleep:               2 µA
Sonstige (LDO etc.):     10 µA
─────────────────────────────
Gesamt Sleep:            ~47 µA bei 3,3V

Zeit im Sleep (20 Events/Tag à 30 s aktiv):
Sleep-Zeit: 86400 s - (20 × 30 s) = 85800 s ≈ 23,8 h

Sleep-Energieverbrauch/Tag:
47 µA × 3,3 V × 23,8 h = 3,7 mWh

─── Aktiv pro Event (30 Sekunden) ───────────────────────────
Aufwachen + MCU Init:     100 mA × 0,1 s   = 2,8 mAs
mmWave aktiv:             180 mA × 0,5 s   = 25 mAs
Klassifikation (MCU):      80 mA × 0,2 s   = 4,5 mAs
LoRa Senden (22 dBm):     120 mA × 0,1 s   = 3,3 mAs
─────────────────────────────
Gesamt pro Event: ~35,6 mAs = ~9,9 µAh

20 Events/Tag: 20 × 9,9 µAh = 198 µAh/Tag = 0,73 mWh/Tag (bei 3,7V)

─── Gesamtverbrauch ──────────────────────────────────────────
Gesamt/Tag: 3,7 + 0,73 = 4,43 mWh/Tag

Laufzeit: 11100 mWh / 4,43 mWh/Tag = ~2506 Tage ≈ 6,8 Jahre

ACHTUNG: Reale Verluste einrechnen:
- Akku-Selbstentladung: -15–20 %/Jahr bei LiPo
- LDO/Buck-Boost-Verluste: -10–15 %
- Tieftemperatur-Kapazitätsverlust: -20–30 %
- PIR-Fehlalarme (Faktor 3–5 mehr Events): Entscheidend!

Realistischer Schätzwert mit Faktor 5 Fehlalarme:
~6,8 Jahre / 5 = ~1,4 Jahre pro 18650-Zelle (3000 mAh)
```

**Fazit:** Mit einem einzelnen 18650-Akku ist eine Laufzeit von **6–18 Monaten** realistisch, stark abhängig von der Fehlalarmrate.

### 8.2 Optimierungsmaßnahmen

**Hardware-Ebene:**
- Verwendung von nRF52840 statt ESP32-S3: Deep Sleep < 3 µA statt 15 µA
- Schaltbares 3,3V-Rail für mmWave (mittels P-FET): Radar vollständig abschalten wenn nicht benötigt
- Superkondensator (0,1–1 F) als Pufferspeicher für LoRa-Sendespitzen

**Software-Ebene:**
- Adaptive Erfassungsintervalle (nachts weniger Aktivierungen erwartet)
- Debounce-Zeit nach Erkennung (30–120 s Cooldown)
- Heartbeat-Intervall reduzieren (z. B. nur alle 6 Stunden statt stündlich)
- PIR-Empfindlichkeit im Wind-Modus reduzieren (per digitalen Eingang)

### 8.3 Solarbetrieb

Für stationäre Knoten (Zaunpfähle, Gebäudekanten) ist Solarergänzung sinnvoll:

**Komponenten:**
- Monokristallines Solarpanel: 2W / 6V (~60×90 mm) – 5–15 €
- CN3791 oder TP4056 MPPT-Laderegler – 1–3 €
- LiPo 18650 als Puffer

**Energieertrag (Mitteleuropa, Nov–Jan Worst Case):**
- ~2–3 kWh/m²/Tag im Dezember
- 60 cm² Panel × 20 % Wirkungsgrad × 2 kWh/m²/Tag ≈ 24 mWh/Tag

Dies übersteigt den Verbrauch von 4–20 mWh/Tag deutlich – auch im Winter ausreichend für einen normalen Knoten.

### 8.4 Batterietypen im Vergleich

| Typ               | Kapazität   | Temp.-Bereich | Selbstentladung | Preis  |
|-------------------|-------------|---------------|-----------------|--------|
| LiPo 18650        | 2000–3500 mAh | -20 bis +60°C | ~3 %/Monat     | 3–10 € |
| LiFePO4 (3,2 V)   | 1500–3500 mAh | -30 bis +70°C | ~1 %/Monat     | 5–15 € |
| Li-SOCl2 (3,6 V)  | 2000–19000 mAh | -60 bis +85°C | ~1 %/Jahr      | 5–25 € |
| 4x AA Alkaline    | ~2500 mAh (6V)| -20 bis +50°C | ~2 %/Jahr      | 2–5 €  |

**Empfehlung:**
- **Prototyp:** 18650 LiPo (einfach verfügbar, wiederaufladbar)
- **Produktion outdoor/Winter:** LiFePO4 (bessere Tieftemperaturstabilität) oder Li-SOCl2 (sehr lange Laufzeit, nicht wiederaufladbar)

---

## 9. Zentrale Einheit, Server und Dashboard

### 9.1 Hardware der Zentraleinheit

**Option A: Raspberry Pi 4 / 5 (für aktive Deployments)**
- Raspberry Pi 4 (2 GB): ~55 €
- LoRa-Hat (RAK2287 oder Dragino PG1302): ~50–120 €
- MicroSD 32 GB: ~10 €
- Stromversorgung: 5V/3A USB-C

**Option B: Raspberry Pi Zero 2 W (kostengünstig)**
- RPi Zero 2 W: ~18 €
- LoRa-Modul (per SPI direkt): 10–15 €
- Geeignet für kleine Systeme (< 10 Knoten)

**Option C: Industrierechner / NUC (für professionelle Anwendung)**
- Intel NUC oder ähnlich: 150–400 €
- USB-basiertes LoRaWAN-Gateway
- Deutlich robuster für 24/7-Betrieb

### 9.2 Software-Stack

```
Raspberry Pi / Server
├── OS: Raspberry Pi OS Lite (64-bit) / Ubuntu Server
│
├── LoRa-Empfang
│   ├── ChirpStack Gateway OS (LoRaWAN-Stack, empfohlen)
│   │   ├── Packet Forwarder (SX1302-basiert)
│   │   ├── ChirpStack Network Server
│   │   └── ChirpStack Application Server
│   └── ODER: direktes P2P LoRa via Python/pyLoRa (für einfache Setups)
│
├── Nachrichtenbroker
│   └── Mosquitto MQTT Broker (Port 1883/8883 TLS)
│
├── Datenbankschicht
│   ├── InfluxDB (Zeitreihendaten, Sensordaten)
│   └── PostgreSQL / SQLite (Konfiguration, Knoten-Metadaten)
│
├── Backend API
│   └── Node.js (Express) / Python (FastAPI) – REST + WebSocket
│
└── Dashboard
    ├── Grafana (empfohlen für schnellen Start, InfluxDB-Integration)
    └── ODER: Vue.js / React Frontend (custom, mehr Flexibilität)
```

### 9.3 Dashboard-Funktionen

Das Dashboard soll folgende Ansichten bieten:

**Hauptansicht – Live-Karte:**
- Knotenstandorte auf einer Karte (OpenStreetMap via Leaflet.js)
- Farbcodierte Knoten: Grün = ok, Gelb = niedrige Batterie, Rot = Alarm/offline
- Klick auf Knoten: Detail-Popup mit letzten Ereignissen

**Ereignis-Timeline:**
- Chronologische Liste aller Erkennungen
- Filterbar nach Knoten, Klassifikation, Zeitraum
- Export als CSV/JSON

**Knoten-Detail-Seite:**
- Batteriespannung-Verlauf (Grafik)
- RSSI-Verlauf (Signalqualität)
- Ereignis-Häufigkeit (Heatmap nach Tageszeit)
- Letzter Kontakt, Firmware-Version

**Alarm-Konfiguration:**
- Regeln: Wenn Knoten X Mensch erkennt → Benachrichtigung senden
- Kanäle: E-Mail, Telegram-Bot, Webhook (für Home Assistant, Zapier etc.)
- Zeitfenster: Alarm nur zwischen 22:00 und 06:00 Uhr

### 9.4 Benachrichtigungsarchitektur

```
Ereignis eingehend
    │
    ▼
Regelengine (Node-RED oder custom)
    │
    ├── Telegram-Bot API → Nachricht mit Knoten-ID, Zeit, Typ
    ├── E-Mail (SMTP)    → Zusammenfassung
    ├── Webhook          → Home Assistant / Zapier / IFTTT
    └── Push-Notification (via Firebase FCM → Android/iOS App)
```

---

## 10. Datenfluss vom Sensor bis zur Anzeige

### 10.1 Ende-zu-Ende-Datenfluss

```
[Physische Welt]
  Mensch betritt Überwachungsbereich
          │
          ▼
[Sensorknoten]
  1. PIR-Interrupt weckt MCU aus Deep Sleep (< 1 ms)
  2. mmWave-Radar hochfahren (100–300 ms)
  3. Radarmessung (200–500 ms)
  4. Klassifikationsalgorithmus (10–50 ms auf MCU)
  5. Ereignis-Paket erstellen + AES-128 verschlüsseln (< 5 ms)
  6. LoRa-Modul senden (100–500 ms)
  7. MCU zurück in Deep Sleep
          │ LoRa 868 MHz
          │ Latenz: ~200 ms Übertraung + Propagation
          ▼
[Gateway / Zentrale]
  1. LoRa-Modul empfängt Paket
  2. Paket entschlüsseln, CRC prüfen
  3. MQTT-Nachricht an Broker publishen (Topic: sensors/<node_id>/event)
  4. Backend subscribed auf MQTT, verarbeitet Ereignis
  5. In InfluxDB schreiben (Zeitstempel, Daten)
  6. Regelengine prüft Alarmbedingungen
  7. WebSocket-Push an alle offenen Dashboard-Clients
          │
          ▼
[Dashboard im Browser]
  1. WebSocket-Nachricht empfangen
  2. React-State aktualisieren
  3. Knotenmarker auf Karte blinkt rot
  4. Neue Zeile in Ereignis-Timeline erscheint
  5. Toast-Benachrichtigung im Browser

[Benachrichtigungskanal (parallel)]
  1. Telegram-Bot sendet Nachricht
  2. Push-Notification an App
──────────────────────────────────────────────
Gesamtlatenz Sensor → Dashboard: ~1–5 Sekunden (typisch)
```

### 10.2 Heartbeat und Statusübertragung

Zusätzlich zu Ereignissen sendet jeder Knoten regelmäßig einen Heartbeat:

- Intervall: alle 1–6 Stunden (konfigurierbar)
- Inhalt: Batteriespannung, RSSI letzter Empfang, Temperatur, Eventcounter
- Dashboard markiert Knoten als "offline" wenn kein Heartbeat nach 2× Intervall

---

## 11. Menschenerkennung ohne klassische Videoüberwachung

### 11.1 Datenschutzkonforme Erkennungsmethoden

Das System ist bewusst so ausgelegt, dass **keine identifizierbaren Bilddaten** erfasst oder gespeichert werden. Stattdessen werden physikalische Merkmale genutzt:

**mmWave-Radar-basierte Erkennung:**

Der Radar misst ein Doppler-Spektrum. Menschen erzeugen ein charakteristisches **Mikro-Doppler-Muster** durch:
- Schrittbewegung der Beine (±0,5–2 m/s relativ zum Körper)
- Armschwin (±0,3–1 m/s)
- Atemthoraxbewegung (±0,5–3 cm/s)

Diese Signatur unterscheidet sich von:
- Flatternder Vegetation: breitbandiges, zufälliges Rauschen
- Regen: gleichmäßige, feine Rückreflexionen
- Vögeln: kleiner Radarquerschnitt, hohe Flügelfrequenz (5–50 Hz)

**Thermalkamera-basierte Erkennung:**

Mit 32×24 Pixeln (MLX90640) kann ein KI-Modell auf dem MCU trainiert werden:

```
Trainingsbeispiele:
  - Mensch stehend/gehend: charakteristische Wärmeverteilung
    (Kopf ~37°C, Körper ~35°C, helle Fläche auf dunklem Hintergrund)
  - Hund: Körper ~37°C, aber andere Silhouette (niedriger, horizontal)
  - Vogel: sehr kleines Wärmepixel, bewegend
  - Vegetation: nahe Umgebungstemperatur, kein deutlicher Kontrast

Modell: TinyML / TensorFlow Lite Micro
  - Quantisiertes CNN (4–8 Bit): 3–10 kB Flash
  - Inferenzzeit auf ESP32-S3: 5–50 ms
  - Genauigkeit (Trainingsdaten, kontrolliert): ~80–92 %
```

### 11.2 Klassifikations-Pipeline auf dem MCU

```python
# Pseudocode: Klassifikation auf ESP32-S3

def classify_event(pir_trigger, radar_data, thermal_frame):
    score = 0.0
    label = "UNKNOWN"
    
    # PIR ist nur Trigger, nicht Klassifikation
    if not pir_trigger:
        return None
    
    # mmWave Presence Score
    presence = radar.get_presence_score()  # 0.0 - 1.0
    if presence < 0.3:
        return None  # Kein Objekt vorhanden
    
    # Radar-Feature-Extraktion
    radar_features = extract_doppler_features(radar_data)
    # features: [max_velocity, mean_rcs, micro_doppler_entropy, ...]
    
    # Thermalbild-Analyse
    if thermal_available:
        hot_pixels = count_pixels_above_threshold(thermal_frame, ambient + 5)
        max_temp = thermal_frame.max()
        aspect_ratio = compute_blob_aspect_ratio(thermal_frame)
    
    # Regelbasierte Klassifikation (einfach, robust):
    if presence > 0.7 and radar_features.max_velocity > 0.2:
        if thermal_available:
            if hot_pixels > 20 and max_temp > 33:
                if aspect_ratio > 1.5:  # Hoch (Mensch)
                    label = "HUMAN"
                    score = 0.85
                else:  # Breit/niedrig (Tier)
                    label = "ANIMAL"
                    score = 0.75
        else:
            label = "HUMAN_OR_ANIMAL"
            score = 0.6
    
    if score > THRESHOLD:
        return Event(label=label, confidence=score)
    return None
```

### 11.3 Grenzen der Menschenerkennung ohne Kamera

| Szenario                      | mmWave allein | mmWave + Thermal | RGB-Kamera |
|-------------------------------|---------------|------------------|------------|
| Mensch geht normal            | ~80 %         | ~90 %            | ~96 %      |
| Mensch steht still (> 10 s)   | ~85 %*        | ~88 %            | ~95 %      |
| Mensch hinter dünner Wand     | ~60 %         | ~30 %            | 0 %        |
| Nacht, keine Wärmequellen     | ~80 %         | ~88 %            | ~20 %      |
| Starker Regen                 | ~65 %         | ~70 %            | ~40 %      |
| Mehrere Personen gleichzeitig | ~70 %         | ~75 %            | ~90 %      |

*mmWave kann Atmung und Herzschlag erkennen → auch still stehende Personen

---

## 12. Erkennung von Hunden und großen Tieren

### 12.1 Merkmale und Unterschiede

Die Unterscheidung zwischen Mensch und Hund ist die schwierigste Klassifikationsaufgabe des Systems:

| Merkmal               | Mensch (Erwachsen) | Hund (Groß, z.B. Schäferhund) |
|-----------------------|--------------------|-------------------------------|
| Höhe                  | 1,6–2,0 m          | 0,5–0,8 m                     |
| Breite                | 0,4–0,6 m          | 0,3–0,5 m                     |
| Körpertemperatur      | 36–37 °C           | 37–39 °C                      |
| Körpermasse           | 60–100 kg          | 15–50 kg                      |
| Bewegungsgeschwindigkeit | 0,5–2 m/s (gehen) | 0,5–5 m/s (laufen) |
| Radarquerschnitt      | ~0,5 m²            | ~0,1–0,3 m²                   |
| Gangmuster-Frequenz   | ~1–2 Hz (bipedal)  | ~2–4 Hz (quadruped)            |

### 12.2 Machbare Erkennungsstrategien

**Mit mmWave-Radar:**
- Körperhöhe kann aus Radar-Elevationsprofil abgeschätzt werden (bei 3D-Radar wie IWR6843AOP)
- Unterschiedliche Mikro-Doppler-Muster: Mensch (bipedal mit charakteristischer Armbewegung) vs. Hund (4 Beine, andere Frequenz)
- Realistisch: ~60–70 % korrekte Mensch/Hund-Unterscheidung

**Mit Thermalkamera:**
- Höhe-zu-Breite-Verhältnis der Wärme-Silhouette (Hund: breiter als hoch; Mensch: höher als breit)
- Realistisch: ~65–80 % korrekte Unterscheidung bei gutem Wärmekontrast

**Mit Sensorfusion (mmWave + Thermal):**
- Kombination von Radarquerschnitt, Körperhöhe und Silhouetten-Verhältnis
- Realistisch: ~75–85 % korrekte Mensch/Hund-Unterscheidung

### 12.3 Pragmatische Empfehlung

Vollständig zuverlässige Hund/Mensch-Unterscheidung ist mit dem beschriebenen Budget-System **nicht garantiert erreichbar**. Eine pragmatische Strategie:

1. **Primärziel:** Mensch oder großes Tier erkannt → Alarm mit Klassifikation "Mensch/Tier"
2. **Sekundärziel (Best-Effort):** Bei ausreichend gutem Radarecho und/oder Thermalbild: verfeinere auf "wahrscheinlich Mensch" oder "wahrscheinlich Tier"
3. **Klassifikations-Ausgabe:** Dreistufig: `HUMAN` | `LARGE_ANIMAL` | `UNCLEAR` – nie "sicher" ohne Kameraverifizierung

**Was kleine Tiere (Katze, Hase) betrifft:**
- Katzen (~4–5 kg): Radarquerschnitt sehr klein, PIR-Auslösung möglich
- Mit mmWave: kleiner Presence-Score, Schwellwert kann so gesetzt werden, dass Katzen ignoriert werden
- Vögel: Sehr kleiner Querschnitt, hohe Doppler-Frequenz durch Flügelschlag → filterbar

---

## 13. Strategien zur Reduktion von Fehlalarmen

### 13.1 Hardware-Ebene

**Sensorausrichtung:**
- PIR-Sensor möglichst senkrecht zur erwarteten Bewegungsrichtung ausrichten (maximale Empfindlichkeit)
- mmWave-Radar nicht direkt auf stark reflektierende Metallflächen richten
- Abdeckung oder physikalische Blende für PIR bei starker Sonneneinstrahlung

**Windschutz:**
- PIR-Linse durch halb-transparente Abdeckung schützen (reduziert Auslösungen durch sonnenerwärmte, windbewegte Vegetation)
- Freifeld vor Sensor von hohem Gras freihalten

### 13.2 Software-Ebene

**Schwellwert-Management:**
- Adaptiver Schwellwert: Grundnoise-Level kontinuierlich messen, Schwelle dynamisch anpassen
- Mindest-Score für Weiterleitung: z. B. Presence Score > 0,5 UND Velocity > 0,1 m/s

**Zeitliche Filterung:**
- Doppelauslösung verhindern: Mindest-Abstand zwischen zwei Ereignissen (30–120 s)
- Kurze Pulse < 200 ms ignorieren (Insekten, Tropfen auf Linse)

**Umgebungskontext:**
- Windgeschwindigkeit via einfachem Anemometer (optional): Bei Wind > 5 m/s Schwelle erhöhen
- Regen-Detektor (kapazitiv, < 2 €): Bei Regen mmWave-Schwelle erhöhen, PIR-Only-Modus aktivieren
- Tageszeit: Nachts (0–5 Uhr) generell weniger Fehlalarme zu erwarten

**Mehrfachbestätigung (Multi-Sensor-Voting):**
```
Alarm wird nur ausgelöst wenn:
  [PIR ausgelöst] UND [Presence Score > 0.5] UND [Thermal-Blob > 10 Pixel (falls vorhanden)]
  
  ODER
  
  [Presence Score > 0.8] (starkes Radar-Signal auch ohne PIR-Trigger)
```

**Machine Learning-basierte Fehlalarm-Filterung:**
- Lokales Training auf Zieldaten des spezifischen Standorts
- Nach 2–4 Wochen Betrieb: Muster von Fehlalarmen lernen und zukünftig filtern
- Umsetzbar mit TinyML-Framework auf ESP32-S3 oder als Post-Processing auf Zentraleinheit

### 13.3 Architektur-Ebene

- **Zwei-Knoten-Verifikation:** Alarm erst wenn zwei benachbarte Knoten gleichzeitig (±30 s) eine Erkennung melden
- **Plausibilitätsprüfung auf Zentraleinheit:** Wenn Knoten #3 seit 50 Tagen keine Fehlalarme hatte und plötzlich 20 in einer Stunde meldet → manuell prüfen, möglicherweise Sensor-Hardware defekt

---

## 14. Sicherheitsaspekte und Verschlüsselung

### 14.1 Bedrohungsmodell

| Bedrohung                      | Wahrscheinlichkeit | Auswirkung |
|--------------------------------|--------------------|------------|
| Abhören der Funk-Übertragung   | Mittel             | Mittel     |
| Replay-Angriff                 | Mittel             | Hoch       |
| Spoofing (gefälschte Events)   | Gering             | Hoch       |
| Physischer Diebstahl des Knotens | Gering           | Mittel     |
| Unbefugter Zugriff auf Dashboard | Mittel           | Hoch       |

### 14.2 Verschlüsselung der Funkübertragung

**LoRaWAN (empfohlen):**
- **AES-128-Verschlüsselung** standardmäßig auf Anwendungsebene (AppSKey)
- **Geräte-Authentifizierung** via DevEUI + AppKey (OTAA-Join-Prozedur)
- **Sequenznummern** verhindern Replay-Angriffe (Frame Counter)
- Jedes Gerät hat individuellen Schlüssel

**P2P LoRa (einfachere Variante):**
- Eigene AES-128-Verschlüsselung implementieren (Arduino Cryptography Library)
- Nonce / Rolling Counter im Paket zum Replay-Schutz
- Pre-Shared Key pro Gerät in Firmware hartkodiert (oder via Secure Element)

### 14.3 Schlüsselverwaltung

- **Secure Element:** ATECC608A (Microchip) – dedizierter Kryptochip, speichert Schlüssel unveränderlich, ~1 € – sehr empfohlen für Produktionsgeräte
- **Alternatif:** Flash-Speicher des MCU mit Schreibschutz, weniger sicher
- Schlüssel nie im Klartext übertragen, nicht im regulären Flash speichern

### 14.4 Physische Sicherheit

- **Manipulationsdetektion:** LIS3DH-Beschleunigungssensor erkennt wenn Knoten bewegt oder geöffnet wird → Alarm senden
- **Anti-Tamper-Siegel:** Visuell erkennbarer Schutz am Gehäuse
- **Firmware-Signierung:** Nur signierte Firmware-Updates akzeptieren (MCU-Secure-Boot aktivieren bei STM32 / ESP32)

### 14.5 Dashboard-Sicherheit

- **HTTPS/TLS** für alle Web-Verbindungen (Let's Encrypt Zertifikat)
- **Authentifizierung:** Mindestens Username + starkes Passwort; besser: 2-Faktor-Authentifizierung (TOTP)
- **MQTT-Broker:** TLS auf Port 8883, Client-Zertifikate oder Username/Passwort
- **Netzwerk-Isolierung:** Dashboard nicht direkt aus dem Internet erreichbar; VPN (WireGuard) bevorzugt
- **Datensparsamkeit:** Keine Bilddaten speichern (Grundsatz des System-Designs)

---

## 15. Grober Prototyp mit realistischen Komponenten

### 15.1 Stückliste (Bill of Materials) – Ein Sensorknoten

| Komponente                          | Produkt                         | Preis ca. |
|-------------------------------------|---------------------------------|-----------|
| Mikrocontroller-Modul               | Seeed XIAO ESP32-S3             | 7 €       |
| mmWave-Radar                        | DFRobot SEN0395 (24 GHz)        | 25 €      |
| PIR-Sensor                          | AM312 Mini-PIR                  | 1 €       |
| LoRa-Modul                          | EBYTE E22-868M22S (SX1262)      | 10 €      |
| Antenne                             | 868 MHz SMA-Antenne, 3 dBi      | 3 €       |
| Umgebungssensor                     | BME280 (Temp/Feuchte/Druck)     | 3 €       |
| Akku                                | Li-Ion 18650 3000 mAh (2x)      | 10 €      |
| Akkuhalter + Schutzelektronik       | TP4056 + DW01 Modul             | 2 €       |
| Spannungsregler                     | XC6220 LDO 3.3V                 | 1 €       |
| Gehäuse                             | ABS-Box IP65, 100×68×50mm       | 8 €       |
| Kabeldruchführungen, Antennenbuchse | M16 PG-Verschraubung, SMA-Flansch| 3 €      |
| Platine (Prototyp)                  | 5×7 cm Lochrasterplatine        | 1 €       |
| Kleinteile (Widerstände, Kondensatoren, etc.) |                        | 3 €       |
| **Gesamt pro Knoten**               |                                 | **~77 €** |

### 15.2 Stückliste – Zentraleinheit

| Komponente                          | Produkt                         | Preis ca. |
|-------------------------------------|---------------------------------|-----------|
| Einplatinencomputer                 | Raspberry Pi 4B 2GB             | 55 €      |
| LoRa-Gateway-HAT                    | Dragino PG1302 (SX1302)         | 80 €      |
| Speicherkarte                       | SanDisk 32 GB microSD           | 10 €      |
| Netzteil                            | USB-C 5V/3A                     | 8 €       |
| Gehäuse                             | Raspberry Pi-Box mit Kühlung    | 10 €      |
| **Gesamt Zentraleinheit**           |                                 | **~163 €**|

### 15.3 Software-Stack (Open Source)

```
Sensorknoten:
  - Plattform: Arduino-Framework (ESP-IDF-Basis) oder ESP-IDF direkt
  - LoRa-Bibliothek: RadioLib (supports SX1262, LoRaWAN)
  - Radar-Bibliothek: DFRobot SEN0395 Bibliothek (UART-basiert)
  - Verschlüsselung: Arduino Cryptography Library (AES-128)
  - OTA-Updates: ESP32 OTA via LoRaWAN-Downlink (optional)

Zentraleinheit:
  - OS: Raspberry Pi OS Lite 64-bit
  - ChirpStack (LoRaWAN Stack): Docker-Compose-Deployment
  - MQTT-Broker: Mosquitto (Docker)
  - Zeitreihendatenbank: InfluxDB 2.x (Docker)
  - Dashboard: Grafana (Docker, vorkonfigurierte Dashboards)
  - Alarm-Weiterleitung: Node-RED (Docker, visuelle Regelkonfiguration)
  
  docker-compose.yml umfasst alle Services, einzeilig deploybar.
```

### 15.4 Prototyp-Aufbau Schritt für Schritt

**Phase 1 (2–4 Wochen): Einzelner Knoten, lokale Auswertung**
1. ESP32-S3 + SEN0395 Radar verbinden, Presence-Detection testen
2. PIR AM312 als Interrupt anschließen, Wake-Up-Logik implementieren
3. BME280 hinzufügen, Grundtelemetrie lesen
4. Einfache Klassifikationslogik: Presence Score > Schwellwert → Alarm-LED
5. Stromverbrauch messen: Multimeter in Serienschaltung, Sleep-Strom verifizieren

**Phase 2 (2–4 Wochen): LoRa-Kommunikation**
1. LoRa-Modul E22 anschließen, P2P-Übertragungstest mit zwei Modulen
2. Ereignispaket definieren und übertragen
3. Raspberry Pi mit LoRa-USB-Dongle (oder HAT) als Empfänger einrichten
4. MQTT-Integration: Empfangene Pakete an Mosquitto-Broker weitergeben

**Phase 3 (2–4 Wochen): Dashboard und Alerts**
1. ChirpStack oder einfacher Node.js-Server auf Raspberry Pi
2. Grafana-Dashboard mit Knotenstatus und Ereignis-Timeline
3. Node-RED: Alarmregel für Telegram-Bot konfigurieren
4. Batterie-Monitoring: Spannung über Spannungsteiler an ADC-Pin lesen

**Phase 4 (fortlaufend): Feinjustierung**
1. Schwellwerte optimieren (Fehlalarmrate messen)
2. Outdoor-Test bei verschiedenen Wetterbedingungen
3. Klassifikationslogik verbessern (ggf. zweiten Sensor hinzufügen)

---

## 16. Skalierbarkeit

### 16.1 Kapazitätsgrenzen der Technologien

**LoRaWAN-Gateway:**
- Ein einziges LoRaWAN-Gateway kann **hunderte bis tausende Knoten** bedienen
- Praktische Grenze bei ~1000 Knoten (abhängig von Sendehäufigkeit)
- Duty-Cycle-Beschränkung: Bei 20 Knoten und einem Event/Tag pro Knoten: unkritisch

**Raspberry Pi als Zentraleinheit:**
- Bis ~50 Knoten problemlos
- Ab ~100 Knoten: Speicher und CPU-Last prüfen (InfluxDB/ChirpStack)
- Ab ~500 Knoten: Dedizierter Server empfohlen (x86, 8+ GB RAM)

**Datenbankwachstum (InfluxDB):**
- ~100 Knoten × 50 Events/Tag × 100 Byte/Event = 500 KB/Tag = 180 MB/Jahr
- Für Raspberry Pi und 32 GB SD-Karte über Jahre unkritisch

### 16.2 Topologie-Erweiterung

```
Klein (< 10 Knoten):
  P2P LoRa → Raspberry Pi → Grafana
  Kosten: ~250 € gesamt

Mittel (10–100 Knoten):
  LoRaWAN → ChirpStack auf RPi 4 → InfluxDB + Grafana
  Kosten: ~600–2000 € je nach Knotenanzahl

Groß (100–1000 Knoten):
  LoRaWAN → mehrere Gateways → Cloud-ChirpStack oder On-Premise-Server
  → InfluxDB Cluster → Grafana Enterprise
  Kosten: 3000–20000 €
```

### 16.3 Multi-Standort-Betrieb

- Mehrere Standorte können auf denselben Cloud-Server berichten
- LTE/4G-Gateway pro Standort (z. B. RAK7268C mit LTE): ~250 €
- Kein Backbone zwischen Standorten nötig

---

## 17. Technische Risiken und Grenzen

### 17.1 Erkennungsgenauigkeit

| Risiko | Schwere | Wahrscheinlichkeit | Maßnahme |
|--------|---------|-------------------|----------|
| Hohe Fehlalarmrate durch Vegetation | Hoch | Hoch | Sensorfusion, adaptive Schwellwerte |
| Menschenerkennung bei Kälte (-10 °C) | Mittel | Mittel | Wärmekontrast sinkt, Radar weniger betroffen |
| Keine Erkennung bei sehr langsamer Bewegung | Mittel | Gering | mmWave erkennt auch Atmung |
| Fehlklassifikation Hund als Mensch | Gering | Mittel | Dreistufige Klassifikation, "Unklar" als Fallback |

### 17.2 Kommunikation

| Risiko | Schwere | Wahrscheinlichkeit | Maßnahme |
|--------|---------|-------------------|----------|
| Funkloch durch Gelände | Hoch | Mittel | Repeater/Gateway hinzufügen, Antennenwahl |
| Duty-Cycle-Verletzung (EU 868 MHz) | Hoch | Gering | Sendehäufigkeit begrenzen, Paketgröße minimieren |
| Paketverlust bei schlechtem RSSI | Mittel | Mittel | Wiederholungs-Mechanismus, Datumstempel |

### 17.3 Energieversorgung

| Risiko | Schwere | Wahrscheinlichkeit | Maßnahme |
|--------|---------|-------------------|----------|
| LiPo-Versagen bei -15 °C | Hoch | Mittel (Winter) | LiFePO4 oder Li-SOCl2 verwenden |
| SD-Karten-Korruption bei Spannungsunterbrechung | Mittel | Mittel | UPS/Supercap, graceful shutdown |
| Überhitzung im geschlossenen IP65-Gehäuse (Sommer) | Mittel | Mittel | Entlüftungsfilter, Gehäuse nicht in Direktsonne |

### 17.4 Regulatorische Grenzen

- **EU 868 MHz (SRD-Band):** Max. 25 mW ERP, Duty Cycle 1 % (36 s/h) in Subband 868,0–868,6 MHz
- **Datenschutz (DSGVO):** Keine erkennbaren Bilder dürfen gespeichert werden. Das System ist bei 32×24-Pixel-Thermalsensorik konform. Bei Kameraeinsatz: rechtliche Prüfung erforderlich
- **Überwachung öffentlicher Bereiche:** Lokale Rechtslage beachten, ggf. Kennzeichnungspflicht

### 17.5 Technologiereife

| Technologie | Reifegrad | Risiko |
|-------------|-----------|--------|
| LoRa/LoRaWAN | Sehr hoch | Gering |
| PIR-Sensor | Sehr hoch | Gering |
| DFRobot SEN0395 mmWave | Mittel | Mittel (Firmware-Updates, Library-Support) |
| TI IWR6843 mmWave | Hoch | Mittel (Komplexe Konfiguration) |
| Acconeer XM125 | Mittel | Mittel (Neues Produkt, SDK im Aufbau) |
| MLX90640 Thermal | Hoch | Gering |
| TinyML auf ESP32 | Mittel | Mittel (Trainingsdaten nötig) |

---

## 18. Empfehlung für den ersten Prototyp

### 18.1 Empfohlene Technologiekombination

Nach Abwägung aller Faktoren lautet die Empfehlung für den **ersten Prototypen**:

```
┌─────────────────────────────────────────────────────────┐
│              EMPFOHLENE PROTOTYP-KOMBINATION             │
│                                                         │
│  Sensorknoten:                                          │
│  ├── MCU: ESP32-S3 (Seeed XIAO ESP32-S3)               │
│  ├── Primärsensor: DFRobot SEN0395 (24 GHz mmWave)     │
│  ├── Trigger: AM312 Mini-PIR                            │
│  ├── Funk: EBYTE E22-868M22S (SX1262, LoRa)            │
│  ├── Telemetrie: BME280                                 │
│  └── Akku: 2× 18650 LiPo (6000 mAh parallel)          │
│                                                         │
│  Kommunikation: LoRaWAN (868 MHz, EU)                  │
│                                                         │
│  Zentraleinheit:                                        │
│  ├── Hardware: Raspberry Pi 4B 2GB                     │
│  ├── Gateway: Dragino PG1302 HAT                       │
│  └── Software: ChirpStack + InfluxDB + Grafana         │
│                                                         │
│  Gesamtkosten: ~240 € (1 Knoten + Zentrale)            │
│  Erweiterung: ~77 € pro zusätzlichem Knoten            │
└─────────────────────────────────────────────────────────┘
```

### 18.2 Begründung der Wahl

**ESP32-S3:** Bekannte Plattform, sehr gute Bibliotheksunterstützung, ULP-Coprozessor für effizienten Deep Sleep, Arduino + ESP-IDF Framework, starke Community. Ideal für schnelle Prototypenentwicklung.

**DFRobot SEN0395:** Der einfachste Einstieg in mmWave-Radar mit fertig konfigurierter UART-Schnittstelle. Keine komplexe FMCW-Konfiguration nötig. Erkennt zuverlässig Presence und Bewegung. Kostengünstig (~25 €). Nachteil: Weniger Klassifikationstiefe als 60-GHz-Systeme – für Phase 2 durch Acconeer XM125 oder TI IWR6843 ersetzen.

**PIR AM312:** Minimalinvasiv, < 1 €, perfekter Wake-Up-Trigger. Reduziert Gesamtstromverbrauch drastisch.

**SX1262 (868 MHz LoRa):** Industriestandard, beste Reichweite, niedrigster Stromverbrauch unter den LoRa-Chips, gute Bibliotheksunterstützung (RadioLib).

**ChirpStack:** Vollständiger, Open-Source-LoRaWAN-Stack. Läuft problemlos auf Raspberry Pi, mit Web-UI für Geräteverwaltung. Professionell, skalierbar, keine Cloud-Abhängigkeit.

**Grafana + InfluxDB:** Industriestandard für Zeitreihendaten und Dashboards. Vorkonfigurierte Dashboards für IoT-Szenarien verfügbar, schnelle Produktiv-Nutzung.

### 18.3 Upgrade-Pfad nach dem Prototyp

```
Prototyp (Phase 1)         →  Phase 2                →  Produktion
─────────────────────         ──────────────────────     ────────────────────
ESP32-S3                   →  nRF52840               →  Custom PCB
SEN0395 (24 GHz)           →  Acconeer XM125 (60 GHz)→  XM125 + MLX90640
2× 18650 LiPo              →  LiFePO4 + Solar MPPT   →  LiFePO4 + 2W Solar
P2P LoRa / LoRaWAN         →  LoRaWAN OTAA            →  LoRaWAN OTAA + FOTA
RPi + Dragino              →  Dedizierter LoRaWAN-GW  →  Multi-GW + Cloud
Grafana Basic              →  Custom Dashboard        →  Mobile App + API
Keine Verschlüsselung      →  AES-128 P2P             →  LoRaWAN + ATECC608A
```

### 18.4 Kritischer Erfolgsfaktor: Fehlalarmrate

Die wichtigste Metrik ist die **Fehlalarmrate im realen Einsatz**. Empfehlung:

1. **In den ersten 2–4 Wochen:** Alle Auslösungen loggen, Fehlalarme manuell markieren
2. **Schwellwerte iterativ anpassen** bis Fehlalarmrate < 10 % der Gesamtalarme
3. **Erst dann:** System für echten Überwachungseinsatz freigeben
4. **Kein System der Welt** erreicht 0 % Fehlalarme in einer Outdoor-Umgebung – eine Rate von 5–15 % ist ein realistisches Ziel

### 18.5 Zeitplan für den Prototyp

| Phase | Dauer  | Meilenstein |
|-------|--------|-------------|
| Komponentenbeschaffung | 2 Wochen | Alle Teile verfügbar |
| Phase 1: Einzelknoten | 3–4 Wochen | Stabile Erkennung indoor, Deep-Sleep verifiziert |
| Phase 2: LoRa + Zentrale | 3–4 Wochen | Ende-zu-Ende-Übertragung, Grafana zeigt Daten |
| Phase 3: Outdoor-Test | 4–8 Wochen | Fehlalarmrate gemessen, Schwellwerte angepasst |
| Phase 4: Mehrere Knoten | 2–4 Wochen | 3–5 Knoten parallel im Betrieb |
| **Gesamt** | **~4–5 Monate** | **Funktionsfähiger Prototyp** |

---

## Anhang A: Komponentenquellen

| Komponente | Quelle | Suchbegriff |
|------------|--------|-------------|
| Seeed XIAO ESP32-S3 | Seeed Studio, Mouser | XIAO ESP32S3 |
| DFRobot SEN0395 | DFRobot, Berrybase | SEN0395 mmWave |
| EBYTE E22-868M22S | Aliexpress, Amazon | EBYTE E22 868 SX1262 |
| AM312 PIR | Aliexpress, Amazon | AM312 mini PIR |
| BME280 | Reichelt, Conrad, Mouser | BME280 module I2C |
| Dragino PG1302 | Dragino Store | PG1302 |
| MLX90640 (Phase 2) | Mouser, Digikey, Adafruit | MLX90640 33° |
| ATECC608A (Phase 2) | Mouser, Digikey | ATECC608A-MAHDA-S |

---

## Anhang B: Glossar

| Begriff | Bedeutung |
|---------|-----------|
| mmWave | Millimeter Wave – Radarfrequenzen im Bereich 30–300 GHz |
| PIR | Passive Infrared – passiver Infrarot-Bewegungsmelder |
| FMCW | Frequency Modulated Continuous Wave – Radarprinzip |
| LoRa | Long Range – proprietäres Spread-Spectrum-Modulationsverfahren |
| LoRaWAN | LoRa Wide Area Network – Protokollstack auf Basis von LoRa |
| OTAA | Over-the-Air Activation – sichere Geräteregistrierung in LoRaWAN |
| RSSI | Received Signal Strength Indicator – Empfangssignalstärke |
| TinyML | Machine Learning-Inferenz auf Mikrocontrollern |
| Duty Cycle | Maximale Sendezeit im Verhältnis zur Gesamtzeit (EU-Regulierung) |
| Deep Sleep | Niedrigenergiezustand des Mikrocontrollers |
| MPPT | Maximum Power Point Tracking – optimierte Solarladung |
| SRD | Short Range Device – Kurzstreckenfunk-Geräteklasse |
| DSGVO | Datenschutz-Grundverordnung |

---

*Konzept erstellt: 2026-06-05*  
*Nächste Überprüfung empfohlen: Nach Abschluss Phase 1 des Prototyps*
