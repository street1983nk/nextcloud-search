# Französische Wortlaute, vollständig und zur Abnahme

Die App liefert heute genau eine Übersetzungssprache, Deutsch, und zwar unter beiden
deutschen Sprachcodes: `php/l10n/de.json`, `php/l10n/de.js`, `php/l10n/de_DE.json` und
`php/l10n/de_DE.js`, vier Dateien mit demselben Wortlaut (Begründung im Kopf von
`backend/tests/test_admin_ui_contract.py`, Abschnitt `L10N_DE_DE_JSON`). Diese Datei
trägt die französischen Wortlaute für **alle** Schlüssel dieser vier Kataloge, in einer
Tabelle, damit der Owner sie in einem Lesevorgang prüfen kann und nicht als Diff über
vier Dateien.

**Stand 11.09.2026 (Plan 11-05):** Die Bedingung, unter der der französische Katalog
kommt, ist eingelöst. Sie steht weiter unten unverändert als Geschichte, und jeder ihrer
fünf Punkte ist hier bedient: alle Zeichenketten statt nur der 24 der Ergebnisseite
(diese Tabelle), beide Dateiformate und der erweiterte Schlüsselvergleich (Plan 11-08),
echte Akzente und Guillemets (unten geprüft), und das alles vor der Store-Abgabe. Aus
dieser Tabelle entstehen `php/l10n/fr.json` und `php/l10n/fr.js` mechanisch, ohne zweite
Textrunde.

## Die Schlüsselmenge, aus der Datei gezählt

Nicht aus der Recherche übernommen, sondern mit `json.load` über `php/l10n/de.json`
gezählt:

| Größe | Wert | Recherche (10.09.) |
|---|---:|---:|
| Schlüssel in `de.json` | **174** | 173 |
| davon mit printf-Direktiven (`%s`, `%1$s`, `%n`) | **34** | |
| davon mit Direktiven, ohne die Pluralschlüssel | **29** | 29 |
| davon mit Pluralformen (Wert ist eine Liste) | **5** | 5 |
| Zeilen in der Tabelle unten | **173** | |

**Die 174 statt 173 ist keine Abweichung, sondern der Entscheid V-1a vom 10.09.2026**
(`11-VORENTSCHEIDE.md`, Abschnitt V-1, Zeile 116). Plan 11-13 hat den 174. Schlüssel in
Welle 2 in alle vier deutschen Kataloge geschrieben: englischer Quellstring
`Other files contain this word, but none that you may open.`, deutscher Wortlaut
`Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen.` Er steht in
der Tabelle unten wie jeder andere. Die harte Zahl in
`test_the_german_catalogue_covers_both_german_language_codes` steht bereits auf 174.

Die zweite und die dritte Zeile sind zwei Messungen derselben Sache: die 29 der
Recherche zählen die Schlüssel mit Platzhaltern **ohne** die fünf Pluralschlüssel, deren
`%n` ebenfalls eine Direktive ist. Beide Zahlen stehen hier, damit die nächste Zählung
nicht bei einer der beiden für falsch gehalten wird.

**Die Tabelle hat 173 Zeilen und nicht 174.** Der fehlende Schlüssel ist `Findling`,
und er steht als benannte Ausnahme unter der Tabelle, mit seinem Wortlaut. Siehe dort;
der Grund ist ein Befund und keine Nachlässigkeit.

## Wortwahl

Damit die Abnahme eine Entscheidung je Begriff ist und nicht 174 Einzelfälle. Die Linie
folgt `README.fr.md` und den französischen Teilen von `php/appinfo/info.xml`, die beide
seit dem 07.09.2026 stehen.

| Englisch | Französisch | Warum |
|---|---|---|
| the backend | le service | So steht es seit Phase 9 im abgenommenen Wortlaut der Ergebnisseite (`Findling n'a pas pu joindre son service`). Wo der Eigenname der App gemeint ist, bleibt er stehen: `l'application externe "Findling Backend"` |
| searchable, findable | trouvé par la recherche, trouvable par le sens | Zwei Hälften derselben Aussage, deshalb dieselbe Verbform. `interrogeable` wäre kürzer und für einen Verwaltungsnutzer dunkler |
| OCR | reconnaissance optique | Steht so in `README.fr.md` und in `info.xml` |
| text recognition | reconnaissance de texte | Die Quelle trennt beide Begriffe, die Übersetzung auch |
| run (Lauf, Abgleichlauf, Hintergrundlauf) | passage, passage de comparaison, passage en arrière-plan | `exécution` ist das schwerere Wort für dieselbe Sache |
| upload | téléverser | Die Wortwahl von Nextcloud selbst, kein Anglizismus |
| MB | Mo | `README.fr.md` schreibt bereits `4 Go` und `2 Go` |
| storage | espace de stockage, stockage externe | |
| Team Folders | Team Folders | Eigenname der Nextcloud-Funktion, in der französischen Oberfläche unübersetzt |
| remedy (die Abhilfe, oft nur `None.`) | `Aucune.` | Weiblich, weil es sich auf `la solution` bezieht, und deshalb nicht `Aucun.` |

## Typografie

