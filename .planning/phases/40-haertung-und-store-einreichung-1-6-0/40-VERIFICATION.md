---
phase: 40-haertung-und-store-einreichung-1-6-0
verified: 2026-10-29T12:10:57Z
status: gaps_found
score: 3/5 Kriterienblöcke verifiziert (SC2, SC3, SC4 voll; SC1 teilweise; Restpunkte teilweise)
tag: v1.6.0
tag_head: 91a0603f2b69213037c0d8ac2101121f9ba767b2
overrides_applied: 0
gaps:
  - truth: "SC1: Das Audit-Gate der Phase (Security/Bugs/Performance über alle v1.6-Änderungen, mit Zertifikats- und Dedup-Randpfaden) endet mit 0 CRIT / 0 HIGH / 0 MEDIUM"
    status: partial
    reason: "40-AUDIT.md (audited 2026-10-28) prüft v1.5.1..336ccae7, Code-Kopf efcf26c5. Danach kamen 10 Produkt-Commits mit 570 Einfügungen und 54 Löschungen in 11 Dateien (git diff --stat efcf26c5 91a0603f -- backend/src php/lib php/js php/templates) in 1.6.0, die kein Audit-Gate gesehen haben: Migration Version001600 (40-02), das Issue-#36-Paket aus 40-06 (poller.py, client.py, writer.py, resources.py, status.py, GatewayController.php, SearchService.php, AdminViewService.php, admin.php, admin.js) und der Nachtrag 991b1eff (Eskalation ohne Gutschrift), der nach 40-06-VERIFICATION.md kam und von keiner unabhängigen Prüfung erfasst ist. 40-06-VERIFICATION.md ist eine Funktionsprüfung des Plans und kein Security/Bugs/Performance-Audit. Die Owner-Vorlage Block D nennt den Auditumfang offen, das Owner-GO ist aber keine Abnahme eines Audits für diese Änderungen."
    artifacts:
      - path: ".planning/phases/40-haertung-und-store-einreichung-1-6-0/40-AUDIT.md"
        issue: "Umfang endet bei 336ccae7/efcf26c5, 40-02-Migration und 40-06 inklusive Nachtrag fehlen"
    missing:
      - "Nachaudit Security/Bugs/Performance über efcf26c5..91a0603f (Produktcode), Schwerpunkte: SearchService catch StorageNotAvailableException (fail-closed bestätigen), GatewayController 422-Log, _RefusalsPiledUp/_abort charged (Budget, Lock-Timeout, Starvation), Fill-Refresh-Thread in resources.py, Version001600-Migration"
      - "Befunde ab MEDIUM als 1.6.1 einplanen, LOW dokumentiert entscheiden; Ergebnis als Nachtrag in 40-AUDIT.md"
      - "Alternativ: Owner-Override (siehe Abschnitt Gaps Summary)"
  - truth: "Offene Restpunkte sind in STATE.md bzw. deferred-items.md als deferred erfasst"
    status: partial
    reason: "Zwei der fünf Punkte stehen nur in 40-OWNER-VORLAGE.md (Abschnitt Nach dem Release), 40-ABNAHME.md G2 und 40-06-SUMMARY.md, aber weder in .planning/STATE.md noch in deferred-items.md: (a) Anzeige-Satz D unscharf bei Häufungs-Eskalation (v1.7), (b) Endverdikt gateway_error statt repeatedly_stuck nach erschöpftem Budget (v1.7). Auch der Kaltstart-Satz G1 steht nur dort."
    artifacts:
      - path: ".planning/STATE.md"
        issue: "Deferred Items und Operator Next Steps ohne Satz D und ohne Endverdikt gateway_error"
      - path: ".planning/phases/40-haertung-und-store-einreichung-1-6-0/deferred-items.md"
        issue: "nur Tombstones/F-40-06 und Issue-#36-Befund, keine v1.7-Merkliste aus 40-04"
    missing:
      - "deferred-items.md (oder STATE.md Deferred Items): Satz D Unschärfe -> v1.7, Endverdikt gateway_error statt repeatedly_stuck -> v1.7, Kaltstart-Satz G1 -> v1.7"
      - "Nebenbei: STATE.md Operator Next Steps und docs/store-listing.md Beleg (12) sagen noch 'Nachführung offen' für appapi_apps.json, der Katalog führt findling_backend 1.6.0 inzwischen (Abruf 12:10Z)"
