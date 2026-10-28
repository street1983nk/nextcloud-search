# Phase 36: Haertung und Store-Einreichung 1.5.0 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md , this log preserves the alternatives considered.

**Date:** 2026-10-20
**Phase:** 36-haertung-und-store-einreichung-1-5-0
**Areas discussed:** Boesartiger Formatkorpus, M-32-02 Nachweis, Offene Owner-Textfragen, Release-Ablauf

---

## Boesartiger Formatkorpus

| Option | Description | Selected |
|--------|-------------|----------|
| Generatoren in Tests | Testhelfer bauen Dateien zur Laufzeit deterministisch (wie build_cfb), keine boesartigen Binaries im public Repo | ✓ |
| Committeter Korpus | Echte Dateien unter testdata/ wie der Injection-Korpus | |
| Mix | Generatoren fuer Bomben/Traversal, committete Winzlinge fuer Eckfaelle | |

| Option | Description | Selected |
|--------|-------------|----------|
| Erweitert | Pflichtfamilien PLUS XML-Bomben, Bild-Dekompressionsbomben, uebergrosse Eintraege, polyglotte Dateien | ✓ |
| Nur Pflichtfamilien | Exakt Archive, Mails, OLE | |

| Option | Description | Selected |
|--------|-------------|----------|
| Bestehende Klassen | Vorhandene Fehler-/Skip-Klassen mit benanntem Grund | |
| Neue Urteilsklasse | Eigene Klasse in file_errors und Admin-Karte | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Eine Sammelklasse + Vorabplan | Eine Klasse fuer alle Familien, Detailgrund in Diagnose-Zeile, Wortlaute de/en/fr via Vorabplan | ✓ |
| Mehrere Klassen + Vorabplan | Getrennte Klassen je Familie | |
| Eine Sammelklasse ohne Vorabplan | Wortlaute erst in der Playwright-Abnahme | |

**User's choice:** Generatoren in Tests; erweiterter Umfang; EINE neue Sammelklasse mit Wortlaut-Vorabplan.
**Notes:** Owner wich bei der Urteilsform bewusst von der Empfehlung (bestehende Klassen) ab: boesartige Dateien sollen fuer Admins als eigene Klasse sichtbar sein.

---

## M-32-02 Nachweis

| Option | Description | Selected |
|--------|-------------|----------|
| SQL-Rueckdatierung | Test datiert Erstsichtungs-Zeitstempel per SQL zurueck; 30 Tage fest im Code | ✓ |
| Konfigurierbare Karenz | Karenzdauer als Env/App-Config | |

| Option | Description | Selected |
|--------|-------------|----------|
| Dev-8090 + CI-Test | Live-Beleg mit Positivkontrolle plus dauerhafter CI-Integrationstest | ✓ |
| Nur Dev-8090 | Einmaliger Live-Beleg mit Protokoll | |
| Nur CI | Nur der Integrationstest | |

**User's choice:** SQL-Rueckdatierung; Beleg zweigleisig Dev-8090 + CI.
**Notes:** Definition "verschwundener externer Speicher" bleibt Claude's Discretion (Research).

---

## Offene Owner-Textfragen

| Option | Description | Selected |
|--------|-------------|----------|
| Halbsatz ergaenzen | embeddings.md:497: Praeteritum bleibt, Ergaenzung "seit 2026 wieder gepflegt, weiterhin ES-gekoppelt" | ✓ |
| So lassen | Keine Aenderung | |
| Neutral umformulieren | Verwaist-Argument streichen | |

| Option | Description | Selected |
|--------|-------------|----------|
| Praezisieren | info.xml:113 auf "the machine running the backend" umstellen (analog Admin-Karte 1.4.1), EN/DE/FR | ✓ |
| So lassen | "the box" bleibt | |

**User's choice:** Beide Stellen anpassen.

---

## Release-Ablauf

| Option | Description | Selected |
|--------|-------------|----------|
| Auf WARNING heben | httpx/httpcore-Logger im Image auf WARNING, keine fileid/userId im Standardlog | ✓ |
| Belassen + dokumentieren | INFO bleibt, Hinweis in der Doku | |

| Option | Description | Selected |
|--------|-------------|----------|
| Umsetzen | Quellpakete (git archive des Tags) als Release-Assets anhaengen | ✓ |
| Verwerfen | GitHub-Auto-Archive reichen | |

| Option | Description | Selected |
|--------|-------------|----------|
| CI + lokale frische NC | CI-Beweis amd64 plus einmalige lokale Docker-Fremdinstallation mit Sichtprobe | ✓ |
| Nur CI | Nur CI-Beweis | |
| CI + arm64-Box | Zusaetzlich gemietete m7g-Box | |

**User's choice:** httpx auf WARNING; Quellpakete umsetzen; Fremdinstallation CI + lokal ohne Box.
**Notes:** Einreichungs-Reihenfolge wie 1.4.2 bestaetigt (seriell auf main, jedes Push-Wort einzeln, Tag-Link-Pruefung vor Abnahme).

## Claude's Discretion

- Definition "verschwundener externer Speicher" + Abgleich-Mechanik
- Konkrete Entpack-/Parserlimits
- Aufbau der Generator-Helfer
- Technik des Quellpaket-Schritts in release.yml

## Deferred Ideas

- 186 DB-Abfragen je Poll: bleibt v1.6-Kandidat, kein Umbau in Phase 36
- v1.6-Future-Liste (granite r2, #25-Dedup, Reranker, CLIP, whisper.cpp) unveraendert
