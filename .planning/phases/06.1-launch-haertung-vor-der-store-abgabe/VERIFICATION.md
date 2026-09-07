---
phase: 06.1-launch-haertung-vor-der-store-abgabe
verified: 2026-09-07T18:00:00Z
status: gaps_found
score: 4/5 Erfolgskriterien voll verifiziert, 1 mit offenem Nebenpunkt
overrides_applied: 0
gaps:
  - truth: "Kriterium 3 / E-H1: die Versionsfenster-Aussage steht widerspruchsfrei an allen fuenf von E-H1 selbst benannten Stellen"
    status: partial
    reason: "E-H1 benennt woertlich fuenf zu aendernde Fundstellen, darunter 'REQUIREMENTS.md (PKG-03) und die Stack-Tabelle in CLAUDE.md', und sagt ausdruecklich, dass Plan 06.1-09 alle fuenf 'gemeinsam' nachzieht, 'weil eine Versionszusage, die an fuenf Stellen steht und an einer geaendert wird, sich danach selbst widerspricht'. Tatsaechlich wurden nur die drei ausgelieferten/gateten Stellen (beide info.xml, deploy-harp.yml, README.md) gesetzt. CLAUDE.md und REQUIREMENTS.md wurden NICHT nachgezogen, das ist in der 06.1-09-SUMMARY offen benannt und in deferred-items.md als DI-06.1-03 aufgenommen (fuenf betroffene Stellen: CLAUDE.md dreimal, REQUIREMENTS.md/PKG-03, zwei PHP-Kommentare, ein CI-Kommentar, docs/uninstall.md fuenffach). DI-06.1-03 wurde ueber den gesamten Rest der Phase (Plaene 10 bis 24) nie wieder aufgegriffen und nie als ERLEDIGT markiert, obwohl Plan 06.1-19 (der die ROADMAP wegen E-H1 ohnehin oeffnet) als Zielort dafuer explizit vorgesehen war."
    artifacts:
      - path: "CLAUDE.md"
        issue: "Zeile 43 (Tabelle 'Kernentscheidungen'): 'min-version 32, max-version 35'; Zeile 133ff Abschnitt 'Nextcloud-Versionsfenster'; Zeile 236 Tabelle 'Version Compatibility': 'NC 32 bis 34 (max-version 35)' -- widerspricht dem tatsaechlichen, ausgelieferten Fenster NC 33-35"
      - path: ".planning/REQUIREMENTS.md"
        issue: "Zeile 57 und 117: PKG-03 nennt weiterhin 'Nextcloud 32-34 (max-version 35)' bzw. 'NC 32-34'"
      - path: "docs/uninstall.md"
        issue: "mehrere Stellen (Z. 65, 168, 279, 283, 338 laut DI-06.1-03) sprechen weiterhin von vier Laeufen / Nextcloud 32 als Beispiel, obwohl die Matrix jetzt drei Laeufe (33/34/35) faehrt"
      - path: "php/lib/Service/StorageService.php"
        issue: "Zeile 19: Kommentar 'the app declares min-version 32' ist sachlich falsch (jetzt 33)"
      - path: "php/lib/Settings/Section.php"
        issue: "Zeile 16: derselbe veraltete Kommentar"
      - path: ".github/workflows/integration.yml"
        issue: "Zeile 111: Kommentar nennt 'stable32 / stable33 / stable34' statt der tatsaechlich gefahrenen stable33/34/35"
    missing:
      - "CLAUDE.md an den drei genannten Stellen auf min-version 33 nachziehen"
      - "REQUIREMENTS.md PKG-03 (Text und Rueckverfolgungstabelle) auf NC 33-35 nachziehen"
      - "DI-06.1-03 entweder schliessen oder explizit als bewusst zurueckgestellt mit Zieltermin markieren, statt es stillschweigend ueber 15 weitere Plaene mitzuschleifen"
deferred: []
human_verification: []
---

# Phase 06.1: Launch-Haertung vor der Store-Abgabe Verification Report

