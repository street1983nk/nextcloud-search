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
| Fixes im Lauf | V-45-10-04: f7457dac (RED), 685e5578 (GREEN). V-45-10-05: b056b3b9 (Freigabe), 8988ba79 (RED), 1d832d03 (GREEN, auf der Instanz 500, siehe `## Befunde`), d5efe7cd (RED %n-Gate), GREEN-Commit der Nachbesserung siehe Nachtrag. Bilder der betroffenen Zustände danach neu |

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
| 33 | EN | Wiederzulassen, echt | keine Bestätigung, Nachindexierung beim nächsten regulären Abgleich | grün: gespeichert 16:52:54 UTC ohne Bestätigung, "Rules saved. The next run applies them.", `[]`; echter Abgleich 18:03:17 UTC ("reconcile round walked, mounts=8 ..."); danach admin vt45lokal 1 Treffer, bob über die Freigabe 1 Treffer | `bilder/en/x-an-1.json`, Backend-Log | `bilder/en/x-an-1-danach.png` |
| 34 | FR | Ausschließen und entfernen, echt | Bestätigung, Speichern, Dokumente nach dem Abgleich weg | grün: 17:05:21 UTC Speicher 2 (Markup, testuser), Bestätigung, POST 200, "Règles enregistrées. Le prochain passage les applique.", `[2]`; Abgleich 18:03:17 UTC "storage sweep, ... deselected=1 ... removed storages [4]" (Speicher 4 = local::/srv/ext45/markup-a/); danach testuser vt45markupa 0 Treffer, Gegenkontrolle alice vt45markupb 1 Treffer | `bilder/fr/x-aus-2.json`, Backend-Log | `bilder/fr/x-aus-2-bestaetigung.png` |
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

Neulauf nach dem Fix V-45-10-05 (Admin-Teil je Sprache neu erfasst, dazu alle Nutzer- und Ausschlussdateien, 18:30 UTC): DE 591 Zeilen, 346 im Katalog, 0 Fehler, 245 zur Handbewertung, Positivkontrolle 1 Fehler gefunden; FR 592, 337, 0, 255, Positivkontrolle 1 Fehler; EN 591, 325, 0, 266. Die offenen Zeilen enthalten außer Saatwörtern, Pfaden, Zahlen und Kernsätzen von Nextcloud keinen englischen Satz unter DE oder FR (gezielte Suche nach englischen Funktionswörtern: nur der Doku-Link und zwei Pfade). Der Überblick zeigt jetzt "1 Datei konnte nicht gelesen werden ..." / "1 file could not be read ..." / "1 fichier n'a pas pu être lu ...".

Handbewertung der offenen Zeilen: Pfade, Muster, Saatnamen, Zahlen, Code (`occ app_api:app:unregister findling_backend`, `FINDLING_*`), Typnamen von files_external ("Lokal", unter FR "Local" wie Nextclouds eigener Katalog), Bruchstücke der um Platzhalter geschnittenen Sätze; kein englischer Satz unter DE oder FR. Sichtprüfung über die Bögen: keine falsche Sprache, kein Tippfehler, kein ASCII-Umlaut im Deutschen.

Gefunden in der Sichtprüfung der Texte mit Zahlen: Befund V-45-10-05 (Zahl 1 bzw. 0 vor einem Nomen im Plural, alle drei Sprachen), behoben, siehe `## Befunde` und die Proben P-PLU.

## zh_TW und zh_Hant_TW

| Probe | Ergebnis gemessen | Bild |
|---|---|---|
| Admin, Sprache zh_TW, Locale zh_Hant_TW | `lang="zh-TW"`, `data-locale="zh_Hant_TW"`; Zähler "剩餘 1 個空位（共 64 個），這是最後一個。", Muster "剩餘 32 個空位（共 32 個）", Speicherliste mit "本站 ID 2/3", "SFTP ID 4", Überschrift "規則與限制", Kacheln 48/9/1/0; keine Konsolenfehler (1280 hell, 375 dunkel) | `bilder/zh_TW/admin-locale-1280-hell.png`, `-375-dunkel.png` |
| Admin, Locale gelöscht | Nextcloud rendert dann `data-locale="en_US"`, Seite wie oben, keine Konsolenfehler | `bilder/zh_TW/admin-rueckfall-*.png` |
| Rückfall auf root.lang (SIMULATION: `data-locale` per Init-Skript entfernt, weil Nextcloud es immer setzt) | `data-locale` fehlt, `lang="zh-TW"`, Zahlen und Sätze wie oben, keine Konsolenfehler | `bilder/zh_TW/admin-sim-*.png` |
| Nutzer testuser zh_TW, Ergebnisseite und Unified Search | "「vt45home」的搜尋結果", Treffer mit Ausschnitt, Gruppe "檔案內容"; Leerzustand "沒有檔案包含「vt45nichtsda」" | `bilder/zh_TW/u-t-*.png` |

