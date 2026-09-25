# Phase 21: Go/No-Go-Entscheid des Owners

**Datum:** 2026-09-25
**Entscheid:** GO
**Grundlage:** 21-RESEARCH.md (Commit 6999581), Rezeptmessung im Wegwerf-Container
(python:3.13-slim-trixie, wdutch=1:2.20.19+1-3, tantivy==0.26.2)

Erfuellt damit Erfolgskriterium 1 der Phase (datiertes Go/No-Go vor dem ersten
Codeschritt).

## Teilentscheide (alle Owner, 2026-09-25)

| Frage | Entscheid |
|-------|-----------|
| NL-Wortliste nach Automatenbau | **freigeben** (17,6 MB Zusatzkosten statt 37,2 MB) |
| Zerlegungsfenster | **4 bis 14 Zeichen** (21/28 Komposita, null Fehlzerlegungen an 33 Waechterwoertern; 4-12 verworfen wegen Fehlzerlegungen, Muster des verworfenen deutschen Rezepts D) |
| Lizenznennung THIRD-PARTY.md | **CC-BY-3.0** (Bezug aus Debian-Paket wdutch, Debians Lizenzdatei nennt genau diese; Upstream-Wahlfreiheit BSD-3/CC-BY-3.0 als Anmerkung zulaessig) |

## Harte Leitplanken aus der Research

- ANALYZER_VERSION darf NICHT steigen (sonst Vollreindex ~19 h auf jeder Installation).
- Siebte Marke `wordlist_hash_nl` verhaelt sich exakt wie die Sprachmarke:
  nicht vorbelegen, Fehlen bei inaktivem nl = Altbestand, Schreiben nur hinter
  Verzeichnistausch bzw. beim Anlegen eines neuen Verzeichnisses.
- Splitter steht HINTER der Faltung (Position aus Phase 17 unveraendert),
  Fugenlaute s, e, en, Liste mit tantivy ascii_fold aufbereitet (316.740 Eintraege).
- Vor dem Bau per Test klaeren: stempelt der Rueckfallpfad ueber Vollreindex
  die Verzeichnismarken? (Offene Frage 4 der Research.)
- Native ARM-RAM-Messung erst in der Box-Anfahrt (qemu-Werte unbrauchbar).
