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

Entscheid Layout 46-03: "Ok" (2026-11-27 07:20, Claude-Code-Chat) Entscheid: A
Freigabe Docker-Fenster 46-03 Messung: "Ok" (2026-11-27 07:20, Claude-Code-Chat) Entscheid: ja
Hinweis: Zeit in UTC. Antwort auf "Nehme ich Variante A, und darf der Agent für die Prüfung nach dem Fix noch einmal Docker nutzen?". Gedeckt: Variante A (Chip unter dem Grund unter 360 px, Spalte Zustand ausgeblendet); ein Docker-Fenster für die Messung am GREEN-Stand von 46-03 Task 3, ein Stack, danach gestoppt.

Freigabe Version 46-05: "Ja" (2026-11-27 07:48, Claude-Code-Chat) Entscheid: ja (1.7.1 für findling und findling_backend)
Freigabe Changelog 46-05: "Ja" (2026-11-27 07:48, Claude-Code-Chat) Entscheid: ja (Wortlaut EN/DE/FR wie vorgelegt, FR zweiter Punkt: "La touche Entrée dans le champ des dossiers ou des motifs exclus ajoute l'élément comme le bouton voisin ; si elle valide un mot d'une méthode de saisie, elle n'ajoute rien.")
Entscheid Tag-Datum 46-05: "Ja" (2026-11-27 07:48, Claude-Code-Chat) Entscheid: 2026-11-28 vorläufig (anderer Tag: Datumszeile am Tag-Kopf nach 46-08 Fall 2)
Freigabe Storetext 46-05: "Ja" (2026-11-27 07:48, Claude-Code-Chat) Entscheid: ja (nur Links blob/v1.7.1, Text sonst gleich)
Freigabe README 46-05: "Ja" (2026-11-27 07:48, Claude-Code-Chat) Entscheid: READMEs unverändert; docs/admin-page.md je ein Satz zu Enter und zur Fehlerliste unter 360 px
Freigabe Docker-Fenster 46-06: "Ja" (2026-11-27 07:48, Claude-Code-Chat) Entscheid: ja (PHPUnit und PHP-Gates vor dem Push, ein Stack, danach gestoppt)
Hinweis: Zeit in UTC. Antwort auf "Gibst du die fünf Punkte so frei, und auch das Docker-Fenster für 46-06?". Kein Push.

Freigabe Push 46-06: "Ja" (2026-11-27 08:30, Claude-Code-Chat) Entscheid: ja
Freigabe Dispatch coverage-e2e 46-06: "Ja" (2026-11-27 08:30, Claude-Code-Chat) Entscheid: ja
Hinweis: Zeit in UTC. Gedeckt: Push der lokalen Commits über origin/main 09ca4d23 bis einschließlich dieser Zeile auf main, ohne Tag, ohne Store; ein CI-Warter, höchstens ein Rerun; genau ein workflow_dispatch von coverage-e2e.yml auf main nach dem Push. Kein Kommentar.
