---
phase: 10-vergleichsmessung-auf-der-aws-box
plan: 07
subsystem: docs
tags: [messbericht, audit, phase-abschluss, aws-box, di-nachzug]
requires:
  - 10-06-SUMMARY.md (die Rohdaten, das Kernaussage-Blatt, die zwei Nachmessungen)
  - docs/measurements/2026-09-05-semantiklauf-m7g/ (die v1.0-Grundlinie)
  - docs/measurements/2026-09-nachmessung-m7g/ (die Vergleichsform)
provides:
  - docs/measurements/2026-09-vergleichsmessung-m7g/README.md (der Messbericht, 19 Abschnitte)
  - docs/audits/2026-09-phase-10/README.md (das Audit-Gate der Phase)
  - MESS-01, MESS-02, MESS-03 abgehakt mit Beleg
  - DI-07-02 gemessen und an Phase 11 uebergeben, DI-07-03 Messteil geschlossen
  - DI-10-01 bis DI-10-05 als Phase-10-Befunde
  - die angehaltene Box mit Abschlusszahlen
affects:
  - docs/performance.md (zwei abgeloeste Zeiger, ein neuer Abschnitt, der vierte Verbleib)
  - CLAUDE.md (RAM-Budget-Tabelle, Posten Tokenizer und Splitter)
  - .planning/REQUIREMENTS.md, .planning/ROADMAP.md
  - Phase 11 (REL-01 traegt den Nachzug der Zahlen, drei offene Befunde)
tech-stack:
  added: []
  patterns:
    - "Vergleichsform der Nachmessung: Posten, Grundlinie, dieser Lauf, Differenz, Rohdatei"
    - "Jede Zahl ohne Entsprechung ist eine Erstmessung und keine Vergleichszeile"
    - "Ein Befund an einer Dokumentationszahl bekommt keinen Test, und der Bericht sagt warum"
key-files:
  created:
    - docs/measurements/2026-09-vergleichsmessung-m7g/README.md
    - docs/audits/2026-09-phase-10/README.md
    - .planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md
  modified:
    - docs/performance.md
    - docs/measurements/2026-09-vergleichsmessung-m7g/00-kernaussage.md
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/93-kosten-und-verbleib.txt
    - docs/measurements/2026-09-grundlast-fein/README.md
    - CLAUDE.md
    - .planning/phases/07-gemeinsame-embedding-engine/deferred-items.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
decisions:
  - "Erfolgskriterium 2 bleibt teilweise belegt statt aufgerundet (Owner: So lassen)"
  - "Der Nachzug der Zahlen in README.md und docs/store-listing.md faellt in Phase 11, eine Textrunde statt zwei"
  - "T-09-29 bleibt auf accept, jetzt mit Zahlen: der Vektorscan laeuft einmal je Anfrage, nicht je Seite"
  - "DI-07-02 wird nicht geschlossen, sondern mit negativer Marge an Phase 11 uebergeben"
  - "Die Box wird angehalten, nicht abgebaut; der Abbau ist ein eigener Plan in Phase 11"
  - "CLAUDE.md bekommt den Posten Tokenizer und Splitter mit 0 im Ruhezustand und 544 MB Spitze"
metrics:
  duration: "rund 2 h 40 min (2026-09-10, 15:52Z bis 18:30Z)"
  completed: 2026-09-10
  tasks: 4
  files_changed: 11
  commits: 4
---

# Phase 10 Plan 07: Bericht, Audits und Berichtsabnahme Summary

Der Messbericht der Vergleichsmessung steht in 19 Abschnitten neben dem
v1.0-Bericht, jede Zahl mit ihrer Rohdatei und jede Verschlechterung in eigener
Ueberschrift; das Audit-Gate ist gefahren, die drei MESS-Anforderungen sind mit
Beleg abgehakt, und die Box ist nach der Owner-Abnahme mit 31,05 Stunden und
3,5969 USD unter beiden Deckeln angehalten worden.

## Was gebaut wurde

**Der Messbericht** (`docs/measurements/2026-09-vergleichsmessung-m7g/README.md`,
1.070 Zeilen, 19 Abschnitte, 154 Verweise auf Rohdateien). Er folgt der
Abschnittsfolge des v1.0-Berichts und der Vergleichsform der Nachmessung
(Posten, Grundlinie, dieser Lauf, Differenz), stellt 05-21 als vierte Spalte
daneben, wo sie etwas hinzufuegt, und weist jede Zahl ohne Entsprechung als
Erstmessung aus. Abschnitt 19 "Was dieser Lauf nicht besser gemacht hat" fuehrt
dreizehn Punkte in eigenen Unterueberschriften.