Jede Regel unten ist maschinell geprüft, das Ergebnis steht im Abschnitt "Maschinelle
Prüfungen".

- **Echte Akzente und Guillemets**, wie in den 24 Wortlauten der Ergebnisseite:
  `Résultats`, `« %s »`, mit einfachem Leerzeichen innerhalb der Guillemets.
- **Apostroph als ASCII `'`**, nicht U+2019. Das ist der Bestand in `README.fr.md`
  (`d'elles-même`, `l'utilisateur`) und in den französischen Store-Texten, und ein
  gemischter Bestand ist eine Diff-Falle.
- **Einfaches Leerzeichen vor `:`, `;`, `?` und `!`**, nicht das geschützte
  Leerzeichen U+00A0 und nicht das schmale U+202F. Das ist die Form, die der
  französische Bestand des Repositoriums führt (`Confidentialité : tout fonctionne
  localement`, `qui demande ; mesuré par`), und die einzige, die einen Katalog nicht mit
  unsichtbaren Zeichen füllt, die niemand in einem Diff sieht.
- **Kein Gedankenstrich.** Französische Zeitungstypographie bringt ihn mit, dieses
  Repositorium verbietet ihn (weder U+2014 noch U+2013).
- **Die Platzhalter sind die des Schlüssels**, in Art und Zahl. `%1$s in %2$s` wird
  `%1$s dans %2$s` und niemals `%s dans %s`.

## Pluralformen

Die französische Regel lautet

```
nplurals=2; plural=(n > 1);
```

und **nicht** die deutsche `nplurals=2; plural=(n != 1);`. Der Unterschied ist n gleich
0: dort steht im Französischen der **Singular** (`0 jour`), im Deutschen der Plural.
Diese Zeichenkette gehört als `"pluralForm"` in `php/l10n/fr.json` und als vierter
Parameter von `OC.L10N.register` in `php/l10n/fr.js` (Plan 11-08, Gate G4).

Die fünf Pluralschlüssel tragen in der Tabelle genau zwei Formen, durch ` / ` getrennt,
zuerst der Singular. Die deutsche Spalte ist ebenso gesetzt; dass `and %n more` im
Deutschen zweimal denselben Wortlaut trägt, ist der Bestand von `de.json` und kein
Fehler dieser Tabelle.

## Die Tabelle

Die Spalten `Schluessel` und `DE` sind nicht abgetippt, sondern aus `php/l10n/de.json`
erzeugt; die Reihenfolge ist die der Datei. Der Spaltenname ist ASCII, weil er ein
Vertragsbezeichner ist und die Projektregel echte Umlaute der deutschen Prosa vorbehält.
Der Schlüssel ist der englische Quellstring: er steht wörtlich so im Template, läuft dort
durch `$l->t()` und ist in allen vier deutschen Katalogdateien bereits der Schlüssel der
deutschen Übersetzung.

