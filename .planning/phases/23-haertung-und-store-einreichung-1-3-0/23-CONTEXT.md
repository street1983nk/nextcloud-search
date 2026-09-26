# Phase 23: Haertung und Store-Einreichung 1.3.0 - Context

**Gathered:** 2026-09-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Findling 1.3.0 steht als signiertes App-Paar im Store, mit ehrlich dokumentierten Grenzen des Sprachausbaus (HART-04, HART-05, REL-03). Die Haertung schliesst zwei beschlossene Produkt-Nacharbeiten ein: den Kaltstart-Fix V-22-01/V-22-02 (leere erste Suche nach Neustart bei Schalter 0) und den Reparaturlauf fuer die alten skipped(gone)-Eintraege aus Issue #14. Dazu gehoeren der Versionssprung beider info.xml auf 1.3.0, die Aufraeumbefunde HART-04 (fastembed-Pin, numpy), die Ende-zu-Ende-Strecken (Fremdinstallation frisch, Upgrade 1.2.0 auf 1.3.0 inkl. Umbau-Fall) und die Einreichung mit 2x HTTP 201 nach Owner-Abnahme.

</domain>

<decisions>
## Implementation Decisions

### Kaltstart-Fix V-22-01/V-22-02 (Owner 26.09.)
- **D-01:** Der Kaltstart-Befund wird IN 1.3.0 gefixt, auf BEIDEN Routen (/search und /snippets). Fix-Weg: die erste Suche nach Neustart antwortet sofort rein lexikalisch (Tantivy, unter dem 1,5-s-Deckel) und stoesst das Laden der Modellgewichte im Hintergrund an; Semantik greift ab der naechsten Anfrage. NIE eine leere Treffergruppe wegen Modell-Ladens.
- **D-02:** /snippets bekommt zusaetzlich die Einwortregel, die /search schon kennt: fuer einwortige Anfragen wird die semantische Seite gar nicht erst aufgebaut (kein query_may_load fuer Einwort-Zeilen).
- **D-03:** KEIN Vorwaermen beim Containerstart. Das Lazy-Load-Prinzip bleibt: RAM-Kosten der Gewichte (~250-400 MB) fallen erst bei der ersten semantischen Nutzung an (4-GB-Boxen-Budget).

### Alte gone-Zeilen (Issue #14)
- **D-04:** Die 1.3.0-Migration reiht ALLE als skipped(gone) markierten Eintraege einmalig neu ein (Reparaturlauf beim Upgrade). Der neue ACL-Code (Merge 257caac) sortiert sie dann korrekt: indexieren oder ehrlich unreadable/gone. Kein manueller Eingriff fuer Betroffene noetig; Preis ist ein einmalig laengerer Scan nach dem Upgrade.

### Release-Text-Zuschnitt
- **D-05:** Issue-14-Fix: eigene Changelog-Zeile mit Dank an budachst und Verweis auf #14. Nach dem Release eine kurze Antwort im Issue (1.3.0 enthaelt Fix plus Reparaturlauf). Der Store-Kurztext bleibt frei davon (Faktenlisten-Regel).
- **D-06:** HART-05-Grenzen: alle vier Punkte als Kurzliste ("Known limitations") IM Store-Text UND identisch in der Doku: (1) ano und ano fallen zusammen, (2) pt-Rechtschreibreform wird nicht vereinheitlicht, (3) Komposita nur fuer de und nl, (4) Franzoesisch hat kein Koerperfeld. Erfuellt HART-05 woertlich; bleibt Faktenliste.

### Audit-Tiefe
- **D-07:** Security-Audit VOLL ueber die ganze App (wie vor jeder Abgabe). Bug- und Performance-Audit GEZIELT auf die seit 1.2.0 geaenderten Pfade: Schema/Marken/Umbauweg (18), Frageseite (19), Kataloge es/it/nl/pt (20), NL-Komposita (21), Kaltstart-Fix und gone-Reparaturlauf (23). Begruendung: Phasen 17-22 hatten je eigene Audits. Endstand bleibt 0 CRIT / 0 HIGH, MEDIUM behoben, LOW dokumentiert entschieden.

### Claude's Discretion
- Mechanik des Hintergrundladens (Task/Lock-Zuschnitt, Doppelstart-Schutz) und Nachweis (Test + Nachmessung der Kaltstartroute in CI).
- Zuschnitt des Reparaturlaufs (Migrationsschritt vs. Startup-Job), solange er einmalig laeuft und idempotent ist.
- HART-04-Weg: fastembed==0.8.0-Pin entfernen oder Import belegen, numpy sauber deklarieren oder eliminieren; Ergebnis muss die Abhaengigkeitsliste dem Container-Ist angleichen.
- Reihenfolge der Haertungsschritte; E2E-Strecken nach dem probe-92d.yml-Muster.
- Kleine offene Doku-Befunde mitnehmen (Messbericht 21-04 Abschn. 4.3: 41,9 statt 42,1 MB).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Befunde, die diese Phase fixt
- `.planning/phases/22-messanfahrt-bl-f03/deferred-items.md` , V-22-01/V-22-02 mit Messbelegen (innerMs 1505-1596 gegen ceilingMs 1500, beide Routen), Herkunft des Kaltstart-Falls (Vorfall 10.09.), Versionssprung-Merker (beide info.xml tragen noch 1.2.0), 94b-Leserfehler
- `backend/src/findling/api/search.py`, `backend/src/findling/api/snippets.py`, `backend/src/findling/embed/engine.py` , die query_may_load-Stellen (V-22-01/02-Fixorte)
- `backend/src/findling/extract/errors.py` (GONE-Reason) und `backend/src/findling/store/repo.py` (~Zeile 271) , gone-Status im Store, Ansatzpunkt des Reparaturlaufs
- Merge `257caac` / GitHub Issue #14 (budachst) , der ACL-Fix, auf dem der Reparaturlauf aufsetzt