**Die Nachzuege in den Projektdokumenten.** `docs/performance.md` bekommt zwei
Zeilen in "Stand dieses Berichts", einen eigenen Abschnitt "Die
Vergleichsmessung v1.1 gegen v1.0" neben denen der zwei Vorlaeufer, und den
vierten Verbleib der Box. **Zwei Zeiger auf Phase 10 sind abgeloest**, nicht
einer: der bekannte an der urspruenglichen Zeile 3509 und ein zweiter ("Das p95
ueber den vollen Bestand gehoert Phase 10"), der beim Nachziehen gefunden
wurde. `CLAUDE.md` traegt den Posten "Tokenizer und Splitter" in der
RAM-Budget-Tabelle, und der Feinmessungsbericht sagt nicht mehr, dass die Frage
offen ist.

**Der Auditbericht** (`docs/audits/2026-09-phase-10/README.md`) mit V2, V3, V4,
V7 und V14 je mit Pruefung und Beleg, allen 47 Threats namentlich abgehakt,
fuenf Zahlen-Randfaellen mit Eintritt und Faenger, dem Performance-Vergleich
gegen jedes Budget und der Entscheidung ueber T-09-29.

## Zahlen, die diesen Plan tragen

| Groesse | 06-11 (v1.0) | dieser Lauf | Differenz |
|---|---:|---:|---:|
| Grundlast im Leerlauf | 691,8 MB | **103,2 MB** | minus 588,6 MB |
| anon-Spitze des Laufs | 1.837,8 MB | **1.764,2 MB** | minus 73,6 MB |
| `memory.events max` | 2.796 | **21.939** | plus 19.143 |
| p95 Stufe 8 (die Zusage) | 1.915,0 ms | **2.125,5 ms** | plus 11,0 Prozent |
| Laufzeit beider Spuren | 18 h 56 min | **26 h 37 min** | plus 40,6 Prozent |
| Bestand | 51.961 | **52.111** | plus 150 |
| Byte je Dokument, Vektoren | 1.321,0 | **1.318,3** | minus 2,7 |

Alle drei Schadenszaehler stehen auf null, `OOMKilled=false`,
`RestartCount=0`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ein zweiter Zeiger auf Phase 10 in `docs/performance.md`**

- **Found during:** Task 2, beim Verify des Plans
- **Issue:** Der Plan nannte genau eine Stelle (Zeile 3509). Die Verify-Zusicherung `'gehoert Phase 10' not in p` schlug trotzdem fehl: an Zeile 3412 stand ein zweiter Satz derselben Art ("Das p95 ueber den vollen Bestand gehoert Phase 10"). Ein Zeiger, der auf eine gelaufene Phase zeigt, ist genau der Widerspruch, den T-10-49 verhindern soll, und er zaehlt nicht weniger, weil der Plan ihn nicht kannte.
- **Fix:** Beide Saetze abgeloest, beide zeigen jetzt auf den Bericht mit seinem Datum, und beide lassen die alte Formulierung erkennbar ("Bis dahin stand hier, es gehoere Phase 10").
- **Files modified:** `docs/performance.md`
- **Commit:** `5cefe1f`

**2. [Rule 2 - Missing correctness] Die CLAUDE.md-Zeile in der falschen Spalte**

- **Found during:** Task 2
- **Issue:** Die Owner-Vorgabe lautete "Tokenizer und Splitter, 544 MB". In der RAM-Budget-Tabelle haette die Zahl in der Spalte "Ruhezustand" gestanden, und das waere falsch: der Posten ist seit Plan 07-03 **faul gebaut** und faellt erst beim ersten Chunkerlauf an. Die gemessene Grundlast dieses Laufs von 103,2 MB enthaelt ihn ausdruecklich nicht. Eine Budget-Tabelle, die 544 MB als Ruhezustand fuehrt, laesst eine 4-GB-Box schlechter aussehen als sie ist, und zwar um mehr als ein Achtel ihres Speichers.
- **Fix:** "0 bei faulem Bau" im Ruhezustand, 544 MB als Spitze, mit allen drei gemessenen Zahlen (amd64 544,3 / arm64 nativ 543,7 / auf der Box 542,8) und der Stellschraube.
- **Files modified:** `CLAUDE.md`
- **Commit:** `5cefe1f`

**3. [Rule 1 - Bug] Die Laufnummer des gruenen CI-Laufs war als unbekannt eingetragen**

- **Found during:** Task 1
- **Issue:** `rohdaten/98-sprachfaelle.txt` schreibt `ci-beleg: der letzte gruene integration.yml-Lauf ist unbekannt`. Der Plan verlangt in Abschnitt 12 ausdruecklich Laufnummer und Commit als zweiten Beleg.
- **Fix:** Ueber `gh run list --workflow integration.yml --status success` nachgetragen: Lauf **34339346666**, Commit `0dd007d3b20c1185e93b38d4e071e4ec086f2ea2`, 2026-09-09T10:16:38Z auf `main`. Die Rohdatei bleibt unveraendert, die Ergaenzung steht im Bericht.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`
- **Commit:** `aa9c6bd`

**4. [Rule 1 - Bug] Eine falsche Zahl in der Kopfzeile einer Rohdatei**

- **Found during:** Task 1
- **Issue:** `rohdaten/99-seitenroute.txt` begruendet die Erstmessung mit "diese Instanz HAT eine vectors.db mit 145.854 Vektoren". 145.854 ist die Chunk-Zahl aus 06-11; diese Instanz traegt 146.171.
- **Fix:** Die Rohdatei bleibt unveraendert (eine nachtraeglich verbesserte Rohdatei belegt nicht mehr, was das Skript geschrieben hat). Die Korrektur steht im Bericht, Abschnitt 11, mit beiden Zahlen und dem Satz, welche gilt. Als LOW-Befund L-02 des Audits mit Wiedervorlage gefuehrt.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, `docs/audits/2026-09-phase-10/README.md`
- **Commits:** `aa9c6bd`, `c51415f`

### Auslassungen, die keine sind

**Die Phase hat keinen Produktionscode geaendert.** `git diff af18542..HEAD
--name-only | grep -E '^(php/|backend/src/)'` liefert keine Zeile ueber alle
102 Dateien und 36 Commits. Das ist der erste Auditbefund und der Grund, warum
V5 und V6 nicht zutreffen.

## Die drei Erkenntnisse der Nachmessungen, mit ihrer Einordnung

**Sprachfaelle 6 von 10: kein Sprachdefekt.** Die deutsche Analysekette teilt
die Tokens nachweislich (`grundstuck`, `verkehr`, `genehm`), und jede Suche
liefert im Index zehn Treffer; sie gehoeren aber alle dem Lasttest-Konto mit
seinen 52.111 Dokumenten. Fuer drei von vier geprueften Begriffen kommt die
Datei des fragenden Kontos unter den ersten 2.000 Kandidaten nicht vor, fuer
`Bescheid` steht sie auf Rang 1.925. **Ein eigener Nutzer trennt die
Berechtigung und nicht den Index.** Im Bericht als Erstmessung mit
Mess-Setup-Vorbehalt gefuehrt, im Audit als M-01, als DI-10-02 an Phase 11.

**Kaltstart: eine Methodik-Korrektur, die allen bisherigen Zahlen fehlte.** Die
gemessenen Dauern sind die **ganze OCS-Anfrage**, die Decke von 1.501 ms gilt
nur fuer den **inneren Containeraufruf**. Eine Gesamtdauer ueber 1,5 s beweist
deshalb keinen Abbruch: die drei Reproduktionen liegen bei 1.598, 1.805 und
2.468 ms und liefern **je sechs Treffer**. Der eine Abbruch ist trotzdem belegt
(`cURL error 28: Operation timed out after 1501 milliseconds` um 14:05:17Z, bei
kaltem Wirtscache). Die Korrektur steht im Bericht Abschnitt 9.2, in DI-07-02
und in `docs/performance.md`.

**Der Werkzeugbefund, und er ist der unangenehmere.** Stufe 16 der Lastreihe
traegt **17 abgebrochene Containeraufrufe bei gemeldeten `failures: 0`**. Die
Route antwortet bei einem abgebrochenen Containeraufruf mit HTTP 200 und ohne
Containerteil, also zaehlt `search_load.py` einen Ausfall als Erfolg. Der
Fingerabdruck steht in den Trefferzahlen: 5,40 je Anfrage auf den Stufen 1 und
4, nur 4,16 auf Stufe 16. Stufen 1 bis 12 unberuehrt, die Stufe-8-Zusage steht.
Als **DI-10-01** vergeben.

## Auditbefunde

| Schwere | Zahl | Stand |
|---|---:|---|
| CRITICAL | 0 | |
| HIGH | 0 | |
| MEDIUM | 1 | M-01, Deutung in diesem Lauf korrigiert, Skriptaenderung als DI-10-02 an Phase 11 |
| LOW | 5 | L-01 bis L-05, je mit Entscheidung und Wiedervorlage |

**Die V4-Frage zum Driftfall ist beantwortet, und die Antwort ist nein.** Nach
der Ruecknahme der Freigaben um 14:14:14Z lieferten zehn Suchen **null Treffer
und null Snippetaufrufe**. Die Berechtigungsgrenze hat gehalten. Dass der
Recheck das verhindert hat oder der Vorfilter schon Bescheid wusste, ist fuer
die Sicherheitsfrage gleichgueltig und fuer die Messfrage nicht; der Bericht
trennt die beiden.

**T-09-29 aus Phase 9 ist entschieden:** `accept` bleibt, jetzt mit Zahlen
statt mit deren Abwesenheit, und mit einer anderen Begruendung als vermutet:
nicht "der Scan ist billig", sondern **"der Scan laeuft einmal je Anfrage und
nicht je Seite"** (tiefe Seite 0,333 s gegen erste Seite 0,332 s).

## Owner-Checkpoint, Task 4

Signal **"bericht abgenommen"** am 2026-09-10. Die Antworten, wortgetreu
uebernommen:

| Frage | Antwort des Owners | Datum |
|---|---|---|
| Punkt 6, Nachzug in README und Store-Text | Erst **Phase 11** mit der Store-Text-Abnahme, eine Textrunde statt zwei; DI-10-03 bleibt stehen | 2026-09-10 |
| Merker fuer Phase 11 | "wer eine Messzahl aendert, aendert DREI Stellen (README.en.md + beide info.xml, Gate haelt sie deckungsgleich)" | 2026-09-10 |
| Erfolgskriterium 2 | "So lassen", also weiter als **teilweise belegt** und nicht schoengerechnet | 2026-09-10 |
| Punkt 7, Nacharbeit | Keine Zahl beanstandet, keine Nacharbeit auf der Box noetig | 2026-09-10 |

## Der Verbleib der Box

`scripts/ops/aws_box.sh stop` nach der Abnahme gefahren:

| Groesse | Wert |
|---|---|
| `BOX_STOPPED_ISO` | **2026-09-10T16:22:50Z** |
| `BOX_LAST_UPTIME_HOURS` | **31.05** |
| `BOX_LAST_UPTIME_COST_USD` | **3.5969** |
| `BOX_PARKED_COST_USD_PER_DAY` | 0.3130 |
| Zustand aus der API, 16:23:15Z | `stopped`, nicht `running` |
| gegen den angehobenen Deckel | 31,05 von 34 Stunden, 3,5969 von 4,00 USD, **nicht gerissen** |

**Angehalten, nicht abgebaut.** Beide Datentraeger bleiben, mit Korpus, beiden
Indizes und den Abbildern. Der Abbau ist ein eigener Entscheid und braucht
einen eigenen Plan in Phase 11.

Die harte Linie, die der Orchestrator daneben gesetzt hatte (bei 19:10Z
anhalten, egal ob abgenommen), ist nicht gebraucht worden: die Abnahme kam vor
dem Deckel.

## Authentication Gates

Keine im Sinne einer Unterbrechung. Die AWS-Zugangsdaten wurden fuer die
`status`- und `stop`-Aufrufe aus einer Datei ausserhalb des Arbeitsbaums in die
Umgebung geladen; weder ihr Inhalt noch ihr Pfad steht in einer Rohdatei, einer
Ausgabe oder einem Commit.

## Known Stubs

Keine. Dieser Plan erzeugt Dokumentation und keinen Code; kein Platzhalter, kein
`TODO`, keine leere Datenquelle. Die Fehlstellen des Laufs sind in Bericht
Abschnitt 16 mit zehn Punkten benannt und jeweils mit dem Ort versehen, an den
sie gehoeren.

## Threat Flags

Keine. Diese Phase aendert keine Datei unter `php/` oder `backend/src/`, also
entsteht kein neuer Netzwerkendpunkt, kein Auth-Pfad, kein Dateizugriffsmuster
und keine Schemaaenderung an einer Vertrauensgrenze. Der Diff-Befund steht als
erster Auftrag des Auditberichts.

## Was an Phase 11 uebergeben ist

| ID | Was | Warum nicht hier |
|---|---|---|
| **DI-07-02** | Die Entscheidung ueber `REQUEST_TIMEOUT_SECONDS`, mit Marge minus 338,4 ms auf vollem Bestand | Eine hoehere Decke laesst jeden Nutzer bei jeder Suche laenger warten; die Alternativen sind nicht gemessen |
| **DI-07-03** | Die Frage an den Rechteabgleich: die Schleife holt keine zweite Runde nach | Der Rechteabgleich ist die Berechtigungskette, also per Definition nicht klein |
| **DI-10-01** | `search_load.py` zaehlt abgebrochene Containeraufrufe als Erfolge | Ein Werkzeug, das mitten in einer Reihe geaendert wird, macht die Reihe unvergleichbar |
| **DI-10-02** | Der Messaufbau der Sprachfaelle | Braucht eine neue Box, also eine neue Anfahrt und eine neue Freigabe |
| **DI-10-03** | Der Nachzug der Zahlen in `README.md` und `docs/store-listing.md`, mit dem Drei-Stellen-Merker | Owner-Entscheid: eine Textrunde in Phase 11 |
| **DI-10-04** | Welcher Kandidat die Mehrlaufzeit traegt | Braucht eine Messung, die kein Plan dieser Phase vorsieht |
| **DI-10-05** | Darf ein Messlauf gegen `:dev` pruefen? | Aenderung an der Auslieferungskette |
| **T-09-29** | Wiedervorlage bei einem deutlich groesseren Vektorbestand | Diese Messung traegt die Entscheidung bis dahin |

## Verification

- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`: 19 Ueberschriften der Ebene 2, 1.070 Zeilen, 154 Verweise auf `rohdaten/`, alle 18 geforderten Grundlinienzahlen vorhanden, kein Em-Dash und kein En-Dash. **gruen**
- `docs/performance.md`: nennt die neue Messreihe, kein Zeiger auf Phase 10 mehr, 1.837,8 MB steht weiter als Vergleich. **gruen**
- DI-07-02 traegt `REQUEST_TIMEOUT_SECONDS`, DI-07-03 traegt `MAX_ROUNDS`. **gruen**
- `.planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md` existiert mit DI-10-01 bis DI-10-05. **gruen**
- `REQUIREMENTS.md`: MESS-01 bis MESS-03 abgehakt mit Belegpfad und Kernzahl, Traceability auf Complete. **gruen**
- `ROADMAP.md`: die vier Kriterien einzeln belegt, Kriterium 2 als teilweise, Progress 7/7 Complete mit Datum. **gruen**
- `docs/audits/2026-09-phase-10/README.md`: V2, V3, V4, V7, V14 vorhanden, alle 47 Threats abgehakt, T-09-29 entschieden, "Was ausdruecklich in Ordnung ist" vorhanden. **gruen**
- `cd backend && uv run python -m pytest -q`: **1968 passed, 15 skipped**
- `ruff check .`: All checks passed. `ruff format --check .`: 120 files already formatted. `pyright`: 0 errors, 0 warnings. `vulture src tests --min-confidence 80`: sauber. **gruen**
- `git diff af18542..HEAD --name-only` nennt keine Abhaengigkeitsdatei und keine Datei unter `php/` oder `backend/src/`. **gruen**
- Kein Em-Dash und kein En-Dash in einer geaenderten Datei. **gruen**
- CI nach dem Push: kein neuer Lauf, weil alle Aenderungen unter `docs/**`, `.planning/**` und `CLAUDE.md` liegen und die Pfadfilter nicht greifen. **erwartet**

## Self-Check: PASSED

Dateien geprueft, alle vorhanden:

- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` (1.070 Zeilen)
- `docs/audits/2026-09-phase-10/README.md`
- `.planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md`
- `.planning/phases/10-vergleichsmessung-auf-der-aws-box/10-07-SUMMARY.md`

Commits geprueft, alle im Log: `aa9c6bd`, `5cefe1f`, `c51415f`.

Die Verify-Zusicherungen der Tasks 1 bis 3 sind **nach** den Nachtraegen des
Box-Stops erneut gefahren worden und sind gruen. Em-Dash-Gate ueber alle zwoelf
geaenderten Dateien: kein Treffer.

**Ein Befund des Self-Checks, ausserhalb des Scope dieses Plans:** das Wort
"Archiv" steht in `.planning/REQUIREMENTS.md` Zeile 3 und in
`.planning/ROADMAP.md`, beide Male in Bestandstext, der auf
`.planning/milestones/` verweist, und beide Male nicht von diesem Plan
eingefuegt. Die Vokabular-Regel des Owners gilt fuer nach aussen sichtbare
Artefakte (README, Store-Texte, Changelog); Planungsdateien sind es nicht.
Nicht angefasst, hier benannt.
