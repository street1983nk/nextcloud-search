---
phase: 46
slug: findling-1-7-1
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-28
---

# Phase 46: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Risiken und Audit-Trail.
> Register aus den `<threat_model>`-Blöcken von 46-01 bis 46-12 (register_authored_at_plan_time: true), jede ID genau einmal; 46-10 bringt keine eigene ID (seine Wirkung trägt T-46-19).
> Geprüfter Stand: Tag-Kopf K = a3c94c1635b2fe13436394524ed3bb3aa05792b5 (46-ABNAHME.md), audited_head = ci_head = K, Code gleich origin/main 7806e83a. Belege je ID im Detail: 46-AUDIT.md `## Nachtrag Threats vor dem Tag` (Proben Q1 bis Q6). Alle Proben mit `git show a3c94c16:...`, nie mit `git show v1.7.1`; es gibt keinen Tag v1.7.1 (lokal, entfernt).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Katalog -> Admin-Seite | übersetzte Werte in Template und admin.js | Markup-Risiko (XSS) |
| Admin-Browser -> Regelfelder (Enter) | neuer Tastaturweg zu denselben Funktionen wie der Knopf | Admin-Eingaben |
| Template -> Fehlerliste unter 360 px | zweite Fassung des Chips | Markup-Risiko |
| CI-Runner -> apt (apt_install.sh) | Paketnamen, Umgebung, Zeitbudget | Shell, Verfügbarkeit der CI |
| Store upgrade 2b -> Log | Wartezeile | Pfade, IDs |
| Container -> Begleit-App (Ausschnitte, #63) | leere Ausschnitte über den Draht | Suchergebnisse |
| Executor -> Owner-Entscheide | Push, Dispatch, Signatur, Release-Texte | Entscheidungshoheit |
| CI-Runner -> Signaturschlüssel | Environment release | Schlüssel |
| Volltest -> Kandidat | geprüfter Stand gleich ausgeliefertem Stand | Aussagekraft der Abnahme |
| Tag-Kandidat | ein offener Threat am Kandidaten ginge mit dem Tag in den Store | alles oben |

---

## Threat Register

Beleg-Konvention: Datei:Zeile am Kandidaten K; Lauf-IDs per `gh run view --json conclusion,headSha` am 2026-11-28 gegengeprüft (46076437121, 46076437005, 46076437035, 46076437149, 46076437150, 46076437214, 46076437153, 46076437084 je success auf a3c94c16; 46083361339 Signatur-Probe success auf 7806e83a; 45973260375 Workflow security lint success auf a66b016c). Q1 bis Q6 = Proben in 46-AUDIT.md `## Nachtrag Threats vor dem Tag`.

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-46-01 | Tampering | Katalogwert mit Markup oder neuem Platzhalter | mitigate | Q1: eigenes Skript über 18 Kataloge an K, 0 Markup, 0 Platzhalter-Abweichung, Positivkontrolle rot; Ausgabe nur über `p()` (admin.php Z. 1597) | closed |
| T-46-02 | Repudiation | Arbeit ohne Owner-Entscheid | mitigate | E-46-01 bis E-46-08 in 98bd5713, Ahne des ersten Code-Commits 66570830 | closed |
| T-46-03 | Tampering (XSS) | Markup im Feldwert über den Enter-Weg | mitigate | `git show K:php/js/admin.js \| grep -c innerHTML` = 0; Enter ruft `addFolderEntry`/`addPatternEntry`, Zeile per Klon und `textContent`; ExclusionService.php seit v1.7.0 ohne Diff; P-XSS in 46-VOLLTEST.md, admin.js-Blob dort gleich K | closed |
| T-46-04 | Denial of Service | Enter-Dauerdruck über die Listengrenze | mitigate | `too_many` in beiden Funktionen (admin.js Z. 1491, 1559); MAX_PREFIXES 64, MAX_PATTERNS 32 unverändert | closed |
| T-46-05 | Tampering (XSS) | zweite Ausgabe des Chips | mitigate | nur `p()` aus `$chip()` (admin.php Z. 844 bis 907), Template an K ohne print_unescaped/echo; Psalm-Taint OCP 33/34/35 success im Lauf 46076437005 an K | closed |
| T-46-06 | Information Disclosure | Bilder der Saat in .planning | mitigate | eigene Sichtprüfung bilder/layout: nur Saat der Dev-Instanz | closed |
| T-46-07 | Tampering | Paketname oder Umgebung als Shell-Code | mitigate | Q3: Skript von K mit fünf bösen Namen je rc 2, gültiger Name rc 0; Array statt String; feste Namen an allen fünf Aufrufstellen, kein `${{ }}` im run-Text; shellcheck (46076437121) und zizmor (45973260375) grün | closed |
| T-46-08 | Denial of Service | Wiederholung verlängert einen roten Lauf | mitigate | Q4: eigenes Skript, kleinstes Job-Limit 25 min, schlimmster Fall 410 s unter 750 s; Bereichsprüfung der Umgebung (Q3) | closed |
| T-46-09 | Repudiation | Warteschleife verdeckt einen echten Fehler | mitigate | Q5: Schleife an derselben Frist, danach unveränderte rote Prüfung `left`; Mutation M3 "Abbruchbedingung" rot (46-04-SUMMARY.md Z. 51) | closed |
| T-46-10 | Information Disclosure | Wartezeile nennt Pfad | mitigate | Q5: deploy-harp.yml Z. 4560 nur Zeilenzahl, kind, Restsekunden | closed |
| T-46-11 | Tampering | Versionen laufen auseinander | mitigate | 1.7.1 in php info.xml, backend info.xml version und image-tag an K; Python gates an K success | closed |
| T-46-12 | Tampering | ungeplante Migration im Patch | mitigate | `git diff --name-only v1.7.0 K` über Migration und Schemadateien leer | closed |
| T-46-13 | Repudiation | Release-Text ohne Owner | mitigate | Freigaben 46-05 (b22b123d) vor 03c53f11/2dfe0f38; Changelog 46-07 und #63 je vor ihrem Commit | closed |
| T-46-14 | Repudiation | Push ohne Freigabe (46-06) | mitigate | Q6: vier Pushes 46-06 je nach ihrer Zeile, Zeile im gepushten Commit | closed |
| T-46-15 | Tampering | Rerun verdeckt einen CI-Fehler | mitigate | rote Läufe 45966198418, 45966177681: attempt 1, kein Rerun; Fix per TDD | closed |
| T-46-16 | Information Disclosure | Volltest-Bilder zeigen echte Daten | mitigate | eigene Sichtprüfung bilder/volltest: nur Saat (Fuellordner45, P46Ordner) | closed |
| T-46-17 | Tampering | Volltest prüft einen anderen Stand als den Kandidaten | mitigate | Docker-Fenster nach `Freigabe Docker-Fenster T-46-17 46-10` (23:48:17 UTC, Chatprotokoll), Start 23:48:38 und nach Neustart 00:00:01 UTC: per HTTP ausgeliefert admin.js 88b23b75...ab58 und admin.css be22a5a0...ec78 = K, 18 Kataloge im Container = K, Mount = php/ des Arbeitsbaums, `git diff a3c94c16 HEAD -- php/` leer (46-AUDIT.md `## Nachtrag Docker-Fenster T-46-17`, Rohausgaben im Chatprotokoll gegengeprüft) | closed |
| T-46-18 | Repudiation | Fix-Push ohne Freigabe | mitigate | `Korrektur Freigabe Push #63 46-07` (4b6cda07): "Go" vor dem Push, 22:40 war geschätzt; unabhängig im Chatprotokoll: Frage "Darf ich die 8 Commits pushen?", Owner-"Go" 22:24:08.578Z, `git push` 22:24:11Z, Push 22:24:16 UTC | closed |
| T-46-19 | Tampering | ungeprüfter Code zwischen Härtung und Tag | mitigate | Tag-Kopf = audited_head = ci_head = K, acht Läufe success an K, Code K gleich origin/main | closed |
| T-46-20 | Repudiation | Push oder Dispatch ohne Freigabe (46-08, 46-09) | mitigate | Q6: Push 7806e83a nach `Freigabe Push 46-08`, Dispatch 46083361339 nach `Freigabe Signatur 46-09` | closed |
| T-46-21 | Information Disclosure | Signaturschlüssel im Log | mitigate | release.yml seit v1.7.0 ohne Diff; `environment: release`, Schlüssel nur über env aus secrets | closed |
| T-46-22 | Spoofing | Signatur-Probe auf fremdem Stand | mitigate | Lauf 46083361339 auf 7806e83a, Code gleich K (Diff nur .planning) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Nach dem Release nachzuprüfen

Entstehen in 46-11 und 46-12, Prüfung im Nachtrag von 46-12; zählen nicht in threats_open vor dem Tag.

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-46-23 | Tampering | Tag auf falschem Kopf | mitigate | Vorprüfung, verify Tag-Commit gleich Tag-Kopf | nach dem Release |
| T-46-24 | Spoofing | unsignierte Pakete im Store | mitigate | Verified OK, SHA-256, Fremdinstallation aus den Release-Assets | nach dem Release |
| T-46-25 | Information Disclosure | Store-Token | mitigate | nur im Environment app-store, Dispatch nur nach Freigabe | nach dem Release |
| T-46-26 | Repudiation | Veröffentlichung ohne Owner | mitigate | getrennte Freigabezeilen Tag und Store | nach dem Release |
| T-46-27 | Denial of Service | Store-API-Sperre | mitigate | B9, höchstens alle 10 Minuten, höchstens drei Versuche | nach dem Release |
| T-46-28 | Repudiation | Kommentar ohne Freigabe | mitigate | E-46-07; je Thread eine Freigabezeile vor dem Posten | nach dem Release |
| T-46-29 | Information Disclosure | interne Details oder @-Erwähnung im Kommentar | mitigate | nur öffentliche Links, `grep -c @` je Body 0, wortgleich zum Entwurf | nach dem Release |

---

## Accepted Risks Log

Keine. Alle Threats der Phase haben die Disposition mitigate.

---

## Unregistered Flags

Keine. Keine SUMMARY der Phase 46 führt einen Abschnitt `## Threat Flags`. Die Änderungen nach dem ersten Audit (1a0abda0..a3c94c16: #63 in snippets.py und ExAppService::filterSnippets, Beispielwörter in 14 Katalogen) bringen keine neue Angriffsfläche (46-AUDIT.md, Abschnitt "Änderungen nach dem ersten Audit"); keine ID T-46-30.

Hinweise ohne Threat-Bezug: I-46-04-01 (LOW, Backlog per Owner-Entscheid); der Budget-Gate rechnet ohne `--kill-after` (380 s statt 410 s), Urteil unverändert.

---

## Security Audit Trail

### Security Audit 2026-11-28

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-28 | 22 vor dem Tag (T-46-01 bis T-46-22) + 7 nach dem Release | 20 | 2 | Executor 46-10 nach secure-phase.md, Proben selbst am Kandidaten |

- Zählung vor dem Tag: 22 IDs, alle mitigate, 0 accept, 0 transfer. T-46-23 bis T-46-29 nach dem Release.
- ASVS-Level 1, block_on: high; offen T-46-17 und T-46-18 (beide Beleglücken, kein Code-Befund). Der Tag ist gesperrt.
- Wege zum Schließen: T-46-17 entweder ein Docker-Fenster mit Freigabe, in dem der SHA-256 der von der Dev-Instanz ausgelieferten admin.js und admin.css gegen die Werte an K (88b23b75...ab58, be22a5a0...ec78) verglichen und die Katalogwerte an K einmal gesichtet werden, oder eine Zeile `Akzeptanz Threat T-46-17 46-10: ...`. T-46-18 eine Korrekturzeile des Owners zur tatsächlichen Zeit seines "Go" (vor 22:24 UTC) oder `Akzeptanz Threat T-46-18 46-10: ...`. Danach secure-phase erneut.
- Proben am Kandidaten K: 46-AUDIT.md `## Nachtrag Threats vor dem Tag` (Q1 bis Q6), unabhängig vom Muster der Umsetzung, mit Positivkontrollen (Q1, Q3).
- Implementierungsdateien nicht verändert.

### Security Audit 2026-11-28 (Nachprüfung T-46-17, T-46-18)

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-28 | 22 vor dem Tag (T-46-01 bis T-46-22) + 7 nach dem Release | 22 | 0 | secure-phase Nachprüfung, ohne Docker, Belege selbst gegengeprüft |

- T-46-18 closed: Korrekturzeile des Owners in 4b6cda07. Unabhängig belegt im Chatprotokoll der Sitzung: Frage "Darf ich die 8 Commits pushen?", Owner-"Go" 2026-11-27T22:24:08.578Z, danach `git push` (22:24:11Z), Push 22:24:16 UTC, Lauf createdAt 22:24:19Z. Die Korrekturzeile nennt keine Minute, nur "vor dem Push"; das Protokoll schließt diese Lücke. Der Wortlaut der Korrektur stammt aus dem Vorschlag des Ausführers, der Owner bestätigte mit "Ja" (23:48:17Z).
- T-46-17 closed: `Freigabe Docker-Fenster T-46-17 46-10` (Owner-"Ja" 23:48:17Z, Zeile in 4b6cda07 um 23:49:18 UTC) liegt vor jedem Docker-Befehl (erster Start 23:48:38Z, nach RAM-Abbruch und Neustart `docker start` 00:00:01Z, `docker stop` 00:01:07Z) und vor dem Nachtrag 0a0f8dfa (00:01:28 UTC). Rohausgaben im Protokoll gegengeprüft: HTTP 200, admin.js 88b23b75d8b79d5365033068de194120fce6d7dc0dee0ef45d2cbf912fecab58 und admin.css be22a5a0b36e5250bea8c08df6749e3c14ab99bfc732c372b63f4f544d44ec78 gleich `git show a3c94c16:...` (selbst nachgerechnet), 18 Kataloge im Container 0 Abweichungen, die 9 .js auch per HTTP gleich; die 9 .json-Scheinabweichungen sind die 404-Seite (4932 Byte, Code 404). Mount laut `docker inspect` = php/ des Arbeitsbaums; selbst geprüft: `git diff --stat a3c94c16 HEAD -- php/` leer, `git status --short php/` leer, Diff a3c94c16..HEAD nur fünf Dateien unter .planning.
- Rest ohne Einfluss auf das Urteil: der Hash gilt für den Stand jetzt, nicht für den Zeitpunkt des Volltests; die Brücke sind die gleichen Repo-Blobs an 029d7307, 1a0abda0 und K sowie der Mount des Arbeitsbaums. Der Katalogvergleich ging über den Wortlaut der Freigabe (nur admin.js, admin.css) hinaus, nur lesend im selben Fenster.
- Kein neuer Threat, keine unregistrierten Flags. Implementierungsdateien nicht verändert.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log (keine)
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** offen; alle 22 Threats vor dem Tag belegt geschlossen (2026-11-28). Es fehlt nur die Owner-Zeile `Abschluss Security 46-10`.
