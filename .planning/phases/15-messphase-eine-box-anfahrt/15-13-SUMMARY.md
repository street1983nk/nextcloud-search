---
plan: 15-13
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-21
requirements-completed: []  # MEM-02 wird in 15-16 abgehakt, MESS-05 ebenda
---

# 15-13 SUMMARY: Wiederaufwaermen (A/B), MEM-02, Owner-Entscheid 900 s

## Task 1: Die vier Auspraegungen (Erfolgskriterium 5)

| Auspr | Schalter | Cache | erste-suche-ms | Treffer | zweite-suche-ms |
|---|---|---|---|---|---|
| 1 | 120 | kalt | **1996** | 26 | 1038 |
| 2 | 120 | warm | **1418** | 26 | 745 |
| 3 | 0 | kalt | 2051 | (transient 0) | 776 |
| 4 | 0 | warm | 1613 | 26 | 743 |

Konto lasttest (kurzzeitig in admin-Gruppe fuer die Overview-Lesung, danach
wieder entfernt), Reihenfolge 1,3,2,4 (kalt vor warm). **Erfolgskriterium 5:**
die Entladung kostet nicht mehr als ein normaler Kaltstart, im selben
Cachezustand je weniger (1996<2051 kalt, 1418<1613 warm); die erste Suche der
Nutzerroute traegt die Volltextseite, waehrend die Gewichte im Hintergrund
nachladen (nachwaermdauer-s=0).

## Task 2: MEM-02 (Rueckkehr zur Grundlast)

- Marke A (vor Indexlauf): 103,9 MB
- Marke B (nach Indexlauf, geladen): 1109,4 MB
- Marke C (nach Entladung): 731,9 MB
- **rueckkehr-zur-grundlast-mb = 377,5** (Marke B minus C), ueber der E13-Schwelle
  von 300 MB. Auf Zielhardware (m7g.large, aarch64) gegen das ausgelieferte
  v1.2-Abbild, im Unterschied zur Sichtprobe 14-12 (376,3 MB ohne malloc_trim,
  ein Hinweis, jetzt ein Beleg). Schalter stand auf 120 (D-02), nicht 0.
  Zeilenstaende: 52.137 vor, 52.149 nach dem Indexlauf (12 neue Dateien).

**MEM-02 hat damit seine Zahl an seiner Messgroesse.** Abgehakt wird das
Requirement erst in 15-16.

## Task 3: Owner-Entscheid zum Vorschlagswert 900 s (Wortlaut)

Vorgelegt: E14 (Belegkriterium, seit 15-07 committet, Zeitstempel vor den
Rohdaten). E13 (Rueckkehr > 300 MB) haelt. **E12 (erste Suche < 1,5 s) reisst
im kalten Fall (1996 ms), haelt im warmen (1418 ms).** Die auf der Dev-Maschine
duenne Marge (1,37-1,44 s) ist auf der langsameren Box im kalten Eckfall
aufgezehrt, im Alltag (warm) gehalten, genau wie die Phase-14-Abnahme es als
moeglich benannt hat.

**Owner-Entscheid: "900 s bleibt + Vorbehalt (E14-Regel)."** Der Vorschlagswert
900 s bleibt als gekennzeichnete Schaetzung; seine Beschreibung bekommt die
Box-Zahlen (kalt 1996 / warm 1418 ms) daneben und den Satz, dass die 1,5-s-Decke
nur im kalten Boot-Eckfall reisst und im laufenden Betrieb haelt. Kein
Korrigieren des Werts, genau wie E14 es fuer den E12-Riss vorschreibt. Eine
Frist laesst sich nicht belegen, nur ihre Folgen; die Empfehlung bleibt eine
Empfehlung.

## Offener Befund fuer 15-15/15-16: der Bodensatz

`bodensatz-mb = 628,0` (Marke C minus Marke A) weicht stark von der
E13-Erwartung "rund 16 MB" ab. Die 16 MB der Erwartung stammen aus der
Zielast ueber fuenf Zyklen im Vorprueflauf (per-Zyklus-Akkumulation); die 628 MB
der Box sind der absolute Bodensatz nach EINEM Zyklus (Modulimporte
onnxruntime/numpy und Laufzeitstrukturen, die nach der ersten Einbettung
resident bleiben, auch wenn die Gewichte frei sind). Zwei verschiedene
Messgroessen unter einem Namen. Das gehoert in 15-15 sauber getrennt und in
15-16 dem Owner als eigene Zahl vorgelegt: 731,9 MB residenter Stand nach
einem Indexlauf mit entladenem Modell ist auf einer 4-GB-Box eine Zahl, die
man kennt. Kein Blocker der Phase, aber ein benannter Punkt.

## Werkzeug-Befunde dieses Plans (fuer 15-15)

- 95b/94b nutzen BENUTZER=admin per Vorgabe, der Korpus gehoert aber lasttest:
  Suche liefert 0 Treffer, semantische Seite nicht ablesbar. Behelf: lasttest
  kurzzeitig in die admin-Gruppe. Nachtrag: die Werkzeuge sollten den
  Korpus-Eigentuemer als Vorgabe fuehren oder die Overview-Lesung von der
  Suche trennen.
- 94b ruft `sudo "$SAMPLER"` direkt; die Datei steht 100644 im Repo, also
  `command not found` und Abbruch 32. Behelf: chmod +x auf der Box. Nachtrag:
  `sudo sh "$SAMPLER"` wie in 96/97, oder das Ausfuehrungsbit im Repo.

## Verification

- 4 Rohdateien mit entladeschalter-ist, erste-suche-ms; 1,2 Schalter >0, 3,4 = 0;
  1,2 mit unloaded belegt; Reihenfolge 1,3,2,4 per Zeitstempel: GRUEN.
- 94b: rueckkehr-zur-grundlast-mb, bodensatz-mb, kein "Grundlast minus",
  Zeilenstaende vor/nach unterschiedlich, Schalter auf Ruhezeit: GRUEN.
- Geheimnis-Gate ueber alle 15-13-Rohdateien: leer.

## Naechster Schritt

15-14: Schlusszahlen VOR dem Abbau in die Rohdatei, dann Abbau (nur der
Ende-Snapshot faellt, der Korpus-Snapshot snap-03f1d1d9ad9262704 bleibt).
