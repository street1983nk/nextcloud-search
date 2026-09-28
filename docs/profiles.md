# Leistungsprofile: Owner-Tor, Formel und Grenzen der Phase 24

Findling kennt ab 1.4 drei Profile: `economy` (Sparsam), `standard` (Standard)
und `performance` (Leistung). Ein Profil ist ein Anteil an der erkannten
Hardware mit Obergrenzen, keine feste Slotzahl. Diese Seite hält fest, was der
Owner am 27.09.2026 entschieden hat, wie die Werte berechnet werden, wie ein
Admin das Profil setzt und was Phase 24 bewusst noch nicht tut.

Code: `backend/src/findling/profile.py` (Vorschlag, wirksame Stufe,
Wertetabelle), `backend/src/findling/hardware.py` (Erkennung), Konstanten in
`backend/src/findling/config.py`.

## Owner-Tor vom 27.09.2026

Diese Entscheide sind gefallen, bevor Code sie implizit treffen konnte. Quelle:
`.planning/phases/24-owner-tor-profil-ger-st-und-marken-reparatur/24-CONTEXT.md`.

- **D-24-01 (27.09.2026), Profil-Weg:** Weg B. Die PHP-Seite bekommt eine
  OCS-Route nach dem Muster `queues/documents/stats`, der Container fragt das
  Profil einmal je Runde ab. Wechsel ohne Container-Neustart, gespeichert wird
  PHP-seitig in appconfig. Weg A (Umgebungsvariable mit Neustart) und Weg C
  (Datei im Persistenzpfad) sind verworfen.
- **D-24-02 (27.09.2026), Fehlersemantik:** Der Container merkt sich das zuletzt
  erfolgreich gelesene Profil für die laufende Prozesslebensdauer. War noch nie
  eines lesbar (Erststart, Companion ohne Route), läuft Sparsam.
- **D-24-03 (27.09.2026), Anteile:** Standard = 50 % der Kerne, 40 % des
  Speichers, höchstens 4 OCR-Slots. Leistung = Kerne minus 1, 60 % des
  Speichers, höchstens 16 OCR-Slots. Sparsam bleibt fest bei 1 Slot, ohne
  Anteile, Wert für Wert gepinnt.
- **D-24-04 (27.09.2026), Store-Satz:** wörtlich festgelegt, siehe nächster
  Abschnitt.
- **D-24-05 (27.09.2026), fp32-Lieferweg:** Nachladen bei Opt-in. int8 bleibt
  ins Abbild gebacken. fp32 wird erst geladen, wenn der Admin es ausdrücklich
  wählt: Download ins persistente Verzeichnis mit Digest-Prüfung, klares
  Verdikt bei Offline oder Proxy ("fp32 nicht verfügbar, int8 bleibt aktiv").
  Der Start lädt weiterhin nichts. Gebaut wird der Weg in Phase 25 (MOD-02).
- **D-24-06 (27.09.2026), Vorschlags-Schwellen:** Standard ab 6 GB und 3 Kernen,
  Leistung ab 12 GB und 6 Kernen, darunter Sparsam. Nur ein Vorschlag über die
  Statusroute, nie automatisches Hochschalten.
- **D-24-07 (27.09.2026), Schrumpfung:** Das gespeicherte Profil bleibt stehen.
  Der Container arbeitet auf der größten noch passenden Stufe und meldet beides,
  gewählt und wirksam. Wächst die Hardware wieder, gilt ohne Zutun wieder das
  gewählte Profil.
- **D-24-08 (27.09.2026), Leistung ohne r-Abzug:** Im Profil Leistung rechnet
  der Kernterm glatt Kerne minus 1, ohne zusätzlichen Abzug der
  Nextcloud-Grundlast r. Für Standard bleibt der r-Abzug.

## Store-Satz für 1.4.0 (wörtlich, nicht umformulieren)

Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung).

Der Satz reist mit Release 1.4.0 (REL-04) in den Store-Text.

## Formel

Sparsam ist die Zeile des heutigen Containers und rechnet nichts. Standard und
Leistung leiten die OCR-Slots so ab:

```
OCR-Slots = max(1, min(Kernterm,
                       floor((Anteil x M_frei - Reserve - Grundlinie) / Kosten_je_Slot),
                       Obergrenze))
```

- Kernterm Standard: `floor(0,5 x C - r)` mit r = 0,25 (Anteil eines Kerns, den
  Nextcloud selbst beim Indexieren belegt).
- Kernterm Leistung: `floor(C - 1)` (D-24-08).
- Kosten je Slot: 235 MiB. Grundlinie des Hauptprozesses mit geladenem Modell:
  1.257,5 MiB. Reserve: 20 % des Speicheranteils bei Standard, 15 % bei
  Leistung. Die Messwerte stammen aus `docs/performance.md`.

Beispiele:

- Standard bringt erst ab 5 Kernen mehr als einen OCR-Slot, denn 4 Kerne ergeben
  `floor(0,5 x 4 - 0,25) = 1`. Das ist gewollt konservativ.
- Leistung auf 16 Kernen und 64 GiB ergibt 15 Slots: Kernterm 15, Speicherterm
  weit darüber, Obergrenze 16.

## Hardware-Erkennung

