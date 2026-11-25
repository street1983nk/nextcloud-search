# Volltest DE/EN/FR Findling 1.7.0 (Plan 45-10, Neulauf auf dem finalen Kopf)

Muster: 32-07-ABNAHME.md. Grün heißt gemessen. Jede Umstellung, die nicht der normale Betrieb ist, steht als SIMULATION da und wurde danach zurückgesetzt. Alle Bilder liegen im Scratchpad unter `C:\Users\Student\AppData\Local\Temp\claude\f797e4cbc4775e2e\e3c27546-7ed2-4952-b9c8-13a53e542538\scratchpad\bilder\` (unten kurz `bilder/`), Kontaktbögen unter `bilder/blatt/`.

## Stand

| Punkt | Wert |
|---|---|
| Datum | 2026-11-25, 15:25 bis 17:50 UTC |
| Kopf beim Start | 8c02b706 (= origin/main), audited_head d3e6d76a047421482af9ea3adcbff42fa0b690d6 (45-AUDIT.md, `## Nachtrag 45-10`) |
| Vorbedingung | `Freigabe Push 45-10` in 45-FREIGABEN.md (0324db4c); `git rev-list HEAD..origin/main` leer, kein Rebase; R-45-21-08 erfüllt (Integration-Lauf 45425766124, Job `watermark-59 (stable34, 8.2)` success) |
| CI am Kopf | ein Warter beim Koordinator (B4), Ergebnis von dort |
| Backend | Image `findling-backend:45-10-head`, gebaut am Kopf (15:25 bis 15:27 UTC); SHA-256 von poller.py `441e77da...` und repo.py `9d5199c2...` im Image gleich dem Repo |
| Instanz Volltest | `findling-vt`, Nextcloud 34.0.3 (SQLite), http://localhost:8090, php/ des Hauptarbeitsbaums als Bind-Mount, Backend als Container (Registrierung wie docs/dev-setup.md über `register-exapp.sh`, angepasst auf den Container wie in 45-20) |
| admin.js | per HTTP ausgeliefert `e0f55c17...` = `php/js/admin.js` im Repo |
| Playwright | 1.63.0, Chromium headless, Skripte `scratchpad/pw/` |
| Docker | vor dem Start leer; seriell, nie zwei Stapel gleichzeitig |
| Fix im Lauf | f7457dac (RED) und 685e5578 (GREEN), siehe `## Befunde` V-45-10-04; Bilder der betroffenen Zustände danach neu |

## Saat

- Nutzer admin, testuser, alice, bob (Dev-Passwörter der Wegwerf-Instanz).
- files_external an, vier Admin-Speicher: ID 1 `/Projektablage` (Lokal, `/srv/ext45/lokal`), ID 2 `/<img src=x onerror=alert(1)>` (Lokal, `markup-a`), ID 3 derselbe Einhängepunkt (Lokal, `markup-b`), ID 4 derselbe Einhängepunkt (SFTP, `sftp.invalid`, nicht erreichbar). Persönlicher Speicher ID 5 `/Privat45` von testuser. Je Speicher eine Textdatei mit eindeutigem Wort (vt45lokal, vt45markupa, vt45markupb, vt45privat).
- Begründung der Zuständigkeit: drei Admin-Speicher auf einem Einhängepunkt hängt Nextcloud für dieselbe Person nur einmal ein (gesehen: admin fand vt45markupa nicht, Diagnose `found:false`). Deshalb gilt ID 2 nur für testuser, ID 3 nur für alice, ID 4 nur für admin; Liste und Bestätigung lesen die Konfiguration und zeigen alle drei (Probe P-V02). ID 1 gilt für alle, für R-45-21-12 ab 16:29 UTC nur für admin, mit `enable_sharing true` und einer Freigabe `/Projektablage/Notiz-Lokal.txt` an bob.
- Ordnerliste 62 Einträge per occ: Alt-Eintrag `Archiv*` und `Fuellordner45/01` bis `/61`; Index externer Speicher an.
- richdocuments 11.1.3 (ohne Collabora-Server), Wasserzeichen in der App `files`: bob besitzt `vt45e3ohne.odt` (an alice ohne Download, Freigabe-Attribut download=false) und `vt45e3mit.odt` (an alice mit Download). Für P-POL `vt45e3tag.odt` von bob mit Tag 1 unter allTags gelesen, Urteil `failed/policy_blocked` (Datei-ID 146). Danach Modus M1: `watermark_enabled yes`, `watermark_shareDisabledDownload yes`, allTags no.
- Für P-UNR `testuser/files/Gesperrt.txt` mit `chmod 000` im Datenverzeichnis: Gateway 422, Urteil `skipped/unreadable` (Datei-ID 145).
- `occ findling:index --restart` nach `files:scan --all` (die direkt auf die Speicher gelegten Dateien kannte der Dateicache noch nicht).
- firstrunwizard abgeschaltet (sein Willkommensdialog lag über der Admin-Seite und fing Klicks, gemessen per elementFromPoint).

## Probentabelle

