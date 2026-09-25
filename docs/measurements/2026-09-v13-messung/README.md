# Die v1.3-Messanfahrt (Phase 22)

Diese Anfahrt liefert den Messbeleg von BL-F03 und der v1.3: das Bündel aus
MESS-07 (M-01 auf Zielhardware, Wirkungsnachmessung 92c und 99d, Bodensatz im
zweiten Zyklus, die übersprungenen und fehlgeschlagenen Dateien einzeln,
Kaltstartlatenz mit Treffern), MESS-08 (Indexgröße bei sechs Sprachfeldern und
Wandzeit des Umbaus) und MESS-09 (der disjunction_max-Entscheid), dazu die
BL-F04-Mitmessliste B1 bis B6. Der Ablauf und die vorher aufgeschriebene
Erwartung stehen in `skripte/00-ablauf.md`, die Rohdaten in `rohdaten/`.

Anfahrt freigegeben: offen (Owner-Checkpoint 22-07)

Die Freigabe erteilt der Owner am Checkpoint 22-07, zusammen mit den Antworten
auf die drei Fragen in `skripte/00-ablauf.md`, Abschnitt 6. Vor dieser Zeile
läuft keine Boxminute.

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt echte Umlaute.
Adressen, Kennungen und Passwörter der Box stehen in keiner Zeile dieser Datei.

---

## 1. Rechenblatt

Offen. Wird vor dem Checkpoint 22-07 gefüllt: Planwerte je Block aus
`skripte/00-ablauf.md`, Abschnitt 2, der Deckel D-01 als eigene Zeile und B4
als eigener Deckelposten.

## 2. W4-Vorabkurve

Offen. Wird nach dem CI-Lauf des Jobs `slots` gefüllt: F4 nach der Definition
in `skripte/00-ablauf.md`, Abschnitt 8, und die Folge für B4 nach D-03.

## 3. Generalprobe

Offen. Wird nach der Generalprobe der Werkzeuge gegen die lokale Test-Nextcloud
gefüllt.

## 4. Laufwerte

Offen. Wird am Checkpoint 22-07 gefüllt: `DECKEL_MINUTEN`,
`DECKEL_REST_MINUTEN`, `B4_GEPLANT`, `EINZELWEG`, mit Herleitung aus dem
gewählten Deckel.

## 5. Offene Owner-Fragen

Offen. Die drei Fragen stehen in `skripte/00-ablauf.md`, Abschnitt 6.

## 6. Bericht

Offen. Wird nach der Anfahrt geschrieben: Urteil je Erwartung E1 bis E14,
gestrichene Blöcke und Lücken, Kosten gegen den Deckel.
