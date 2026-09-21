---
plan: 15-12
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-21
requirements-completed: []  # MESS-05 an 15-16
---

# 15-12 SUMMARY: Laststufen, Filter/Sortierung, Sprachfaelle

## Task 1: Die fuenf Laststufen (Erfolgskriterium 3)

| Stufe | p95 v1.2 | p95 v1.1 | Trefferdichte v1.2 (v1.1) | Verdikt |
|---|---|---|---|---|
| 1 | 480,5 | 464,3 | 5,40 (5,40) | nicht regressiv |
| 4 | 1.006,8 | 1.068,0 | 5,40 (5,40) | **behoben** |
| 8 | 1.992,0 | 2.125,5 | 5,25 | **behoben** |
| 12 | 2.950,6 | 3.453,4 | 5,40 | **behoben** |
| 16 | 4.091,1 | 4.446,2 | 5,21 (4,16) | **behoben** |

Alle vier regressiven Stufen unterschreiten die v1.1-Zahl mit gehaltener oder
besserer Trefferdichte. Die vom Werkzeug notierten +4,0 % (Stufe 8) und +8,2 %
(Stufe 16) beziehen sich auf v1.0, nicht v1.1. Alle Ausfaelle sind
EmptyResultGroup (Leertreffer), keine Timeouts. **Unabhaengige Gegenrechnung**
(Nextcloud-Protokoll, cURL error 28): NULL im Lastfenster 02:10-02:13; die
failures-Zaehlung des Werkzeugs ist damit bestaetigt (Unterschied zu v1.1, wo
das Protokoll 17 verschluckte Timeouts fuehrte). Kaltstart (95-spitze nachher):
anon-Spitze 526,4 MB, ~2 s Wandzeit; der Einzelrequest traf einen Leerbegriff
(EmptyResultGroup), die Latenz ist damit fuer DI-07-02 nicht sauber ablesbar
(Befund fuer 15-15). search_load.py unveraendert.

## Task 2: Filter- und Sortierblock (D-01, Erstmessung)

Drei Sortiermodi (Median/p95/Treffer): relevance 341,3/449,0/25, newest
175,2/220,3/25, oldest 174,7/235,6/25. Faktor relevance zu newest/oldest ~2
(E11 bestaetigt: relevance faehrt die Vektorfusion, die anderen sind rein
lexikalisch, score=0.0). Drei Seiten geblaettert, je 25 Treffer, Seitenzahlen
1/2/3, keine doppelten Kennungen, Weiter-Link je gezogen. Filter-Typgruppe pdf.
Fund: 99c liest das Passwort NICHT aus PWFILE, sondern erwartet
FINDLING_LOAD_PASSWORD in der Umgebung; ohne sie erst 401/Abbruch 34, mit
gesetzter Variable sauber (Befund fuer 15-15).

## Task 3: Sprachfaelle (Erfolgskriterium 4)

10 Faelle, dreiwertig am Rang: **5 GRUEN (Rang 1), 0 ROT, 5 NICHT MESSBAR**.
Bilanz: bestanden 5 von 10, davon 5 nicht messbar, rote Faelle 0. Die nicht
messbaren sind haeufige Begriffe (Genehmigung/Frist/Vertrag/bescheid/
type:pdf bescheid, index 33k-52k), deren eigene Datei im 52.111er-Fremdbestand
ausserhalb Rang 64 steht: kein Sprachbefund, sondern Verduennung. E3 erfuellt
(drei Monate + Belehrung messbar, keiner rot). ci-beleg 35471225104 (frische
Instanz ohne Fremdbestand). Abschnitt 0 (Bestandssonde, aus 15-10 hierher
verschoben): kein 26er-Deckel, haeufige Begriffe 33.226-51.965 (E1 erfuellt).

## Verification

- 97: hits_per_request, vier Verdikte, search_load.py unberuehrt: GRUEN.
- 99c: blaettern-seite-1-ms, sortierung-relevance, Erstmessung: GRUEN.
- 98c: ci-beleg, Abschnitt 3b, entladeschalter-ist=0 (nachgetragen): GRUEN.
- Geheimnis-Gate ueber alle Rohdateien: leer (die Treffer "OC-FileId"/"password"
  sind Kennungszahl und occ-Ausgabe, keine Werte).

## Naechster Schritt

15-13: MEM-02 (Rueckkehr zur Grundlast nach Indexlauf), Kaltstart und die
Entlade-A/B-Messung (Schritt 8, beide Schalterstellungen).