## impeccable

Ablauf: `DEGRADED: single-context` (kein Werkzeug für Unteragenten in dieser Sitzung). Assessment A zuerst aus Quelle und Bildern, dann B mit dem gebündelten Detektor über CDP (`impeccable detect --cdp 9333 --target settings/admin/findling --json`, Chromium nur auf 127.0.0.1) in 1280 hell und 375 dunkel; Rohdaten `bilder/impeccable-detect-1280-hell.json`, `-375-dunkel.json`.

Critique (Modus Operate, DESIGN.md als Rahmen): Der Regelblock folgt dem Muster der Nextcloud-Einstellungen (fieldset, legend, Hilfesatz, Checkbox-Zeilen ohne Karten); die Bestätigung ist die einzige Fläche in Fehlerfarbe und nennt Folge und Ausweg; Zähler und Markierung tragen die Bedeutung im Satz. Heuristiken: Sichtbarkeit 3, Sprache der Nutzer 3, Kontrolle 4 (Dateien indexiert lassen), Konsistenz 4, Fehlervermeidung 4, Wiedererkennen 3, Effizienz 3, Ästhetik 3, Fehlererholung 3 (vor dem Fix 2: Feldfehler nur grau), Hilfe 3; zusammen 33/40. Schwächen: Feldfehler und Warnungen ohne ihre Farbe (V-45-10-04, behoben), Zahlensätze ohne Pluralform (V-45-10-05, behoben), das Beispiel im Hilfesatz der Ordner bleibt "Backups" neben dem übersetzten Platzhalter (I-45-10-04).

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
| V-45-10-05 | MEDIUM (Owner-Regel: Sprachfehler sind No-Go) | Sätze mit Zahl ohne Pluralform: bei 1 (und in FR bei 0) stand das Nomen im Plural, in allen drei Sprachen ("1 Dateien konnten nicht gelesen werden", "also removes 1 already indexed documents", "1 fichiers n'ont pas pu être lus"); Bestand vor 1.7.0 | `bilder/<lang>/eins-Eins45.png` (vorher), `bilder/plural/` (nachher) | behoben nach `Freigabe Texte V-45-10-05` (Option a, Owner "Ok" 17:23 UTC): sechs Sätze (acht Schlüssel) mit Einzahl über `n()` und `$l->n`, 18 Kataloge, sechs Sprachtabellen, CHANGELOG EN/DE/FR; Gate `test_no_number_stands_before_a_plural_noun_without_a_singular_form` (RED 8988ba79, 15 Funde), Mutation je Aufrufstelle rot (15 von 15). Der erste GREEN-Stand 1d832d03 ließ die Admin-Seite mit 500 antworten (`The arguments array must contain 2 items, 1 given`, L10NString.php Z. 54): `$l->n` wählt die Form nur über `%n`; gefunden in der Live-Probe vor jedem Push, nie ausgeliefert. Nachbesserung: die sieben vom Server gerenderten Schlüssel tragen die Zahl als `%n`, `$counted` (PHP) und `counted` (Skript) geben ihr das Format der Locale; neues Gate `test_every_server_plural_carries_its_count_as_the_first_directive` (RED d5efe7cd: 7 Funde am Stand 1d832d03). Wortlaut unverändert wie freigegeben, nur der Platzhalter der Zahl ist `%n` statt `%s` |
| I-45-10-01 | INFO | Doku-Links der Admin-Seite zeigen auf den Tag v1.5.0 (`#limits-per-file`, drei Umstiegs-Links); der Kommentar in admin.php sagt "documentation of exactly this release". Inhalt geprüft: der verlinkte Abschnitt ist zu HEAD byte-gleich (SHA-256 der 40 Zeilen ab dem Anker gleich), die drei Umstiegsdokumente sind seit v1.5.0 unverändert. Kein falscher Inhalt, nur ein veralteter Kommentar | `git diff --stat v1.5.0 HEAD -- docs/migrate-from-fulltextsearch*.md` leer | zur Kenntnis, kein Fix in 45-10 |
| I-45-10-02 | INFO | Wasserzeichen-Moduswechsel per occ wirken im Webprozess nach 2 bis 3 s (Konfig-Cache von Nextcloud) | "M1 wirkt nach 3 s, 2 Versuche" | kein Befund von Findling |
| I-45-10-03 | INFO | Unter M1 (S3-Rückfall) zeigen auch Treffer auf externen Admin-Speichern keinen Ausschnitt | testuser vt45lokal mit Pfad als Unterzeile | zugelassen nach `Entscheid E3-Weg 45-22` |
| I-45-10-04 | INFO | Hilfesatz der Ordnerliste nennt "Beispiel: Backups" (DE, FR ebenso), der Platzhalter ist seit 45-25 übersetzt ("Sicherungen", "Sauvegardes") | r01, Regelblock-Kopf | UI-SPEC lässt den Hilfesatz bewusst unverändert; "Backups" ist auch im Deutschen üblich; zur Kenntnis |
| I-45-10-05 | INFO | deploy-harp.yml Z. ~4054 und ~5576 werten den repeatedly_stuck-Bestand aus (Hinweis aus 45-27) | lokal kein Auslösen des Backstops; im Log des HaRP-deploy-Laufs 45644218559 am Kopf 8c02b706 keine echte Zeile "part A candidate" oder "part B candidate", Treffer nur in den mitgeloggten Skriptquellen (Auswertung des Koordinators) | kein Befund |
| V-45-10-07 | MEDIUM (Owner: "Fixen Aufjdenfall") | Der Detailhinweis "Für die gefragten Nutzer nicht lesbar" in `.findling-errors` (565 Zeichen) bleibt einzeilig, rund 3800 px breit; die Admin-Seite scrollt waagerecht auf jeder Breite (1280 und 375). Ursache: `table { white-space: nowrap }` aus core/css/server.css von Nextcloud. Im Volltest-Bild `bilder/de/a01-abschnitt-findling-errors.png` schon sichtbar, aber nicht erkannt | `abn/02-fehlerliste.png`, `abn/13-zhtw-375-dunkel.png` | offen, Fix in Task 3 per TDD (`white-space: normal` für die Detailzeilen), dazu neue Prüfung: kein waagerechtes Scrollen auf allen Breiten |
| I-45-10-06 | INFO | Enter im Eingabefeld der Ordner- und Musterliste fügt keinen Eintrag hinzu, nur der Knopf | gemeinsame Abnahme Schritt 2 | für 1.7.1 vorgemerkt (Owner "Ok" zur Empfehlung) |
| I-45-10-07 | INFO | Ein leeres, gesperrtes Kästchen (Hauptschalter aus) erscheint als gefülltes graues Quadrat | `abn/05-hauptschalter-aus.png` | Darstellung aus Nextcloud selbst, kein Befund von Findling |
| V-45-10-06 | LOW | Zwei weitere Sätze mit einer Zahl vor einem Nomen im Plural, die die Freigabe von V-45-10-05 nicht deckte: "OCR limit %1$s pages per file, set by %2$s" (zeigt 1 unter `FINDLING_OCR_MAX_PAGES=1`) und "Removing an entry takes effect within %1$s hours, ...". Korrektur zu meinem Bericht: die Stunden des zweiten Satzes kommen in 1.7.0 aus der Konstante `AdminViewService::RECONCILE_INTERVAL_HOURS = 24` und nicht aus `FINDLING_RECONCILE_MIN_INTERVAL_HOURS`; eine 1 ist dort heute nicht erreichbar, die Einzahl sichert eine spätere Änderung ab | Gate ohne Ausnahme (RED fb57b51f, 2 Funde) | behoben nach `Freigabe Texte V-45-10-06` (Owner "Ok" 2026-11-26 01:44 UTC): 9965e30b, `%n` und `$counted` wie bei V-45-10-05, 18 Kataloge, sechs Sprachtabellen, keine eigene CHANGELOG-Zeile; drei Mutationen rot (OCR-Satz zurück auf `$l->t`, Abgleichsatz ohne `%n`, Abgleichsatz zurück auf `$l->t`) |

