---
phase: 11-haertung-und-store-einreichung-v1-1
verified: 2026-09-11T09:53:23Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
deferred:
  - truth: "DI-10-02/DI-11-01: Sprachfall-Vorpruefung misst den Bestand hinter dem Antwortdeckel, nicht nur den Deckel selbst"
    addressed_in: "v1.2-Haertung (auesserhalb der v1.1-Roadmap, dokumentiert in deferred-items.md)"
    evidence: "docs/audits/2026-09-phase-11/README.md, L-08: 'DI-10-02 bleibt offen, DI-11-01 wird mit ihm zusammengelegt... Ziel: ein eigener Plan ohne Box, in der v1.2-Haertung'"
  - truth: "DI-10-04: Ursache der Mehrlaufzeit des Volllaufs bewiesen statt eingegrenzt"
    addressed_in: "v1.2-Messplanung"
    evidence: "deferred-items.md DI-10-04: 'Wohin es gehoert: die v1.2-Messplanung, zusammen mit dem Box-Wiederaufbau-Runbook'"
  - truth: "DI-11-02/DI-11-03/DI-11-05/DI-11-06: Messwerkzeug- und Protokollfeinheiten der Lastreihen"
    addressed_in: "v1.2-Messplanung / v1.2-Haertung"
    evidence: "deferred-items.md, jeweils mit Zieladresse 'naechster Box-Lauf' bzw. 'v1.2-Haertung'"
---

# Phase 11: Haertung und Store-Einreichung v1.1 -- Verification Report

**Phase Goal:** v1.1 steht als signiertes App-Paar im Nextcloud App Store, nachdem es jenseits des Happy Path getestet wurde und der Owner die Texte abgenommen hat.
**Verified:** 2026-09-11T09:53:23Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (5 Success Criteria aus ROADMAP.md)