### Requirements und Store
- `.planning/REQUIREMENTS.md` , HART-04, HART-05, REL-03 (Zeilen 37-39)
- `docs/store-listing.md` , Store-Text-Gates (Faktenliste, eine Messzahl an drei Stellen)
- `docs/store-identity.md`, `docs/certificates.md` , Signierung des App-Paars, Submission-Identitaeten
- `.github/workflows/store-submit.yml` , Submission-Mechanik (2x HTTP 201)
- `backend/pyproject.toml` (Zeilen 32-42) , fastembed==0.8.0-Pin und onnx/numpy-Begruendungskommentare (HART-04)

### Grenzen des Sprachausbaus (HART-05-Wortlaut-Quellen)
- `docs/language-analyzers.md` , Analysekette je Sprache
- `docs/l10n-spanish.md`, `docs/l10n-portuguese.md`, `docs/l10n-french.md`, `docs/l10n-dutch.md`, `docs/l10n-italian.md` , die vier Grenzen im Detail

### E2E-Strecken und Praezedenz
- `.github/workflows/probe-92d.yml` , Praezedenz Upgrade-E2E in CI (echtes App-Update, Volumen und Bestand bleiben; occ upgrade Exit 3 = nichts zu tun)
- `docs/performance.md` , Zahlenquelle fuer den Store-Text (Abschnitt v1.3-Anfahrt, E1-E14); traegt auch die Umbau-Zahl 581 s fuer den Umbau-Fall der Upgrade-Strecke
- `docs/install-check.md`, `docs/uninstall.md` , Fremdinstallations- und Rueckbau-Strecken

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Einwortregel existiert bereits auf /search; /snippets uebernimmt sie (D-02).
- `probe-92d.yml`: fertiges CI-Muster fuer die Upgrade-Strecke mit Bestandstor (fail-closed Marken `bestand-bestanden`).
- Migration `Version001300Date20260924000000` existiert bereits (entfernt den gemerkten Backend-Versionsschluessel); der Reparaturlauf kann als weiterer Migrationsschritt daneben treten.

### Established Patterns
- Nach jeder Phase Security-, Bug- und Performance-Audit; Befunde vor Phase-Abschluss fixen (Owner-Regel 15.08.).
- Launch-Haertung vor der Store-Abgabe, Abgabe erst nach Owner-Abnahme (Owner-Regel 06.09.).
- Store-Texte: Faktenliste, hoechstens eine Messzahl, Entwurf vor Release dem Owner zeigen (Owner-Regel 07.09.).
- Versionsgleichlauf: PHP-App und ExApp fuehren dieselbe Version (beide info.xml auf 1.3.0 heben).

### Integration Points
- Kaltstart-Fix beruehrt den Embed-Engine-Ladepfad (query_may_load) und beide API-Routen.
- Reparaturlauf haengt an der Upgrade-Migration der PHP-App bzw. dem Backend-Start nach Upgrade.
- Changelog/Store-Text reisen mit der Submission (store-submit.yml, 2x HTTP 201).

</code_context>

<specifics>
## Specific Ideas

- Der Owner nimmt den Store-Textentwurf UND die Haertung vor der Abgabe explizit ab; die Submission startet erst danach (REL-03).
- Kill-Kriterium Nextcloud Conference zuletzt 21.09.2026 geprueft, nicht ausgeloest.
- Nach dem Release: kurze Antwort in Issue #14 an budachst (D-05); passt zur laufenden Reddit-/Community-Spur, dort meldet budachst auch Erstscan-Dauer (BL-F04-Signal, NICHT Teil dieser Phase).

</specifics>

<deferred>
## Deferred Ideas

- Erstindex-Beschleunigung (BL-F04) bleibt v1.4; budachsts Beschleunigungsfrage aus Issue/Reddit reist dort.
- FR-Koerperfeld, pt_BR/pt_PT-Wortlaute, NL-Betonungsakzente, Sortierung Name/Groesse, Mimetype-Gruppen, Pro-Schiene: unveraendert auf der Nach-v1.3-Liste der ROADMAP.
- Snapshot `snap-03f1d1d9ad9262704`: Wiedervorlage beim Milestone-Close (ROADMAP).

</deferred>

---

*Phase: 23-Haertung und Store-Einreichung 1.3.0*
*Context gathered: 2026-09-26*