## Nachtrag

### Kurzprobe V-45-10-06 (2026-11-26, 02:10 bis 02:20 UTC, Admin-Seite je Sprache HTTP 200, Konsole leer)

| Zustand | DE | EN | FR |
|---|---|---|---|
| `FINDLING_OCR_MAX_PAGES=1` (Deploy-Option) | "OCR-Deckel 1 Seite je Datei, gesetzt durch FINDLING_OCR_MAX_PAGES" | "OCR limit 1 page per file, set by FINDLING_OCR_MAX_PAGES" | "Limite OCR 1 page par fichier, définie par FINDLING_OCR_MAX_PAGES" |
| `FINDLING_OCR_MAX_PAGES=2` | "OCR-Deckel 2 Seiten je Datei, ..." | "OCR limit 2 pages per file, ..." | "Limite OCR 2 pages par fichier, ..." |
| Abgleichsatz mit 24 (Normalbetrieb) | "... innerhalb von 24 Stunden, ..." | "... within 24 hours, ..." | "... sous 24 heures, ..." |
| Abgleichsatz mit 1, SIMULATION (Konstante `RECONCILE_INTERVAL_HOURS` kurz auf 1, 02:14:38 bis 02:15:12 UTC, Datei per SHA-256 byte-gleich zurück, e0eaa943) | "... innerhalb von 1 Stunde, ..." | "... within 1 hour, ..." | "... sous 1 heure, ..." |

