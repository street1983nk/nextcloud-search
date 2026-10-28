---
phase: 33-ausschlussmuster-und-admin-feinschliff
verified: 2026-10-19T00:00:00Z
status: passed_with_conditions
score: 5/5 Erfolgskriterien verifiziert, 5/5 Anforderungen erfüllt
overrides_applied: 0
deferred:
  - truth: "Der Tag-Link des Grenzblocks (blob/v1.5.0/docs/admin-page.md#limits-per-file) liefert heute 404"
    addressed_in: "Phase 36"
    evidence: "Tag v1.5.0 entsteht erst mit der Einreichung; blob/main desselben Abschnitts liefert 200 mit Anker (33-10-ABNAHME Probe 4)"
  - truth: "Store-Text trägt noch das Wort 'box' (php/appinfo/info.xml, backend/appinfo/info.xml, docs/store-listing.md)"
    addressed_in: "Phase 36"
    evidence: "deferred-items.md Plan 33-07; Phase 36 SC3 (Owner-Abnahme Store-Text, REL-05)"
  - truth: "LOW-accept L-33-02, L-33-03, L-33-05, L-33-06 und Owner-Fragen F1 bis F3"
    addressed_in: "Phase 36"
    evidence: "33-AUDIT.md LOW-Entscheidungen, Zielphase 36 (Launch-Korpus)"
  - truth: "SubtreeExpandJob nach geleertem Papierkorb (Could not fetch storage root), Fund aus Zeile e3de49a2, nicht im Diff der Phase"
    addressed_in: "Phase 36"
    evidence: "deferred-items.md Plan 33-11"
---

# Phase 33: Ausschlussmuster und Admin-Feinschliff, Verifikationsbericht