| # | Truth (Success Criterion) | Status | Evidence |
|---|---|---|---|
| 1 | Beide Apps tragen dieselbe Version 1.1.0, sind signiert, und eine frische Nextcloud installiert sie aus den Release-Artefakten auf amd64 und arm64 und findet ohne Handgriff Inhalte | VERIFIED | Tag `v1.1.0` auf Commit `891bc6d` (`git log -1 891bc6d`, per `git tag -l` bestaetigt). `gh release view v1.1.0` zeigt genau 4 Assets: `findling.tar.gz` (282.432 B), `findling.tar.gz.sig`, `findling_backend.tar.gz` (28.524 B), `findling_backend.tar.gz.sig`. Release-Lauf `34573687101` gruen ("Build, sign and size check both archives"). HaRP-Lauf `34571130221` alle vier Aeste gruen: `stable34`/amd64, `stable35`/amd64 (tolerate-failure), `stable33`/amd64, **`stable34`/`ubuntu-24.04-arm`**. `php/appinfo/info.xml` und `backend/appinfo/info.xml` beide `<version>1.1.0</version>`, `<image-tag>1.1.0</image-tag>` identisch. Release-Asset-Modus in `deploy-harp.yml` (`RELEASE_TAG`/`release_tag`-Input) live gepruewft (Zeilen 52, 289, 1467ff). |
| 2 | Ein Upgrade von 1.0.x auf 1.1.0 laesst den bestehenden Index unangetastet oder verlangt sichtbar einen Reindex; kein stiller Verlust von Indexinhalt | VERIFIED | HaRP-Lauf `34571130221`, Job `stable34`/amd64, Schritt "Store upgrade 4": Log-Zeile `installed_version went from 1.0.3 to 1.1.0` (per `gh run view --log`, selbst nachgezaehlt). Kanariensuche nach dem Upgrade: `"the container after the upgrade answers the canary search"` (1 Treffer, `entries[0].title == "findling-canary"`). **Echter Produktfehler gefunden und behoben:** Migration `php/lib/Migration/Version001100Date20260911000000.php` existiert im Baum (mit begleitendem Unit-Test `Version001100Date20260911000000Test.php`) und dokumentiert im Klassenkommentar den Befund wortgleich mit der Owner-Vorlage ("thirty canary searches came back empty with companion 1.1.0, backend 1.0.3"). Der Fix verwirft die veraltete Versionsmarke statt sie zu raten. DI-11-06 (Fenster zwischen Update und erstem Aufruf der Einstellungsseite) bleibt offen mit Zieladresse v1.2 -- dokumentierte Absicht, kein Gap. |
| 3 | Security-, Bug- und Performance-Audit erneut gefahren, alle Befunde ab MEDIUM gefixt, LOW dokumentiert entschieden | VERIFIED | `docs/audits/2026-09-phase-11/README.md` gelesen (vollstaendig, 1113 Zeilen): Frontmatter `critical: 0, high: 0, medium: 1, low: 11`. Der einzige MEDIUM-Befund M-01 (DI-07-03) ist mit Belegstelle `11-13-SUMMARY.md` und sieben Commits als geschlossen dokumentiert ("Status: geschlossen. Der Befund ist... gebaut."). Alle 11 LOW-Befunde einzeln mit Verdikt: 2 in diesem Lauf behoben (L-05, L-06 -- Commits `ab39d37`, `2e8502b`), 4 hingenommen (L-01 bis L-04), 5 dokumentiert weitergereicht (L-07 bis L-11), jeweils mit Zieladresse. Backend-Testsuite live nachgefahren: `uv run python -m pytest -q` in `backend/` = **2026 passed, 15 skipped** (Audit-Zeitpunkt meldete 2020/15 -- Differenz durch spaeter hinzugekommene Tests aus Plan 11-11/11-12 plausibel, kein Widerspruch). Franzoesische Katalog-Gates separat nachgefahren: `pytest -k "french or catalogue"` = 21 passed. Keine TBD/FIXME/XXX/PLACEHOLDER-Marker in den 15 durch die Phase im Companion-Paket geaenderten PHP-Dateien gefunden (eigener Grep). |
| 4 | Store-Texte sind kurze Faktenlisten nach der Kurztext-Regel, Owner-Entwurf vor Einreichung gesehen und abgenommen | VERIFIED | `docs/store-listing.md` Zeile 476 traegt die Abnahmezeile: "Textabnahme: 2026-09-11, Fassung B, Messsatz dreisprachig, FR-Gate Teil 2 von 2 abgenommen (D-06, D-07, D-08)". `docs/l10n-french.md` Zeile ~336: "FR-Gate abgenommen: 2026-09-11, Teil 1 von 2 (Katalog), D-07", vollstaendig gegengelesen (173 Zeilen, 174 Schluessel, ohne Korrektur). Owner-Nachtrag "Angebot anfordern" nachgewiesen per `git show fb371a0` (Kontakt eingebaut in Store-Text + 3 READMEs) und `git show eba04b1` ("Owner-Abnahme vom 11.09.2026... ohne Aenderung eingebaut"). FR-Katalog-Vorbedingung erfuellt: `php/l10n/fr.json`/`fr.js` je 174 Schluessel (`node`-Vergleich gegen `de.json`: gleiche Schluesselzahl, `Findling`-Schluessel vorhanden), 4 Gates (`test_all_six_catalogues_carry_the_same_keys`, `test_every_french_value_carries_a_french_wording`, `test_no_french_value_loses_or_invents_a_placeholder`, `test_the_french_catalogues_carry_the_french_plural_rule`) live gruen. |
| 5 | v1.1 ist eingereicht, und die Release-Artefakte im Repo entsprechen dem Eingereichten | VERIFIED | Store-Submit-Lauf `34573857157` gruen, Log zeigt woertlich: `release findling v1.1.0: HTTP 201` und `release findling_backend v1.1.0: HTTP 201` (per `gh run view --log` selbst nachgezaehlt, nicht nur SUMMARY geglaubt). `docs/store-listing.md` Zeile 480-497 traegt die Belegzeile mit Tag/Lauf-IDs identisch zu den nachgepruewften Werten und nennt explizit, dass die Store-Seiten (`apps.nextcloud.com/apps/findling`, `.../findling_backend`) "beide 1.1.0" nennen. REL-01 in `.planning/REQUIREMENTS.md` als `[x]` und in ROADMAP-Progress-Tabelle als "Complete" gefuehrt. |

**Score:** 5/5 truths verified

### Deferred Items