**Phase Goal:** Findling ist vor der ersten Store-Abgabe so robust und fehlerfrei wie moeglich: Fehler- und Randpfade, Rechte-Grenzen, Betriebsuebergaenge, Ressourcengrenzen, Fremdinstallation ueber den Store-Weg und die Store-Vorgaben sind getestet statt angenommen, die drei Audits sind erneut gefahren und gefixt, die Speicherzahl ist nach dem Engine-Fix neu gemessen, und der Owner hat die Phase abgenommen.
**Verified:** 2026-09-07T18:00:00Z
**Status:** gaps_found (ein Nebenpunkt, keiner der fuenf Erfolgskriterien scheitert am Kern)
**Re-verification:** No , initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Jede in 06.1-CONTEXT.md benannte Massnahme hat einen Test, der rot sein kann, plus Beleg im Repo; kein "nur manuell geprueft" | ✓ VERIFIED | Alle 24 Plaene liefern SUMMARYs mit konkreten Testdateien und "Rotlauf gefahren"-Vermerken (z.B. `test_extract_edge_paths.py`, `test_wordlist.py::test_the_setting_decides_which_recipe_the_index_gets`, `test_embed_engine.py::test_a_load_that_threw_is_tried_again_after_the_cooldown`, `test_sandbox.py` fuer den Office-Fix, `QueueServiceTest.php` mit 10 Faellen fuer den Widerrufspfad). Stichprobe: `test_instance_marker.py` lokal ausgefuehrt, 30/30 gruen; `test_sandbox.py`+`test_embed_engine.py` lokal ausgefuehrt, 33 bestanden/3 uebersprungen (uebersprungen = Box-gebundene Faelle, korrekt markiert). Kein Fund von "nur manuell geprueft" in den 24 SUMMARYs. Grep auf zentrale neue Dateien (`instance.py`, `embed/model.py`, `FileStateService.php`) zeigt keine TODO/FIXME/Placeholder. |
| 2 | Suchseite und Arbeiter teilen eine Embedding-Engine; ARM-Nachmessung zeigt anon-Spitze unter 1.837,8 MB bei oom/oom_kill/oom_group_kill = 0 | ✓ VERIFIED | `embed/engine.py::shared_model()` als prozessweiter Halter, `load_count()` als Gegenprobe in CI (`resilience.yml`). Nachmessung in 06.1-18-SUMMARY: anon-Spitze **1.812,7 MB** (< 1.837,8 MB), alle sechs `memory.events`-Zaehler auf 0 einschliesslich `max` (vorher 2.796). Zahl konsistent in README.md, `docs/embeddings.md` und beiden `info.xml` (DE/EN/FR) wiedergefunden. |
| 3 | Frische Nextcloud (docker-compose, NC 33-35, amd64 **und** arm64) installiert beide Apps aus Release-Artefakten und findet Inhalte ohne Handgriff; Deinstallation raeumt auf; Federated benannt nicht abgedeckt (E-H6); AIO benannt nicht abgedeckt (E-H1/E-H5-Fassung) | ✓ VERIFIED (mit Nebenpunkt, siehe Gap) | `docs/install-check.md` dokumentiert einen vollstaendigen amd64-Lauf (Abschnitt 1) und einen arm64-Lauf (Abschnitt 5) je mit Zero-Config-Nachweis, Integritaetsbeweis und den sechs Deinstallations-Feststellungen. Beide `info.xml` zeigen `min-version="33" max-version="35"` und die verankerte Routenform `^/search$` etc. (grep bestaetigt). CI (`gh run list`) zeigt "HaRP deploy" gruen auf `main` (688eef7, 07.09.2026 14:34Z). Federated-Nichtabdeckung und AIO/all-in-one-Nichtabdeckung sind mit Wortlaut in Roadmap und install-check.md vermerkt (E-H6, E-H5). **Nebenpunkt:** die Versionszusage steht laut E-H1 explizit an fuenf Stellen "gemeinsam"; zwei davon (CLAUDE.md, REQUIREMENTS.md) wurden nicht nachgezogen und blieben als offener DI-06.1-03 ueber die restliche Phase stehen -- siehe Gap unten. Das beruehrt keine ausgelieferte/gegatete Zusage, aber es widerspricht der eigenen Owner-Entscheidung, die eine geteilte Aenderung "gemeinsam" verlangte. |
| 4 | Security-, Bug- und Performance-Audit erneut gefahren; alle Befunde >= MEDIUM gefixt, LOW dokumentiert entschieden | ✓ VERIFIED | Alle drei Audit-Dateien vorhanden mit Commit-Referenzen fuer jeden Fix. Security: 0 CRIT/0 HIGH/1 MED (M1 gefixt in `44556f5`)/3 LOW (L1, L3 textlich behoben, L2 bewusst als DI-06.1-18 zurueckgestellt mit Begruendung). Bugs: 0 CRIT/2 HIGH (H1 `d527184`+`1c7bb7d`, H2 `45d0d1b`)/2 MED (M1+M2 `dbafdee`)/2 LOW (bewusst entschieden liegen gelassen, mit Begruendung). Performance: 0 CRIT/0 HIGH/1 MED (`d527184`+`1c7bb7d`, mit Nachmessung nach der Behebung)/1 LOW (bewusst entschieden liegen gelassen). Alle referenzierten Commit-Hashes existieren im Repo (`git cat-file -e` bestaetigt fuer alle neun geprueften Hashes). Zwei zusaetzliche Befunde aus der Owner-Sichtprobe (Befund 8 Office/OpenBLAS, Befund 9 stehen gebliebenes failed-Urteil) wurden **zusaetzlich** vor der Abgabe in Plan 06.1-24 gefixt (`revokeFailures`/`revocableFileIds` in `FileStateService.php` verifiziert vorhanden, `_pin_native_thread_pools` in `sandbox.py` mit drei Tests). |
| 5 | Owner hat die Phase nach eigener Sichtprobe abgenommen; erst danach beginnt Plan 06-12 | ✓ VERIFIED | `docs/install-check.md` Abschnitt 6+7 dokumentiert zwei Runden der Sichtprobe (vor und nach dem Fix von Befund 8, auf Wunsch des Owners "Weg B"). Abschnitt 6 zeigt das erste, noch ungefixte Abbild mit Befund 8 (Office-Dateien "File damaged"); Abschnitt 7 zeigt Runde 2 am neu gebauten `:dev`-Abbild mit 5/5 Suchtreffern und Befund 8 als "widerlegt". Abnahme-Vermerk woertlich zitiert: "ok abgenommen weiter der rest wie deine empfehlung" (07.09.2026). Owner entscheidet im selben Zug, dass die zwei verbliebenen Befunde (9, CI-Luecke) noch VOR der Abgabe geschlossen werden, was Plan 06.1-24 dann auch belegt hat (siehe oben). APPSTORE_TOKEN-Rotation dokumentiert mit `gh secret list`-Zeitstempel 2026-09-07T11:01:21Z. |