**Phasenziel:** Admins können Pfade per Platzhalter ausschließen (inklusive Mac-Bundles aus #22) und sehen die wirksamen Grenzwerte auf der Admin-Seite
**Verifiziert:** 2026-10-19
**Status:** passed_with_conditions
**Re-Verifikation:** Nein, Erstverifikation
**Stand:** main, HEAD af9a7a86. Seit dem letzten Code-Commit 3657bb43 (Stand aller acht CI-Workflows) hat sich außerhalb von `.planning/` nur `docs/admin-page.md` geändert (`git diff --name-only 3657bb43..af9a7a86`, Doku-Präzisierung L-33-03). Die Dependabot-Merges 9b402212 und 0514ae62 danach gehören nicht zur Phase; der rote Lauf "Python gates" auf 08749a1d ist ein Dependabot-Bump derselben Nachphase und nicht Gegenstand.

## Zielerreichung

### Beobachtbare Wahrheiten (ROADMAP-Erfolgskriterien)

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| 1 | SC1 / EXCL-01: Admin pflegt Muster wie `*.photoslibrary` oder `*/node_modules/*`; Präfix-Ausschlüsse aus 1.4.2 wirken unverändert weiter | VERIFIED | `php/lib/Service/ExclusionService.php` (1350 Zeilen): eigener Matcher, "Shift-And with self loops for the stars" (Z. 884), eine Liste `exclusion_patterns` neben der unveränderten `exclusions`. `hasRules()` (Z. 756) an allen drei Guards: `ExclusionSweepJob.php:150`, `ReconcileController.php:334`, `FileEventListener.php:444` (plus `QueueService.php:889`). Präfixliste in der Abnahme unverändert `["Archiv"]` neben dem neuen Muster (33-10-ABNAHME Probe 2); Fixture von 1.4.2 im Treiber `backend/tests/drivers/exclusion_driver.php` (33-AUDIT). Admin-Seite: Liste "Excluded patterns" in de/en/fr gesichtet und vom Owner abgenommen (33-10 Probe 1, "abgenommen" 18.10.2026) |
| 2 | SC2 / EXCL-02: Mit einer Regel verschwindet ein Mac-Bundle-Ordner komplett aus dem Index, auch bereits indexierte Treffer | VERIFIED | Weg A: `ExclusionSweepJob::clear()` (Z. 291-310) reiht in EINER Transaktion `KIND_DELETE` ein und löscht die Urteilszeilen (`forgetVerdicts`), also verschwinden Treffer und Kacheln. Weg C: Abgleich im Container (33-03, eff4a9bf). 33-09-NACHWEIS auf 8090 mit Positivkontrolle und Gegenprobe (Gegenprobe-Worktree vor 33-03 zeigt das alte Verhalten). 33-10 Probe 2: `*.photoslibrary` gespeichert, nach cron.php P 0 Treffer, Kontrolle Q weiter 1 Treffer, Unified Search im Browser leer für das Bundle; Probe 8: neue Datei im Bundle wird nie eingereiht |
| 3 | SC3 / EXCL-03: Ausgeschlossenes erscheint als "excluded", nie als Fehler; zu viele, zu lange oder Regex-artige Eingaben werden verständlich abgelehnt, kein ReDoS | VERIFIED | Diagnose: Chip "Ausgeschlossen", `skipped` / `excluded`, Abhilfe nennt beide Listen (33-10 Probe 7 in de/en/fr; `occ findling:diagnose 3018`); Kachel stieg 3 auf 4, Fehlerliste ohne Bundle-Einträge (Probe 8). Ablehnung: Grenzen 32 Muster, 60 Zeichen, Codes `empty`, `too_long`, `too_many`, `duplicate`, `traversal`, `double_star`, `unsupported_character`, `negation`, `control_character`, `no_literal`, `no_wildcard`; Audit-Ablehnungskorpus 65 Fälle, nie 5xx nach Fix (33-AUDIT S2). Kein ReDoS: Matcher ohne `fnmatch`, `eval`, Regex; in `ExclusionService.php` kommt `preg_` nur einmal vor (`trimmed()`, Z. 1295, Schrägstriche falten), `fnmatch` und `eval(` gar nicht (grep); Orakel-Korpus 2593 Paare, 0 Abweichungen auf der Laufzeit der Instanz (33-AUDIT S1); Performance-Messungen in 33-AUDIT Abschnitt Performance |
| 4 | SC4 / POL-01: Zellgrenze, Adressraum, Größengrenze, OCR-Seitendeckel nur lesend mit Änderungshinweis (#21) | VERIFIED | Container liefert `maxCells` und `extractAddressSpaceBytes` (`backend/src/findling/api/status.py:316-317`, `:581-582`, `:715-716`). Grenzblock "Limits per file": vier Zeilen mit Werten und Variablennamen, Hinweis mit `occ app_api:app:unregister findling_backend` als code, Link auf `docs/admin-page.md#limits-per-file`, 0 Eingabeelemente (33-10 Probe 4, de/en/fr). Doku-Anker vorhanden: `docs/admin-page.md:978` `<a id="limits-per-file">`, Überschrift "Grenzen je Datei ändern"; `blob/main`-URL HTTP 200 mit genau einem Anker. Alter AppAPI-Satz im Feld "Largest file to read" ersetzt (Probe 5) |
| 5 | SC5 / POL-03: Hardware-Hinweis in allen Katalogen verständlich umformuliert, Katalog-Gates grün | VERIFIED | `grep "This box has fewer"` in `php/`, `backend/src`, `docs`: 0 Treffer. Neuer Satz "Findling sees fewer CPU cores or less memory than this profile requires. Standard requires at least 3 cores and 6 GB ..." in `php/l10n/fr.json` übersetzt. Alle acht `.json` tragen 340 Schlüssel (Zählung per Skript), alle acht `.js` 340 Zeilen plus Kopf. fr-Einheiten `B/KB/MB/GB/TB/PB` = `o/Ko/Mo/Go/To/Po` in `fr.json`; der Satz zu 50 MB sagt "Mo". Katalog-Gates in CI "PHP and store metadata gates" 39189895915 success, "Python gates" 39189895896 success |

**Score:** 5/5 Erfolgskriterien verifiziert

### Weitere geprüfte Wahrheiten

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| 6 | Eine Nicht-Liste an der Regelroute ergibt 400 mit Code statt HTTP 500 (H-33-01) | VERIFIED | `SettingsController.php:484-486` (`listOf()` gibt bei `!is_array` die Codeliste `ERROR_EMPTY` zurück), Fix ff4deaa9; Regressionstest im Audit-Test |
| 7 | Ein Musterschlüssel anderen Typs ist eine leere Liste und hält Listener, Seite und Übersicht nicht an (H-33-02) | VERIFIED | Fix 3657bb43; Zweitschreiber-Probe S3 in 33-AUDIT |
| 8 | Wortlaut vom Owner abgenommen, keine Selbstabnahme | VERIFIED | `33-WORTLAUT.md` Z. 4: "vom Owner abgenommen am 13.10.2026"; `33-10-ABNAHME.md` Z. 210: "Owner-Abnahme: 18.10.2026, ... abgenommen" (nach Fix fr "Mo überall" und Sichtprobe) |
| 9 | Audit abgeschlossen: Befunde HIGH gefixt, LOW entschieden, kein `xfail` | VERIFIED | `33-AUDIT.md` Kopf: `status: fixed`, `fixed: [H-33-01, H-33-02]`, `still_open` nur L-33-01 bis L-33-06 (alle LOW, mit Entscheidung und Zielphase); `grep -c xfail backend/tests/test_phase33_audit.py` = 0 |
| 10 | Debt-Marker-Gate | VERIFIED | Keine TBD/FIXME/XXX in den für diese Phase genannten Dateien gefunden; offene Punkte stehen nur in `deferred-items.md` mit Phasenzuordnung |

### Zurückgestellte Punkte (kein Lückenbefund)

| # | Punkt | Adressiert in | Beleg |
|---|---|---|---|
| 1 | Tag-Link des Grenzblocks bis v1.5.0 tot | Phase 36 | Tag entsteht bei der Einreichung; main-Link lebt |
| 2 | Store-Text mit "box" | Phase 36 | deferred-items.md, REL-05 |
| 3 | LOW L-33-02, -03, -05, -06 samt Owner-Fragen F1 bis F3 | Phase 36 | 33-AUDIT.md |
| 4 | SubtreeExpandJob nach geleertem Papierkorb | Phase 36 | deferred-items.md |

### Erforderliche Artefakte

| Artefakt | Erwartet | Status | Details |
|---|---|---|---|
| `php/lib/Service/ExclusionService.php` | Matcher, Codes, NFC, hasRules | VERIFIED | 1350 Zeilen, wired an Controller, Job, Listener, QueueService |
| `php/lib/Controller/SettingsController.php` | zwei Listen, 400 bei Nicht-Liste | VERIFIED | `listOf()` Z. 484 |
| `php/lib/BackgroundJobs/ExclusionSweepJob.php` | Kehrjob Weg A | VERIFIED | `clear()` mit Transaktion, Urteilszeilen gelöscht |
| `php/l10n/*.json` und `*.js` | 340 Schlüssel, 16 Kataloge | VERIFIED | Zählung per Skript |
| `backend/tests/test_phase33_audit.py` | Audit-Regression ohne xfail | VERIFIED | 0 xfail |
| `docs/admin-page.md` | Anker `limits-per-file` | VERIFIED | Z. 978 |
| 33-01 bis 33-11 PLAN und SUMMARY, 33-WORTLAUT, 33-CONTEXT, 33-09-NACHWEIS, 33-10-ABNAHME, 33-AUDIT, deferred-items | vollständig | VERIFIED | Verzeichnis geprüft, alle 22 Plan/Summary-Dateien vorhanden |

### Verhaltens-Stichprobe und CI

| Prüfung | Befehl | Ergebnis | Status |
|---|---|---|---|
| Gate D und Audit-Test lokal | `uv run python -m pytest -q -p no:randomly tests/test_exclusion_path_space.py tests/test_phase33_audit.py` | 0 Fehler; ein Teil grün, der Großteil übersprungen, weil lokal weder Docker-Treiber noch Instanz 8090 verfügbar sind (Skip-Gründe im Modul) | PASS mit Einschränkung |
| CI auf 3657bb43 | `gh run list --commit 3657bb43` | alle 8 Workflows success: Integration 39189895884, HaRP deploy 39189895882, Python gates 39189895896, PHP and store metadata gates 39189895915, Resilience 39189895905, Multi-arch image 39189895922, Security scans 39189895934, OpenSSF Scorecard 39189895921 | PASS |
| CI auf 417d9a2c | Doku-/Testlauf | Security scans 39192390285, OpenSSF Scorecard 39192390276 success | PASS |
| CI auf af9a7a86 | Doku-Lauf | Security scans 39193659442, OpenSSF Scorecard 39193659431 success | PASS |

### Anforderungsabdeckung

| Anforderung | Quelle | Status | Beleg |
|---|---|---|---|
| EXCL-01 | 33-02, 33-05 | SATISFIED | SC1; `REQUIREMENTS.md:24` `[x]`, Traceability Zeile 91 Complete |
| EXCL-02 | 33-03, 33-04, 33-09 | SATISFIED | SC2; `REQUIREMENTS.md:25` `[x]`, Zeile 92 Complete |
| EXCL-03 | 33-02, 33-05, 33-11 | SATISFIED | SC3; `REQUIREMENTS.md:26` `[x]`, Zeile 93 Complete |
| POL-01 | 33-03, 33-06 | SATISFIED | SC4; `REQUIREMENTS.md:45` `[x]`, Zeile 103 Complete |
| POL-03 | 33-07 | SATISFIED | SC5; `REQUIREMENTS.md:47` `[x]`, Zeile 105 Complete |

Keine verwaiste Anforderung: REQUIREMENTS.md ordnet Phase 33 genau diese fünf IDs zu.

### Anti-Muster

Keine Blocker. Info: `backend/.coverage` liegt unversioniert im Arbeitsbaum (Testartefakt, nicht Teil der Phase).

### Bedingungen

1. **Tag-Link tot bis v1.5.0:** Der Link im Grenzblock zeigt auf `blob/v1.5.0/...`, das erst mit dem Tag der Phase 36 auflöst. Die Zielseite ist über `blob/main` belegt. Vor der Einreichung prüfen.
2. **Hardware-Satz nicht live ausgelöst:** `hardware_short` ließ sich auf 8090 (Windows-Backend meldet keinen Speicher, Urteil `memory_unknown`) und 8096 (HaRP-Backend nicht verbunden) nicht an der Instanz zeigen (33-10 Probe 6). Der Satz ist über Katalog, Wortlaut-Tabelle F und die grünen Katalog-Gates belegt, der Owner hat den Wortlaut abgenommen. Ein Live-Beleg wäre in der Phase-36-Härtung auf einer Maschine mit gemeldeter Hardware nachzuholen.
3. **LOW-Entscheidungen in der Nacht ohne Owner:** L-33-01 bis L-33-06 wurden nach Entscheidungslinie des Orchestrators als accept entschieden, der Owner kann sie überstimmen (F1 bis F3 offen, keine blockiert).
4. **Lokaler Lauf nur teilweise:** Die schweren Audit-Proben (Docker, Instanz) sind in dieser Verifikation nicht neu gelaufen; Beleg sind die Audit-Protokolle, die Abnahmeprotokolle und die grüne CI auf 3657bb43.
5. **ROADMAP Zeile 85:** Die Phasenübersicht trägt Phase 33 noch als `[ ]`, während die elf Plan-Zeilen und REQUIREMENTS `[x]` sind. Der Orchestrator hakt beim Abschluss ab.

### Lücken-Zusammenfassung

Keine Lücke, die das Phasenziel verfehlt. Alle fünf Erfolgskriterien sind am Code und an den Abnahme- und Auditprotokollen belegt, die Bedingungen sind Vorwärtspunkte für Phase 36.

---

_Verifiziert: 2026-10-19_
_Verifier: Claude (gsd-verifier)_