| Schluessel | DE | FR |
|---|---|---|
| `Search coverage` | Deckungsgrad der Suche | Couverture de la recherche |
| `%1$s of %2$s indexable files are searchable` | %1$s von %2$s indexierbaren Dateien sind durchsuchbar | %1$s des %2$s fichiers indexables peuvent être trouvés par la recherche |
| `The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.` | Der Anteil ist im Moment nicht berechenbar, weil das Backend nicht antwortet. %s Dateien dieser Instanz sind indexierbar. | La part ne peut pas être calculée pour le moment, car le service ne répond pas. %s fichiers de cette instance sont indexables. |
| `Deliberately left out: %s` | Bewusst ausgelassen: %s | Volontairement laissés de côté : %s |
| `Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.` | Diese Dateien sind zu groß, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen. Sie stehen nicht im Nenner darüber, damit der Deckungsgrad 100 Prozent erreichen kann. | Ces fichiers sont trop volumineux, d'un type que Findling ne lit pas, ou exclus par une règle. Ils ne figurent pas au dénominateur ci-dessus, afin que la couverture puisse atteindre cent pour cent. |
| `Provisional figure, %1$s of %2$s storages have been counted through.` | Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt. | Chiffre provisoire, %1$s espaces de stockage sur %2$s ont été entièrement comptés. |
| `Findable by meaning` | Auffindbar nach Bedeutung | Trouvable par le sens |
| `%1$s of %2$s indexable files can also be found by meaning` | %1$s von %2$s indexierbaren Dateien sind auch nach Bedeutung auffindbar | %1$s des %2$s fichiers indexables peuvent aussi être trouvés par le sens |
| `The semantic share cannot be worked out right now. The backend does not answer, or it does not report this figure yet.` | Der semantische Anteil ist im Moment nicht berechenbar. Das Backend antwortet nicht, oder es meldet diese Zahl noch nicht. | La part sémantique ne peut pas être calculée pour le moment. Le service ne répond pas, ou il ne communique pas encore ce chiffre. |
| `The model is in memory, the semantic search is answering.` | Das Modell liegt im Speicher, die semantische Suche antwortet. | Le modèle est en mémoire, la recherche sémantique répond. |
| `The model is read when it is first needed. That is the normal state.` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | Le modèle est chargé au premier besoin. C'est le cas normal. |
| `The semantic half is switched off in the settings of the container.` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | La moitié sémantique est désactivée dans les paramètres du conteneur. |
| `There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.` | In diesem Abbild liegt kein Modell. Die Suche liefert weiterhin Volltexttreffer, die semantische Hälfte bleibt leer. | Cette image ne contient aucun modèle. La recherche continue de répondre avec des résultats en texte intégral, la moitié sémantique reste vide. |
| `Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.` | Das Laden des Modells ist einmal gescheitert und wird in Kürze erneut versucht. Bis dahin liefert die Suche Volltexttreffer. | Le chargement du modèle a échoué une fois et sera retenté sous peu. D'ici là, la recherche répond avec des résultats en texte intégral. |
| `This container does not report the state of the model yet.` | Dieser Container meldet den Zustand des Modells noch nicht. | Ce conteneur ne communique pas encore l'état du modèle. |
| `The full text search covers every indexed document. The semantic search covers the beginning of each document, and this second figure fills up after the first index has finished.` | Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem Erstindex nach. | La recherche en texte intégral couvre chaque document indexé. La recherche sémantique couvre le début de chaque document, et ce second chiffre se complète après la fin de la première indexation. |
| `Up to date, last checked %s` | Aktuell, letzte Prüfung %s | À jour, dernière vérification %s |
| `Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.` | Die Indexierung kommt seit %s nicht voran. In dieser Zeit hat weder ein Hintergrundauftrag noch das Backend etwas fertiggestellt. | L'indexation n'a pas progressé depuis %s. Pendant ce temps, ni une tâche de fond ni le service n'ont terminé quoi que ce soit. |
| `No background job of this app has run yet. Background jobs may not be running.` | Noch kein Hintergrundauftrag dieser App ist gelaufen. Möglicherweise laufen die Hintergrundaufträge nicht. | Aucune tâche de fond de cette application n'a encore été exécutée. Les tâches de fond ne fonctionnent peut-être pas. |
| `Indexing is running.` | Die Indexierung läuft. | L'indexation est en cours. |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | Die Zahlen konnten nicht aktualisiert werden. Die Werte unten sind die letzten, die diese Seite bekommen hat. | Les chiffres n'ont pas pu être actualisés. Les valeurs ci-dessous sont les dernières que cette page a reçues. |
| `%n minute` | %n Minute / %n Minuten | %n minute / %n minutes |
| `%n hour` | %n Stunde / %n Stunden | %n heure / %n heures |
| `%n day` | %n Tag / %n Tage | %n jour / %n jours |
| `Waiting in the queue` | Wartet in der Warteschlange | En attente dans la file |
| `Being processed` | Wird gerade verarbeitet | En cours de traitement |
| `Indexed` | Indexiert | Indexé |
| `Skipped` | Übersprungen | Ignoré |
| `Failed` | Fehlgeschlagen | Échoué |
| `Excluded` | Ausgeschlossen | Exclu |
| `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst. | Les fichiers exclus ne comptent pas dans la couverture. Ce sont les fichiers auxquels Findling ne touche pas, sur instruction. |
| `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter. | Peu d'espace disque disponible. L'indexation est en pause afin que l'index reste intact. La recherche continue de fonctionner. |
| `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer. | L'index a été construit avec une analyse de texte plus ancienne. Le reconstruire avec "occ findling:index --restart", sinon des résultats continueront de manquer. |
| `No numbers yet` | Noch keine Zahlen | Pas encore de chiffres |
| `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` | Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen. | La première indexation n'est pas encore terminée. Findling a démarré de lui-même, il n'y a rien à configurer. |
| `The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.` | Die beiden Hälften von Findling melden unterschiedliche Versionen: diese App ist %1$s, das Backend ist %2$s. Solange sie nicht zusammenpassen, antwortet die Suche ohne Ergebnisse, weil eine falsche Antwort ohne Hinweis schlimmer wäre. Beide Hälften auf dieselbe Version bringen. | Les deux moitiés de Findling annoncent des versions différentes : cette application est en %1$s, le service est en %2$s. Tant qu'elles ne concordent pas, la recherche répond sans résultats, car une réponse fausse et muette serait pire. Mettre les deux moitiés dans la même version. |
| `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` | Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist. | Le service Findling ne répond pas. Les chiffres ci-dessous sont les derniers que cette application a enregistrés. Vérifier sous Applications que l'application externe "Findling Backend" est installée et démarrée. |
| `Estimate for the first index` | Schätzung für den Erstindex | Estimation pour la première indexation |
| `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | %1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index. | %1$s fichiers, dont %2$s avec reconnaissance optique. Environ %3$s et environ %4$s d'index. |
| `%1$s files, %2$s of them need OCR.` | %1$s Dateien, davon %2$s mit OCR. | %1$s fichiers, dont %2$s avec reconnaissance optique. |
| `%1$s to %2$s` | %1$s bis %2$s | %1$s à %2$s |
| `Counting the files, this takes a moment.` | Die Dateien werden gezählt, das dauert einen Moment. | Les fichiers sont en cours de comptage, cela prend un moment. |
| `Startup value, being measured.` | Startwert, wird gemessen. | Valeur de départ, mesure en cours. |
| `The space needed is measured as soon as the first documents are in the index.` | Der Platzbedarf wird gemessen, sobald die ersten Dokumente im Index sind. | L'espace nécessaire est mesuré dès que les premiers documents sont dans l'index. |
| `The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.` | Der Index braucht voraussichtlich mehr Platz, als auf diesem Datenträger frei ist. Die Indexierung pausiert, bevor der Datenträger voll wird, und die Suche funktioniert weiter. | L'index devrait avoir besoin de plus d'espace qu'il n'en reste sur ce volume. L'indexation se met en pause avant que le volume ne soit plein, et la recherche continue de fonctionner. |
| `Findling does not wait for a confirmation. The first index has already started.` | Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits. | Findling n'attend aucune confirmation. La première indexation est déjà en cours. |
| `Files that were not indexed` | Nicht indexierte Dateien | Fichiers non indexés |
| `Files that were not indexed, grouped by reason` | Nicht indexierte Dateien, nach Grund gruppiert | Fichiers non indexés, groupés par motif |
| `Every file was indexed. Nothing was skipped and nothing failed.` | Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen. | Tous les fichiers sont indexés. Rien n'a été ignoré, rien n'a échoué. |
| `Reason` | Grund | Motif |
| `Files` | Dateien | Fichiers |
| `State` | Zustand | État |
| `Show example paths` | Beispielpfade anzeigen | Afficher les exemples de chemins |
| `Hide example paths` | Beispielpfade verbergen | Masquer les exemples de chemins |
| `and %n more` | und %n weitere / und %n weitere | et %n autre / et %n autres |
| `File no longer exists (ID %s)` | Datei existiert nicht mehr (ID %s) | Le fichier n'existe plus (ID %s) |
| `%s (in the trash bin)` | %s (im Papierkorb) | %s (dans la corbeille) |
| `Indexed, text truncated` | Indexiert, Text gekürzt | Indexé, texte tronqué |
| `Unknown reason (%s)` | Unbekannter Grund (%s) | Motif inconnu (%s) |
| `This app does not know this code. It may come from a newer version of the backend.` | Diese App kennt diesen Code nicht. Er kann von einer neueren Fassung des Backends kommen. | Cette application ne connaît pas ce code. Il peut provenir d'une version plus récente du service. |
| `Text truncated` | Text gekürzt | Texte tronqué |
| `The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.` | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. | Le début du document peut être trouvé par la recherche, le reste non. Les documents très longs sont coupés volontairement. |
| `Too large` | Zu groß | Trop volumineux |
| `Raise the value under "Largest file to read".` | Den Wert unter "Größte zu lesende Datei" erhöhen. | Augmenter la valeur sous "Taille maximale des fichiers à lire". |
| `File type not supported` | Dateityp nicht unterstützt | Type de fichier non pris en charge |
| `None. Findling reads PDF, Office, OpenDocument, text and images.` | Keine. Findling liest PDF, Office, OpenDocument, Text und Bilder. | Aucune. Findling lit les PDF, Office, OpenDocument, le texte et les images. |
| `Password protected` | Passwortgeschützt | Protégé par mot de passe |
| `None. Without the password the content cannot be read.` | Keine. Ohne Passwort ist der Inhalt nicht lesbar. | Aucune. Sans le mot de passe, le contenu ne peut pas être lu. |
| `No text in the document` | Kein Text im Dokument | Aucun texte dans le document |
| `None. The document carries neither a text layer nor recognisable writing.` | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. | Aucune. Le document ne contient ni couche de texte ni écriture reconnaissable. |
| `No text content` | Kein Textinhalt | Aucun contenu textuel |
| `None. The file is readable but carries no text.` | Keine. Die Datei ist lesbar, enthält aber keinen Text. | Aucune. Le fichier est lisible mais ne contient aucun texte. |
| `Spreadsheet too large` | Tabelle zu groß | Feuille de calcul trop volumineuse |
| `None. Very large spreadsheets are skipped so the container does not fall over.` | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. | Aucune. Les très grandes feuilles de calcul sont ignorées afin que le conteneur ne s'effondre pas. |
| `File no longer present` | Datei nicht mehr vorhanden | Fichier absent |
| `None. The file was already deleted or moved when it was read.` | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. | Aucune. Le fichier était déjà supprimé ou déplacé au moment de la lecture. |
| `Image without recognisable writing` | Bild ohne erkennbare Schrift | Image sans écriture reconnaissable |
| `None.` | Keine. | Aucune. |
| `Excluded by a rule` | Durch Regel ausgeschlossen | Exclu par une règle |
| `Remove the matching entry under "Excluded folders".` | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. | Supprimer l'entrée correspondante sous "Dossiers exclus". |
| `File is empty` | Datei ist leer | Fichier vide |
| `None. The file has 0 bytes.` | Keine. Die Datei hat 0 Byte. | Aucune. Le fichier fait 0 octet. |
| `File damaged` | Datei beschädigt | Fichier endommagé |
| `Check the file outside of Nextcloud and upload it again.` | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. | Vérifier le fichier en dehors de Nextcloud et le téléverser à nouveau. |
| `Document structure faulty` | Dokumentstruktur fehlerhaft | Structure du document défectueuse |
| `Open the document in the program it came from and save it again.` | Das Dokument im Ursprungsprogramm öffnen und neu speichern. | Ouvrir le document dans le programme d'origine et l'enregistrer à nouveau. |
| `Character set not recognised` | Zeichensatz nicht erkannt | Jeu de caractères non reconnu |
| `Save the file as UTF-8 and upload it again.` | Die Datei als UTF-8 speichern und neu hochladen. | Enregistrer le fichier en UTF-8 et le téléverser à nouveau. |
| `Timed out while reading` | Zeitüberschreitung beim Lesen | Délai dépassé pendant la lecture |
| `The next run tries again.` | Wird beim nächsten Lauf erneut versucht. | Une nouvelle tentative aura lieu au prochain passage. |
| `Not enough memory while reading` | Zu wenig Speicher beim Lesen | Mémoire insuffisante pendant la lecture |
| `The next run tries again. If it happens again, lower the size cap.` | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken. | Une nouvelle tentative aura lieu au prochain passage. Si cela se reproduit, abaisser la limite de taille. |
| `File was not retrievable` | Datei war nicht abrufbar | Fichier non récupérable |
| `Stuck repeatedly` | Mehrfach hängen geblieben | Bloqué à plusieurs reprises |
| `Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.` | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. | Findling ne réessaie plus ce fichier. Utiliser la vérification d'un fichier pour voir s'il s'ouvre en dehors de Nextcloud. |
| `Text recognition failed` | Texterkennung fehlgeschlagen | Échec de la reconnaissance de texte |
| `Text recognition not available` | Texterkennung nicht verfügbar | Reconnaissance de texte non disponible |
| `The backend could not start Tesseract. Check the log of the External App.` | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. | Le service n'a pas pu démarrer Tesseract. Vérifier le journal de l'application externe. |
| `Look up one file` | Einzelne Datei prüfen | Vérifier un fichier |
| `Path or file ID` | Pfad oder Datei-ID | Chemin ou ID du fichier |
| `A path as Nextcloud stores it, or the numeric ID from the list above.` | Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben. | Un chemin tel que Nextcloud le conserve, ou le nombre de la liste ci-dessus. |
| `Look up file` | Datei prüfen | Vérifier le fichier |
| `Looking up a single file needs JavaScript. Everything above stays complete without it.` | Die Einzelprüfung braucht JavaScript. Alles darüber bleibt auch ohne vollständig lesbar. | La vérification d'un fichier nécessite JavaScript. Tout ce qui précède reste lisible en entier sans lui. |
| `No file at this path, and no file with this ID.` | Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID. | Aucun fichier à ce chemin, et aucun fichier avec cet ID. |
| `Not seen yet` | Noch nicht gesehen | Pas encore vu |
| `State unknown right now` | Zustand im Moment unbekannt | État inconnu pour le moment |
| `File ID: %s` | Datei-ID: %s | ID du fichier : %s |
| `Last checked %s` | Zuletzt geprüft: %s | Dernière vérification : %s |
| `The lookup did not work. Nothing about this file has changed.` | Die Prüfung hat nicht funktioniert. An dieser Datei hat sich nichts geändert. | La vérification n'a pas fonctionné. Rien n'a changé pour ce fichier. |
| `The state of this file is unknown right now because the backend does not answer.` | Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet. | L'état de ce fichier est inconnu pour le moment, car le service ne répond pas. |
| `This file has not reached the queue. The next comparison run picks it up.` | Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab. | Ce fichier n'est pas encore arrivé dans la file d'attente. Le prochain passage de comparaison le prendra en charge. |
| `It was indexed before and is recorded again on the next comparison run.` | Sie war vorher indexiert und wird beim nächsten Abgleichlauf neu erfasst. | Il était indexé auparavant et sera de nouveau enregistré au prochain passage de comparaison. |
| `This file was indexed and has since been deleted. It is out of the index with it.` | Diese Datei war indexiert und ist inzwischen gelöscht. Damit ist sie auch aus dem Index heraus. | Ce fichier était indexé et a été supprimé depuis. Il est donc sorti de l'index. |
| `In the trash bin` | Im Papierkorb | Dans la corbeille |
| `Restore the file. The next comparison run picks it up.` | Die Datei wiederherstellen. Der nächste Abgleichlauf holt sie ab. | Restaurer le fichier. Le prochain passage de comparaison le prendra en charge. |
| `Storage is not indexed` | Speicherort wird nicht indexiert | Cet espace de stockage n'est pas indexé |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | Findling liest die Heimatverzeichnisse der Nutzer. Team Folders und externer Speicher sind eigene Einstellungen. | Findling lit les répertoires personnels de vos utilisateurs. Les Team Folders et le stockage externe relèvent de paramètres distincts. |
| `This is a folder` | Das ist ein Ordner | Ceci est un dossier |
| `Enter the path of a file. A folder has no state of its own.` | Den Pfad einer Datei eingeben. Ein Ordner hat keinen eigenen Zustand. | Saisir le chemin d'un fichier. Un dossier n'a pas d'état propre. |
| `Attempts so far: %s` | Bisherige Versuche: %s | Tentatives jusqu'ici : %s |
| `The next background run picks this file up (%s).` | Der nächste Hintergrundlauf holt diese Datei ab (%s). | Le prochain passage en arrière-plan prendra ce fichier en charge (%s). |
| `The content of this file is searchable.` | Der Inhalt dieser Datei ist durchsuchbar. | Le contenu de ce fichier peut être trouvé par la recherche. |
| `A worker holds this file. The claim runs out in %n second if nothing acknowledges it.` | Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunde aus, wenn ihn niemand quittiert. / Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunden aus, wenn ihn niemand quittiert. | Un processus de traitement détient ce fichier. La réservation expire dans %n seconde si personne ne la confirme. / Un processus de traitement détient ce fichier. La réservation expire dans %n secondes si personne ne la confirme. |
| `Rules and limits` | Regeln und Grenzen | Règles et limites |
| `Excluded folders` | Ausgeschlossene Ordner | Dossiers exclus |
| `Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups` | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, keine Platzhalter und keine Muster. Beispiel: Backups | Comparaison par préfixe sur le chemin tel que les listes de cette page l'affichent, sans caractères génériques ni motifs. Exemple : Backups |
| `Add exclusion` | Ausschluss hinzufügen | Ajouter une exclusion |
| `Remove exclusion %s` | Ausschluss %s entfernen | Supprimer l'exclusion %s |
| `No folder is excluded.` | Kein Ordner ist ausgeschlossen. | Aucun dossier n'est exclu. |
| `Largest file to read` | Größte zu lesende Datei | Taille maximale des fichiers à lire |
| `Files above this size are recorded as skipped (too large) and never read.` | Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen. | Les fichiers plus grands sont notés comme ignorés (trop volumineux) et ne sont jamais lus. |
| `The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container.` | Das Backend dieser Instanz liest höchstens %s MB. Für mehr FINDLING_MAX_FILE_BYTES in den App-Einstellungen von AppAPI anheben, was den Container neu startet. | Le service de cette instance lit au maximum %s Mo. Pour davantage, augmenter FINDLING_MAX_FILE_BYTES dans les paramètres d'application d'AppAPI, ce qui redémarre le conteneur. |
| `Index Team Folders` | Team Folders indexieren | Indexer les Team Folders |
| `Index external storage` | Externen Speicher indexieren | Indexer le stockage externe |
| `External storage can be slow or charged per request. Indexing reads every file once.` | Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal. | Le stockage externe peut être lent ou facturé à la requête. L'indexation lit chaque fichier une fois. |
| `The next run applies the new rules. Nothing restarts.` | Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu. | Le prochain passage applique les nouvelles règles. Rien ne redémarre. |
| `Save rules` | Regeln speichern | Enregistrer les règles |
| `Rules saved. The next run applies them.` | Regeln gespeichert. Der nächste Lauf übernimmt sie. | Règles enregistrées. Le prochain passage les applique. |
| `The rules were not saved. Nothing changed.` | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | Les règles n'ont pas été enregistrées. Rien n'a changé. |
| `Enter a size between %1$s and %2$s MB.` | Eine Größe zwischen %1$s und %2$s MB eingeben. | Saisir une taille comprise entre %1$s et %2$s Mo. |
| `Enter a folder path.` | Einen Ordnerpfad eingeben. | Saisir un chemin de dossier. |
| `This path is already excluded.` | Dieser Pfad ist bereits ausgeschlossen. | Ce chemin est déjà exclu. |
| `Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.` | Einen Eintrag zu entfernen wirkt innerhalb von %1$s Stunden, wenn der nächste Abgleichlauf diese Dateien wieder aufnimmt. Mit "%2$s" sofort übernehmen. | Supprimer une entrée prend effet sous %1$s heures, lorsque le prochain passage de comparaison reprend ces fichiers. Utiliser "%2$s" pour l'appliquer immédiatement. |
| `Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %1$s entfernt außerdem %2$s bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Supprimer les contenus indexés ? L'exclusion de %1$s retire également de l'index %2$s documents déjà indexés sous ce chemin. Les fichiers eux-mêmes restent intacts sur le disque. |
| `Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Supprimer les contenus indexés ? L'exclusion de %s retire également de l'index les documents déjà indexés sous ce chemin. Les fichiers eux-mêmes restent intacts sur le disque. |
| `at least %s` | mindestens %s | au moins %s |
| `Exclude and remove` | Ausschließen und entfernen | Exclure et supprimer |
| `Keep files indexed` | Dateien indexiert lassen | Garder les fichiers indexés |
| `Search` | Suchen | Rechercher |
| `Search term` | Suchbegriff | Terme de recherche |
| `invoice 2026` | Rechnung 2026 | facture 2026 |
| `Search file names only` | Nur Dateinamen durchsuchen | Rechercher uniquement dans les noms de fichiers |
| `Results for "%s"` | Treffer für „%s“ | Résultats pour « %s » |
| `Search results` | Suchergebnisse | Résultats de recherche |
| `%1$s in %2$s` | %1$s in %2$s | %1$s dans %2$s |
| `last opened` | zuletzt geöffnet | ouvert en dernier |
| `Show all results` | Alle Treffer anzeigen | Afficher tous les résultats |
| `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | Ouvre la page de résultats de Findling |
| `Previous page` | Vorherige Seite | Page précédente |
| `Next page` | Nächste Seite | Page suivante |
| `Page %s` | Seite %s | Page %s |
| `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | D'autres résultats existent. Affinez la recherche pour les voir. |
| `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | Recherchez dans le contenu de vos fichiers |
| `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | Saisissez un mot tiré d'un document. Findling recherche le texte à l'intérieur de vos fichiers, y compris les PDF numérisés. |
| `No file contains "%s"` | Keine Datei enthält „%s“ | Aucun fichier ne contient « %s » |
| `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | Essayez un autre mot, une partie d'un mot composé ou vérifiez l'orthographe. |
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen. | D'autres fichiers contiennent ce mot, mais aucun que vous soyez autorisé à ouvrir. |
| `The search is not answering right now` | Die Suche antwortet gerade nicht | La recherche ne répond pas pour le moment |
| `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | Findling n'a pas pu joindre son service. Vos fichiers sont inchangés. Réessayez dans un instant et prévenez votre administration si cela persiste. |
| `Try again` | Erneut versuchen | Réessayer |
| `Findling is not ready to search` | Findling ist nicht suchbereit | Findling n'est pas prêt à rechercher |
| `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | Les deux moitiés de Findling annoncent des versions différentes. L'administration doit les mettre à jour ensemble. |
| `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | L'index est encore en construction, des résultats peuvent donc manquer. |