Bewusst offen gelassene Befunde, die als dokumentierte Absicht und nicht als Luecke gelten (Owner-/Audit-Entscheid, jeweils mit Zieladresse belegt):

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | DI-10-02 / DI-11-01: Sprachfall-Vorpruefung misst Antwortdeckel (exakt 26 Treffer unabhaengig von Tiefe/Begriff), nicht den tatsaechlichen Fremdbestand | v1.2-Haertung | Audit L-08: "DI-10-02 bleibt offen... Ziel: ein eigener Plan ohne Box, in der v1.2-Haertung" |
| 2 | DI-10-04: Mehrlaufzeit des Volllaufs (+40,6%) eingegrenzt, nicht ursaechlich bewiesen | v1.2-Messplanung | Audit L-07 / deferred-items.md: "Wohin es gehoert: die v1.2-Messplanung, zusammen mit dem Box-Wiederaufbau-Runbook" |
| 3 | DI-11-02 (leere Antwort ohne Protokollspur), DI-11-03 (Zaehler unterscheidet leer nicht von abgebrochen), DI-11-05 (pgsql-Ast flattert, per Rerun 34555358815 gruen bestaetigt), DI-11-06 (Suche kennt Containerversion nur vom Hoerensagen) | v1.2-Messplanung / v1.2-Haertung | deferred-items.md, je mit Verdikt und Zieladresse; DI-11-06 zusaetzlich in 11-11-SUMMARY.md als "nicht in dieser Phase, Zieladresse v1.2" |

Diese Punkte beruehren kein Success Criterion negativ (Kriterium 3 verlangt "LOW dokumentiert entschieden", nicht "LOW behoben") und wurden deshalb nicht als Gaps gezaehlt.

### Required Artefakte (Stichprobe gegen echte Belege)