**Score:** 5/5 Kriterien im Kern erreicht, 1 mit einem dokumentierten, aber nie geschlossenen Nebenbefund (DI-06.1-03), der laut der eigenen Owner-Entscheidung E-H1 haette mitgezogen werden sollen.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/appinfo/info.xml`, `php/appinfo/info.xml` | min-version 33, max-version 35, verankerte Routen, AGPL-3.0-or-later, aktuelle Store-Zahl | ✓ VERIFIED | grep bestaetigt alle vier Eigenschaften in beiden Dateien |
| `docs/install-check.md` | Protokoll amd64+arm64+Sichtprobe+Abnahme | ✓ VERIFIED | 1032 Zeilen, 7 Abschnitte, Abnahme-Zitat vorhanden |
| `06.1-AUDIT-SECURITY.md`, `-BUGS.md`, `-PERF.md` | 0 CRIT, MEDIUM+ gefixt mit Commit, LOW entschieden | ✓ VERIFIED | Alle referenzierten Commits existieren im Repo |
| `backend/tests/test_instance_marker.py` | Testdatei fuer DI-06.1-27/Instanz-Marke | ✓ VERIFIED | Existiert, 30/30 Tests lokal gruen |
| `php/tests/Unit/QueueServiceTest.php` | Testdatei fuer den Widerruf | ✓ VERIFIED | Existiert (7003 Bytes); kein lokales PHP verfuegbar, daher nur ueber CI verifizierbar ("PHP and store metadata gates" gruen auf 688eef7) |
| `php/lib/Service/FileStateService.php::revokeFailures` | Widerruf des failed-Urteils (Befund 9) | ✓ VERIFIED | Methode existiert, Zeile 316 |
| `backend/src/findling/instance.py` | Instanz-Marke gegen Volumenkollision | ✓ VERIFIED | Datei existiert, keine Debt-Marker |
| `CLAUDE.md`, `.planning/REQUIREMENTS.md` | E-H1-Versionsfenster nachgezogen (laut E-H1 selbst Pflicht) | ✗ STUB (unveraendert) | Beide Dateien zeigen weiterhin "min-version 32" bzw. "NC 32-34"; als DI-06.1-03 offen dokumentiert, nie geschlossen |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `embed/engine.py::shared_model()` | Suchseite (`api/resources.py`) + Arbeiter (`worker/poller.py`) | gemeinsamer Prozess-Halter | ✓ WIRED | `load_count()`-Gate in `resilience.yml` haelt die Eins-Instanz-Zusage dauerhaft nach; SUMMARY 06.1-04 belegt "load_count() bleibt bei 1" |
| `docs/install-check.md` Abschnitt 6/7 | Owner-Abnahme | woertliches Zitat | ✓ WIRED | Zitat vorhanden, mit Zeitstempel und Kontext (Weg B, zwei Runden) |
| `FileStateService::revokeFailures` | `QueueService::revocableFileIds` | Mengenarithmetik des Widerrufs | ✓ WIRED | Beide Methoden im Repo vorhanden, 10 Testfaelle laut SUMMARY 06.1-24, Datei bestaetigt Existenz von `revokeFailures` |
| E-H1 (Versionsfenster) | CLAUDE.md, REQUIREMENTS.md | "gemeinsames Nachziehen" laut Entscheidung | ✗ NOT_WIRED | Die Entscheidung selbst verlangt gemeinsames Nachziehen; zwei von fuenf Stellen wurden nicht angefasst und blieben offen (DI-06.1-03) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `CLAUDE.md` | 43, 133ff, 236 | veraltete Versionsangabe (NC 32 statt 33) | ⚠️ Warning | Widerspricht der ausgelieferten Zusage; kein Blocker fuer die Store-Abgabe selbst, aber ein Selbstwiderspruch im eigenen Projektgedaechtnis |
| `.planning/REQUIREMENTS.md` | 57, 117 | PKG-03 nennt "NC 32-34" | ⚠️ Warning | Requirements-Traceability zeigt ein anderes Fenster als das ausgelieferte |
| `.github/workflows/integration.yml` | 111 | Kommentar nennt stable32 als Teil der Matrix | ℹ️ Info | Nur ein Kommentar, keine funktionale CI-Zeile betroffen |
| `docs/uninstall.md` | mehrere (laut DI-06.1-03) | "vier Laeufe" / NC 32-Beispiel statt drei Laeufe 33-35 | ℹ️ Info | Dokumentationsdrift, kein funktionaler Fehler |

Kein TBD/FIXME/XXX/HACK ohne Referenz in den geprueften zentralen Produktionsdateien (`instance.py`, `embed/model.py`, `FileStateService.php`) gefunden.

### Requirements Coverage

| Requirement | Beschreibung | Status | Evidence |
|---|---|---|---|
| SEM-01, SEM-03 | Haertung der semantischen Suche (geteilte Engine, Distanzriegel, Stempel) | ✓ SATISFIED | Plaene 06.1-02, 06.1-10, 06.1-20 mit Tests und Nachmessung |
| PKG-05 | Store-Vorgaben, Fremdinstallation | ✓ SATISFIED | Plaene 06.1-12, 06.1-13, 06.1-16, 06.1-19 |
| PKG-03 (Traceability, nicht Phase-Scope) | "NC 32-34" in REQUIREMENTS.md | ⚠️ Inkonsistent | Text stimmt nicht mehr mit dem tatsaechlichen Fenster ueberein (siehe Gap) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Instanz-Marke schuetzt Volumen | `uv run pytest tests/test_instance_marker.py -q` | 30 passed | ✓ PASS |
| Sandbox-Fix + Engine-Lock-Verhalten | `uv run pytest tests/test_sandbox.py tests/test_embed_engine.py -q` | 33 passed, 3 skipped (Box-gebundene Faelle, korrekt markiert) | ✓ PASS |
| info.xml Versionsfenster | `grep min-version backend/appinfo/info.xml php/appinfo/info.xml` | `min-version="33" max-version="35"` in beiden | ✓ PASS |
| Verankerte Routenform | `grep "<url>" backend/appinfo/info.xml` | `^/search$`, `^/snippets$`, `^/status$`, `^/rates$`, `^/diagnose$` | ✓ PASS |
| CI-Status main | `gh run list --branch main --limit 8` | alle 8 juengsten Laeufe "completed success", u.a. "PHP and store metadata gates", "Integration", "HaRP deploy", "Resilience" auf 688eef7 | ✓ PASS |
| Commit-Existenz der Audit-Fixes | `git cat-file -e <hash>` fuer 9 in den Audits zitierte Hashes | alle 9 existieren | ✓ PASS |
| `revokeFailures` existiert | `grep -n revokeFailures php/lib/Service/FileStateService.php` | Zeile 316, Methode vorhanden | ✓ PASS |
| PHP-Testsuite lokal | n/a | kein PHP/phpunit auf dieser Maschine installiert | ? SKIP (nur ueber CI verifizierbar, dort gruen) |

### Human Verification Required

Keine offenen Punkte. Die zentrale visuelle/Verhaltens-Pruefung (Owner-Sichtprobe D-H5) ist bereits durch den Owner selbst durchgefuehrt und im Wortlaut protokolliert (`docs/install-check.md`, Abschnitt "Die Abnahme, 07.09.2026"). Es gibt keinen weiteren Punkt, der zwingend eine erneute menschliche Pruefung braucht, bevor Plan 06-12 beginnen kann.

### Gaps Summary

Der einzige gefundene Gap ist **kein** Kern-Blocker fuer den Store-Weg: Die ausgelieferten, gegateten Artefakte (beide `info.xml`, `deploy-harp.yml`-Matrix, `README.md`) tragen durchgaengig und korrekt das Fenster NC 33-35, mit einem CI-Gate, das beide Haelften zusammenhaelt. Was fehlt, ist die Nachfuehrung von **zwei der fuenf Stellen, die die Owner-Entscheidung E-H1 selbst als gemeinsam zu aendernd benannt hat**: `CLAUDE.md` und `.planning/REQUIREMENTS.md` (PKG-03) zeigen weiterhin das alte Fenster NC 32-34/35. Das ist in der Phase selbst ehrlich als offener Befund dokumentiert (`deferred-items.md`, DI-06.1-03, gefunden in Plan 06.1-09), aber der dort selbst vorgeschlagene Zielort (Plan 06.1-19, der die ROADMAP wegen E-H1 ohnehin oeffnet) hat ihn nicht aufgegriffen, und keiner der Plaene 10 bis 24 hat DI-06.1-03 geschlossen oder auch nur erneut erwaehnt. Das Repository widerspricht damit an zwei gut sichtbaren Stellen (dem eigenen Projektgedaechtnis CLAUDE.md und der Anforderungs-Traceability) seiner eigenen ausgelieferten Zusage.

Da dies eine reine Dokumentationsinkonsistenz ohne funktionale Wirkung ist (kein Gate, kein Nutzerpfad, keine Store-Zusage haengt an CLAUDE.md oder REQUIREMENTS.md), ist es als WARNING/kleiner Gap und nicht als Blocker fuer Plan 06-12 einzustufen. Es sollte aber vor oder waehrend Plan 06-12 (der die Store-Texte ohnehin nochmal anfasst) in einem kleinen Schritt geschlossen werden, damit die Owner-Entscheidung E-H1 nicht dauerhaft nur zu drei Fuenfteln umgesetzt bleibt.

Alle uebrigen offenen DIs am Ende der Phase (DI-06.1-23, -25, -26, -28, -32, -33, -36, -37, -38) sind vom Orchestrator selbst als klein, benannt und laut Owner-Entscheiden nicht abgabeblockierend eingestuft; die Verifikation hat dafuer keine gegenteilige Evidenz gefunden. DI-06.1-31 und DI-06.1-34 (die zwei aus der Sichtprobe uebernommenen Befunde 8 und 9) sind ueber Plan 06.1-24 nachweislich geschlossen (Code + Tests vorhanden, CI gruen auf 688eef7).

---

*Verified: 2026-09-07T18:00:00Z*
*Verifier: Claude (gsd-verifier)*