Bilder `bilder/plural/sechs-<zustand>-<lang>.png`. Danach Abnahmestand wiederhergestellt: `FINDLING_OCR_MAX_PAGES` entfernt (Zeile verborgen), Backend-Umgebung `FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1`, `FINDLING_RECONCILE_HOUR=18`, Admin-Sprache DE, Stapel gestoppt, Volumes erhalten.

### Proben P-PLU nach dem Fix V-45-10-05 (2026-11-25, 18:05 bis 18:15 UTC, Admin-Seite HTTP 200)

| Sprache | Satz "nicht lesbar" (1 Datei), Server und nach dem Poll | Ordnerbestätigung 1 Dokument (`Eins45`) | Ordnerbestätigung 0 Dokumente | Bild |
|---|---|---|---|---|
| DE | "1 Datei konnte nicht gelesen werden oder ist mehrfach hängen geblieben. Sie zählt als nicht durchsuchbar und senkt den Deckungsgrad." (beide gleich) | "... entfernt außerdem 1 bereits indexiertes Dokument unter diesem Pfad ..." | "... 0 bereits indexierte Dokumente ..." | `bilder/plural/*-de-1280-hell.png`, `-375-dunkel.png` |
| EN | "1 file could not be read or got stuck repeatedly. It counts as not searchable and lowers the coverage figure." | "... also removes 1 already indexed document under that path ..." | "... 0 already indexed documents ..." | `bilder/plural/*-en-*.png` |
| FR | "1 fichier n'a pas pu être lu ou est resté bloqué à plusieurs reprises. Il ne peut pas être trouvé par la recherche et fait donc baisser la couverture." | "... retire également de l'index 1 document déjà indexé ..." | "... 0 document déjà indexé ..." (Singular bei 0 nach `plural=(n > 1)`) | `bilder/plural/*-fr-*.png` |

Dazu je Sprache, 1280 hell: Satz bei stummem Backend (Backend kurz gestoppt) "... 55 Dateien dieser Instanz sind indexierbar." / "... 55 files of this instance are indexable." / "... 55 fichiers de cette instance sont indexables." (`bilder/zustand/plural-unknown-*.png`); Banner der Neueinbettung nach Wahl von Standard mit fp32 (nicht gespeichert): "Neueinbettung von 49 Dokumenten. ..." / "Re-embedding of 49 documents. ..." / "Recalcul des vecteurs de 49 documents. ..." (`bilder/plural/reembed-*.png`). Keine Konsolenfehler.