| Nr. | Sprache | Probe | Erwartung | Ergebnis gemessen | Beleg | Bild |
|---|---|---|---|---|---|---|
| 1 | alle | P-UPD Update 1.6.5 -> 1.7.0, Begleit-App zuerst, echt | Suche liefert direkt nach dem Update Treffer, vor dem ersten Aufruf der Admin-Seite; backend_app_version leer | grün: 1.6.5 -> 1.7.0 in der Reihenfolge Begleit-App zuerst (Instanz `findling-upd`, NC 34.0.3, Worktree v1.6.5 06a0d7c8, Backend ghcr 1.6.5); vor dem Update Admin-Seite einmal geöffnet, backend_app_version `1.6.5`; `occ upgrade` "Updated <findling> to 1.7.0", backend_app_version leer, oc_migrations `001700Date20261123000000`; dann Container am Kopf; 15:35:49 UTC OCS-Suche als admin nach `pupdwortfindling`: 1 Treffer (`pupd.txt` mit Ausschnitt) vor dem ersten Aufruf der Admin-Seite; Zeilen "the two halves report different versions" vorher 0, nachher 0; backend_app_version leer | `scratchpad/upd/` (upgrade.txt, suche-nach-update.json, backend-170.log, nextcloud.log) | keins (OCS) |
| 2 | DE | P-V02 Bestätigung bei gleichem Einhängepunkt | IDs in Liste und Bestätigung, Markup als Text | grün: Liste "Lokal ID 2", "Lokal ID 3", "SFTP ID 4"; Bestätigung mit drei IDs; `code` ohne Kindelemente, 0 `img[src=x]`, kein Dialog; Fokus auf "Dateien indexiert lassen", danach alle Haken wieder gesetzt | `bilder/de/admin-steps-mounts.json` m01, m02, m04, m05 | `bilder/de/m04-bestaetigung-drei.png` |
| 3 | EN | P-V02 | wie 2 | grün: "Local ID 2/3", "SFTP ID 4", Bestätigung mit drei IDs, 0 img, 0 Kinder | `bilder/en/admin-steps-mounts.json` | `bilder/en/m04-bestaetigung-drei.png` |
| 4 | FR | P-V02 | wie 2 | grün: "Local ID 2/3", "SFTP ID 4", Bestätigung mit drei IDs, 0 img, 0 Kinder | `bilder/fr/admin-steps-mounts.json` | `bilder/fr/m04-bestaetigung-drei.png` |
| 5 | DE | P-V03 Platzhalter der Diagnose | Sprache der Seite | grün: `alice/files/Verträge/Miete.pdf` | a01b | `bilder/de/a01b-platzhalter.png` |
| 6 | EN | P-V03 | Sprache der Seite | grün: `alice/files/Contracts/Rent.pdf` | a01b | `bilder/en/a01b-platzhalter.png` |
| 7 | FR | P-V03 | Sprache der Seite | grün: `alice/files/Contrats/Loyer.pdf` | a01b | `bilder/fr/a01b-platzhalter.png` |
| 8 | DE | P-PLH Platzhalter Ordnerfeld, Musterfeld | `Sicherungen`, `*.photoslibrary` | grün: Ordnerfeld `Sicherungen`, Musterfeld `*.photoslibrary` | a01b, r01 | `bilder/matrix/de-zaehler2-1280-hell.png` |
| 9 | EN | P-PLH | `Backups`, `*.photoslibrary` | grün: `Backups`, `*.photoslibrary` | a01b, r01 | `bilder/en/r07-zaehler-0.png` |
| 10 | FR | P-PLH | `Sauvegardes`, `*.photoslibrary` | grün: `Sauvegardes`, `*.photoslibrary` | a01b, r01 | `bilder/fr/r07-zaehler-0.png` |
| 11 | DE | P-POL policy_blocked in der Fehlerliste und Diagnose | Label und Abhilfe | grün: "Durch eine Regel blockiert", 1, Fehlgeschlagen, Abhilfe mit "Wasserzeichen von Nextcloud Office, das auch für den Besitzer gilt" und "bis zu dreimal" | a01-abschnitt-findling-errors, a06b | `bilder/de/a06b-diagnose-policy.png` |
| 12 | EN | P-POL | Label und Abhilfe | grün: "Blocked by a rule", 1, Failed, Abhilfe wie freigegeben | a01, a06b | `bilder/en/a06b-diagnose-policy.png` |
| 13 | FR | P-POL | Label und Abhilfe | grün: "Bloqué par une règle", 1, Échoué, Abhilfe | a01, a06b | `bilder/fr/a06b-diagnose-policy.png` |
| 14 | DE | P-UNR Abhilfe unreadable | Besitzer zuerst | grün: "Für die gefragten Nutzer nicht lesbar", "fragt zuerst ihren Besitzer, dann ihre übrigen Nutzer in alphabetischer Reihenfolge, höchstens 20" | a01, a06 | `bilder/de/a06-diagnose-unlesbar.png` |
| 15 | EN | P-UNR | owner first | grün: "Not readable for the users asked", "asks its owner first, then its other users in alphabetical order, 20 at most" | a01, a06 | `bilder/en/a06-diagnose-unlesbar.png` |
| 16 | FR | P-UNR | propriétaire d'abord | grün: "Illisible pour les utilisateurs consultés", "interroge d'abord son propriétaire, puis ses autres utilisateurs par ordre alphabétique, 20 au plus" | a01, a06 | `bilder/fr/a06-diagnose-unlesbar.png` |
| 17 | DE | P-E3 M1 shareDisabledDownload | alice ohne, bob mit Ausschnitt | grün: Freigabe ohne Download ohne Ausschnitt und Freigabe mit Download ohne Ausschnitt für alice (Ergebnisseite und Unified Search zeigen den Dateinamen als Unterzeile, Rückfall auf S3 aus 45-22, zugelassen), bob mit Ausschnitt für beide Dateien | `bilder/de/u-e3m1-alice.json`, `u-e3m1-bob.json` | `bilder/de/u-e3m1-alice-seite-vt45e3mit.png` |
| 18 | DE | P-E3 Positivkontrolle | Ausschnitt für alice | grün: Wasserzeichen aus, Freigabe mit Download mit Ausschnitt für alice (alice nicht betroffen); OCS zusätzlich unter nur allTags (beide Dateien ohne Tag): Ausschnitt | `bilder/de/u-e3aus-alice.json` | `bilder/de/u-e3aus-alice-seite-vt45e3mit.png` |
| 19 | EN | P-E3 M1 shareDisabledDownload | alice ohne, bob mit Ausschnitt | grün: Freigabe ohne Download ohne Ausschnitt und Freigabe mit Download ohne Ausschnitt für alice, bob mit Ausschnitt | `bilder/en/u-e3m1-*.json` | `bilder/en/u-e3m1-alice-seite-vt45e3mit.png` |
| 20 | EN | P-E3 Positivkontrolle | Ausschnitt für alice | grün: Wasserzeichen aus, Freigabe mit Download mit Ausschnitt für alice | `bilder/en/u-e3aus-alice.json` | `bilder/en/u-e3aus-alice-seite-vt45e3mit.png` |
| 21 | FR | P-E3 M1 shareDisabledDownload | alice ohne, bob mit Ausschnitt | grün: Freigabe ohne Download ohne Ausschnitt und Freigabe mit Download ohne Ausschnitt für alice, bob mit Ausschnitt | `bilder/fr/u-e3m1-*.json` | `bilder/fr/u-e3m1-alice-seite-vt45e3mit.png` |
| 22 | FR | P-E3 Positivkontrolle | Ausschnitt für alice | grün: Wasserzeichen aus, Freigabe mit Download mit Ausschnitt für alice | `bilder/fr/u-e3aus-alice.json` | `bilder/fr/u-e3aus-alice-seite-vt45e3mit.png` |
| 23 | DE | P-LCK Hinweis Dateisperren (SIMULATION je Zustand) | sichtbar unter APCu und ArrayCache, unsichtbar unter Standard und unter `filelocking.enabled` false mit `APCu` | grün, SIMULATION: APCu sichtbar (16:34:15 UTC, Text 5 wörtlich, 1280 hell und 375 dunkel), ArrayCache sichtbar (16:34:58), Standard (memcache.locking gelöscht, 16:35:16) unsichtbar, filelocking.enabled false mit APCu (16:35:34) unsichtbar; 16:35:52 beide Werte gelöscht wie vorher | `bilder/zustand/lck-*.json` | `bilder/zustand/lck-apcu-de-1280-hell.png`, `lck-apcu-de-375-dunkel.png` |
| 24 | EN | P-LCK (SIMULATION) | wie 23 | grün, SIMULATION: APCu sichtbar, ArrayCache sichtbar, Standard unsichtbar, filelocking.enabled false mit APCu unsichtbar; Text 5 EN wörtlich | `bilder/zustand/lck-*.json` | `bilder/zustand/lck-apcu-en-1280-hell.png`, `lck-apcu-en-375-dunkel.png` |
| 25 | FR | P-LCK (SIMULATION) | wie 23 | grün, SIMULATION: APCu sichtbar, ArrayCache sichtbar, Standard unsichtbar, filelocking.enabled false mit APCu unsichtbar; Text 5 FR wörtlich | `bilder/zustand/lck-*.json` | `bilder/zustand/lck-apcu-fr-1280-hell.png`, `lck-apcu-fr-375-dunkel.png` |
| 26 | DE | P-REC Hinweis des wartenden Abgleichs #25 (SIMULATION) | sichtbar ab einem Intervall | grün, SIMULATION: Backend gestoppt, `reconcile_quiet_held_since` 65 min alt (Intervall 1 h), gestartet, overview `reconcileHeldSince` gesetzt, Hinweis sichtbar 1280 hell und 375 dunkel, Text gleich 45-23-PLAN (SHA-256 der drei Sätze gleich); danach Marke leer, `reconcileHeldSince null` | `bilder/zustand/reconcile-held.json` | `bilder/zustand/reconcile-held-de-1280-hell.png`, `-375-dunkel.png` |
| 27 | EN | P-REC (SIMULATION) | wie 26 | grün, SIMULATION, Text wörtlich | dito | `bilder/zustand/reconcile-held-en-1280-hell.png`, `-375-dunkel.png` |
| 28 | FR | P-REC (SIMULATION) | wie 26 | grün, SIMULATION, Text wörtlich | dito | `bilder/zustand/reconcile-held-fr-1280-hell.png`, `-375-dunkel.png` |
| 29 | DE | P-FAIL Satz `findling-rules-mounts-failed` und R-45-21-12 (SIMULATION) | nur im Fehlerzustand; Speichern hebt Ausschlüsse nicht auf | grün, SIMULATION: nach der Anmeldung Tabelle `oc_external_mounts` umbenannt (vor der Anmeldung scheitert schon der Login von Nextcloud), Admin-Seite HTTP 200, Satz wörtlich wie freigegeben, Liste 0 Zeilen; Speichern mit neuem Muster: Bestätigung, POST 200, `excluded_external_mounts` vorher `[1]`, nachher `[1]`; Tabelle zurück; im Normalzustand ist der Satz nicht im DOM | `bilder/zustand/mounts-failed-de.json` | `bilder/zustand/mounts-failed-de-1280-hell.png`, `-375-dunkel.png` |
| 30 | EN | P-FAIL (SIMULATION) | wie 29 | grün, SIMULATION, Satz wörtlich, `[1]` bleibt | `mounts-failed-en.json` | `bilder/zustand/mounts-failed-en-1280-hell.png`, `-375-dunkel.png` |
| 31 | FR | P-FAIL (SIMULATION) | wie 29 | grün, SIMULATION, Satz wörtlich, `[1]` bleibt | `mounts-failed-fr.json` | `bilder/zustand/mounts-failed-fr-1280-hell.png`, `-375-dunkel.png` |
| 32 | DE | R-45-21-12 Ausschluss mit Abgleich, echt | ausgeschlossener Speicher bleibt aus, auch mit Freigabe | grün: 16:29:29 UTC "Ausschließen und entfernen" für `/Projektablage`, POST 200, `[1]`; Treffer bleiben bis zum Abgleich (Doku: "verlassen den Index im nächsten vollständigen Abgleich"); echter Abgleich 16:49:01 "storage sweep, ... deselected=1 ... removed storages [3]" (Speicher 3 = local::/srv/ext45/lokal/); 16:49:48 admin vt45lokal 0 Treffer, bob über die Freigabe 0 Treffer; Gegenkontrolle testuser vt45markupa, vt45privat, alice vt45markupb je 1 Treffer | `bilder/de/x-aus-1.json`, Backend-Log | `bilder/de/x-aus-1-bestaetigung.png` |
| 33 | EN | Wiederzulassen, echt | keine Bestätigung, Nachindexierung beim nächsten regulären Abgleich | gespeichert 16:52:54 UTC: keine Bestätigung, "Rules saved. The next run applies them.", `[]`; Ergebnis der Suche nach dem nächsten Abgleich: siehe Nachtrag unten | `bilder/en/x-an-1.json` | `bilder/en/x-an-1-danach.png` |
| 34 | FR | Ausschließen und entfernen, echt | Bestätigung, Speichern | grün: 17:05:21 UTC Speicher 2 (Markup, testuser), Bestätigung, POST 200, "Règles enregistrées. Le prochain passage les applique.", `[2]`; Entfernen nach dem nächsten Abgleich: siehe Nachtrag | `bilder/fr/x-aus-2.json` | `bilder/fr/x-aus-2-bestaetigung.png` |
| 35 | DE | Regelblock vollständig (r01 bis r24) | jede Feldmeldung, Zähler, Markierung, Bestätigung | grün: empty, wildcard, duplicate, too_long (Ordner, 258 Byte), too_many (Ordner 65., Muster 33.), no_wildcard, double_star, unsupported_character, negation, no_literal, traversal (Muster und Ordner), "Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert.", Zähler 2/1/0 bei Ordnern und 31 bis 0 bei Mustern, Ansage bei 0, Markierung `Archiv*`, Ordnerbestätigung mit Zahl, "Dateien indexiert lassen" | `bilder/de/admin-steps-regeln.json` | `bilder/de/r*.png` |
| 36 | EN | Regelblock vollständig | wie 35 | grün, alle Meldungen in EN wie Katalog | `bilder/en/admin-steps-regeln.json` | `bilder/en/r*.png` |
| 37 | FR | Regelblock vollständig | wie 35 | grün, alle Meldungen in FR wie Katalog | `bilder/fr/admin-steps-regeln.json` | `bilder/fr/r*.png` |
| 38 | DE/EN/FR | Hauptschalter aus und an | Liste gesperrt, Satz, keine Tabstopps | grün je Sprache: `disabled` true, 0 Tabstopps, Satz "Hauptschalter aus" sichtbar, Hilfesatz verborgen; an: umgekehrt | m06, m07 je Sprache | `bilder/<lang>/m06-hauptschalter-aus.png` |
| 39 | DE/EN/FR | übrige Admin-Seite (Pause, Diagnose leer/unbekannt/Markup, Profilwahl, alle Abschnitte) | Texte in der Sprache, keine Konsolenfehler | grün je Sprache; Diagnose eines Pfads mit Markup zeigt den Pfad als Text, 0 img | a00 bis a08 je Sprache | `bilder/<lang>/a0*.png` |
| 40 | DE/EN/FR | Suchoberfläche als testuser (Ergebnisseite, Unified Search, Leerzustand) | Texte in der Sprache, Treffer | grün je Sprache: vt45home und vt45lokal mit Treffer, vt45nichtsda Leerzustand mit Hilfesatz | `bilder/<lang>/u-t.json` | `bilder/<lang>/u-t-*.png` |
| 41 | alle | P-LIVE neue Passzeile | `handed_ocr`/`handed_embed` im Log | grün: "pass finished, claimed=1 indexed=1 skipped=0 failed=0 unchanged=0 handed_ocr=0 handed_embed=1 requeued=1 embedded=0 committed=1 slots=1 throttled=0" (findling-upd, Container am Kopf) und gleiche Form auf findling-vt | Backend-Logs | keins |
| 42 | alle | P-LIVE Backstop | kein Auslösen ohne kreisende Datei | grün: keine warning-Zeile "demanded handovers", kein failed/repeatedly_stuck im Bestand (overview reasons: empty_text 7, image_not_ocrable 1, unreadable 1) | Backend-Log, overview | keins |