## Ausnahmen für das Vollständigkeitsgate G2

Gate G2 von Plan 11-08 fordert, dass kein FR-Wert leer und keiner mit dem englischen
Quellstring identisch ist. Genau zwei Schlüssel sind es absichtlich. Das ist eine
benannte Liste und ausdrücklich **keine** Toleranzschwelle: eine Schwelle würde einen
vergessenen Wortlaut mitdecken, eine Liste nicht.

- `Findling`: Eigenname der App, in allen drei Sprachen derselbe. Steht als Schluessel in de.json und muss deshalb in fr.json stehen, hat aber keinen eigenen Wortlaut.
- `Page %s`: Das Wort Page ist im Franzoesischen dasselbe Wort. Eine Abweichung waere eine Verschlechterung.

**Befund zu `Findling`, weil diese Datei bisher das Gegenteil behauptet hat.** Der
Abschnitt "Warum die Tabelle der Ergebnisseite 24 Zeilen hat" unten sagt, `Findling` sei
"kein Übersetzungsschlüssel und wurde in Plan 09-05 auch nicht als einer angelegt".
Gegen die Datei gehalten stimmt das nicht: `Findling` ist **Schlüssel 1 von 174** in
`php/l10n/de.json` und trägt dort sich selbst als Wert. Für die Ergebnisseite war die
Aussage richtig gemeint (die Copy-Tabelle der Phase 9 hat ihn nicht als 25. Wortlaut
gebraucht), für den Katalog ist sie falsch. **Folge für Plan 11-08:** `fr.json` und
`fr.js` müssen den Schlüssel `Findling` mit dem Wert `Findling` tragen, sonst geht Gate
G1 (Schlüsselgleichheit über alle sechs Dateien) rot. Er steht deshalb nicht in der
Tabelle, aber hier, mit seinem Wortlaut.