Format der Zahl gegengeprüft (eigene Probe, nicht das Muster des Gates): Skript `counted` mit Intl de-DE "12345 Dateien sind durchsuchbar." -> "12.345 Dateien sind durchsuchbar.", fr-FR "1234 fichiers, dont 1234 ..." -> "1 234 fichiers, dont 1234 ..." (nur die Zahl am %n), Platzhalter `%1$s`/`%2$s` unberührt; Template `$counted` mit NumberFormatter de_DE in der Instanz "12345 Dateien, davon 12345 mit OCR." -> "12.345 Dateien, davon 12345 mit OCR." (`scratchpad/pw/zahlform.js`, `scratchpad/vt/zahlform.php`).

Stand der Saat nach den Proben: `excluded_external_mounts` = `[2]` (Speicher 2 ausgeschlossen, für die gemeinsame Abnahme Schritt 3 bereit), `/Projektablage` zugelassen; Backend-Umgebung `FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1`, `FINDLING_RECONCILE_HOUR=18`.

## Owner-Abnahme

Gemeinsam per Playwright am 2026-11-26, 06:00 bis 14:35 UTC, Stand dd92da51 (audited_head 9965e30b), Admin-Sprache DE, Bilder `scratchpad/abn/01` bis `14`.

| Schritt | Ergebnis |
|---|---|
| 1 Speicherliste | Typ und ID je Speicher sichtbar, Bestätigung bei doppeltem Einhängepunkt, Hauptschalter aus sperrt die Liste: erwartet |
| 2 Zähler, Feldfehler, Markierung, no_wildcard | Zähler bis 0 mit Warnfarbe, Feldfehler in Fehlerfarbe, Markierung alter Ordnereinträge, Meldung zu Platzhaltern beim Speichern: erwartet |
| 3 Ausschließen und Wiederzulassen | Speicher 2 ausgeschlossen: testuser `vt45markupa` 0 Treffer, alice `vt45markupb` 1 Treffer (Kontrolle). Wieder zugelassen gegen 07:12 UTC, Abgleich 08:31:03 UTC (mounts 8 -> 9), danach testuser "Bericht-A.txt", alice "Bericht-B.txt": erwartet |
| 4 EN, FR, zh_TW 375 dunkel | Texte richtig; Zahlen im Format fr_FR, da das Admin-Konto diese Locale hat (gewollt); waagerechtes Scrollen auch auf 375, gleiche Ursache wie V-45-10-07 |
| 5 Neuerungen seit 45-17 | E3 unter M1: alice nur Dateiname bei `vt45e3ohne`/`vt45e3mit`, bob Ausschnitt. policy_blocked live: "Durch eine Regel blockiert", 1 Fehlgeschlagen, Hinweis samt "vt45e3tag.odt (ID 146)". Hinweis #25 live in DE. Platzhalter Diagnose "alice/files/Verträge/Miete.pdf", "Sicherungen", "*.photoslibrary". P-LCK aus dem Volltest (`bilder/zustand/lck-apcu-*`) |

Befunde: V-45-10-07 (MEDIUM, Fix beschlossen), I-45-10-04 und I-45-10-06 für 1.7.1, I-45-10-07 aus Nextcloud selbst.

Panne in der Testumgebung: Um `vt45e3tag.odt` neu einlesen zu lassen, lud der Koordinator die Datei als bob per curl herunter und wieder hoch. Der Download war unter Secure View gesperrt (403), so ersetzte der Fehlertext den Inhalt. Sofort über die Versionen wiederhergestellt (`MOVE .../versions/146/1795621942` nach `restore/target`, 201; 786 Bytes, ODT). Die Version 1795677254 mit dem Fehlertext steht weiter im Verlauf. Nur Testdaten betroffen; Wasserzeichen danach zurück auf M1 (`watermark_allTags` no).

Entscheid des Owners: abgenommen mit Änderung V-45-10-07 ("Ok", 2026-11-26 14:40 UTC). Nach dem Fix folgt eine kurze zweite Sichtprüfung.