V-02-Regel c DE: Liste `/<img src=x onerror=alert(1)> Lokal ID 2`; `/<img src=x onerror=alert(1)> Lokal ID 3`; `/<img src=x onerror=alert(1)> SFTP ID 4`, Bestätigung `Indexierte Inhalte entfernen? Der Ausschluss der externen Speicher /<img src=x onerror=alert(1)> (ID 2), /<img src=x onerror=alert(1)> (ID 3), /<img src=x onerror=alert(1)> (ID 4) entfernt außerdem ihre bereits indexierten Dokumente aus dem Index. Die Dateien selbst bleiben unverändert auf dem Speicher.`
V-02-Regel c EN: Liste `/<img src=x onerror=alert(1)> Local ID 2`; `/<img src=x onerror=alert(1)> Local ID 3`; `/<img src=x onerror=alert(1)> SFTP ID 4`, Bestätigung `Remove indexed content? Excluding the external storages /<img src=x onerror=alert(1)> (ID 2), /<img src=x onerror=alert(1)> (ID 3), /<img src=x onerror=alert(1)> (ID 4) also removes their already indexed documents from the index. The files themselves stay untouched on the storage.`
V-02-Regel c FR: Liste `/<img src=x onerror=alert(1)> Local ID 2`; `/<img src=x onerror=alert(1)> Local ID 3`; `/<img src=x onerror=alert(1)> SFTP ID 4`, Bestätigung `Supprimer les contenus indexés ? L'exclusion des stockages externes /<img src=x onerror=alert(1)> (ID 2), /<img src=x onerror=alert(1)> (ID 3), /<img src=x onerror=alert(1)> (ID 4) retire également de l'index leurs documents déjà indexés. Les fichiers eux-mêmes restent intacts sur le stockage.`

