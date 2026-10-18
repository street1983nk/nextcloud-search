# Phase 33 Plan 10: Abnahmeprotokoll (Proben vorab und Abnahme durch den Owner)

**Stand:** Task 1 erledigt (Proben vorab, 18.10.2026). Task 2 (gemeinsame Runde mit dem Owner)
steht aus; dieses Protokoll ist ihre Vorlage. Keine Selbstabnahme (D-33-02): die Spalte
"Ergebnis" sagt nur, ob die Maschine die Erwartung gesehen hat, nicht ob der Owner den Wortlaut
abnimmt.

## Stand

| Punkt | Wert |
|---|---|
| Datum | 18.10.2026, Beginn 21:04 Ortszeit (19:04Z), Proben bis 21:22 |
| Commit | `6af42d77` (main, gleich origin/main) |
| Instanz | `findling-nextcloud`, http://localhost:8090, Nextcloud 34.0.3, `php/` als Bind-Mount von main |
| Apps | findling 1.4.2 (`php/` von main), findling_backend 1.4.2 als Host-Prozess auf Port 10035 (Heartbeat 200), app_api 34.0.0 |
| Regeln vorher | `exclusions` = `["Archiv"]`, `exclusion_patterns` fehlt (`config:app:get` Exit 1), Queue 0, Kanarie 1 Treffer |
| Browser | Playwright 1.63 (Node, Chromium headless), Viewport 1600 x 1000; vor jeder Sichtprobe alle Findling-Skripte und -Stile per `fetch(url,{cache:'reload'})` neu geladen, dann die Seite neu geladen |
| Sprache | Nutzereinstellung des Admins (`occ user:setting admin core lang` de, en, fr), am Ende wieder `de` wie vorher |
| Suche | OCS `/ocs/v2.php/search/providers/findling/search` als testuser und Unified Search im Browser als testuser |
| Bildschirmfotos, Rohprotokoll, Skripte | Scratch `C:\Users\Student\AppData\Local\Temp\claude\C--Users-Student\ff065565-87a8-4a94-8154-2bd2009e899b\scratchpad\abnahme3310\` (`protokoll.log` mit Zeitstempel je ERWARTUNG vor dem ERGEBNIS, JSON je Probe) |

Bildnamen unten sind Dateien in diesem Ordner. Die Bilder mit Präfix `p1-` stammen aus dem ersten
Lauf (vor dem Speichern, leere Musterliste); dort verdeckt die feste Kopfleiste von Nextcloud die
oberste Zeile des Blocks. Ab Probe 3 (zweiter Lauf) und bei `p1b-` sind die Blöcke mit einem
höheren Viewport mittig aufgenommen, ohne Verdeckung. Passwörter stehen in keiner Datei dieses
Protokolls; die Skripte lesen das Admin-Passwort aus `scripts/dev/compose.yaml`.

## Saat (WebDAV, testuser)

Wörter ohne deutsche Wortbestandteile (zyq-Muster wie 33-09). Vorher je 0 Treffer, Kanarie 1.

| Kürzel | Pfad | Wort | Datei-ID | nach der Indexierung |
|---|---|---|---|---|
| P | `/Abnahme33/Mediathek.photoslibrary/database/notiz.txt` | zyqpemar | 3018 | 1 Treffer |
| Q (Kontrolle) | `/Abnahme33/Kontrolle/notiz.txt` | zyqquilo | 3019 | 1 Treffer |
| P2 (für Probe 8, nach dem Speichern) | `/Abnahme33/Mediathek.photoslibrary/database/notiz2.txt` | , | 3020 | nie eingereiht |

Alle MKCOL und PUT 201; Queue direkt danach je eine Zeile für 3018 und 3019, abgeholt
(`claimed=2 indexed=2`), P 1 und Q 1 um 21:05:46.

## Proben

| Nr. | Probe | Erwartung (vorher notiert) | Ergebnis | Bilder |
|---|---|---|---|---|
| 1 | Regelblock | Ordnerliste mit `Archiv`, darunter leere Liste "Excluded patterns" mit Hilfesatz, zwei Beispielen als code, Leer-Satz; je de, en, fr | erfüllt in allen drei Sprachen: Ordnerliste `Archiv` (Leer-Satz verborgen), Ordnerhilfe mit neuem Satz, Label der Musterliste, Hilfesatz mit `*.photoslibrary` und `*/node_modules/*` als code-Elemente, Leer-Satz sichtbar, Platzhalter `*.photoslibrary`, `maxlength` 60, Knopf "Add pattern" | `p1-regelblock-de.png`, `p1-regelblock-en.png`, `p1-regelblock-fr.png`; Endstand mit Muster `p1b-regelblock-{de,en,fr}.png` |
| 2 | `*.photoslibrary` eintragen und speichern | Bestätigung ohne Zahl, Muster im code-Element, Ordnerzeile verborgen; gespeichert; nach cron.php und Poller P 0, Q 1 in der Unified Search | erfüllt. Bestätigung in en und fr gezeigt und mit "Keep files indexed" abgebrochen, in de angenommen; keine Ziffer im Satz außerhalb des Musters, Muster als Textknoten im code-Element, Ordnerzeile verborgen. Rückmeldung "Regeln gespeichert. Der nächste Lauf übernimmt sie."; Anfragen: 3 Vorschau-POST, genau 1 POST `/admin/rules`; appconfig `exclusion_patterns` = `["*.photoslibrary"]`, `exclusions` unverändert `["Archiv"]`; genau ein ExclusionSweepJob. cron.php (21:08): Kehrjob weg, Löschzeilen für 3018 und (wie Hinweis H1 in 33-09) für 289 und 290 unter `Archiv`, keine für 3019; Poller holte sie nach 24 s ab. OCS P 0, Q 1; Unified Search im Browser als testuser: P "Keine passenden Suchergebnisse", Findling-Antwort leer; Q Gruppe "Dateiinhalte" mit `notiz.txt`, "Notiz Kontrolle zyqquilo" | `p2-bestaetigung-en.png`, `p2-bestaetigung-fr.png`, `p2-bestaetigung-de.png`, `p2-gespeichert-de.png`, `p2-suche-zyqpemar.png`, `p2-suche-zyqquilo.png` |
| 3 | Ablehnungen sichtbar | je Code der Satz am Musterfeld, Kopfzeile "nicht gespeichert", keine Bestätigung, kein Speicher-POST; 61 Zeichen und 33. Muster lokal abgelehnt; appconfig byte-gleich | erfüllt in de, en, fr (Sätze siehe Wortlaut-Tabelle B). `[0-9]*`, `**/x`, `!foo`, `*`, `node_modules`: Vorschau HTTP 400, Satz am Musterfeld, Kopfzeile unter dem Speicherknopf, keine Bestätigung, 0 Speicher-POST. 61 Zeichen: `fill` kommt mit 60 an (`maxlength`), per Skript gesetzt lokal "too_long", keine Zeile. 33. Muster: lokal "too_many", 32 Zeilen. Am Formular vorbei (gleiche Sitzung): 61 Zeichen 400 `too_long`, 33 Muster 400 `too_many`. appconfig vor und nach beiden Läufen `cmp`-gleich, kein Kehr- oder Expand-Job | `p3-r01-{de,en,fr}.png` (`[0-9]*`), `p3-r02-*` (`**/x`), `p3-r03-*` (`!foo`), `p3-r04-*` (`*`), `p3-r07-*` (`node_modules`), `p3-r05-*` (61 Zeichen), `p3-r06-*` (33. Muster) |
| 3a | Threat-Probe T-33-31 `*<img src=x>*` | Ablehnung oder Text, kein neues DOM-Element, kein Dialog | erfüllt als **Text**: Das Muster ist gültig (nur `[ ] { } \` sind gesperrt), die Zeile zeigt es escaped (`*&lt;img src=x&gt;*` im span und im `aria-label`), die Bestätigung zeigt es als Textknoten im code-Element; `img[src=x]` vorher 0, nachher 0; 0 Dialoge; Bestätigung abgebrochen, 0 Speicher-POST, appconfig unverändert. Hinweis: Die Gesamtzahl `img` stieg in jeder Teilprobe gleich um 2 (37 auf 39, auch bei `[0-9]*`), also unabhängig vom Muster | `p3-r08-{de,en,fr}.png` |
| 4 | Grenzblock "Limits per file" | vier Zeilen mit Werten und Variablennamen, Änderungshinweis mit Befehl als code, Link in Tag-URL-Form, kein Eingabeelement; Abschnitt über `blob/main` mit Anker | erfüllt in de, en, fr: Datei 50,0 MB (`FINDLING_MAX_FILE_BYTES`), Speicher 512,0 MB (`FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`), Zellen 200.000 (`FINDLING_MAX_CELLS`), Seiten 30 in der Profilform "aus dem Profil Sparsam" (Umgebungsform verborgen, Quelle `profile`); Hinweis mit `occ app_api:app:unregister findling_backend` als code; Link `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/admin-page.md#limits-per-file`, `target="_blank"`, `rel="noreferrer noopener"`; 0 Eingabeelemente. `blob/main/docs/admin-page.md#limits-per-file`: HTTP 200, Anker `user-content-limits-per-file` genau 1, Überschrift "Grenzen je Datei ändern". **Tag-Link geht erst mit v1.5.0 auf** (heute 404, kein Tag `v1.5*` am Remote) | `p1-grenzblock-{de,en,fr}.png`, `p1b-grenzblock-{de,en,fr}.png`, `p4-doku-anker-main.png` |
| 5 | Feld "Largest file to read" | alter AppAPI-Satz weg, neuer Satz da | erfüllt in de, en, fr: "The backend of this instance reads at most 50 MB. This ceiling is a deploy option, see "Limits per file"." und Übersetzungen; kein "AppAPI" und kein "restarts the container" im Hilfetext; Feld `max` 50 | `p1-regelblock-{de,en,fr}.png` (unter dem Feld) |
| 6 | Hardware-Satz `hardware_short` | an der Instanz auslösen, sonst begründen | **nicht auslösbar**, Begründung unten (Abschnitt "Probe 6"); der Satz steht in der Wortlaut-Tabelle F. Sichtbar sind die übrigen G5-Sätze des Profilblocks ("Wie viel der Server-Hardware ...", "Vorschlag für diese Hardware: ...", "Ein Profil wählen und auf diesem Server prüfen. ...") | `p1-profil-de.png`, `p1b-profil-de.png`, `p6-profil-8096-vorher.png` |
| 7 | Diagnose der P-Datei | "Excluded by a rule" mit Abhilfe, die beide Listen nennt; je de, en, fr | erfüllt: Chip "Ausgeschlossen" / "Excluded" / "Exclu", Pfad `testuser/files/Abnahme33/Mediathek.photoslibrary/database/notiz.txt`, Label "Durch Regel ausgeschlossen" / "Excluded by a rule" / "Exclu par une règle", Abhilfe nennt beide Listen (Tabelle D). Meine Vorab-Erwartung nannte den Chip "übersprungen" und das Label "Durch eine Regel ausgeschlossen"; beides ist der Katalogbestand seit Phase 4, kein Befund. `occ findling:diagnose 3018`: `skipped` / `excluded`, gleiche Abhilfe; Kontrolle 3019 `indexed` | `p7-diagnose-de.png`, `p7-diagnose-en.png`, `p7-diagnose-fr.png` |
| 8 | Kacheln nach Recount, Fehlerliste | Kachel "Excluded by a rule" gestiegen, Fehlerliste ohne Bundle-Einträge | erfüllt, mit Vermerk: Die Ausgangskachel 3 war ein Zählstand vom 14.10. (enthielt noch die gelöschte 33-09-Datei `Archiv/alt.txt`). Erster Recount nach dem Speichern (19:12:20Z): `excluded` 3 = 289, 290 (`Archiv`) und 3018 (P). Gegenprobe P2 (3020) unter dem Bundle: PUT 201, keine Queue-Zeile; erzwungener ScanRecountJob (`occ background-job:execute --force-execute`) und cron.php: `excluded` 4, Kachel "Durch Regel ausgeschlossen" **4**. Fehlerliste: keine Urteilszeile unter `Abnahme33` (SQL `findling_file_state` 0 Zeilen), kein `photoslibrary` im Text der Liste. Die Saat dieses Plans trägt keine Urteilszeile im Bundle; das Verschwinden einer solchen Zeile (B2) ist in 33-09 A11 belegt | `p8-kacheln-de.png`, `p8-fehlerliste-de.png` |
| 9 | Konsole der Admin-Seite | keine Fehler aus admin.js über alle Proben | erfüllt: 0 `pageerror`, 0 Konsolenfehler aus `admin.js` in allen Läufen; dazu 45 s Admin-Seite mit Poll (`GET /admin/overview`) ohne Fehler. Die einzigen Konsolenzeilen vom Typ error sind Netzmeldungen des Browsers "Failed to load resource: 400" für die absichtlich abgelehnten Vorschau- und Speicher-POSTs aus Probe 3 | `p9-seite-de-ganz.png`, `p9-regelblock-endstand-de.png` |