## Maschinelle Prüfungen

Gefahren über die Wortlaute dieser Tabelle, nicht per Augenmaß:

| Prüfung | Ergebnis |
|---|---|
| Jeder Schlüssel aus `de.json` kommt in dieser Datei vor | fehlend: 0 |
| Platzhalter-Parität Schlüssel gegen FR-Wert, über alle 34 Schlüssel mit Direktiven | 0 Abweichungen |
| Pluralschlüssel mit genau zwei Formen | 5 von 5 |
| Pluralschlüssel im FR gleich der Menge im DE | ja |
| U+2019 (typographischer Apostroph) | 0 |
| U+2014 und U+2013 (Gedankenstriche) | 0 |
| U+00A0 und U+202F (geschützte Leerzeichen) | 0 |
| FR-Wert identisch mit dem englischen Quellstring | 2, beide oben benannt |

Was keine Maschine prüfen kann, ist die Sprache. Das ist der Gegenstand der Abnahme.

## Abnahme

D-07 verlangt, dass der Owner alle französischen Zeichenketten prüft. Die Abnahme
zerfällt in zwei Teile: den Katalog (diese Datei) und die Texte drumherum
(`docs/store-listing.md`, `README.fr.md`, die französischen Teile von `info.xml`, Plan
11-09).

