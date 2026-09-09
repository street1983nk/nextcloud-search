# Französische Wortlaute der Ergebnisseite, vorbereitet und vertagt

Die App liefert heute genau eine Übersetzungssprache, Deutsch, und zwar unter beiden
deutschen Sprachcodes: `php/l10n/de.json`, `php/l10n/de.js`, `php/l10n/de_DE.json` und
`php/l10n/de_DE.js`, vier Dateien mit demselben Wortlaut (Begründung im Kopf von
`backend/tests/test_admin_ui_contract.py`, Abschnitt `L10N_DE_DE_JSON`). Die
französischen Wortlaute der Ergebnisseite aus Phase 9 sind trotzdem vollständig
geschrieben und stehen hier, damit ein französischer Katalog später ein mechanischer
Nachzug bleibt und keine zweite Textrunde.

Diese Datei ist die Ablage einer bewussten Vertagung, kein Rückstand: die Entscheidung
steht als offener Punkt 3 in `.planning/phases/09-eigene-ergebnisseite/09-UI-SPEC.md`
und als Open Question 3 in `09-RESEARCH.md`, und sie ist in Plan 09-08 so getroffen
worden, wie sie unten begründet ist.

## Die 24 Wortlaute

Reihenfolge und Elementnamen sind die der Copy-Tabelle in `09-UI-SPEC.md`, Abschnitt
"Copywriting Contract". Der englische Quellstring ist der Schlüssel: er steht wörtlich
so im Template, läuft dort durch `$l->t()` und ist in allen vier deutschen
Katalogdateien bereits der Schlüssel der deutschen Übersetzung.

| # | Element | EN (Quellstring) | FR |
|---|---------|------------------|----|
| 1 | Primary CTA | `Search` | Rechercher |
| 2 | Feld-Label | `Search term` | Terme de recherche |
| 3 | Feld-Platzhalter | `invoice 2026` | facture 2026 |
| 4 | Filter-Label | `Search file names only` | Rechercher uniquement dans les noms de fichiers |
| 5 | Überschrift mit Suchbegriff | `Results for "%s"` | Résultats pour « %s » |
| 6 | Liste (Accessible Name) | `Search results` | Résultats de recherche |
| 7 | Trefferzeile (Accessible Name) | `%1$s in %2$s` | %1$s dans %2$s |
| 8 | Rückkehr-Markierung (nur für Screenreader) | `last opened` | ouvert en dernier |
| 9 | Einstieg im Suchdialog, Titel | `Show all results` | Afficher tous les résultats |
| 10 | Einstieg im Suchdialog, Unterzeile | `Opens the Findling results page` | Ouvre la page de résultats de Findling |
| 11 | Paginierung zurück | `Previous page` | Page précédente |
| 12 | Paginierung vor | `Next page` | Page suivante |
| 13 | Seitenmarke | `Page %s` | Page %s |
| 14 | Obergrenze erreicht | `More results exist. Narrow the search to see them.` | D'autres résultats existent. Affinez la recherche pour les voir. |
| 15 | Empty state ohne Suchbegriff, Überschrift | `Search your file contents` | Recherchez dans le contenu de vos fichiers |
| 16 | Empty state ohne Suchbegriff, Text | `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Saisissez un mot tiré d'un document. Findling recherche le texte à l'intérieur de vos fichiers, y compris les PDF numérisés. |
| 17 | Empty state ohne Treffer, Überschrift | `No file contains "%s"` | Aucun fichier ne contient « %s » |
| 18 | Empty state ohne Treffer, Text | `Try another word, a part of a compound word, or check the spelling.` | Essayez un autre mot, une partie d'un mot composé ou vérifiez l'orthographe. |
| 19 | Error state Backend stumm, Überschrift | `The search is not answering right now` | La recherche ne répond pas pour le moment |
| 20 | Error state Backend stumm, Text | `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling n'a pas pu joindre son service. Vos fichiers sont inchangés. Réessayez dans un instant et prévenez votre administration si cela persiste. |
| 21 | Error state Backend stumm, Knopf | `Try again` | Réessayer |
| 22 | Error state Versionsdrift, Überschrift | `Findling is not ready to search` | Findling n'est pas prêt à rechercher |
| 23 | Error state Versionsdrift, Text | `The two halves of Findling report different versions. Your administrator has to update both together.` | Les deux moitiés de Findling annoncent des versions différentes. L'administration doit les mettre à jour ensemble. |
| 24 | Hinweis Index im Aufbau | `The index is still being built, so results can be missing.` | L'index est encore en construction, des résultats peuvent donc manquer. |

Es sind 24 und nicht 25 Zeilen, obwohl die Copy-Tabelle 25 Zeilen führt. Die
fehlende ist der Navigationseintrag und Seitenname `Findling`: er lautet in allen
drei Sprachen gleich, ist deshalb kein Übersetzungsschlüssel und wurde in Plan 09-05
auch nicht als einer angelegt. Die 24 hier sind genau die 24 Schlüssel, die dieser
Plan den beiden deutschen Katalogen hinzugefügt hat (149 auf 173).

## Warum vertagt

Ein Katalog, der 24 von 173 Zeichenketten übersetzt, ergibt eine halb französische
Oberfläche: die Ergebnisseite spräche Französisch, die Verwaltungsseite und jede
Meldung daneben weiter Englisch, und ein Nutzer könnte an keiner Stelle erkennen,
welche der beiden Sprachen die vollständige ist. Eine ganz englische Oberfläche ist
für denselben Nutzer die ehrlichere und die brauchbarere, deshalb steht hier eine
Liste und nicht ein `fr.json` mit 24 Einträgen.

## Bedingung, unter der der französische Katalog kommt

Vollständig oder gar nicht, und vor der Store-Abgabe. Im Einzelnen:

1. **Alle Zeichenketten der App**, nicht nur die 24 dieser Seite. Maßgeblich ist die
   Schlüsselmenge von `php/l10n/de.json` zum Zeitpunkt der Übersetzung, heute 173.
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
   Die Wortlaute oben sind bereits in dieser Form geschrieben und können wörtlich
   übernommen werden.
5. **Vor der Store-Abgabe**, also in Phase 11. `php/appinfo/info.xml` und
   `docs/store-listing.md` führen Französisch bereits als dritte Sprache; ein Katalog,
   der nach der Abgabe kommt, kommt für dieses Release zu spät.

Wo das wieder auftaucht: `.planning/ROADMAP.md`, Phase 11, als Vorbedingung der
Abgabe mit einem Zeiger auf diese Datei.