Erwartung nach Regel c (45-19): jede Zeile mit gleichem Einhängepunkt trägt "ID n", gleich welcher Typ, die Bestätigung nennt jeden Speicher als "Einhängepunkt (ID n)". Liste und Bestätigung entsprechen dem in allen drei Sprachen.

Zeilen in Probenform für verify (dieselben Messungen wie oben):

- P-E3 DE: M1 shareDisabledDownload, Freigabe ohne Download ohne Ausschnitt, Freigabe mit Download ohne Ausschnitt (beides für alice, Rückfall auf S3 aus 45-22, zugelassen), bob mit Ausschnitt.
- P-E3 DE: Positivkontrolle mit Wasserzeichen aus, alice nicht betroffen: Freigabe mit Download mit Ausschnitt.
- P-E3 EN: M1 shareDisabledDownload, Freigabe ohne Download ohne Ausschnitt, Freigabe mit Download ohne Ausschnitt (beides für alice), bob mit Ausschnitt.
- P-E3 EN: Positivkontrolle mit Wasserzeichen aus, alice nicht betroffen: Freigabe mit Download mit Ausschnitt.
- P-E3 FR: M1 shareDisabledDownload, Freigabe ohne Download ohne Ausschnitt, Freigabe mit Download ohne Ausschnitt (beides für alice), bob mit Ausschnitt.
- P-E3 FR: Positivkontrolle mit Wasserzeichen aus, alice nicht betroffen: Freigabe mit Download mit Ausschnitt.
- P-LCK DE: SIMULATION, sichtbar unter APCu, sichtbar unter ArrayCache, unsichtbar unter dem Standard, unsichtbar unter `filelocking.enabled` false mit `APCu`; danach beide vorigen Werte zurück.
- P-LCK EN: SIMULATION, sichtbar unter APCu, sichtbar unter ArrayCache, unsichtbar unter dem Standard, unsichtbar unter `filelocking.enabled` false mit `APCu`; danach beide vorigen Werte zurück.
- P-LCK FR: SIMULATION, sichtbar unter APCu, sichtbar unter ArrayCache, unsichtbar unter dem Standard, unsichtbar unter `filelocking.enabled` false mit `APCu`; danach beide vorigen Werte zurück.
- P-UPD: 1.6.5 -> 1.7.0, Begleit-App zuerst, backend_app_version leer, 1 Treffer vor dem ersten Aufruf der Admin-Seite (alles echt).