| Artefakt | Erwartung | Status | Details |
|---|---|---|---|
| Tag `v1.1.0` | zeigt auf finalen Bump-Commit | VERIFIED | `891bc6d2c17f324e01894dc5ada398bae63c5e9d`, `git log -1 891bc6d` bestaetigt |
| GitHub Release v1.1.0 Assets | genau 4 signierte Assets | VERIFIED | `gh release view --json assets` liefert exakt 4 Eintraege wie erwartet |
| `php/appinfo/info.xml`, `backend/appinfo/info.xml` | `<version>1.1.0</version>`, `<image-tag>1.1.0</image-tag>` | VERIFIED | per `grep` selbst gelesen |
| `php/lib/Migration/Version001100Date20260911000000.php` | echter Fix fuer den gefundenen Upgrade-Bug | VERIFIED | Datei existiert, Klassenkommentar dokumentiert Befund und Fix-Logik, begleitender Unit-Test vorhanden |
| `php/l10n/fr.json`, `php/l10n/fr.js` | 174 Schluessel je, inkl. `Findling` | VERIFIED | `node`-Skript: 174 == 174, `Findling` vorhanden |
| `docs/audits/2026-09-phase-11/README.md` | 0/0/1/11 Befunde, alle mit Verdikt | VERIFIED | Volltext gelesen (1113 Zeilen), Frontmatter und Bilanztabelle stimmen ueberein |
| `docs/store-listing.md`, `docs/l10n-french.md` | Abnahmezeilen vorhanden | VERIFIED | beide Belegzeilen an den genannten Stellen gefunden |
| `.github/workflows/store-submit.yml` | fuehrt die Einreichung aus | VERIFIED | Datei existiert, Lauf 34573857157 nutzt sie erfolgreich |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `deploy-harp.yml` (Upgrade-Block) | GitHub Release v1.0.3 Assets | `RELEASE_TAG`/Download ohne Fallback | WIRED | Live im Log bestaetigt: `UPGRADE_FROM_TAG: v1.0.3` durchgehend, `installed_version went from 1.0.3 to 1.1.0` |
| Migration `Version001100Date...` | `oc_appconfig.backend_app_version` | verwirft veraltete Marke statt sie zu erben | WIRED | Klassenkommentar + Test-Datei vorhanden, Verhalten im HaRP-Lauf beobachtet (Kanariensuche nach Upgrade liefert Treffer) |
| `store-submit.yml` | `apps.nextcloud.com/api/v1/apps/releases` | POST mit Release-Download-URL + Signatur | WIRED | Log zeigt 2x HTTP 201 fuer beide Haelften |
| `fr.json`/`fr.js` | Katalog-Gates (`test_all_six_catalogues_carry_the_same_keys` etc.) | pytest in `backend/tests/test_admin_ui_contract.py` | WIRED | live ausgefuehrt, 21 passed |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Release-Assets vollstaendig und signiert | `gh release view v1.1.0 --json assets` | 4 Assets (2 Archive, 2 Signaturen) | PASS |
| HaRP-Lauf 4 Aeste gruen | `gh run view 34571130221` | alle 4 Jobs success | PASS |
| Store-Submit HTTP 201 x2 | `gh run view 34573857157 --log` | `HTTP 201` fuer findling und findling_backend | PASS |
| Upgrade-Beweis ohne stillen Verlust | `gh run view 34571130221 --log` (grep) | `installed_version went from 1.0.3 to 1.1.0`, Kanariensuche danach 1 Treffer | PASS |
| Backend-Testsuite | `uv run python -m pytest -q` (backend/) | 2026 passed, 15 skipped | PASS |
| FR-Katalog-Gates | `pytest -k "french or catalogue"` | 21 passed | PASS |
| Debt-Marker in Phasen-PHP-Dateien | grep TBD/FIXME/XXX/PLACEHOLDER ueber 15 geaenderte php/-Dateien | keine Treffer | PASS |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh`-Dateien fuer diese Phase deklariert oder konventionell vorhanden. Die CI-Laeufe (HaRP deploy, Release, Store-Submit) uebernehmen die Funktion der Probes und wurden unter "Behavioral Spot-Checks" live gegengeprueft. SKIPPED (keine formalen Probe-Skripte im Sinn von Schritt 7c).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| REL-01 | 11-01 bis 11-13 (alle 13 Plaene) | v1.1 im Nextcloud App Store eingereicht (signiert, Store-Texte nach Kurztext-Regel, Owner-Abnahme) | SATISFIED | Alle 5 Erfolgskriterien verifiziert, `REQUIREMENTS.md` und `ROADMAP.md` fuehren REL-01 als "Complete"/`[x]` |

Keine Waisen: `ROADMAP.md` "Requirement Coverage"-Tabelle weist Phase 11 genau 1 Requirement zu (REL-01), und alle 13 Plaene deklarieren `requirements: [REL-01]` -- keine zusaetzliche Kennung in `REQUIREMENTS.md` fuer Phase 11 gefunden.

### Anti-Patterns Found

Keine. Grep nach `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` ueber alle 17 durch die Phase (seit `721bde6`) unter `php/` geaenderten Dateien liefert null Treffer. Kein Debt-Marker-Blocker.

### Human Verification Required

Keine. Alle fuenf Erfolgskriterien sind gegen Live-CI-Laeufe (`gh run view`, `gh release view`), gegen den Arbeitsbaum (info.xml, Migration, Katalogdateien) und gegen eine live nachgefahrene Testsuite verifiziert worden, nicht nur gegen SUMMARY-Behauptungen.

### Gaps Summary

Keine Gaps. Alle 5 Success Criteria aus ROADMAP.md sind mit eigenstaendig reproduzierten Belegen (nicht nur SUMMARY-Zitaten) verifiziert:

1. Tag, Release-Assets, Signaturen und die vier-Aeste-CI-Matrix (inkl. natives arm64) existieren und sind gruen.
2. Der Upgrade-Pfad 1.0.3 -> 1.1.0 ist Ende-zu-Ende im CI-Log nachgewiesen; der dabei gefundene echte Produktfehler (stumme Suche nach Minor-Upgrade) ist durch eine dokumentierte, getestete Migration behoben.
3. Der Audit-Bericht ist vollstaendig gelesen und stimmt mit der behaupteten Bilanz (0/0/1/11) ueberein; die Testsuite laeuft live gruen.
4. Beide Owner-Abnahmen (Store-Text Fassung B / FR-Gate Teil 2, FR-Katalog Teil 1) sind an den genannten Stellen vorhanden, ebenso der spaetere Owner-Nachtrag "Angebot anfordern" mit Abnahme-Commit.
5. Die Store-Submission ist per Live-Log mit zwei HTTP-201-Antworten belegt, und die eingereichten Release-Assets entsprechen den vier im Repo/Release vorhandenen signierten Archiven.

Die dokumentierten offenen Punkte (DI-10-02/DI-11-01, DI-10-04, DI-11-02/03/05/06) sind explizit als "nicht diese Phase, sondern v1.2" entschieden und tragen jeweils eine Zieladresse -- das ist die vom Auftrag verlangte Behandlung ("KEINE LUECKEN, SONDERN DOKUMENTIERTE ABSICHT") und wurde entsprechend als `deferred`, nicht als `gap`, gefuehrt.

---

*Verified: 2026-09-11T09:53:23Z*
*Verifier: Claude (gsd-verifier)*