---

# Phase 40: Härtung und Store-Einreichung 1.6.0, Verifikationsbericht

**Phasenziel:** Findling 1.6.0 ist gehärtet, die Upgrade-Strecke ab 1.5.x ist bewiesen, und beide Apps sind nach Owner-Abnahme im Store eingereicht.
**Geprüft:** 2026-10-29T12:10:57Z, main = origin/main (b8d804d3), Tag v1.6.0 -> 91a0603f2b69213037c0d8ac2101121f9ba767b2
**Status:** gaps_found (zwei Lücken, beide ohne Folge für das ausgelieferte Artefakt, aber gegen den Wortlaut von SC1 bzw. den Restpunkte-Auftrag)
**Re-Verifikation:** nein, erste Phasenverifikation (40-06-VERIFICATION.md ist die Planverifikation von 40-06)

Grundlage sind ausschließlich eigene Abrufe: git, gh run view, gh release, die Store-Kataloge und das heruntergeladene Release-Archiv. SUMMARY-Behauptungen wurden nicht übernommen.

## Erfolgskriterien

| # | Kriterium | Verdikt | Beleg |
|---|-----------|---------|-------|
| SC1 | Audit-Gate über alle v1.6-Änderungen, 0 CRIT / 0 HIGH / 0 MEDIUM, LOW entschieden | PARTIAL (Lücke) | 40-AUDIT.md: 0/0/0, sechs LOW, F-40-01..04 gefixt (7193cb5a, 12f7dfe0, 7a2a68a2, 0c875261), F-40-05/06 accept mit Begründung. Umfang aber v1.5.1..336ccae7, Kopf efcf26c5. Nicht im Audit: 10 Produkt-Commits efcf26c5..91a0603f (570+/54-, 11 Dateien), darunter 40-06 und Nachtrag 991b1eff. Stichprobe SearchService: die drei neuen catch-Zweige setzen `$node = null` und lassen den Treffer fallen (fail-closed), kein Befund, aber kein Audit-Ersatz. |
| SC1a | Version 1.6.0 an allen Lockstep-Stellen | VERIFIED | test_lockstep_versions.py nennt drei Stellen: `<version>` php/appinfo/info.xml, `<version>` und `<image-tag>` backend/appinfo/info.xml; alle drei 1.6.0 am Tag (git diff v1.5.1 v1.6.0). Kein `1.5.1` mehr in toml/json/xml/py außerhalb CHANGELOG/Tests/l10n am Tag. Migration php/lib/Migration/Version001600Date20261028000000.php vorhanden, CHANGELOG `## [1.6.0]`. Python gates 40864595569 auf dem Tag success. |
| SC2 | UPGRADE_FROM_TAG v1.5.0, Upgrade-Strecke 1.5.x -> 1.6.0 grün, alle Workflows auf dem Release-Commit grün | VERIFIED | `git show v1.6.0:.github/workflows/deploy-harp.yml` Zeile 186 `UPGRADE_FROM_TAG: v1.5.0`. Tag-Lauf HaRP deploy 40864595641: Job stable34/amd64 hat 12/12 "Store upgrade"-Schritte success (Log: `UPGRADE_FROM_TAG: v1.5.0`, `DRIFT_OLDER: 1.5.0`, Image findling_backend:1.5.0); die drei anderen Zeilen überspringen sie per Design. Probe-Zweig 40817178890 (gsd/40-03-probe) success. Alle sieben Tag-Läufe auf 91a0603f success (Tabelle unten). |
| SC3 | Owner-Abnahme remote, eine Runde, Protokoll im Phasenordner, `GO: ja` | VERIFIED | 40-ABNAHME.md Zeile 5 `GO: ja`, Zitat je Block, Datum 2026-10-29, Kanal genannt, Urteil je Punkt A1..G3 und F. Tag-Kopf im Protokoll 91a0603f2b69213037c0d8ac2101121f9ba767b2 = `git rev-parse v1.6.0^{commit}`. |
| SC4 | Beide Apps 1.6.0 eingereicht (2x HTTP 201), Beleg mit Lauf-ID in docs/store-listing.md und REQUIREMENTS.md | VERIFIED | Store submission 40868132102 success, Log Zeile 154 `release findling v1.6.0: HTTP 201` (11:47:55Z), Zeile 157 `release findling_backend v1.6.0: HTTP 201` (11:47:57Z). docs/store-listing.md "# Release 1.6.0 (29.10.2026)" Punkt 10/11 mit 40868132102; REQUIREMENTS.md Zeile 37/38 `[x] **REL-06**` mit Lauf-ID. Katalog live: siehe unten. |