Hinweise zu den Proben:

- E3 unter M1: auch Treffer auf einem externen Admin-Speicher zeigen allen ohne eigenen Besitz den Pfad statt eines Ausschnitts (testuser vt45lokal: Unterzeile `Projektablage/Notiz-Lokal.txt`); das ist reines S3 nach `Entscheid E3-Weg 45-22` und kein Befund (I-45-10-03).
- Moduswechsel des Wasserzeichens per occ wirkt im Webprozess nach etwa 2 bis 3 s (Konfig-Cache von Nextcloud; gemessen "M1 wirkt nach 3 s, 2 Versuche"). Zwei Proben direkt nach dem Umschalten zeigten deshalb noch den alten Modus; jede Probe oben lief nach der Wartezeit (I-45-10-02).
- Muster too_long ist in der Oberfläche nicht erreichbar: das Feld trägt `maxlength=60`, der Browser kürzt jede längere Eingabe (r14, r14b); der Server prüft die Länge weiter. Kein Befund.
- Speicher-Ausschluss: die Dokumente verlassen den Index erst im nächsten vollständigen Abgleich, wie docs/admin-page.md sagt; der Abgleich wurde mit `FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1` und der passenden Stunde echt abgewartet, nicht simuliert.

## Playwright-Matrix

Alle UI-SPEC-Zustände auf Deutsch in 375, 768 und 1280 px, je hell und dunkel (Farbschema des Browsers, Theme "default" des Servers), Bilder `bilder/matrix/de-<zustand>-<breite>-<modus>.png`, Kontaktbögen `bilder/blatt/<zustand>.png`. Jede Zeile: 6 Bilder, kein Fehler, kein horizontaler Überlauf von `#findling-rules`, keine Konsolenfehler außer dem erwarteten 400 der Vorschau bei no_wildcard.