**FR-Gate abgenommen: 2026-09-11, Teil 1 von 2 (Katalog), D-07**

Der Owner, französischer Muttersprachler, hat die Tabelle vollständig gelesen und ohne
Änderung abgenommen. Keine Zeile ist anders zu lauten, keine ist hinzugekommen und keine
weggefallen; die Tabelle trägt vor und nach der Abnahme dieselben 173 Zeilen. Die drei
Wortwahl-Entscheidungen, die eine Entscheidung und keine Übersetzung sind, sind dabei
ausdrücklich bestätigt worden: `le service` für "the backend", `passage` für "run" und
`un processus de traitement` für "a worker".

Die maschinellen Prüfungen sind nach der Abnahme erneut gefahren worden und stehen
unverändert so, wie sie im Abschnitt "Maschinelle Prüfungen" stehen.

Teil 2 von 2 (Store-Text, `README.fr.md`, die französischen Teile von `info.xml`) steht
aus und ist Gegenstand von Plan 11-09.

## Warum die Tabelle der Ergebnisseite 24 Zeilen hat

Geschichte, Stand Phase 9, unverändert erhalten. Die Wortlaute selbst stehen heute in
der Tabelle oben und sind von dort wörtlich übernommen worden.

Es waren 24 und nicht 25 Zeilen, obwohl die Copy-Tabelle in `09-UI-SPEC.md` 25 Zeilen
führt. Die fehlende ist der Navigationseintrag und Seitenname `Findling`: er lautet in
allen drei Sprachen gleich, ist deshalb kein Wortlaut, der zu schreiben wäre, und wurde
in Plan 09-05 auch nicht als einer behandelt. (Als Katalogschlüssel existiert er
trotzdem; siehe den Befund im Abschnitt "Ausnahmen für das Vollständigkeitsgate G2".)
Die 24 waren genau die 24 Schlüssel, die Plan 09-08 den beiden deutschen Katalogen
hinzugefügt hat, von 149 auf die damaligen 173.

