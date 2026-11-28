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

Freigabe Push 46-06 Fix: "Ok go mit den Empfehlungen" (2026-11-27 09:23, Claude-Code-Chat) Entscheid: ja
Freigabe Dispatch coverage-e2e 46-06 Fix: "Ok go mit den Empfehlungen" (2026-11-27 09:23, Claude-Code-Chat) Entscheid: ja
Hinweis: Zeit in UTC. Gedeckt: Push von e448e02b, 2fa545a9, 3b92228c und dieser Zeile auf main, ohne Tag und Store; ein CI-Warter; genau ein workflow_dispatch von coverage-e2e.yml danach. Kein Kommentar.

Entscheid PHP-Baumhash 46-06: "Ja" (2026-11-27 10:41, Claude-Code-Chat) Entscheid: PHP_TREE_HASH_TODAY auf 7ce0ad5c nachziehen (Folge von 46-03), volle Python-Suite lokal vor dem Push

Freigabe Push 46-06 Baumhash: "Ok" (2026-11-27 11:07, Claude-Code-Chat) Entscheid: ja
Entscheid coverage-e2e Rücksprung 46-06: "Ok" (2026-11-27 11:07, Claude-Code-Chat) Entscheid: Befund rollback_1_6_2 drain_incomplete (Beine upgrade und upgrade-rc1, Lauf 45973279674; letzter grüner Lauf 43094681914 am 2026-11-11, vor Phase 45; Backend seit v1.7.0 unverändert) vor dem Tag untersuchen
Hinweis: Zeit in UTC. Gedeckt: Push von f29fe8ae, ce8a5021 und dieser Zeile auf main, ohne Tag und Store; ein CI-Warter; kein Dispatch von coverage-e2e. Kein Kommentar.

Entscheid V-46-06-03 46-06: "Ja" (2026-11-27 11:44, Claude-Code-Chat) Entscheid: vor dem Tag beheben (Prüfskript ruft nach dem Rücksprung die Admin-Seite einmal auf und prüft backend_app_version = 1.6.2, Test zuerst mit Positivkontrolle; ein Satz in docs/admin-page.md)
Freigabe Push 46-06 Rücksprung: "Ja" (2026-11-27 11:44, Claude-Code-Chat) Entscheid: ja (nach grünen Gates und voller Python-Suite lokal)
Freigabe Dispatch coverage-e2e 46-06 Rücksprung: "Ja" (2026-11-27 11:44, Claude-Code-Chat) Entscheid: ja (genau ein Lauf nach dem Push)
Freigabe Docker-Fenster 46-07: "Ja" (2026-11-27 11:44, Claude-Code-Chat) Entscheid: ja (Volltest DE/EN/FR, nach dem Rücksprung-Fix; RAM-Schwelle 4 GiB, ein Stack, danach gestoppt)
Hinweis: Zeit in UTC. Antwort auf die drei Fragen (Connector F-04/F-05, Findling Rücksprung vor dem Tag mit coverage-e2e, Docker-Fenster 46-07). Kein Kommentar.

Entscheid Ablehnungsmeldung 46-07: "Noch angleichen in 1.7.1" (2026-11-27 13:22, Claude-Code-Chat) Entscheid: Meldung "Folders take no * or ?. For a pattern like Backup* use ..." nennt in jeder Sprache das übersetzte Beispiel (DE Sicherung*, FR Sauvegarde*, übrige Kataloge entsprechend dem Platzhalter), Test zuerst
Hinweis: Zeit in UTC. Gemeinsame Abnahme 46-07 Schritte 1 bis 3 (Hilfesatz, Enter, Fehlerliste 320/375/1280 hell und dunkel, FR, zh_TW) ohne Einwand des Owners; die Zeile "Abnahme Härtung 46-07" folgt nach dem Angleichen und einer kurzen Sichtprüfung.

Entscheid Name-Beispiel 46-07: "Ok" (2026-11-27 14:13, Claude-Code-Chat) Entscheid: "Name*" in der Meldung zum Musterfeld je Sprache übersetzen (FR Nom*, ES Nombre*, IT Nome*, NL Naam*, pt_BR und pt_PT Nome*, zh_TW 名稱*; DE und EN Name*), Test zuerst mit Zuordnungstabelle
Freigabe Changelog 46-07: "Ok" (2026-11-27 14:13, Claude-Code-Chat) Entscheid: vierter Punkt unter Fixed/Behoben/Corrigé: EN "The messages about * and ? in the fields of the excluded folders and patterns name their example in the language of the page." DE "Die Meldungen zu * und ? in den Feldern der ausgeschlossenen Ordner und Muster nennen ihr Beispiel in der Sprache der Seite." FR "Les messages sur * et ? dans les champs des dossiers et des motifs exclus donnent leur exemple dans la langue de la page."

