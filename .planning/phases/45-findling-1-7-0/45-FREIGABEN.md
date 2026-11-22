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