- Einmal beim Start, vor jedem Modellladen, als vierte Startaussage im
  Lifespan. Findlings eigene Modelllast senkt MemAvailable, eine spätere Messung
  würde das Profil gegen sich selbst schrumpfen lassen.
- Kerne = Minimum aus `os.process_cpu_count()` und der Quote in `cpu.max`.
- Die Vorschlags-Schwellen rechnen gegen `memory.max`, sonst MemTotal. Die
  Slot-Formel rechnet gegen `min(memory.max, MemAvailable)`.
- Wächst die Hardware, gilt das gewählte Profil ab dem nächsten Start wieder.
- Ein Fehler der Erkennung stoppt den Start nie; das Profil bleibt dann Sparsam.
  Im Log steht nur der Ausnahmetyp, keine Hardwarewerte und keine Pfade.

## Profil setzen in 1.4-Vorabständen

Bis die Einstellungsseite kommt (Phase 27), wird das Profil per occ gesetzt:

```
occ config:app:set findling profile --value=standard
```

- Gültige Werte: `economy`, `standard`, `performance`. Unbekanntes wirkt als
  `economy`.
- Die Wirkung tritt nach Sekunden bis rund 25 Minuten ein, je nachdem, wann der
  Container das nächste Mal fragt.
- Ein Companion 1.3.x ohne die Profil-Route bedeutet Sparsam.

## Eine Wahrheit: Umgebungsvariable überstimmt

Eine Umgebungsvariable überstimmt den Profilwert nur, wenn ihr Wert gültig ist
UND vom in `info.xml` deklarierten Default abweicht. AppAPI setzt jeden Default
als echte Variable, ein Wert gleich dem Default sagt also nichts über den Admin.

Folge: Wer unter Leistung ausdrücklich 30 Seiten je PDF will, erreicht das nur
über 29 oder 31, denn 30 ist der deklarierte Default.

Die Statusroute `GET /status` meldet im Block `profile` je Wert die Quelle:
`profile` oder `env`.

## Einbettungsspur (Phase 25, PAR-01, PAR-04)

In Standard und Leistung läuft die Einbettung als eigener Nebenläufer neben der
OCR, statt zeitlich getrennt in derselben Schleife wie unter Sparsam (IDX-08).

- **Schwelle:** Technisch läuft die Spur ab 2 Kernen. Wirksam wird sie erst
  dort, wo Standard vorgeschlagen und gewählt werden kann, also ab 3 Kernen und
  6 GB (D-24-06, D-24-07). Auf einer kleineren Box bleibt die wirksame Stufe
  Sparsam, und die Einbettung läuft seriell wie bisher.
- **Speicherbedingung (D-25-11):** Vor jeder Runde prüft der Läufer zweimal:
  statisch, ob die Slot-Formel nach Abzug der Einbettung noch jeden OCR-Slot
  trägt, und live, ob `anon` gegen `memory.max` noch Platz für eine Runde lässt.
  Bei Nein parkt der Läufer mit `waiting_for_memory`, und die Einbettung läuft
  seriell in der Indexschleife weiter. Es geht nichts verloren.
- **Genau ein Läufer (D-25-12):** Auch Leistung mit `embed_slots` 2 fährt in
  Phase 25 einen Läufer. Der zweite wirkt erst ab Phase 26.
- **Präzision:** fp32 ist nur in Standard und Leistung wählbar (D-25-01). Ein
  Profilwechsel ändert die Präzision nie; ein aktives fp32 unter Sparsam wird als
  `fp32_active_in_economy` gemeldet (D-25-10, D-25-03). Details in
  [`docs/embeddings.md`](embeddings.md), Abschnitt 11.
- **Companion 1.4.0 nötig (K6):** Die Spur braucht den Warteschlangen-Filter
  des Companions 1.4.0. Mit einem Companion 1.3 läuft alles seriell, gemeldet
  als `companion_without_lane`.

`GET /status` meldet den Zustand im Block `lane`: `mode` ist `inline` oder
`parallel`, `reason` sagt, warum die Spur parkt (`economy`,
`companion_without_lane`, `waiting_for_memory`, `runner_failed` nach einer
gescheiterten Runde des Läufers, also einer Warteschlange ohne Antwort oder
einem unerwarteten Fehler, bis zur nächsten beantworteten Runde; leer bei
`parallel`).

Nach einem Start in Standard oder nach einem Rebuild kann eine erste Runde des
Läufers laufen, bevor die Indexschleife die Spur geöffnet hat. Das steht als
`RuntimeError` im Log; die Zeilen gehen an die Warteschlange zurück, und
nichts geht verloren.

## Was Phase 24 bewusst nicht tut

- Keine Slots in Betrieb: die Werte werden berechnet und gemeldet, die
  Nebenläufigkeit kommt mit den Phasen 25 und 26.
- Keine Einstellungsseite und keine Probe: Phase 27.
- Kein fp32-Nachladeweg: Phase 25, beschrieben in `docs/embeddings.md`,
  Abschnitt 11.

Merker für die Phasen 25 und 26:

- Profilwerte wie `ocr_max_pages` erreichen das spawn-Kind der Sandbox nicht
  über `settings()`. Sie müssen beim Spawn übergeben werden.
- Die Markenpräzision muss aus dem tatsächlich geladenen Modell kommen, nicht
  aus dem gewählten Profil.