## Warum vertagt

Geschichte, Stand Phase 9, unverändert erhalten. Die Vertagung ist mit dieser Datei
beendet.

Ein Katalog, der 24 von damals 173 Zeichenketten übersetzt, ergibt eine halb
französische Oberfläche: die Ergebnisseite spräche Französisch, die Verwaltungsseite und
jede Meldung daneben weiter Englisch, und ein Nutzer könnte an keiner Stelle erkennen,
welche der beiden Sprachen die vollständige ist. Eine ganz englische Oberfläche ist für
denselben Nutzer die ehrlichere und die brauchbarere, deshalb stand hier eine Liste und
nicht ein `fr.json` mit 24 Einträgen.

Diese Datei ist die Ablage einer bewussten Vertagung gewesen, kein Rückstand: die
Entscheidung steht als offener Punkt 3 in
`.planning/phases/09-eigene-ergebnisseite/09-UI-SPEC.md` und als Open Question 3 in
`09-RESEARCH.md`, und sie ist in Plan 09-08 so getroffen worden, wie sie unten begründet
ist.

## Bedingung, unter der der französische Katalog kommt

Geschichte, Stand Phase 9, unverändert erhalten, mit einer nachgeführten Zahl. **Am
11.09.2026 in Phase 11 eingelöst**, siehe den Kopf dieser Datei.