| Zustand | 375 hell | 375 dunkel | 768 hell | 768 dunkel | 1280 hell | 1280 dunkel | angesehen |
|---|---|---|---|---|---|---|---|
| Liste mit Speichern, einer ausgeschlossen (`/Projektablage`) | ok | ok | ok | ok | ok | ok | Bogen liste.png |
| Hauptschalter aus (gesperrt) | ok | ok | ok | ok | ok | ok | Bogen mix.png |
| leer (SIMULATION: Admin-Speicher 1 bis 4 kurz als persönliche geführt, danach zurück) | ok | ok | ok | ok | ok | ok | Bogen leer-fxaus.png (erster Lauf versehentlich FR, als fr- abgelegt, dann DE) |
| files_external aus (App kurz abgeschaltet) | ok | ok | ok | ok | ok | ok | dito |
| Bestätigung mit Speicherzeile | ok | ok | ok | ok | ok | ok | Bogen bestaetigung.png |
| Zähler bei 2 | ok | ok | ok | ok | ok | ok | mix.png |
| Zähler bei 1 | ok | ok | ok | ok | ok | ok | nach-fix.png |
| Zähler bei 0 | ok | ok | ok | ok | ok | ok | nach-fix.png |
| Feldfehler wildcard | ok | ok | ok | ok | ok | ok | nach-fix.png |
| Markierung `Archiv*` | ok | ok | ok | ok | ok | ok | nach-fix.png |
| Meldung no_wildcard | ok | ok | ok | ok | ok | ok | nach-fix.png |
| Regelblock-Kopf | ok | ok | ok | ok | ok | ok | mix.png |
| Seite unter zh_TW | ok |  |  |  | ok |  | siehe `## zh_TW und zh_Hant_TW` (1280 hell, 375 dunkel) |

Hoher Kontrast (Stichprobe, Theme light-highcontrast, 1280): Liste, Bestätigung, wildcard, Zähler 0, Markierung, ok (`bilder/blatt/hc.png`, nach dem Fix wildcard, Zähler 0 und Markierung neu).

Vor dem Fix V-45-10-04 zeigten Feldfehler, Zähler 1/0 und Markierung grau statt in Fehler- bzw. Warnfarbe (Bilder unter `bilder/matrix-vor-fix/`); nach dem Fix in der Farbe der UI-SPEC (gemessen per getComputedStyle: hell Fehler rgb(138, 0, 0), Warnung rgb(102, 71, 0); dunkel rgb(255, 204, 204) und rgb(255, 238, 197)).

Angesehen habe ich jeden Kontaktbogen (Matrix je Zustand 6 Bilder, hoher Kontrast, leer und files_external aus, nach dem Fix) und je Sprache EN und FR einen Bogen der Kernschritte (`bilder/blatt/sprache-en.png`, `sprache-fr.png`); die übrigen Einzelbilder der Schritte sind über die mechanische Sprachprüfung und die gemessenen Texte abgedeckt.

## Sprachprüfung

Mechanisch: alle sichtbaren Texte je Schritt (innerText und ARIA-Schnappschuss) gegen den Katalog der Sprache (`scratchpad/pw/sprache.js`); ein englischer Quellsatz unter DE oder FR, der dort anders lautet, ist ein Fehler.

| Sprache | Zeilen | im Katalog | Fehler | zur Handbewertung | Positivkontrolle (B8) |
|---|---|---|---|---|---|
| DE | 445 | 303 | 0 | 142 | absichtlich englischer Satz in einer Kopie: 1 Fehler gefunden |
| FR | 445 | 298 | 0 | 147 | 1 Fehler gefunden |
| EN | 445 | 298 | 0 | 147 | (Quellsprache, Kontrolle nicht anwendbar) |

Handbewertung der offenen Zeilen: Pfade, Muster, Saatnamen, Zahlen, Code (`occ app_api:app:unregister findling_backend`, `FINDLING_*`), Typnamen von files_external ("Lokal", unter FR "Local" wie Nextclouds eigener Katalog), Bruchstücke der um Platzhalter geschnittenen Sätze; kein englischer Satz unter DE oder FR. Sichtprüfung über die Bögen: keine falsche Sprache, kein Tippfehler, kein ASCII-Umlaut im Deutschen.

