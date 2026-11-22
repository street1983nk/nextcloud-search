# Freigaben Phase 45

Freigabe Merge PR57 45-01: "Go" (2026-11-22 01:04, Claude-Code-Chat, Antwort auf Frage a/b/c mit a = beide mergen) Entscheid: ja
Freigabe Merge PR56 45-01: "Go" (2026-11-22 01:04, Claude-Code-Chat, gleiche Antwort) Entscheid: ja
Entscheid docs/l10n-chinese.md englisch 45-01: "Go" (2026-11-22 01:04, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeiten in UTC. Die Freigaben decken nur die zwei Merges mit --match-head-commit auf die geprüften Köpfe (PR57 168b6b13ba7d03b407e94f9f57a17a2970657457, PR56 51690b2ac926bbbb14df4e3f3b5c0fd40bc078d4), keinen Push eigener Commits und keinen Kommentar.

Freigabe Push 45-06: "Ja" (2026-11-22 03:47, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeit in UTC. Die Freigabe deckt den Push der lokalen Commits 45-01 bis 45-06 samt diesem Freigabe-Commit auf main (kein Tag, keine Store-Aktion, kein Kommentar), einen CI-Warter und höchstens einen Rerun fehlgeschlagener Jobs; keinen zweiten Push eines Fixes.

Freigabe Version 45-08: "A" (2026-11-22 05:01, Claude-Code-Chat) Entscheid: ja
Freigabe Changelog 45-08: "A" (2026-11-22 05:01, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeit in UTC. Antwort A = Version ja, CHANGELOG ja (EN gezeigt, DE/FR inhaltsgleich); A heißt auch: liegt der Tag später als 2026-11-22, wird das Datum von [1.7.0] in CHANGELOG.md, CHANGELOG.de.md und CHANGELOG.fr.md beim Release auf das Tag-Datum angepasst. Kein Push, kein Tag, kein Kommentar.

Freigabe Push 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: ja
Entscheid LOW L-45-09-01 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: beheben
Entscheid LOW L-45-09-02 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: beheben
Entscheid LOW L-45-09-03 45-09: "Ok" (2026-11-22 05:36, Claude-Code-Chat) Entscheid: beheben

Hinweis: Zeit in UTC. Der Owner schrieb zuerst "Qualität hat Vorrang" und gab dann mit "Ok" den überarbeiteten Vorschlag des Koordinators frei. Dieser machte aus L-45-09-02 "beheben" statt "akzeptieren", für alle drei Listen (Ordner, Muster, externe Speicher: die Route lehnt ein JSON-Objekt mit 400 und bestehendem Code ab, das Lesen bleibt duldsam), und verlangte für L-45-09-03 vor dem Fix eine Nachstellung auf einer echten Instanz ohne files_external. L-45-09-01: Obergrenze 1000 beim Lesen, Rest als unbrauchbar gezählt. Die Push-Freigabe deckt genau einen Push aller lokalen Commits samt Fixes und diesem Freigabe-Commit nach grünen lokalen Gates, einen CI-Warter (scripts/ci/head_green.sh) und höchstens einen `gh run rerun <id> --failed`; kein Tag, keine Store-Aktion, kein Kommentar.

Entscheid L-45-09-03 enge Form 45-10: "Ok" (2026-11-22 07:26, Claude-Code-Chat) Entscheid: behalten
Freigabe CHANGELOG-Zeile Objekt-Ablehnung 45-10: "Ok" (2026-11-22 07:26, Claude-Code-Chat) Entscheid: ja

Hinweis: Zeit in UTC. L-45-09-03 bleibt in der engeren Form aus 45-09 (leere Menge nur bei fehlender Tabelle oc_external_mounts, nicht bei deaktiviertem files_external), keine Codeänderung. Die CHANGELOG-Freigabe deckt eine kurze Zeile in [1.7.0] von CHANGELOG.md, CHANGELOG.de.md und CHANGELOG.fr.md zur Ablehnung eines JSON-Objekts oder einer Liste mit Lücken in allen drei Regellisten (L-45-09-02); kein Push, kein Tag, kein Kommentar.

Entscheid Fix #59 in 1.7.0 45-17: "Der fix soll in 1.7" (2026-11-22 08:20, Claude-Code-Chat) Entscheid: ja
Freigabe Antwort Issue #59 45-15: "Passt nach dem Release kannst du es posten" (2026-11-22 08:28, Claude-Code-Chat) Entscheid: ja, Claude postet nach Store-Release, Text vorher gegen den fertigen Fix abgleichen
Freigabe V-45-10-02 und V-45-10-03 45-17: "Wenn das die beste Qualität gewährleistet go" (2026-11-22 08:40, Claude-Code-Chat) Entscheid: beheben
Entscheid Rückfragen 45-17: "Ja bitte" (2026-11-22 08:47, Claude-Code-Chat) Entscheid: policy_blocked wie gateway_error bis 3 Nächte; CHANGELOG-Zeile nur für V-45-10-03, nicht für V-45-10-02; CI-Test mit richdocuments, falls ohne Collabora-Server machbar, sonst Kosten am Checkpoint; Requirement COMP-05
Vorgabe Qualität 45-17: "besser mehr Aufwand für beste Qualität, im Anschluss genau alles prüfen, wir wollen kein 1.7.1 um 1.7.0 zu fixen" (2026-11-22 zwischen 08:47 und 09:25 UTC, Uhrzeit nicht exakt überliefert, Claude-Code-Chat) Entscheid: ja
Entscheid E1 Lesen in actAs nur bei Secure View 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja
Entscheid E2 keine Umgehung des Wasserzeichens 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja
Entscheid E3 keine Textausschnitte unter Secure View 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja, Erkennung an der Quelle belegen oder Owner-Checkpoint mit Optionen (45-22)
Entscheid E4 secure-phase vor dem Tag 45-17: "Go mit Empfehlung" (2026-11-22 09:25, Claude-Code-Chat) Entscheid: ja, 45-16 vor 45-14

Hinweis: Zeiten in UTC, wie vom Koordinator übergeben. Die Zeilen decken keinen Push, keinen Tag und keinen Kommentar; die Antwort auf #59 wird erst nach dem Store-Release in 45-15 gepostet, vorher gegen den fertigen Fix abgeglichen (45-21). E1: Findling öffnet eine Datei weiterhin ohne aktive Person und liest sie nur dann erneut in actAs (zuerst als Besitzer, ohne erkennbaren Besitzer als einer der übrigen Nutzer, höchstens 20), wenn das erste Öffnen nachweislich von der Secure View von Nextcloud Office abgelehnt wurde; die Audit-Protokolle nennen für diese Dateien die lesende Person. E2: Gilt das Wasserzeichen auch für den Besitzer, umgeht Findling die Sperre nicht, sondern antwortet mit 403 policy und dem Urteil policy_blocked. E3: Suchtreffer von Dateien, die für die suchende Person unter Secure View oder Wasserzeichen stehen, zeigen Name und Treffer ohne Textausschnitt; die Erkennung wird an der Quelle belegt oder in 45-22 per Owner-Checkpoint mit Optionen entschieden. E4: Die secure-phase (45-16) läuft vor dem Tag und der Store-Abgabe (45-14). Die Sätze zu E1 bis E4 sind aus dem Plan 45-17 (Abschnitte "Entscheid zum Ort und zur Form des Rückfalls" und Objective) gefasst, die Koordinator-Nachricht selbst lag dem Ausführer nicht im Wortlaut vor.