Vollständig oder gar nicht, und vor der Store-Abgabe. Im Einzelnen:

1. **Alle Zeichenketten der App**, nicht nur die 24 der Ergebnisseite. Maßgeblich ist
   die Schlüsselmenge von `php/l10n/de.json` zum Zeitpunkt der Übersetzung: damals 173,
   zum Zeitpunkt der Übersetzung **174** (Entscheid V-1a, gebaut von Plan 11-13).
2. **Beide Dateiformate**, `php/l10n/fr.json` und `php/l10n/fr.js`. Der Browser-Teil
   liest den Katalog aus der `.js`-Fassung; nur `fr.json` anzulegen ergäbe eine
   Oberfläche, die je nach Herkunft der Zeile die Sprache wechselt.
3. **Der Schlüsselvergleich wird auf die französische Sprache erweitert.**
   `test_the_two_translation_files_carry_the_same_keys` hält das Paar `de.json` gegen
   `de.js`, `test_the_german_catalogue_covers_both_german_language_codes` hält die vier
   deutschen Dateien gegeneinander (beide in `backend/tests/test_admin_ui_contract.py`).
   Französisch braucht dieselbe Klammer, sonst kann es auseinanderlaufen, ohne rot zu
   werden. Anders als bei Deutsch ist es dort **keine** Gleichheit der Dateien: `fr` und
   `fr_CA` wären zwei Wortlaute, wenn die App sie je beide führt, und Französisch kennt
   die Du-Sie-Teilung der beiden deutschen Codes nicht.
4. **Echte Akzente und Guillemets**, so wie die deutschen Werte echte Umlaute tragen.
   Die Wortlaute der Ergebnisseite waren bereits in dieser Form geschrieben und sind
   wörtlich übernommen worden.
5. **Vor der Store-Abgabe**, also in Phase 11. `php/appinfo/info.xml` und
   `docs/store-listing.md` führen Französisch bereits als dritte Sprache; ein Katalog,
   der nach der Abgabe kommt, kommt für dieses Release zu spät.

Wo das wieder auftaucht: `.planning/ROADMAP.md`, Phase 11, als Vorbedingung der Abgabe
mit einem Zeiger auf diese Datei.