Gefunden in der Sichtprüfung der Texte mit Zahlen: Befund V-45-10-05 (Zahl 1 bzw. 0 vor einem Nomen im Plural, alle drei Sprachen), siehe `## Befunde`.

## zh_TW und zh_Hant_TW

| Probe | Ergebnis gemessen | Bild |
|---|---|---|
| Admin, Sprache zh_TW, Locale zh_Hant_TW | `lang="zh-TW"`, `data-locale="zh_Hant_TW"`; Zähler "剩餘 1 個空位（共 64 個），這是最後一個。", Muster "剩餘 32 個空位（共 32 個）", Speicherliste mit "本站 ID 2/3", "SFTP ID 4", Überschrift "規則與限制", Kacheln 48/9/1/0; keine Konsolenfehler (1280 hell, 375 dunkel) | `bilder/zh_TW/admin-locale-1280-hell.png`, `-375-dunkel.png` |
| Admin, Locale gelöscht | Nextcloud rendert dann `data-locale="en_US"`, Seite wie oben, keine Konsolenfehler | `bilder/zh_TW/admin-rueckfall-*.png` |
| Rückfall auf root.lang (SIMULATION: `data-locale` per Init-Skript entfernt, weil Nextcloud es immer setzt) | `data-locale` fehlt, `lang="zh-TW"`, Zahlen und Sätze wie oben, keine Konsolenfehler | `bilder/zh_TW/admin-sim-*.png` |
| Nutzer testuser zh_TW, Ergebnisseite und Unified Search | "「vt45home」的搜尋結果", Treffer mit Ausschnitt, Gruppe "檔案內容"; Leerzustand "沒有檔案包含「vt45nichtsda」" | `bilder/zh_TW/u-t-*.png` |

## impeccable

Ablauf: `DEGRADED: single-context` (kein Werkzeug für Unteragenten in dieser Sitzung). Assessment A zuerst aus Quelle und Bildern, dann B mit dem gebündelten Detektor über CDP (`impeccable detect --cdp 9333 --target settings/admin/findling --json`, Chromium nur auf 127.0.0.1) in 1280 hell und 375 dunkel; Rohdaten `bilder/impeccable-detect-1280-hell.json`, `-375-dunkel.json`.

Critique (Modus Operate, DESIGN.md als Rahmen): Der Regelblock folgt dem Muster der Nextcloud-Einstellungen (fieldset, legend, Hilfesatz, Checkbox-Zeilen ohne Karten); die Bestätigung ist die einzige Fläche in Fehlerfarbe und nennt Folge und Ausweg; Zähler und Markierung tragen die Bedeutung im Satz. Heuristiken: Sichtbarkeit 3, Sprache der Nutzer 3, Kontrolle 4 (Dateien indexiert lassen), Konsistenz 4, Fehlervermeidung 4, Wiedererkennen 3, Effizienz 3, Ästhetik 3, Fehlererholung 3 (vor dem Fix 2: Feldfehler nur grau), Hilfe 3; zusammen 33/40. Schwächen: Feldfehler und Warnungen ohne ihre Farbe (V-45-10-04, behoben), Zahlensätze ohne Pluralform (V-45-10-05, offen), das Beispiel im Hilfesatz der Ordner bleibt "Backups" neben dem übersetzten Platzhalter (I-45-10-04).

Audit (Technik): A11y 3 (aria-invalid, Ansage bei 1 und 0, Fokus auf dem harmlosen Knopf, gesperrtes fieldset ohne Tabstopps, Markup immer als Text); Performance 4 (keine Animation, kein Layout-Lesen in Schleifen gesehen); Theming 3 nach dem Fix (alle Farben über Tokens, Dunkel und hoher Kontrast lesbar; vor dem Fix 2); Responsive 4 (375 ohne Überlauf, Typ unter dem Einhängepunkt); Integrität: Detektor, siehe Tabelle.

| Detektor-Fund | Schwere | Bewertung |
|---|---|---|
| line-length `#findling-coverage-leftout`, `#findling-rules-patterns-help`, `#findling-limits-change`, `#findling-rules-mounts-help` (rund 110 bis 122 Zeichen bei 1280) | warning | kein Befund: DESIGN.md legt die Lesespalte mit `max-width: 900px` gleich der h2 des Kerns fest; die Brief-Regel gilt |
| straggler `#findling-coverage-rules-pending` (375) | advisory | kein Befund, Umbruch je nach Breite |
| bounce-easing `body`, shape-assembled-illustration `body` | advisory | Kern von Nextcloud (Theme, Willkommensbild), nicht Findling |

Eigene Gegenprobe zur Integrität (B8, nicht mit dem Muster des Detektors): jede Farbregel aus `php/css/admin.css` gegen die berechnete Farbe der getroffenen Elemente (`scratchpad/pw/css3.js`); sie fand V-45-10-04 (drei Klassen verlieren gegen `.section p` des Kerns). Nach dem Fix bleibt nur die gewollte Überschreibung der Basisklasse durch ihren Modifikator.

## Umlaut-Audit