Logprobe (zusätzlich, Regression L-33-09-01): `nextcloud.log` ab 19:04Z 37 Zeilen, darunter
18 "refused an exclusion pattern that is not a usable pattern", 15 "refused to preview a list of
exclusions that did not validate", 3 "refused a set of rules that did not validate" (Positivkontrolle:
die Ablehnungen stehen da). Darin `photoslibrary`, `img src`, `0-9`, `node_modules`, `!foo`,
`probe0`, `Ordner/aaa`, `Archiv`, `zyq` je 0.

## Probe 6: warum der Hardware-Satz nicht auslösbar ist

- 8090: Das Host-Backend läuft unter Windows und meldet keinen Arbeitsspeicher (Seite: "Dieses
  Backend meldet seine Hardware noch nicht.", Rohwert Kerne 12, Speicher 0 B). `judge_hardware()`
  in `backend/src/findling/probe.py` antwortet dann vor jeder Messung mit `memory_unknown`, nicht
  mit `hardware_short`. Eine Prüfung auf Leistung zeigte also den falschen Satz; sie wurde nicht
  gestartet.
- 8096 (HaRP-Instanz, gleicher `php/`-Bind-Mount, Backend-Container sieht 12 Kerne und 7,6 GB, wäre
  für Leistung zu klein): Das Admin-Passwort aus `compose-harp.yaml` passt nicht ("Wrong login or
  password"). Ein befristetes App-Passwort (`abnahme3310`, ID 13) zeigte die Seite: "Die Prüfung
  braucht das Backend, und es antwortet gerade nicht." Das Backend dort meldet seit dem Start
  "the queue did not answer" (HaRP-Anbindung nicht verbunden). Keine Prüfung gestartet; App-Passwort
  gelöscht (danach 401), Sprache dort unverändert `de_DE`. Bild `p6-profil-8096-vorher.png`.
- Folge: Der Satz wird in der Runde über die Wortlaut-Tabelle F gezeigt (siehe Owner-Frage O4).

## Wortlaut auf der Seite (de, en, fr)

Alle Werte sind von der laufenden Seite gelesen (JSON im Scratch: `p1-block.json`,
`p2-muster.json`, `p3-ablehnung.json`, `p78-diagnose.json`) und zeichengleich mit
33-WORTLAUT.md.

### A: Musterliste und Ordnerhilfe

| Schlüssel (en, wie gezeigt) | de | fr | Bild |
|---|---|---|---|
| Excluded patterns | Ausgeschlossene Muster | Motifs exclus | `p1-regelblock-*.png` |
| Matched against the path as the lists on this page show it. * stands for any number of characters, also across folders. ? stands for exactly one character within a name. Upper and lower case count. Examples: `*.photoslibrary` and `*/node_modules/*` | Vergleich mit dem Pfad, wie ihn die Listen dieser Seite zeigen. * steht für beliebig viele Zeichen, auch über Ordner hinweg. ? steht für genau ein Zeichen innerhalb eines Namens. Groß- und Kleinschreibung zählt. Beispiele: `*.photoslibrary` und `*/node_modules/*` | Comparaison avec le chemin tel que les listes de cette page l'affichent. * remplace un nombre quelconque de caractères, y compris à travers les dossiers. ? remplace exactement un caractère dans un nom. Les majuscules et les minuscules comptent. Exemples : `*.photoslibrary` et `*/node_modules/*` | `p1-regelblock-*.png` |
| No pattern is set. | Kein Muster ist gesetzt. | Aucun motif n'est défini. | `p1-regelblock-*.png` |
| Add pattern | Muster hinzufügen | Ajouter un motif | `p1-regelblock-*.png` |
| Remove pattern *.photoslibrary (aria-label) | Muster *.photoslibrary entfernen | Supprimer le motif *.photoslibrary | (nur vorgelesen) |
| Prefix match on the path as the lists on this page show it, without wildcards. For wildcards use "Excluded patterns". Example: Backups | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, ohne Platzhalter. Für Platzhalter "Ausgeschlossene Muster" verwenden. Beispiel: Backups | Comparaison par préfixe sur le chemin tel que les listes de cette page l'affichent, sans caractères génériques. Pour les caractères génériques, utiliser "Motifs exclus". Exemple : Backups | `p1-regelblock-*.png` |

### B: Ablehnungen (Kopfzeile und Satz am Musterfeld)

| Fall | en | de | fr | Bild |
|---|---|---|---|---|
| Kopfzeile | The rules were not saved. Nothing changed. | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | Les règles n'ont pas été enregistrées. Rien n'a changé. | `p3-r01-*.png` |
| `[0-9]*` | Brackets, braces and the backslash are not allowed. Only * and ? are wildcards. | Eckige und geschweifte Klammern sowie der Backslash sind nicht erlaubt. Nur * und ? sind Platzhalter. | Les crochets, les accolades et la barre oblique inverse ne sont pas autorisés. Seuls * et ? sont des caractères génériques. | `p3-r01-*.png` |
| `**/x` | Use a single *: it already matches across folders. | Einen einfachen * verwenden: Er gilt bereits über Ordner hinweg. | Utiliser un seul * : il couvre déjà plusieurs niveaux de dossiers. | `p3-r02-*.png` |
| `!foo` | A leading ! is not supported. Patterns only exclude. | Ein führendes ! wird nicht unterstützt. Muster schließen nur aus. | Un ! initial n'est pas pris en charge. Les motifs ne font qu'exclure. | `p3-r03-*.png` |
| `*` | A pattern needs at least one character besides * and ?, otherwise it would exclude everything. | Ein Muster braucht mindestens ein Zeichen außer * und ?, sonst schlösse es alles aus. | Un motif doit contenir au moins un caractère autre que * et ?, sinon il exclurait tout. | `p3-r04-*.png` |
| `node_modules` | This entry has no * or ?. Add it under "Excluded folders" instead. | Dieser Eintrag enthält weder * noch ?. Ihn stattdessen unter "Ausgeschlossene Ordner" eintragen. | Cette entrée ne contient ni * ni ?. L'ajouter plutôt sous "Dossiers exclus". | `p3-r07-*.png` |
| 61 Zeichen | A pattern may be at most 60 characters long. | Ein Muster darf höchstens 60 Zeichen lang sein. | Un motif peut compter au maximum 60 caractères. | `p3-r05-*.png` |
| 33. Muster | At most 32 patterns are allowed. | Höchstens 32 Muster sind erlaubt. | Au maximum 32 motifs sont autorisés. | `p3-r06-*.png` |

### C: Bestätigung (ohne Zahl)

| en | de | fr | Bild |
|---|---|---|---|
| Remove indexed content? Excluding `*.photoslibrary` also removes the already indexed documents that match that pattern from the index. The files themselves stay untouched on disk. | Indexierte Inhalte entfernen? Der Ausschluss von `*.photoslibrary` entfernt außerdem die bereits indexierten Dokumente, auf die dieses Muster passt, aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Supprimer les contenus indexés ? L'exclusion de `*.photoslibrary` retire également de l'index les documents déjà indexés qui correspondent à ce motif. Les fichiers eux-mêmes restent intacts sur le disque. | `p2-bestaetigung-{en,fr,de}.png` |

Die Mehrzahlform ("... match these patterns ...") erschien in dieser Runde nicht (ein neues Muster je
Speichern); sie war in 33-09 A5 mit zwei Mustern auf der Seite.

### D: Diagnose-Abhilfe

| en | de | fr | Bild |
|---|---|---|---|
| Remove the matching entry under "Excluded folders" or "Excluded patterns". | Den passenden Eintrag unter "Ausgeschlossene Ordner" oder "Ausgeschlossene Muster" entfernen. | Supprimer l'entrée correspondante sous "Dossiers exclus" ou "Motifs exclus". | `p7-diagnose-{de,en,fr}.png` |

### E: Grenzblock und Satz unter "Largest file to read"

| en | de | fr | Bild |
|---|---|---|---|
| Limits per file | Grenzen je Datei | Limites par fichier | `p1-grenzblock-*.png` |
| Largest file the backend reads: 50.0 MB (`FINDLING_MAX_FILE_BYTES`) | Größte Datei, die das Backend liest: 50,0 MB (`FINDLING_MAX_FILE_BYTES`) | Plus grand fichier lu par le service : 50,0 Mo (`FINDLING_MAX_FILE_BYTES`) | `p1-grenzblock-*.png`, fr nach dem Fix `fix-grenzblock-fr.png` |
| Memory one document may use while it is read: 512.0 MB (`FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`) | Speicher, den ein Dokument beim Lesen belegen darf: 512,0 MB (`FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`) | Mémoire qu'un document peut occuper pendant sa lecture : 512,0 Mo (`FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`) | `p1-grenzblock-*.png`, fr nach dem Fix `fix-grenzblock-fr.png` |
| Cells read per spreadsheet file: 200,000 (`FINDLING_MAX_CELLS`) | Gelesene Zellen je Tabellendatei: 200.000 (`FINDLING_MAX_CELLS`) | Cellules lues par classeur : 200 000 (`FINDLING_MAX_CELLS`) | `p1-grenzblock-*.png` |
| Pages read per scanned document: 30, from the profile Economy | Gelesene Seiten je gescanntem Dokument: 30, aus dem Profil Sparsam | Pages lues par document numérisé : 30, selon le profil Économe | `p1-grenzblock-*.png` |
| These limits are deploy options of Findling Backend. To change one, run `occ app_api:app:unregister findling_backend`, which keeps the data, and deploy Findling Backend again with the new value. | Diese Grenzen sind Deploy-Optionen von Findling Backend. Zum Ändern `occ app_api:app:unregister findling_backend` ausführen, was die Daten behält, und Findling Backend mit dem neuen Wert erneut bereitstellen. | Ces limites sont des options de déploiement de Findling Backend. Pour en modifier une, exécuter `occ app_api:app:unregister findling_backend`, ce qui conserve les données, puis redéployer Findling Backend avec la nouvelle valeur. | `p1-grenzblock-*.png` |
| Steps in the documentation | Schritte in der Dokumentation | Étapes dans la documentation | `p1-grenzblock-*.png` |
| The backend of this instance reads at most 50 MB. This ceiling is a deploy option, see "Limits per file". | Das Backend dieser Instanz liest höchstens 50 MB. Diese Obergrenze ist eine Deploy-Option, siehe "Grenzen je Datei". | Le service de cette instance lit au maximum 50 Mo. Ce plafond est une option de déploiement, voir "Limites par fichier". | `p1-regelblock-*.png` |
| Einheit am Feld "Largest file to read": MB | Einheit am Feld: MB | Unité du champ : Mo | `fix-regelblock-{fr,de}.png` |

Die Umgebungsform der Seitenzeile ("Pages read per scanned document: %1$s (%2$s)") ist an dieser
Instanz verborgen (Quelle `profile`); ihr Wortlaut steht in 33-WORTLAUT.md E.

**Owner-Entscheid O1 vom 18.10.2026:** "fr angleichen sonst abgenommen", Richtung auf Rückfrage
"Mo überall". Umgesetzt in Task 3: Die sechs Einheitensymbole der Seite (`B`, `KB`, `MB`, `GB`,
`TB`, `PB`) sind eigene Katalogschlüssel, im Größenformat des Templates (`$size`), im Formatierer
des Skripts (`sizeUnits()`) und als Einheit am Feld "Largest file to read". Nur fr weicht ab
(o, Ko, Mo, Go, To, Po), alle anderen Sprachen behalten das englische Symbol als Wert. Die Sätze
"... lit au maximum %s Mo" und "Saisir une taille comprise entre %1$s et %2$s Mo." schrieben
schon vorher Mo und blieben unverändert. Probe an 8090 nach dem Fix: fr zeigt "50,0 Mo",
"512,0 Mo" und am Feld "Mo" (`fix-grenzblock-fr.png`, `fix-regelblock-fr.png`), de unverändert
"50,0 MB", "512,0 MB" und "MB" (`fix-grenzblock-de.png`, `fix-regelblock-de.png`).

### F: Hardware-Satz und weitere G5-Sätze

| Satz | en | de | fr | Bild |
|---|---|---|---|---|
| `hardware_short` (nicht ausgelöst, aus dem Template) | Findling sees fewer CPU cores or less memory than this profile requires. Standard requires at least 3 cores and 6 GB of memory, Performance at least 6 cores and 12 GB. If the backend container has a memory or CPU limit, that limit counts. | Findling sieht weniger CPU-Kerne oder weniger Arbeitsspeicher, als dieses Profil verlangt. Standard verlangt mindestens 3 Kerne und 6 GB Arbeitsspeicher, Leistung mindestens 6 Kerne und 12 GB. Ist der Backend-Container begrenzt, zählt diese Grenze. | Findling voit moins de cœurs de processeur ou moins de mémoire que ce profil n'en demande. Standard demande au moins 3 cœurs et 6 Go de mémoire, Performance au moins 6 cœurs et 12 Go. Si le conteneur du service est limité, c'est cette limite qui compte. | keins (O4) |
| Vorschlag | Suggested for this hardware: Economy | Vorschlag für diese Hardware: Sparsam | Suggéré pour ce matériel : Économe | `p1-profil-de.png` |
| Gewählt/wirksam (verborgen, aus dem DOM gelesen) | Chosen Economy, in force Economy: Findling sees less hardware than the chosen profile requires. | Gewählt Sparsam, wirksam Sparsam: Findling sieht weniger Hardware, als das gewählte Profil verlangt. | Choisi Économe, en vigueur Économe : Findling voit moins de matériel que le profil choisi n'en demande. | keins |
| Profilblock (nur de geprüft) | How much of the server's hardware Findling may use. ... / Choose a profile and check it on this server. ... (33-WORTLAUT.md F) | Wie viel der Server-Hardware Findling nutzen darf. Ohne Änderung bleibt Findling bei Sparsam. / Ein Profil wählen und auf diesem Server prüfen. Bis dahin bleibt Sparsam wirksam. | (33-WORTLAUT.md F) | `p1b-profil-de.png` |

## Endstand nach Task 1 (für die gemeinsame Runde)

- `exclusions` = `["Archiv"]`, `exclusion_patterns` = `["*.photoslibrary"]` (bleibt für die Runde gespeichert).
- Saat liegt: `/Abnahme33` mit P (3018), P2 (3020) und Q (3019). Suche P 0, Q 1, Kanarie 1.
- Queue 0, kein Kehr-, Expand- oder Crawl-Job; Sprache des Admins `de` wie vorher.
- Kein Produktcode geändert, kein Commit außer diesem Protokoll.

## Offene Fragen an den Owner

- **O1 Einheiten im Französischen** (entschieden 18.10.2026: "fr angleichen", "Mo überall",
  umgesetzt in Task 3, siehe Tabelle E): Der Grenzblock schrieb in fr "50,0 MB" und "512,0 MB"
  (Größenformat der Seite, `$size`, in allen Sprachen MB), der Satz direkt darüber sagt "50 Mo".
  So lassen (Konvention der Seite) oder für fr "Mo" vorsehen (Formatfrage, eigener Schritt)?
- **O2 Ablehnung und Zeile:** Nach einer Ablehnung bleibt der Eintrag als ungespeicherte Zeile in
  der Liste stehen, ohne Markierung, welche Zeile gemeint ist (Abweichung 1 in 33-05: die Antwort
  trägt keinen Zeilenbezug). Der Satz steht am Musterfeld, die Kopfzeile "nicht gespeichert" rund
  600 Pixel tiefer unter dem Speicherknopf (`p3-r01-de.png`). Verständlich so?
- **O3 Muster mit Markup:** `*<img src=x>*` ist ein gültiges Muster (nur Klammern und Backslash
  sind gesperrt) und erscheint als Text. Recht so, oder sollen `<` und `>` abgelehnt werden
  (neuer Code, eigener Plan)?
- **O4 Hardware-Satz:** An 8090 nicht auslösbar (Host-Backend ohne Speicherangabe), an 8096
  antwortet das Backend nicht und das Admin-Passwort aus der Compose-Datei passt nicht. Für die
  Runde: (a) Satz über die Tabelle F lesen, (b) 8096 gemeinsam reparieren (HaRP-Anbindung,
  Admin-Zugang vom Owner) und dort eine Prüfung auf Leistung starten, (c) anderer Weg?
- **O5 Probe 8:** Die Kachel stieg erst mit der Gegenprobe P2 sichtbar (3 auf 4), weil der alte
  Zählstand eine inzwischen gelöschte Datei enthielt. Die Fehlerliste war ohne Bundle-Einträge,
  weil die Saat keine Urteilszeile im Bundle hat; das Verschwinden solcher Zeilen belegt 33-09 A11.
  Genügt das, oder soll die Runde ein Bild unter einem Bundle mit Urteilszeile zeigen?
- **Vermerk:** Tag-Link geht erst mit v1.5.0 auf.

## Abnahme durch den Owner

Steht aus (Task 2). Der Eintrag mit Datum und wörtlicher Antwort folgt hier; bewusst noch ohne
die Marke, die die Prüfung von Task 2 sucht.
