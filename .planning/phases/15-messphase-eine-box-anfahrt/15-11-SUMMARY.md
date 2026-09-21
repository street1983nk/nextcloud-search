---
plan: 15-11
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-21
requirements-completed: []  # MESS-05 an 15-16
---

# 15-11 SUMMARY: Der Volllauf

## Das Ergebnis in Zahlen (die Auswertung urteilt nicht, das Urteil faellt in 15-15 gegen E9)

| Groesse | v1.0 | v1.1 (Planwert) | **dieser Lauf (v1.2)** |
|---|---|---|---|
| Laufzeit | 18 h 56 min | 26 h 37 min | **19 h 20 min** (Untergrenze) |
| Dokumente / Vektoren | - | 52.111 | **52.137 / 52.137** |
| Zeit ohne Arbeitsvorrat | 0,10 h | 5,85 h (22,0 %) | **0,50 h (2,6 %)** |
| Scheibenabstand | - | effektiv ~12 min | **Median 301 s, Max 361 s** (Deckel 420 s: 0 Risse) |
| OOM | - | - | **keiner** (peak 2.044.096.512 unter 2 GiB) |

Trigger 2026-09-20T03:49:32Z, Ende (00-FERTIG) 23:09:58Z. Untergrenze, weil
startpunkt-indexed 4696 (Poller-Vorlauf seit dem Abbildwechsel; v1.1 startete
vergleichbar mit 1.653). Rohdaten: 96-volllauf-start.txt, 96-volllauf.csv
(13.972 Zeilen RSS-Reihe), 96-statusseite.jsonl (582 Aufnahmen),
96b-waechter.txt (mit Auswertungsblock), 96-oom-beweis.txt,
96-vektorbestand.txt, 96-suchlast-nachlauf/danach.json, 00-FERTIG.

## Task 2, der Zwischenstand beim Owner

Der Owner hat waehrend des Laufs zweimal den Zwischenstand gesehen (in der
Session: 05:49Z bei indexed 41.856/embedded 3.132 und 14:37Z bei 47.466/25.588)
und den Lauf jeweils weiterlaufen lassen. Keiner der drei Abbruchfaelle trat
ein: kein 27/28, Deckelverbrauch weit unter 46 h (Box-Gesamtzeit bei Laufende
~21,5 h), keine Waechter-Auffaelligkeit.

## Befunde dieses Plans

1. **Der waehrend-Zweig von 97-cron-vorpruefung.sh lief nicht** (Versaeumnis
   der Ausfuehrung beim Anstoss in Task 1, bemerkt nach dem Ende). Seine
   Zahlen sind NACHTRAEGLICH aus der aufgezeichneten 120-s-Statusreihe
   berechnet und in 97-cron-vorpruefung-waehrend.txt ausdruecklich so
   gekennzeichnet (A1: die Reihe steht neben jeder Zahl). Nachtrag 15-15:
   00-ablauf.md bekommt den Start des waehrend-Zweigs als eigene Zeile.
2. **96e-ntfy-watch.sh fehlte im v12-Ordner** (in 15-09/15-11 nachgeholt,
   Commit 2374274); die Startmeldung dieses Laufs fiel aus, die Fertigmeldung
   lief ueber den nachgestarteten Wartemodus.
3. **SSH-Regel veraltete ueber Nacht** (Carrier-Lease-Wechsel der eigenen
   Adresse, bekanntes Muster T-06.1-78): revoke+authorize nach dem Vorbild von
   cmd_start, Box selbst war nie unerreichbar (HTTPS durchgehend 200).

## Verification

- laufzeit-ist / dokumente-ist / vektoren-ist / vorrat-null-anteil mit
  Ablesereihe: stehen in 96b-waechter.txt. GRUEN.
- Block der sechs Vergleichbarkeitsgroessen: steht ebenda. GRUEN.
- Kein Urteil ueber die Top-up-Route in den Rohdaten. GRUEN.
- Geheimnis-Gate ueber alle zehn Rohdateien des Laufs: leer. GRUEN.

## Naechster Schritt

15-12: Bestandssonde (jetzt gegen den fertigen Index nachholbar) und
Sprachfaelle mit CI_LAUF.
