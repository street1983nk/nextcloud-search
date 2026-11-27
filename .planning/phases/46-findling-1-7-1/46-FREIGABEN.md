# Freigaben Phase 46

Format je Zeile: `Freigabe <Gegenstand> 46-NN: <Owner-Zitat> (<JJJJ-MM-TT HH:MM>, <Kanal>) Entscheid: ja|nein` bzw. `Entscheid <Name> 46-NN: <Owner-Zitat> (<JJJJ-MM-TT HH:MM>, <Kanal>) Entscheid: <Wert>`. Zeiten in UTC. Eine Freigabe deckt genau ihren Gegenstand und verbraucht sich (B2 in 46-CONTEXT.md).

Erste Runde: Entscheide E-46-01 bis E-46-08 (46-01 Task 1).

Entscheid E-46-01 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: a (Hilfesatz übernimmt das übersetzte Beispiel, hebt die 45-UI-SPEC-Regel "Hilfesatz unverändert" auf)
Entscheid E-46-02 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: a (alle neun Sprachen, 18 Katalogdateien)
Entscheid E-46-03 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: ja (unter 360 px rückt der Chip unter den Grund; Variante wählt der Owner in 46-03)
Entscheid E-46-04 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: a (Wörterbuch plus tesseract in integration.yml und coverage-e2e.yml; übrige apt-Aufrufe ins Backlog)
Entscheid E-46-05 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: a (CHANGELOG nur die drei sichtbaren Fixes, ohne Issue-Nummern)
Entscheid E-46-06 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: a (Store-Texte unverändert bis auf die Links blob/v1.7.1)
Entscheid E-46-07 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: a (keine GitHub-Kommentare zu 1.7.1)
Entscheid E-46-08 46-01: "Ja" (2026-11-27 06:16, Claude-Code-Chat) Entscheid: ja (Docker nur in einzeln freigegebenen Fenstern "Freigabe Docker-Fenster 46-NN")
Hinweis: Zeit in UTC. Antwort auf "Darf ich alle Empfehlungen für beide Projekte so übernehmen?" (je Punkt mit Empfehlung vorgelegt). Offen: Tag-Datum (CHANGELOG-Datum in 46-05) und Dispatch von coverage-e2e.yml nach dem Push; beide werden am jeweiligen Schritt erneut gefragt.

Entscheid Reihenfolge 46-04: "Ok" (2026-11-27 06:38, Claude-Code-Chat) Entscheid: 46-04 vor 46-03 ohne Docker; 46-03 folgt, sobald Docker frei ist
Freigabe Text store-listing 46-05: "Ok" (2026-11-27 06:38, Claude-Code-Chat) Entscheid: ja
Hinweis: Zeit in UTC. Gedeckt: Umformulierung genau der drei Zeilen im Abschnitt "# Release 1.7.0" von docs/store-listing.md mit dem gesperrten Wort (I-46-01-01), sofort statt in 46-05; Inhalt und Belege bleiben gleich. Kein Push.

Freigabe Docker-Fenster 46-03: "Ok" (2026-11-27 07:08, Claude-Code-Chat) Entscheid: ja
Hinweis: Zeit in UTC. Antwort auf "Docker-Fenster für Findling 46-03 gleich nach der NC35-Messung" (NC35 fertig, docker ps leer). Gedeckt: Dev-Instanz für die Bilder der Layout-Varianten 46-03 Task 1, ein Stack, danach gestoppt; RAM vorher prüfen.
Entscheid I-46-04-01 46-04: "Ok" (2026-11-27 07:08, Claude-Code-Chat) Entscheid: Backlog (coverage_e2e.sh und smb_acl_measure.sh nicht in 1.7.1)