Vorfilter `grep -nE "(ae|oe|ue)[a-z]|ss[^a-z]"` über die in v1.6.5..HEAD hinzugefügten Zeilen: `php/l10n/de.json` 23 Zeilen, 6 Treffer; `de_DE.json` identisch zu de.json; README.md 16 Zeilen, 0 Treffer; CHANGELOG.de.md 46 Zeilen, 1 Treffer; docs/admin-page.md 204 Zeilen, 9 Treffer. Handbewertung jedes Treffers: "zuerst", "neuen", "dass", "Ausschluss", "doppelt", englische Wörter in Code und Schlüsseln (queue, comparison, access), Codezeilen (`OCA\FilesAccessControl\...`); keine Ersatzschreibung. docs/migrate-from-fulltextsearch.md in v1.6.5..HEAD nicht berührt. Gedankenstriche U+2013/U+2014 in allen hinzugefügten Zeilen der Kataloge, CHANGELOGs, READMEs, docs, Templates und Skripte: 0.

## Befunde

| ID | Schwere | Befund | Beleg | Status |
|---|---|---|---|---|
| V-45-10-04 | LOW | Feldfehler (`.findling-rules__error`), Zähler bei 1 und 0 (`.findling-rules__slots--low`) und Markierung alter Ordnereinträge (`.findling-rules__row-warning`) zeigen grau statt in Fehler- bzw. Warnfarbe der UI-SPEC: `.section p` aus settings.css von Nextcloud (Spezifität 0,1,1) schlägt eine einzelne Klasse (0,1,0). Die Bedeutung trug weiter der Satz und aria-invalid; der Feldfehler war seit 1.5.0 betroffen, Zähler und Markierung sind neu in 1.7.0 | getComputedStyle hell rgb(107, 107, 107) statt rgb(138, 0, 0) bzw. rgb(102, 71, 0); Liste der Regeln je Element (`css2.js`) | behoben per TDD: RED f7457dac (`test_the_coloured_sentences_outrank_the_muted_paragraphs_of_a_settings_section`, 3 Funde), GREEN 685e5578 (`.section` vor den drei Klassen), Mutationen je Selektor rot, Live-Gegenprobe grün; Owner-Regel 22.11. (LOW sauber beheben); Push nur mit `Freigabe Push 45-10 Fix` |
| V-45-10-05 | MEDIUM (Owner-Regel: Sprachfehler sind No-Go) | Sätze mit Zahl ohne Pluralform: bei 1 (und in FR bei 0) steht das Nomen im Plural, in allen drei Sprachen. Live gesehen: Überblick "1 Dateien konnten nicht gelesen werden oder sind mehrfach hängen geblieben." / "1 files could not be read ..." / "1 fichiers n'ont pas pu être lus ..."; Ordnerbestätigung "entfernt außerdem 1 bereits indexierte Dokumente" / "also removes 1 already indexed documents" / "retire également de l'index 1 documents déjà indexés" (FR auch "0 documents déjà indexés"). Bestand seit vor 1.7.0 (Ordnerbestätigung seit Phase 4, Überblickssatz seit 1.6.x) | `bilder/<lang>/eins-Eins45.png`, a01-abschnitt-findling-coverage je Sprache; Ordner `Eins45` mit genau einer Datei, Vorschau `affectedDocuments 1` | offen, Owner-Entscheid und Textfreigabe nötig (neue Pluralformen in 18 Katalogen) |
| I-45-10-01 | INFO | Doku-Links der Admin-Seite zeigen auf den Tag v1.5.0 (`#limits-per-file`, drei Umstiegs-Links); der Kommentar in admin.php sagt "documentation of exactly this release". Inhalt geprüft: der verlinkte Abschnitt ist zu HEAD byte-gleich (SHA-256 der 40 Zeilen ab dem Anker gleich), die drei Umstiegsdokumente sind seit v1.5.0 unverändert. Kein falscher Inhalt, nur ein veralteter Kommentar | `git diff --stat v1.5.0 HEAD -- docs/migrate-from-fulltextsearch*.md` leer | zur Kenntnis, kein Fix in 45-10 |
| I-45-10-02 | INFO | Wasserzeichen-Moduswechsel per occ wirken im Webprozess nach 2 bis 3 s (Konfig-Cache von Nextcloud) | "M1 wirkt nach 3 s, 2 Versuche" | kein Befund von Findling |
| I-45-10-03 | INFO | Unter M1 (S3-Rückfall) zeigen auch Treffer auf externen Admin-Speichern keinen Ausschnitt | testuser vt45lokal mit Pfad als Unterzeile | zugelassen nach `Entscheid E3-Weg 45-22` |
| I-45-10-04 | INFO | Hilfesatz der Ordnerliste nennt "Beispiel: Backups" (DE, FR ebenso), der Platzhalter ist seit 45-25 übersetzt ("Sicherungen", "Sauvegardes") | r01, Regelblock-Kopf | UI-SPEC lässt den Hilfesatz bewusst unverändert; "Backups" ist auch im Deutschen üblich; zur Kenntnis |
| I-45-10-05 | INFO | deploy-harp.yml Z. ~4054 und ~5576 werten den repeatedly_stuck-Bestand aus (Hinweis aus 45-27) | lokal kein Auslösen des Backstops, kein failed/repeatedly_stuck im Bestand | Bewertung hängt am HaRP-deploy-Job des CI-Laufs am Kopf (Koordinator): erscheint dort "part A candidate ... failed/repeatedly_stuck" oder "part B candidate", ist das ein neuer Befund |

## Nachtrag

(folgt: Ergebnis der Suche nach dem nächsten Abgleich für Proben 33 und 34)