## Tag-Kette

| Prüfung | Ergebnis | Verdikt |
|---|---|---|
| v1.6.0 -> Tag-Kopf aus 40-ABNAHME.md | beide 91a0603f2b69213037c0d8ac2101121f9ba767b2 | VERIFIED |
| Release archives 40864595574 | success, push, v1.6.0, 91a0603f | VERIFIED |
| PHP and store metadata gates 40864595622 | success, 91a0603f | VERIFIED |
| Multi-arch image 40864595511 | success, 91a0603f | VERIFIED |
| HaRP deploy 40864595641 | success, 91a0603f, vier Zeilen | VERIFIED |
| Python gates 40864595569 | success, 91a0603f | VERIFIED |
| Integration 40864595676 | success, 91a0603f | VERIFIED |
| Resilience 40864595571 | success, 91a0603f | VERIFIED |
| Fremdinstallation 40865691730 | HaRP deploy, workflow_dispatch auf main (23bb568e), `RELEASE_TAG: v1.6.0`, success auf stable33, stable34, stable34 arm64, stable35 | VERIFIED |
| head_green auf main (40-ABNAHME) | 40860811447/496/469/488/482/457/483 auf 91a0603f alle success | VERIFIED |
| store-submit 40868132102 | success, zweimal "HTTP 201" | VERIFIED |
| Release v1.6.0 | isDraft false, isImmutable true, 9 Assets; findling.tar.gz SHA-256 890d861d3d3f4513..., gleich dem Store-Download releases/download/v1.6.0/findling.tar.gz | VERIFIED |

## Katalog live (Abruf 2026-10-29 ca. 12:10Z)

| Katalog | Ergebnis | Verdikt |
|---|---|---|
| api/v1/platform/34.0.3/apps.json | findling, neueste Fassung 1.6.0, created 2026-10-29T11:47:55.560497Z, discussion 249775 | VERIFIED |
| api/v1/appapi_apps.json | findling_backend, neueste Fassung 1.6.0, created 2026-10-29T11:47:57.048524Z, discussion 249775 | VERIFIED |

## Abgenommene Texte

| Prüfung | Ergebnis | Verdikt |
|---|---|---|
| A1, A2, A3, G2 zeichengleich | Skriptvergleich der Wortlaute aus 40-OWNER-VORLAGE.md (en-Schlüssel, de, fr) gegen `findling/l10n/de.json` und `fr.json` im heruntergeladenen Release-Archiv und gegen `git show v1.6.0:php/l10n/de.json`: alle vier Sätze True in allen drei Quellen | VERIFIED |
| Release-Notiz | erste acht Zeilen des GitHub-Release-Body gleich dem Codeblock Block C (Listenvergleich True); danach der generierte Block "What's Changed" wie im Plan entschieden | VERIFIED |
| Store-Beschreibungen gegenüber 1.5.1 | `git diff v1.5.1 v1.6.0` auf beiden info.xml: nur die drei blob/v1.5.1 -> blob/v1.6.0-Links je Datei, `<version>`, `<image-tag>`, neues `<discussion>` mit Kommentar. Namen, Zusammenfassungen, Beschreibungen und Cross-Promo-Satz unverändert | VERIFIED |

## Offene Restpunkte (deferred)

