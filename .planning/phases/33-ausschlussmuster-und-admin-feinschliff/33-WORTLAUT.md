# Phase 33: Wortlaut-Entwurf (en, de, fr)

Stand: 13.10.2026, Entwurf aus Plan 33-01 Task 1 auf Basis von Commit c9b76321.
Status: **vom Owner abgenommen am 13.10.2026**, unverändert in en, de und fr (siehe "Owner-Abnahme" am Ende).

Grundlage: 33-CONTEXT.md (D-30-01, D-33-01 bis D-33-03), 33-01-PLAN.md (PE-1 bis PE-10),
33-RESEARCH.md (Muster-Semantik, Grenzwerte für #21, Hardware-Hinweis).

Regeln für alle Zeilen:

- Schlüssel = englischer Quelltext, genau so, wie er in `t()` stehen wird.
- Kein Satz enthält den eingegebenen Wert. Platzhalter `%s` in Fehlermeldungen tragen nur Grenzzahlen.
- Variablennamen, Befehle und Beispielmuster stehen nie im übersetzten Satz, sondern als Code-Marker
  (`%1$s`, `%2$s` an der Stelle des Markers, Technik der env-Zeilen `admin.php:1118-1131`).
- Deutsch folgt dem Katalogbestand (Infinitiv bei Handlungsanweisungen, "Einen Ordnerpfad eingeben.").
- Französisch nach `docs/l10n-french.md`: ASCII-Apostroph, einfaches Leerzeichen vor `:`, `;`, `?`, `!`,
  "service" für backend wie im Bestand.
- es, it, nl, pt_BR, pt_PT stehen nicht hier; 33-07 leitet sie nach der Abnahme ab.
- Vokabelgate (gesperrter Wortstamm aus `test_public_artifacts.py` und `test_store_metadata.py`) und
  Strichprüfung (U+2013, U+2014) über alle Entwurfstexte gelaufen: kein Fund.

## (A) Musterliste "Excluded patterns" (PE-1)

Platz: Template `admin.php`, Block "Rules and limits", direkt unter der Ordnerliste; die Zeilenvorlage
wird gespiegelt. Wie bei der Ordnerliste benennt das Label Liste und Eingabefeld zugleich (kein zweiter
Label-Schlüssel). Platzhalter im Eingabefeld: `*.photoslibrary`, unübersetzt wie heute `Backups`.

| Schlüssel (en) | de | fr | Stelle | Platzhalter |
|---|---|---|---|---|
| Excluded patterns | Ausgeschlossene Muster | Motifs exclus | Template (Label) | keine |
| Matched against the path as the lists on this page show it. * stands for any number of characters, also across folders. ? stands for exactly one character within a name. Upper and lower case count. Examples: %1$s and %2$s | Vergleich mit dem Pfad, wie ihn die Listen dieser Seite zeigen. * steht für beliebig viele Zeichen, auch über Ordner hinweg. ? steht für genau ein Zeichen innerhalb eines Namens. Groß- und Kleinschreibung zählt. Beispiele: %1$s und %2$s | Comparaison avec le chemin tel que les listes de cette page l'affichent. * remplace un nombre quelconque de caractères, y compris à travers les dossiers. ? remplace exactement un caractère dans un nom. Les majuscules et les minuscules comptent. Exemples : %1$s et %2$s | Template (Hilfe) | `%1$s` = Marker `<code>*.photoslibrary</code>`, `%2$s` = Marker `<code>*/node_modules/*</code>` |
| No pattern is set. | Kein Muster ist gesetzt. | Aucun motif n'est défini. | Template + Skript (Leer-Satz) | keine |
| Add pattern | Muster hinzufügen | Ajouter un motif | Template (Knopf) | keine |
| Remove pattern %s | Muster %s entfernen | Supprimer le motif %s | Template + Skript (aria-label je Zeile) | `%s` = das gespeicherte Muster der Zeile (wie "Remove exclusion %s", keine Fehlermeldung) |

Geänderter Hilfesatz der Ordnerliste (Schlüsselwechsel, Schlüsselzahl gleich):

| | en | de | fr |
|---|---|---|---|
| alt | Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, keine Platzhalter und keine Muster. Beispiel: Backups | Comparaison par préfixe sur le chemin tel que les listes de cette page l'affichent, sans caractères génériques ni motifs. Exemple : Backups |
| neu | Prefix match on the path as the lists on this page show it, without wildcards. For wildcards use "Excluded patterns". Example: Backups | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, ohne Platzhalter. Für Platzhalter "Ausgeschlossene Muster" verwenden. Beispiel: Backups | Comparaison par préfixe sur le chemin tel que les listes de cette page l'affichent, sans caractères génériques. Pour les caractères génériques, utiliser "Motifs exclus". Exemple : Backups |

Stelle: Template (`admin.php:1261`). Platzhalter: keine.

## (B) Fehlermeldungen je Code (PE-2, PE-7)

Kopfzeile bleibt unverändert: "The rules were not saved. Nothing changed." / "Die Regeln wurden nicht
gespeichert. Es hat sich nichts geändert." / "Les règles n'ont pas été enregistrées. Rien n'a changé."
Darunter erscheint je Feld der Satz des Codes (Skript, Feldfehler unter dem jeweiligen Eingabefeld).
Wo die Ordnerliste einen Satz schon hat, wird er wiederverwendet (kein neuer Schlüssel).
"Gilt für" nennt die Liste; "nur Muster" heißt: die Ordnerliste vergibt den Code nicht (Präfixe bleiben
unverändert, Erfolgskriterium 1), die Zeile der Ordnerliste ist dann "entfällt".

| Code | Liste | Schlüssel (en) | de | fr | Platzhalter |
|---|---|---|---|---|---|
| empty | Ordner | Enter a folder path. (Bestand) | Einen Ordnerpfad eingeben. | Saisir un chemin de dossier. | keine |
| empty | Muster | Enter a pattern. | Ein Muster eingeben. | Saisir un motif. | keine |
| too_long | Ordner | A folder path may be at most %s bytes long. | Ein Ordnerpfad darf höchstens %s Byte lang sein. | Un chemin de dossier peut compter au maximum %s octets. | `%s` = 256 |
| too_long | Muster | A pattern may be at most %s characters long. | Ein Muster darf höchstens %s Zeichen lang sein. | Un motif peut compter au maximum %s caractères. | `%s` = 60 |
| too_many | Ordner | At most %s folders can be excluded. | Höchstens %s Ordner lassen sich ausschließen. | Au maximum %s dossiers peuvent être exclus. | `%s` = 64 |
| too_many | Muster | At most %s patterns are allowed. | Höchstens %s Muster sind erlaubt. | Au maximum %s motifs sont autorisés. | `%s` = 32 |
| duplicate | Ordner | This path is already excluded. (Bestand) | Dieser Pfad ist bereits ausgeschlossen. | Ce chemin est déjà exclu. | keine |
| duplicate | Muster | This pattern is already in the list. | Dieses Muster steht bereits in der Liste. | Ce motif figure déjà dans la liste. | keine |
| traversal | beide (ein Schlüssel) | The entry must not contain . or .. as a folder name. | Der Eintrag darf . oder .. nicht als Ordnernamen enthalten. | L'entrée ne doit pas contenir . ou .. comme nom de dossier. | keine |
| double_star | Muster (Ordner: entfällt) | Use a single *: it already matches across folders. | Einen einfachen * verwenden: Er gilt bereits über Ordner hinweg. | Utiliser un seul * : il couvre déjà plusieurs niveaux de dossiers. | keine |
| unsupported_character | Muster (Ordner: entfällt) | Brackets, braces and the backslash are not allowed. Only * and ? are wildcards. | Eckige und geschweifte Klammern sowie der Backslash sind nicht erlaubt. Nur * und ? sind Platzhalter. | Les crochets, les accolades et la barre oblique inverse ne sont pas autorisés. Seuls * et ? sont des caractères génériques. | keine |
| negation | Muster (Ordner: entfällt) | A leading ! is not supported. Patterns only exclude. | Ein führendes ! wird nicht unterstützt. Muster schließen nur aus. | Un ! initial n'est pas pris en charge. Les motifs ne font qu'exclure. | keine |
| control_character | Muster (Ordner: entfällt) | The entry contains a control character. | Der Eintrag enthält ein Steuerzeichen. | L'entrée contient un caractère de contrôle. | keine |
| no_literal | Muster (Ordner: entfällt) | A pattern needs at least one character besides * and ?, otherwise it would exclude everything. | Ein Muster braucht mindestens ein Zeichen außer * und ?, sonst schlösse es alles aus. | Un motif doit contenir au moins un caractère autre que * et ?, sinon il exclurait tout. | keine |
| no_wildcard | Muster (Ordner: entfällt) | This entry has no * or ?. Add it under "Excluded folders" instead. | Dieser Eintrag enthält weder * noch ?. Ihn stattdessen unter "Ausgeschlossene Ordner" eintragen. | Cette entrée ne contient ni * ni ?. L'ajouter plutôt sous "Dossiers exclus". | keine |

Hinweise:

- Zeichen im Satz (`*`, `?`, `.`, `..`, `!`) sind Teil der Erklärung, nicht der eingegebene Wert.
- Der Backslash steht bewusst nicht als Zeichen im Satz, sondern als Wort: kein Escape-Fallstrick in
  JSON, JS und den fünf Sprachtabellen.
- Neue Schlüssel in (B): 13 (empty für Muster, too_long je Liste, too_many je Liste, duplicate für
  Muster, traversal und die sechs reinen Muster-Codes; die zwei Bestandssätze der Ordnerliste werden
  wiederverwendet).

## (C) Bestätigung vor dem Speichern neuer Muster, ohne Zahl (PE-5)

Satzform der zahlenlosen Variante aus `admin.js:1102-1108`. `%s` ist wie beim Bestandssatz die vom Admin
selbst eingetragene Regel (bei mehreren mit Komma verbunden), keine Fehlermeldung und keine Serverantwort.
Einzahl und Mehrzahl als zwei Schlüssel.

| Schlüssel (en) | de | fr | Platzhalter |
|---|---|---|---|
| Remove indexed content? Excluding %s also removes the already indexed documents that match that pattern from the index. The files themselves stay untouched on disk. | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente, auf die dieses Muster passt, aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Supprimer les contenus indexés ? L'exclusion de %s retire également de l'index les documents déjà indexés qui correspondent à ce motif. Les fichiers eux-mêmes restent intacts sur le disque. | `%s` = neues Muster |
| Remove indexed content? Excluding %s also removes the already indexed documents that match these patterns from the index. The files themselves stay untouched on disk. | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente, auf die diese Muster passen, aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Supprimer les contenus indexés ? L'exclusion de %s retire également de l'index les documents déjà indexés qui correspondent à ces motifs. Les fichiers eux-mêmes restent intacts sur le disque. | `%s` = neue Muster, mit Komma |

Stelle: Skript. Kommen in einem Speichern neue Ordner und neue Muster zusammen, zeigt das Skript beide
Sätze untereinander (Festlegung für 33-05, kein neuer Wortlaut).

## (D) Diagnose-Abhilfe mit beiden Listen

Stelle: `AdminViewService.php:490-493`, Schlüsselwechsel, Schlüsselzahl gleich.

| | en | de | fr |
|---|---|---|---|
| alt | Remove the matching entry under "Excluded folders". | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. | Supprimer l'entrée correspondante sous "Dossiers exclus". |
| neu | Remove the matching entry under "Excluded folders" or "Excluded patterns". | Den passenden Eintrag unter "Ausgeschlossene Ordner" oder "Ausgeschlossene Muster" entfernen. | Supprimer l'entrée correspondante sous "Dossiers exclus" ou "Motifs exclus". |

## (E) Grenzblock "Limits per file" (POL-01) und Ersatz des B3-Satzes

Platz: Template, Block "Rules and limits", unter dem Feld "Largest file to read". Jede Zeile trägt den
Wert als `%1$s` (Größen über `$size`, Zahlen über `$count`) und den Variablennamen als Code-Marker
`%2$s`. Eine Zeile ohne Wert aus der Statusantwort bleibt verborgen (Container 1.4.x).

| Schlüssel (en) | de | fr | Platzhalter |
|---|---|---|---|
| Limits per file | Grenzen je Datei | Limites par fichier | keine (Überschrift) |
| Largest file the backend reads: %1$s (%2$s) | Größte Datei, die das Backend liest: %1$s (%2$s) | Plus grand fichier lu par le service : %1$s (%2$s) | `%1$s` = Größe, `%2$s` = Marker `FINDLING_MAX_FILE_BYTES` |
| Memory one document may use while it is read: %1$s (%2$s) | Speicher, den ein Dokument beim Lesen belegen darf: %1$s (%2$s) | Mémoire qu'un document peut occuper pendant sa lecture : %1$s (%2$s) | `%1$s` = Größe, `%2$s` = Marker `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` |
| Cells read per spreadsheet file: %1$s (%2$s) | Gelesene Zellen je Tabellendatei: %1$s (%2$s) | Cellules lues par classeur : %1$s (%2$s) | `%1$s` = Zahl, `%2$s` = Marker `FINDLING_MAX_CELLS` |
| Pages read per scanned document: %1$s (%2$s) | Gelesene Seiten je gescanntem Dokument: %1$s (%2$s) | Pages lues par document numérisé : %1$s (%2$s) | Quelle Umgebung: `%1$s` = Zahl, `%2$s` = Marker `FINDLING_OCR_MAX_PAGES` |
| Pages read per scanned document: %1$s, from the profile %2$s | Gelesene Seiten je gescanntem Dokument: %1$s, aus dem Profil %2$s | Pages lues par document numérisé : %1$s, selon le profil %2$s | Quelle Profil: `%1$s` = Zahl, `%2$s` = Profilname (Economy/Standard/Performance übersetzt) |

Änderungshinweis (vollständiger Weg auf der Seite, Link nur für Details, PE-8):

| Schlüssel (en) | de | fr | Platzhalter |
|---|---|---|---|
| These limits are deploy options of Findling Backend. To change one, run %s, which keeps the data, and deploy Findling Backend again with the new value. | Diese Grenzen sind Deploy-Optionen von Findling Backend. Zum Ändern %s ausführen, was die Daten behält, und Findling Backend mit dem neuen Wert erneut bereitstellen. | Ces limites sont des options de déploiement de Findling Backend. Pour en modifier une, exécuter %s, ce qui conserve les données, puis redéployer Findling Backend avec la nouvelle valeur. | `%s` = Marker `<code>occ app_api:app:unregister findling_backend</code>` (ohne `--rm-data`) |
| Steps in the documentation | Schritte in der Dokumentation | Étapes dans la documentation | keine; Linktext zu `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/admin-page.md#limits-per-file` |

Doku-Stelle (legt 33-06 an): neuer Abschnitt "Grenzen je Datei ändern" in `docs/admin-page.md`, davor
fester Anker `<a id="limits-per-file"></a>`, Inhalt deutsch: Abmelden ohne `--rm-data`, Neuregistrieren
bzw. Deploy mit neuem Wert, Daten bleiben.

Ersatz des falschen Satzes `admin.php:1291` (Befund B3, Schlüsselwechsel, Schlüsselzahl gleich):

| | en | de | fr |
|---|---|---|---|
| alt | The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container. | Das Backend dieser Instanz liest höchstens %s MB. Für mehr FINDLING_MAX_FILE_BYTES in den App-Einstellungen von AppAPI anheben, was den Container neu startet. | Le service de cette instance lit au maximum %s Mo. Pour davantage, augmenter FINDLING_MAX_FILE_BYTES dans les paramètres d'application d'AppAPI, ce qui redémarre le conteneur. |
| neu | The backend of this instance reads at most %s MB. This ceiling is a deploy option, see "Limits per file". | Das Backend dieser Instanz liest höchstens %s MB. Diese Obergrenze ist eine Deploy-Option, siehe "Grenzen je Datei". | Le service de cette instance lit au maximum %s Mo. Ce plafond est une option de déploiement, voir "Limites par fichier". |

Platzhalter: `%s` = Decke in MB (`$count($ceilingMb)`), wie heute.

## (F) POL-03: Satz `hardware_short`

Stellen: `admin.php:1072`, `admin.js:1449`, Test `test_admin_ui_contract.py:2974-2986`. Zahlen aus
`SUGGEST_*` in `backend/src/findling/config.py` (3 Kerne, 6 GB, 6 Kerne, 12 GB), platzhalterfrei wie heute.

| | en | de | fr |
|---|---|---|---|
| alt | This box has fewer cores or less memory than the profile needs: Standard needs 3 cores and 6 GB, Performance 6 cores and 12 GB. | Diese Box hat weniger Kerne oder Speicher, als das Profil braucht: Standard braucht 3 Kerne und 6 GB, Leistung 6 Kerne und 12 GB. | Cette machine a moins de cœurs ou de mémoire que le profil n'en demande : Standard demande 3 cœurs et 6 Go, Performance 6 cœurs et 12 Go. |
| neu | Findling sees fewer CPU cores or less memory than this profile requires. Standard requires at least 3 cores and 6 GB of memory, Performance at least 6 cores and 12 GB. If the backend container has a memory or CPU limit, that limit counts. | Findling sieht weniger CPU-Kerne oder weniger Arbeitsspeicher, als dieses Profil verlangt. Standard verlangt mindestens 3 Kerne und 6 GB Arbeitsspeicher, Leistung mindestens 6 Kerne und 12 GB. Ist der Backend-Container begrenzt, zählt diese Grenze. | Findling voit moins de cœurs de processeur ou moins de mémoire que ce profil n'en demande. Standard demande au moins 3 cœurs et 6 Go de mémoire, Performance au moins 6 cœurs et 12 Go. Si le conteneur du service est limité, c'est cette limite qui compte. |

Abweichung zum Research-Vorschlag: fr "conteneur du service" statt "conteneur du backend", weil der
französische Katalog "backend" durchgehend als "service" führt.

Weitere Sätze mit "box" im Katalog (Frage G5): Der Plan nennt drei, im Katalog stehen sechs.

| Fundstelle | alt (en) | Vorschlag neu (en) | de | fr |
|---|---|---|---|---|
| admin.php:1141 | How much of this box Findling may use. Without a change Findling stays on Economy. | How much of the server's hardware Findling may use. Without a change Findling stays on Economy. | Wie viel der Server-Hardware Findling nutzen darf. Ohne Änderung bleibt Findling bei Sparsam. | Quelle part du matériel du serveur Findling peut utiliser. Sans changement, Findling reste sur Économe. |
| admin.php:1146, admin.js:2024 | Suggested for this box: %s | Suggested for this hardware: %s | Vorschlag für diese Hardware: %s | Suggéré pour ce matériel : %s |
| admin.php:1148, admin.js:2047 | Chosen %1$s, in force %2$s: this box has less hardware than the chosen profile needs. | Chosen %1$s, in force %2$s: Findling sees less hardware than the chosen profile requires. | Gewählt %1$s, wirksam %2$s: Findling sieht weniger Hardware, als das gewählte Profil verlangt. | Choisi %1$s, en vigueur %2$s : Findling voit moins de matériel que le profil choisi n'en demande. |
| admin.php:984 | At most half of this box, up to %s OCR slots. | At most half of the hardware Findling sees, up to %s OCR slots. | Höchstens die Hälfte der Hardware, die Findling sieht, bis zu %s OCR-Slots. | Au plus la moitié du matériel visible, jusqu'à %s slots OCR. |
| admin.php:1021, admin.js:1484 | fp32 is set, but this box has too little memory for it. The search uses int8. | fp32 is set, but Findling sees too little memory for it. The search uses int8. | fp32 ist gesetzt, aber Findling sieht zu wenig Arbeitsspeicher dafür. Die Suche nutzt int8. | fp32 est activé, mais Findling voit trop peu de mémoire pour lui. La recherche utilise int8. |
| admin.php:1224 | Choose a profile and check it on this box. Until then Economy stays in force. | Choose a profile and check it on this server. Until then Economy stays in force. | Ein Profil wählen und auf diesem Server prüfen. Bis dahin bleibt Sparsam wirksam. | Choisir un profil et le vérifier sur ce serveur. D'ici là, Économe reste en vigueur. |

G5 ist mit (c) beantwortet: alle sechs Sätze werden in 33-07 ersetzt.

## (G) Fragen an den Owner

**G1 (D-33-03): Grenzen 32 Muster zu je 60 Zeichen bestätigt?**
- (a) Ja, 32 und 60. Schlimmster Fall 8,4 ms je Schreibvorgang (Prototyp), realistische Muster 15 bis 21 Zeichen.
- (b) Andere Werte, z. B. 64 Muster (schlimmster Fall 17,2 ms je Schreibvorgang, wirkt in jedem Write der Instanz).
- Empfehlung: (a).

**G2 (PE-1): `?` passt nie auf `/`, Groß- und Kleinschreibung wird unterschieden?**
- (a) Ja, wie PE-1. Folge (Annahme A1): eine groß geschriebene Bundle-Endung wie `.KEY` wird von `*.key` nicht getroffen; dazu ein Satz in der Doku, auf der Seite sagt es der Hilfesatz ("Groß- und Kleinschreibung zählt").
- (b) Groß/Klein bei Mustern ignorieren: zwei Vergleichsverhalten auf einer Seite, Präfixe bleiben unterscheidend.
- (c) `?` darf auch `/` treffen (Python-fnmatch-Lesart).
- Empfehlung: (a).

**G3 (PE-2): Muster ohne `*` und `?` ablehnen (Code `no_wildcard`, Hinweis auf "Excluded folders")?**
- (a) Ja, ablehnen. Sonst gibt es zwei Schreibweisen derselben Regel, und ein Literal-Muster wirkte anders als der gleichlautende Präfix (verankert ganzer Name statt Präfix).
- (b) Annehmen und als Muster speichern.
- Empfehlung: (a).

**G4 (PE-4): Urteilszeilen ausgeschlossener Dateien auch beim bestehenden Präfix-Räumen löschen?**
- (a) Ja, in beiden Räumwegen. Treffer der Präfixe bleiben gleich, nur die Fehlerliste wird ehrlich (Befund B2, Issue #22 mit 266k Einträgen).
- (b) Nur beim Räumen nach Mustern.
- Empfehlung: (a).

**G5 (PE-6): Nur `hardware_short` ersetzen oder auch die weiteren "box"-Sätze?**
- (a) Nur `hardware_short` (Planer-Entscheidung PE-6, POL-03 nennt nur diesen Satz).
- (b) Zusätzlich die drei Sätze des Profilblocks, die der Plan nennt (`admin.php:1141`, `1146`, `1148`).
- (c) Alle sechs weiteren Sätze mit "box" (Tabelle unter F), damit das Wort ganz von der Seite verschwindet.
- Empfehlung: (c). Die 16-Dateien-Kette läuft in 33-07 ohnehin einmal; Mehraufwand sind sechs Schlüsselwechsel bei gleicher Schlüsselzahl. Bei (a) steht "Findling sieht" neben fünfmal "diese Box" auf derselben Seite.

## Schlüsselbilanz (für 33-07, Stand Entwurf)

- Neu: (A) 5, (B) 13, (C) 2, (E) 8 (Überschrift, 5 Zeilen, Hinweis, Linktext) = 28 neue Schlüssel.
- Gewechselt bei gleicher Zahl: Hilfesatz Ordnerliste, Diagnose-Abhilfe, B3-Satz, `hardware_short`, bei G5 (b) drei, bei (c) sechs weitere.
- Schlüsselzahl im Test von 306 auf 334, sofern die Abnahme nichts ändert.

## Owner-Abnahme

Owner-Antwort vom 13.10.2026, wörtlich (übermittelt über den Orchestrator von `/gsd:execute-phase`):

> - G1: (a) 32 Muster zu je 60 Zeichen.
> - G2: (a) Groß- und Kleinschreibung zählt, `?` passt nie auf `/` (wie PE-1).
> - G3: (a) `no_wildcard` wird abgelehnt.
> - G4: (a) Die Urteilszeilen werden in beiden Räumwegen gelöscht, auch bei den Präfixen.
> - G5: (c) Alle sechs weiteren "box"-Sätze werden ersetzt, zusätzlich zu `hardware_short`. Abweichung von PE-6, Owner-Wort.
> - Wortlaut: "abgenommen", unverändert in de, en und fr.

Folgen für 33-02 bis 33-08:

- G1 bis G4 bestätigen D-33-03, PE-1, PE-2 und PE-4 unverändert; keine Folge für die Pläne.
- G5 weicht von PE-6 ab: 33-07 ersetzt sieben Sätze statt einem, nämlich `hardware_short` und die sechs Sätze der Tabelle unter F, mit dem Wortlaut der Spalten "Vorschlag neu", de und fr. Schlüsselzahl gleich (sechs zusätzliche Schlüsselwechsel). Vermerk steht in 33-07-PLAN.md unter `<context>`.
- Alle Tabellen dieser Datei gelten jetzt als abgenommener Wortlaut; die Folgepläne übernehmen ihn zeichengleich. Schlüsselbilanz: 28 neue Schlüssel, Schlüsselzahl 306 auf 334.