Freigabe Push 46-07: "Ja" (2026-11-27 14:53, Claude-Code-Chat) Entscheid: ja (Commits über 6003b353 bis einschließlich dieser Zeile auf main, ohne Tag und Store; ein CI-Warter)

Entscheid #63 46-07: "Ja" (2026-11-27 15:56, Claude-Code-Chat) Entscheid: #63 (leere Unterzeile bei leerem Ausschnitt, Provider.php:546) in 1.7.1 beheben, Test zuerst, CHANGELOG-Punkt nach Freigabe des Wortlauts; PR #60 nach 1.7.1 prüfen, Merge als 1.8.0

Freigabe Kommentar PR60 und 63 46-07: "Ja" (2026-11-27 15:59, Claude-Code-Chat) Entscheid: ja (Entwürfe wortgleich gepostet, ohne @)

Freigabe Docker-Fenster 46-07 #63: "Ok" (2026-11-27 16:05, Claude-Code-Chat) Entscheid: ja (PHPUnit RED an 7d365b34 und GREEN am Kopf, Mutation, Psalm-Taint, php-cs-fixer; RAM mindestens 4 GiB vorher, ein Container nach dem anderen, danach leer)
Freigabe Changelog #63 46-07: "Ok" (2026-11-27 16:05, Claude-Code-Chat) Entscheid: fünfter Punkt ohne Issue-Nummer: EN "A hit whose excerpt came out empty shows its path below the title in the unified search instead of an empty line." DE "Ein Treffer mit leerem Ausschnitt zeigt in der Unified Search seinen Pfad unter dem Titel statt einer leeren Zeile." FR "Un résultat dont l'extrait est vide affiche son chemin sous le titre dans la recherche unifiée au lieu d'une ligne vide."

Freigabe Push #63 46-07: "Go" (2026-11-27 22:40, Claude-Code-Chat) Entscheid: ja (8 Commits bis a3c94c16 auf main, ohne Tag und Store; CI am Kopf grün, alle 8 Workflows)
Abnahme Härtung 46-07: "Ja" (2026-11-27 23:19, Claude-Code-Chat; gemeinsame Playwright-Abnahme Schritte 1 bis 3 ohne Einwand; Angleichen der Beispiele und #63 umgesetzt, Volltest 7429 grün, CI an a3c94c16 grün) Entscheid: ja

Freigabe Push 46-08: "Ja" (2026-11-27 23:30, Claude-Code-Chat) Entscheid: ja
Freigabe Signatur 46-09: "Ok" (2026-11-27 23:35, Claude-Code-Chat) Entscheid: ja
Korrektur Freigabe Push #63 46-07: "Ja" (2026-11-27 23:48, Claude-Code-Chat) Entscheid: ja ("Go" kam vor dem Push um 22:24:16 UTC; die Zeit 22:40 in der Zeile Freigabe Push #63 46-07 wurde nachträglich geschätzt eingetragen und ist falsch)
Freigabe Docker-Fenster T-46-17 46-10: "Ja" (2026-11-27 23:48, Claude-Code-Chat) Entscheid: ja (Testinstanz starten, SHA-256 der ausgelieferten admin.js und admin.css gegen a3c94c16; RAM mindestens 4 GiB, danach stoppen)
Abschluss Security 46-10: "Ja" (2026-11-28 00:08, Claude-Code-Chat) Entscheid: ja (46-SECURITY.md status verified, threats_open 0, d22d47bb)
Freigabe Push 46-10: "Ja" (2026-11-28 00:09, Claude-Code-Chat) Entscheid: ja (6 Belegcommits 9499a0b2 bis 790ceb25, nur .planning)
Freigabe Tag 46-11: "Ja" (2026-11-28 00:09, Claude-Code-Chat) Entscheid: ja (Tag v1.7.1 auf a3c94c1635b2fe13436394524ed3bb3aa05792b5, Claude führt aus, nur bei grüner Vorprüfung Tag)