| Punkt | Wo erfasst | Verdikt |
|---|---|---|
| F-40-06 -> v1.7 | 40-AUDIT.md LOW-Tabelle "v1.7"; deferred-items.md "Tombstones im Feld indexed ... betrifft auch F-40-06, v1.7"; STATE.md Zeile 110 (accept) | VERIFIED |
| Satz D unscharf bei Häufung -> v1.7 | nur 40-OWNER-VORLAGE.md, 40-ABNAHME.md G2, 40-04-SUMMARY.md; nicht in STATE.md, nicht in deferred-items.md | FAILED (Lücke 2) |
| Endverdikt gateway_error statt repeatedly_stuck -> v1.7 | nur 40-OWNER-VORLAGE.md "Nach dem Release" und 40-06-SUMMARY.md "Grenzen"; nicht in STATE.md, nicht in deferred-items.md | FAILED (Lücke 2) |
| Historische Umlaute (39 Dateien) als Doku-Commit nach Release | STATE.md Operator Next Steps Zeile 250 | VERIFIED |
| Weg-B-/Dedup-Merkliste aus Phase 39 | STATE.md Zeile 103 (D-39-02 Weg B v1.7, offener Punkt check_acl); 39-DEDUP-ERGEBNIS.md Zeilen 51, 69 bis 71 | VERIFIED |

## Platzhalter

| Prüfung | Ergebnis | Verdikt |
|---|---|---|
| "(folgt)", TAGKOPF-PLATZHALTER, TODO/TBD/FIXME/XXX in 40-*.md | einzige Treffer: zwei "(folgt)" in 40-05-SUMMARY.md, Commit-Tabelle; ersetzt durch 09251d04 und b8d804d3 (mit diesem Bericht committet). "Platzhalter" in 40-01/40-AUDIT meint SQL-Platzhalter, kein Befund | VERIFIED (nach Korrektur) |

## Requirements Coverage

| Requirement | Plan | Verdikt | Beleg |
|---|---|---|---|
| REL-06 | 40-05 | SATISFIED mit Vorbehalt | Einreichung 2x HTTP 201, UPGRADE_FROM_TAG v1.5.0 grün, Owner-GO belegt. Der Teil "Audit-Gate der Abschlussphase bestanden" gilt nur für den Stand bis efcf26c5 (Lücke 1). |

Keine weiteren Phase-40-IDs in REQUIREMENTS.md, keine verwaisten Anforderungen.

## Human Verification

Aus 40-OWNER-VORLAGE.md "Nach dem Release" (bewusst nach dem Release, kein Blocker dieser Verifikation): UI-Sichtung der Sätze A1 bis A3, G2 und der Sprachzeile G1 auf einer echten 1.6.0-Instanz durch den Owner.

## Gaps Summary

1. **Auditumfang (SC1):** Das Audit-Gate deckt nicht alle v1.6-Änderungen ab. Das Issue-#36-Paket kam nach dem Audit per Owner-Entscheid in 1.6.0 und ist nur funktional verifiziert; der Nachtrag 991b1eff (Eskalation ohne Gutschrift) gar nicht unabhängig. Das ausgelieferte Artefakt ist dadurch nicht als fehlerhaft belegt, die Stichprobe am Rechtepfad ist unauffällig. Schließen: Nachaudit über efcf26c5..91a0603f, Ergebnis als Nachtrag in 40-AUDIT.md, Fixes ab MEDIUM in 1.6.1. Wenn der Owner das nicht will, ist ein Override passend:

```yaml
overrides:
  - must_have: "Das Audit-Gate der Phase (Security/Bugs/Performance ueber alle v1.6-Aenderungen, mit Zertifikats- und Dedup-Randpfaden) endet mit 0 CRIT / 0 HIGH / 0 MEDIUM"
    reason: "40-06 kam nach dem Audit per Owner-Entscheid in 1.6.0; Umfang in Block D der Owner-Vorlage offengelegt; 40-06 funktional verifiziert (10/10), CI grün"
    accepted_by: "street1983nk"
    accepted_at: "<ISO-Zeitstempel>"
```

2. **Restpunkte-Erfassung:** Satz D (Häufung) und Endverdikt gateway_error stehen nicht in STATE.md oder deferred-items.md. Schließen: drei Zeilen in deferred-items.md (dazu Kaltstart-Satz G1), dazu STATE.md und docs/store-listing.md Beleg (12) auf "appapi_apps.json führt 1.6.0" nachziehen.

Der Phasenhaken in ROADMAP.md bleibt offen, bis beide Lücken geschlossen oder per Override angenommen sind.

---

_Verifiziert: 2026-10-29T12:10:57Z_
_Verifier: Claude (gsd-verifier)_
