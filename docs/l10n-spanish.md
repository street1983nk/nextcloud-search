# Spanische Wortlaute, vollständig

Diese Datei ist die Quelle der beiden spanischen Katalogdateien `php/l10n/es.json` und
`php/l10n/es.js`. Sie trägt die spanischen Wortlaute für **alle** Schlüssel der Adminseite und
der Ergebnisseite, in einer Tabelle, damit ein Leser sie in einem Durchgang prüfen kann und
nicht als Diff über zwei Dateien. Aus dieser Tabelle sind beide Dateien mechanisch entstanden,
ohne zweite Textrunde.

Was für **alle** Sprachdateien dieser Phase gilt, steht nicht hier, sondern einmal in
`docs/l10n-catalogues.md`: warum Nextcloud zehn Dateien und nicht fünf braucht (Abschnitt 1),
warum `es_EC` und `es_MX` bewusst nicht ausgeliefert werden (Abschnitt 2), die wörtlichen
Pluralregeln mit ihrer Herkunft (Abschnitt 3) und die Messung, aus der die Wahl der Formen
folgt (Abschnitt 4). Diese Datei verweist dorthin, statt den Beweis ein zweites Mal zu führen.

## Die Schlüsselmenge, aus der Datei gezählt

Nicht aus einem Dokument übernommen, sondern am 25.09.2026 mit `json.load` über
`php/l10n/de.json` und `php/l10n/es.json` gezählt:

| Größe | Wert |
|---|---:|
| Schlüssel in `de.json` | **202** |
| Schlüssel in `es.json` | **202** |
| davon mit printf-Direktiven (`%s`, `%1$s`, `%n`) | **40** |
| davon mit Direktiven, ohne die Pluralschlüssel | **35** |
| davon mit Pluralformen (Wert ist eine Liste) | **5** |
| Zeilen in der Tabelle unten | **202** |

Die beiden Direktiven-Zeilen sind zwei Messungen derselben Sache: die zweite zählt die
Schlüssel mit Platzhaltern **ohne** die fünf Pluralschlüssel, deren `%n` ebenfalls eine
Direktive ist. Beide Zahlen stehen hier, damit die nächste Zählung nicht bei einer der beiden
für falsch gehalten wird.

Die Tabelle unten führt **202** Zeilen und nicht 201: anders als in `docs/l10n-french.md` steht
auch `Findling` darin, mit sich selbst als Wortlaut. Er ist zugleich der erste Eintrag der
Ausnahmeliste weiter unten; ihn aus der Tabelle zu nehmen hätte eine Zeile gespart und eine
Frage aufgeworfen.

## Wortwahl

Damit die Prüfung eine Entscheidung je Begriff ist und nicht 202 Einzelfälle. Die Linie folgt
den französischen Entscheiden aus `docs/l10n-french.md`, weil die beiden Kataloge dieselben
Sätze übersetzen und eine zweite, abweichende Linie nur die Pflege verteuert hätte.

| Englisch | Spanisch | Warum |
|---|---|---|
| the backend | el servicio | Derselbe Entscheid wie im Französischen (`le service`). Der Nutzer sieht einen Dienst, der antwortet oder nicht antwortet, und kein Fremdwort. Wo der Eigenname gemeint ist, bleibt er stehen: `la aplicación externa "Findling Backend"` |
| run (Lauf, Abgleichlauf, Hintergrundlauf) | pasada, pasada de comparación, pasada en segundo plano | `ejecución` ist das schwerere Wort für dieselbe Sache, und `pasada` trägt dasselbe Bild wie das französische `passage`: etwas geht einmal über den Bestand |
| worker | proceso de tratamiento | Nach dem französischen `processus de traitement`. `trabajador` wäre der Mensch, `worker` der Anglizismus, und beide sagen dem Verwaltungsnutzer weniger als die Umschreibung |
| index (Substantiv) | el índice | Mit Akzent, sonst steht dort `indice` im Sinne von Anzeichen |
| index (Verb), indexing | indexar, la indexación | Und nicht `indizar`, das im Spanischen eher bibliothekarisch klingt; `indexar` ist das Wort, das die Nextcloud-Oberfläche selbst führt |
| coverage | cobertura | Die Zahl, die sagt, welcher Anteil der Dateien durchsuchbar ist |
| searchable, findable | se pueden encontrar con la búsqueda, se pueden encontrar por significado | Zwei Hälften derselben Aussage, deshalb dieselbe Verbform |
| text recognition | reconocimiento de texto | OCR bleibt als Abkürzung stehen, wo der Quellstring sie führt |
| storage | almacenamiento, almacenamiento externo | |
| Team Folders | Team Folders | Eigenname der Nextcloud-Funktion, in der spanischen Oberfläche unübersetzt |
| upload | subir | Die Wortwahl von Nextcloud selbst |
| remedy (die Abhilfe, oft nur `None.`) | `Ninguna.` | Weiblich, weil es sich auf `la solución` bezieht, und deshalb nicht `Ninguno.` |

## Typografie

Jede Regel unten ist maschinell geprüft, das Ergebnis steht im Abschnitt "Maschinelle
Prüfungen".

- **Echte Akzente sind Pflicht**, nicht Schmuck: `información`, `índice`, `búsqueda`,
  `página`, `día`. Eine Fassung ohne Akzente wäre in mehreren Fällen ein anderes Wort.
- **Kein typographischer Apostroph** (U+2019). Das Spanische braucht ohnehin keinen, und ein
  gemischter Bestand wäre eine Diff-Falle für die Dateien, die diesen Katalog später anfassen.
- **Kein geschütztes Leerzeichen**, weder U+00A0 noch das schmale U+202F. Sie sind unsichtbar,
  und ein Katalog voll unsichtbarer Zeichen ist ein Katalog, dessen Diff niemand liest.
- **Kein Gedankenstrich**, weder U+2014 noch U+2013. Das ist die Regel des Repositoriums und
  wird vom Prosa-Scanner über jede Katalogdatei gehalten.
- **Fragen öffnen mit `¿`**, Ausrufe mit `¡`. Betroffen sind die beiden Sätze, die vor dem
  Entfernen indexierter Inhalte rückfragen; Ausrufe kommt auf beiden Seiten keiner vor.
- **Anführung des Suchbegriffs mit `«` und `»`**, ohne Leerzeichen innen, also `«%s»`. Für
  Bezeichner der Oberfläche und für Befehle bleibt es beim geraden ASCII-Anführungszeichen,
  genau wie im deutschen und im französischen Bestand: `"occ findling:index --restart"`,
  `"Carpetas excluidas"`.
- **Die Platzhalter sind die des Schlüssels**, in Art und Zahl. `%1$s in %2$s` wird
  `%1$s en %2$s` und niemals `%s en %s`.
- **Ein literales Prozentzeichen wird `%%` geschrieben.** Der Grund ist gemessen und nicht
  befürchtet: Nextcloud reicht jeden Katalogwert durch `vsprintf`, ein nacktes `%` wirft dort
  einen `ValueError`, und die Seite bleibt weiß. Spanisch ist genau der Fall, für den der
  Scanner `scan_percent_discipline` aus Plan 20-03 gebaut wurde, weil "50 % de los archivos"
  die natürliche Schreibweise ist. **In diesem Katalog steht kein einziges Prozentzeichen
  dieser Art**, auch kein verdoppeltes: wo der deutsche Satz "100 Prozent" sagt, sagt der
  spanische `el cien por cien`. Umformulieren war hier billiger als retten, und der Satz liest
  sich besser als mit `%%`.

## Pluralformen

Die spanische Regel lautet

```
nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
```

und steht wörtlich so als `"pluralForm"` in `php/l10n/es.json` und als vierter Parameter von
`OC.L10N.register` in `php/l10n/es.js`. Sie ist aus `docs/l10n-catalogues.md`, Abschnitt 3,
übernommen und nicht nachgetippt; dort steht auch, dass NC 34.0.3 und NC 35.0.0 für Spanisch
dieselbe Zeichenkette führen.

**Die fünf Pluralwerte tragen drei Formen, und Form 1 und Form 2 sind wortgleich.** Der Grund
steht gemessen in `docs/l10n-catalogues.md`, Abschnitt 4, und wird hier nicht neu entschieden:
PHP liest die deklarierte Regel gar nicht und erreicht Form 2 nie, der Browser wertet die Regel
aus und wählt bei n gleich 2 den Index 2. Stünden dort verschiedene Wörter, liefe dieselbe
Zeile derselben Seite im Server-HTML anders als nach dem ersten Poll. Die Millionenform auf
Index 1, in die die Kerndatei `core/l10n/pt_BR.json` läuft, ist damit ausdrücklich nicht
geschrieben.

In der Tabelle unten stehen die Formen eines Pluralschlüssels durch ` / ` getrennt in einer
Zelle, zuerst der Singular, wie es der französische Bestand macht. Die deutsche Spalte trägt
zwei Formen und die spanische drei; dass die zweite und die dritte spanische Form gleich lauten,
ist der Entscheid oben und kein Fehler dieser Tabelle.

## Die Tabelle

Alle drei Spalten sind aus `php/l10n/de.json` und `php/l10n/es.json` erzeugt und nicht
abgetippt; die Reihenfolge ist die der Dateien. Die Spaltennamen sind ASCII, weil sie
Vertragsbezeichner sind und die Projektregel echte Umlaute der deutschen Prosa vorbehält. Der
Schlüssel ist der englische Quellstring: er steht wörtlich so im Template, läuft dort durch
`$l->t()` und ist in jeder Katalogdatei der Schlüssel der Übersetzung.

Kein Wert und kein Schlüssel kann ein Pipe-Zeichen enthalten, dafür sorgt `scan_pipe_character`
aus Plan 20-03. Diese Tabelle kann also nicht an einem Wortlaut zerbrechen.

| Schluessel | DE | ES |
|---|---|---|
| `Findling` | Findling | Findling |
| `File contents` | Dateiinhalte | Contenido de los archivos |
| `Search coverage` | Deckungsgrad der Suche | Cobertura de la búsqueda |
| `%1$s of %2$s indexable files are searchable` | %1$s von %2$s indexierbaren Dateien sind durchsuchbar | %1$s de %2$s archivos indexables se pueden encontrar con la búsqueda |
| `The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.` | Der Anteil ist im Moment nicht berechenbar, weil das Backend nicht antwortet. %s Dateien dieser Instanz sind indexierbar. | La proporción no se puede calcular en este momento porque el servicio no responde. %s archivos de esta instancia son indexables. |
| `Deliberately left out: %s` | Bewusst ausgelassen: %s | Excluidos a propósito: %s |
| `Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.` | Diese Dateien sind zu groß, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen. Sie stehen nicht im Nenner darüber, damit der Deckungsgrad 100 Prozent erreichen kann. | Esos archivos son demasiado grandes, de un tipo que Findling no lee, o excluidos por una regla. No están en el denominador de arriba, de modo que la cobertura puede alcanzar el cien por cien. |
| `Provisional figure, %1$s of %2$s storages have been counted through.` | Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt. | Cifra provisional, se han contado %1$s de %2$s almacenamientos. |
| `Findable by meaning` | Auffindbar nach Bedeutung | Se puede encontrar por significado |
| `%1$s of %2$s indexable files can also be found by meaning` | %1$s von %2$s indexierbaren Dateien sind auch nach Bedeutung auffindbar | %1$s de %2$s archivos indexables también se pueden encontrar por significado |
| `The semantic share cannot be worked out right now. The backend does not answer, or it does not report this figure yet.` | Der semantische Anteil ist im Moment nicht berechenbar. Das Backend antwortet nicht, oder es meldet diese Zahl noch nicht. | La proporción semántica no se puede calcular en este momento. El servicio no responde, o todavía no informa de esta cifra. |
| `The model is in memory, the semantic search is answering.` | Das Modell liegt im Speicher, die semantische Suche antwortet. | El modelo está en memoria, la búsqueda semántica responde. |
| `The model is read when it is first needed. That is the normal state.` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | El modelo se carga la primera vez que hace falta. Ese es el estado normal. |
| `The semantic half is switched off in the settings of the container.` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | La mitad semántica está desactivada en los ajustes del contenedor. |
| `There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.` | In diesem Abbild liegt kein Modell. Die Suche liefert weiterhin Volltexttreffer, die semantische Hälfte bleibt leer. | En esta imagen no hay ningún modelo. La búsqueda sigue respondiendo con resultados de texto completo, la mitad semántica queda vacía. |
| `Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.` | Das Laden des Modells ist einmal gescheitert und wird in Kürze erneut versucht. Bis dahin liefert die Suche Volltexttreffer. | La carga del modelo falló una vez y se reintenta en breve. Hasta entonces la búsqueda responde con resultados de texto completo. |
| `The model was released to save memory. The next search answers with full text hits and loads it again in the background.` | Das Modell wurde zum Sparen freigegeben. Die nächste Suche antwortet mit Volltexttreffern und lädt es im Hintergrund nach. | El modelo se liberó para ahorrar memoria. La próxima búsqueda responde con resultados de texto completo y lo vuelve a cargar en segundo plano. |
| `This container does not report the state of the model yet.` | Dieser Container meldet den Zustand des Modells noch nicht. | Este contenedor todavía no informa del estado del modelo. |
| `The full text search covers every indexed document. The semantic search covers the beginning of each document, and this second figure fills up after the first index has finished.` | Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem Erstindex nach. | La búsqueda de texto completo cubre todos los documentos indexados. La búsqueda semántica cubre el comienzo de cada documento, y esta segunda cifra se completa después de que termine el primer índice. |
| `Up to date, last checked %s` | Aktuell, letzte Prüfung %s | Al día, última comprobación %s |
| `Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.` | Die Indexierung kommt seit %s nicht voran. In dieser Zeit hat weder ein Hintergrundauftrag noch das Backend etwas fertiggestellt. | La indexación no avanza desde hace %s. En ese tiempo ni una tarea en segundo plano ni el servicio han terminado nada. |
| `No background job of this app has run yet. Background jobs may not be running.` | Noch kein Hintergrundauftrag dieser App ist gelaufen. Möglicherweise laufen die Hintergrundaufträge nicht. | Todavía no se ha ejecutado ninguna tarea en segundo plano de esta aplicación. Puede que las tareas en segundo plano no estén funcionando. |
| `Indexing is running.` | Die Indexierung läuft. | La indexación está en marcha. |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | Die Zahlen konnten nicht aktualisiert werden. Die Werte unten sind die letzten, die diese Seite bekommen hat. | No se han podido actualizar los números. Las cifras de abajo son las últimas que recibió esta página. |
| `_%n minute_::_%n minutes_` | %n Minute / %n Minuten | %n minuto / %n minutos / %n minutos |
| `_%n hour_::_%n hours_` | %n Stunde / %n Stunden | %n hora / %n horas / %n horas |
| `_%n day_::_%n days_` | %n Tag / %n Tage | %n día / %n días / %n días |
| `Waiting in the queue` | Wartet in der Warteschlange | En espera en la cola |
| `Being processed` | Wird gerade verarbeitet | En proceso |
| `Indexed` | Indexiert | Indexado |
| `Skipped` | Übersprungen | Omitido |
| `Failed` | Fehlgeschlagen | Fallido |
| `Excluded` | Ausgeschlossen | Excluido |
| `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst. | Los archivos excluidos no cuentan en la cifra de cobertura. Son los archivos que Findling no toca por indicación suya. |
| `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter. | Queda poco espacio en disco. La indexación está en pausa para que el índice siga intacto. La búsqueda sigue funcionando. |
| `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer. | El índice se construyó con un análisis de texto más antiguo. Reconstruirlo con "occ findling:index --restart", si no seguirán faltando resultados. |
| `Findling is rebuilding its index so that the newly switched on languages can be searched. %1$s of %2$s documents have been carried over. Search keeps answering while this runs, and there is nothing to start or to restart.` | Findling baut seinen Index neu auf, damit die neu eingeschalteten Sprachen durchsucht werden können. %1$s von %2$s Dokumenten sind übertragen. Die Suche antwortet währenddessen weiter, und es gibt nichts zu starten oder neu zu starten. | Findling está reconstruyendo su índice para que se puedan buscar los idiomas recién activados. Se han trasladado %1$s de %2$s documentos. La búsqueda sigue respondiendo mientras tanto, y no hay nada que iniciar ni que reiniciar. |
| `Findling wants to rebuild its index for the newly switched on languages and there is not enough room: %s more are needed next to what the index already uses. Free that much, or set the environment variable FINDLING_REBUILD_FALLBACK=fullreindex to have the backend read the files again instead. Either way the backend only tries again after a restart of the container.` | Findling möchte seinen Index für die neu eingeschalteten Sprachen neu aufbauen, und es ist nicht genug Platz: %s fehlen zusätzlich zu dem, was der Index bereits belegt. Geben Sie so viel frei, oder setzen Sie die Umgebungsvariable FINDLING_REBUILD_FALLBACK=fullreindex, damit das Backend die Dateien stattdessen neu liest. In beiden Fällen versucht es das Backend erst nach einem Neustart des Containers erneut. | Findling quiere reconstruir su índice para los idiomas recién activados y no hay espacio suficiente: hacen falta %s más, además de lo que el índice ya ocupa. Libere esa cantidad, o establezca la variable de entorno FINDLING_REBUILD_FALLBACK=fullreindex para que el servicio vuelva a leer los archivos en su lugar. En ambos casos el servicio no lo vuelve a intentar hasta que se reinicia el contenedor. |
| `Languages of the index: %1$s switched on, %2$s with text in the index.` | Sprachen des Index: %1$s eingeschaltet, %2$s mit Text im Index. | Idiomas del índice: %1$s activados, %2$s con texto en el índice. |
| `No numbers yet` | Noch keine Zahlen | Todavía no hay cifras |
| `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` | Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen. | La primera pasada de indexación aún no ha terminado. Findling arrancó por sí solo, no hay nada que configurar. |
| `The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.` | Die beiden Hälften von Findling melden unterschiedliche Versionen: diese App ist %1$s, das Backend ist %2$s. Solange sie nicht zusammenpassen, antwortet die Suche ohne Ergebnisse, weil eine falsche Antwort ohne Hinweis schlimmer wäre. Beide Hälften auf dieselbe Version bringen. | Las dos mitades de Findling informan de versiones distintas: esta aplicación es %1$s, el servicio es %2$s. Mientras no coincidan, la búsqueda responde sin resultados, porque una respuesta equivocada sin aviso sería peor. Ponga ambas mitades en la misma versión. |
| `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` | Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist. | El servicio de Findling no responde. Los números de abajo son los últimos que registró esta aplicación. Compruebe en Aplicaciones que la aplicación externa "Findling Backend" está instalada y en marcha. |
| `Estimate for the first index` | Schätzung für den Erstindex | Estimación para el primer índice |
| `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | %1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index. | %1$s archivos, %2$s de ellos necesitan OCR. Unos %3$s y unos %4$s de índice. |
| `%1$s files, %2$s of them need OCR.` | %1$s Dateien, davon %2$s mit OCR. | %1$s archivos, %2$s de ellos necesitan OCR. |
| `%1$s to %2$s` | %1$s bis %2$s | %1$s a %2$s |
| `Counting the files, this takes a moment.` | Die Dateien werden gezählt, das dauert einen Moment. | Se están contando los archivos, esto tarda un momento. |
| `Startup value, being measured.` | Startwert, wird gemessen. | Valor inicial, se está midiendo. |
| `The space needed is measured as soon as the first documents are in the index.` | Der Platzbedarf wird gemessen, sobald die ersten Dokumente im Index sind. | El espacio necesario se mide en cuanto los primeros documentos están en el índice. |
| `The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.` | Der Index braucht voraussichtlich mehr Platz, als auf diesem Datenträger frei ist. Die Indexierung pausiert, bevor der Datenträger voll wird, und die Suche funktioniert weiter. | Se prevé que el índice necesite más espacio del que hay libre en este volumen. La indexación se detiene antes de que el volumen se llene, y la búsqueda sigue funcionando. |
| `Findling does not wait for a confirmation. The first index has already started.` | Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits. | Findling no espera ninguna confirmación. El primer índice ya ha comenzado. |
| `Files that were not indexed` | Nicht indexierte Dateien | Archivos que no se indexaron |
| `Files that were not indexed, grouped by reason` | Nicht indexierte Dateien, nach Grund gruppiert | Archivos que no se indexaron, agrupados por motivo |
| `Every file was indexed. Nothing was skipped and nothing failed.` | Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen. | Se indexaron todos los archivos. No se omitió nada y no falló nada. |
| `Reason` | Grund | Motivo |
| `Files` | Dateien | Archivos |
| `State` | Zustand | Estado |
| `Show example paths` | Beispielpfade anzeigen | Mostrar rutas de ejemplo |
| `Hide example paths` | Beispielpfade verbergen | Ocultar rutas de ejemplo |
| `_and %n more_::_and %n more_` | und %n weitere / und %n weitere | y %n más / y %n más / y %n más |
| `File no longer exists (ID %s)` | Datei existiert nicht mehr (ID %s) | El archivo ya no existe (ID %s) |
| `%s (in the trash bin)` | %s (im Papierkorb) | %s (en la papelera) |
| `Indexed, text truncated` | Indexiert, Text gekürzt | Indexado, texto recortado |
| `Unknown reason (%s)` | Unbekannter Grund (%s) | Motivo desconocido (%s) |
| `This app does not know this code. It may come from a newer version of the backend.` | Diese App kennt diesen Code nicht. Er kann von einer neueren Fassung des Backends kommen. | Esta aplicación no conoce este código. Puede venir de una versión más reciente del servicio. |
| `Text truncated` | Text gekürzt | Texto recortado |
| `The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.` | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. | El comienzo del documento se puede buscar, el resto no. Los documentos muy largos se cortan a propósito. |
| `Too large` | Zu groß | Demasiado grande |
| `Raise the value under "Largest file to read".` | Den Wert unter "Größte zu lesende Datei" erhöhen. | Aumente el valor en "Archivo más grande que se lee". |
| `File type not supported` | Dateityp nicht unterstützt | Tipo de archivo no admitido |
| `None. Findling reads PDF, Office, OpenDocument, text and images.` | Keine. Findling liest PDF, Office, OpenDocument, Text und Bilder. | Ninguna. Findling lee PDF, Office, OpenDocument, texto e imágenes. |
| `Password protected` | Passwortgeschützt | Protegido con contraseña |
| `None. Without the password the content cannot be read.` | Keine. Ohne Passwort ist der Inhalt nicht lesbar. | Ninguna. Sin la contraseña no se puede leer el contenido. |
| `No text in the document` | Kein Text im Dokument | No hay texto en el documento |
| `None. The document carries neither a text layer nor recognisable writing.` | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. | Ninguna. El documento no contiene ni capa de texto ni escritura reconocible. |
| `No text content` | Kein Textinhalt | Sin contenido de texto |
| `None. The file is readable but carries no text.` | Keine. Die Datei ist lesbar, enthält aber keinen Text. | Ninguna. El archivo se puede leer, pero no contiene texto. |
| `Spreadsheet too large` | Tabelle zu groß | Hoja de cálculo demasiado grande |
| `None. Very large spreadsheets are skipped so the container does not fall over.` | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. | Ninguna. Las hojas de cálculo muy grandes se omiten para que el contenedor no se caiga. |
| `File no longer present` | Datei nicht mehr vorhanden | El archivo ya no está presente |
| `None. The file was already deleted or moved when it was read.` | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. | Ninguna. El archivo ya estaba borrado o movido cuando se leyó. |
| `Image without recognisable writing` | Bild ohne erkennbare Schrift | Imagen sin escritura reconocible |
| `None.` | Keine. | Ninguna. |
| `Excluded by a rule` | Durch Regel ausgeschlossen | Excluido por una regla |
| `Remove the matching entry under "Excluded folders".` | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. | Quite la entrada correspondiente en "Carpetas excluidas". |
| `Not readable for the users asked` | Für die gefragten Nutzer nicht lesbar | No legible para los usuarios consultados |
| `The file is still there. Check the advanced permissions of the Team Folder: Findling reads a file only as a user who may open it and asks the first 20 of its users in alphabetical order.` | Die Datei ist noch vorhanden. Die erweiterten Berechtigungen des Team Folders prüfen: Findling liest eine Datei nur als Nutzer, der sie öffnen darf, und fragt die ersten 20 ihrer Nutzer in alphabetischer Reihenfolge. | El archivo sigue existiendo. Compruebe los permisos avanzados de la Team Folder: Findling solo lee un archivo en nombre de un usuario que puede abrirlo y consulta a los primeros 20 de sus usuarios en orden alfabético. |
| `The user named in front of the path may not open this file. The diagnosis is about the file itself.` | Der vor dem Pfad genannte Nutzer darf diese Datei nicht öffnen. Die Diagnose gilt der Datei selbst. | El usuario indicado delante de la ruta no puede abrir este archivo. El diagnóstico se refiere al archivo en sí. |
| `File is empty` | Datei ist leer | El archivo está vacío |
| `None. The file has 0 bytes.` | Keine. Die Datei hat 0 Byte. | Ninguna. El archivo tiene 0 bytes. |
| `File damaged` | Datei beschädigt | Archivo dañado |
| `Check the file outside of Nextcloud and upload it again.` | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. | Compruebe el archivo fuera de Nextcloud y vuelva a subirlo. |
| `Document structure faulty` | Dokumentstruktur fehlerhaft | Estructura del documento defectuosa |
| `Open the document in the program it came from and save it again.` | Das Dokument im Ursprungsprogramm öffnen und neu speichern. | Abra el documento en el programa del que procede y vuelva a guardarlo. |
| `Character set not recognised` | Zeichensatz nicht erkannt | Juego de caracteres no reconocido |
| `Save the file as UTF-8 and upload it again.` | Die Datei als UTF-8 speichern und neu hochladen. | Guarde el archivo como UTF-8 y vuelva a subirlo. |
| `Timed out while reading` | Zeitüberschreitung beim Lesen | Tiempo de espera agotado al leer |
| `The next run tries again.` | Wird beim nächsten Lauf erneut versucht. | La próxima pasada lo intenta de nuevo. |
| `Not enough memory while reading` | Zu wenig Speicher beim Lesen | Memoria insuficiente al leer |
| `The next run tries again. If it happens again, lower the size cap.` | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken. | La próxima pasada lo intenta de nuevo. Si vuelve a ocurrir, baje el límite de tamaño. |
| `File was not retrievable` | Datei war nicht abrufbar | No se pudo obtener el archivo |
| `Stuck repeatedly` | Mehrfach hängen geblieben | Atascado varias veces |
| `Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.` | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. | Findling no vuelve a intentarlo con este archivo. Use la consulta para comprobar si se abre fuera de Nextcloud. |
| `Text recognition failed` | Texterkennung fehlgeschlagen | El reconocimiento de texto falló |
| `Text recognition not available` | Texterkennung nicht verfügbar | Reconocimiento de texto no disponible |
| `The backend could not start Tesseract. Check the log of the External App.` | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. | El servicio no pudo iniciar Tesseract. Compruebe el registro de la aplicación externa. |
| `Look up one file` | Einzelne Datei prüfen | Consultar un archivo |
| `Path or file ID` | Pfad oder Datei-ID | Ruta o ID de archivo |
| `A path as Nextcloud stores it, or the numeric ID from the list above.` | Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben. | Una ruta tal como la guarda Nextcloud, o el número de la lista de arriba. |
| `Look up file` | Datei prüfen | Consultar archivo |
| `Looking up a single file needs JavaScript. Everything above stays complete without it.` | Die Einzelprüfung braucht JavaScript. Alles darüber bleibt auch ohne vollständig lesbar. | La consulta de un solo archivo necesita JavaScript. Todo lo de arriba sigue completo sin él. |
| `No file at this path, and no file with this ID.` | Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID. | No hay ningún archivo en esta ruta, ni ningún archivo con este ID. |
| `Not seen yet` | Noch nicht gesehen | Todavía no visto |
| `State unknown right now` | Zustand im Moment unbekannt | Estado desconocido en este momento |
| `File ID: %s` | Datei-ID: %s | ID de archivo: %s |
| `Last checked %s` | Zuletzt geprüft: %s | Última comprobación: %s |
| `The lookup did not work. Nothing about this file has changed.` | Die Prüfung hat nicht funktioniert. An dieser Datei hat sich nichts geändert. | La consulta no funcionó. En este archivo no ha cambiado nada. |
| `The state of this file is unknown right now because the backend does not answer.` | Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet. | El estado de este archivo se desconoce en este momento porque el servicio no responde. |
| `This file has not reached the queue. The next comparison run picks it up.` | Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab. | Este archivo todavía no ha llegado a la cola. La próxima pasada de comparación lo recoge. |
| `It was indexed before and is recorded again on the next comparison run.` | Sie war vorher indexiert und wird beim nächsten Abgleichlauf neu erfasst. | Estaba indexado antes y se vuelve a registrar en la próxima pasada de comparación. |
| `This file was indexed and has since been deleted. It is out of the index with it.` | Diese Datei war indexiert und ist inzwischen gelöscht. Damit ist sie auch aus dem Index heraus. | Este archivo estaba indexado y desde entonces se ha borrado. Con ello también está fuera del índice. |
| `In the trash bin` | Im Papierkorb | En la papelera |
| `Restore the file. The next comparison run picks it up.` | Die Datei wiederherstellen. Der nächste Abgleichlauf holt sie ab. | Restaure el archivo. La próxima pasada de comparación lo recoge. |
| `Storage is not indexed` | Speicherort wird nicht indexiert | El almacenamiento no se indexa |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | Findling liest die Heimatverzeichnisse der Nutzer. Team Folders und externer Speicher sind eigene Einstellungen. | Findling lee los directorios personales de sus usuarios. Team Folders y el almacenamiento externo son ajustes propios. |
| `This is a folder` | Das ist ein Ordner | Esto es una carpeta |
| `Enter the path of a file. A folder has no state of its own.` | Den Pfad einer Datei eingeben. Ein Ordner hat keinen eigenen Zustand. | Introduzca la ruta de un archivo. Una carpeta no tiene estado propio. |
| `Attempts so far: %s` | Bisherige Versuche: %s | Intentos hasta ahora: %s |
| `The next background run picks this file up (%s).` | Der nächste Hintergrundlauf holt diese Datei ab (%s). | La próxima pasada en segundo plano recoge este archivo (%s). |
| `The content of this file is searchable.` | Der Inhalt dieser Datei ist durchsuchbar. | El contenido de este archivo se puede buscar. |
| `_A worker holds this file. The claim runs out in %n second if nothing acknowledges it._::_A worker holds this file. The claim runs out in %n seconds if nothing acknowledges it._` | Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunde aus, wenn ihn niemand quittiert. / Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunden aus, wenn ihn niemand quittiert. | Un proceso de tratamiento retiene este archivo. La reserva caduca en %n segundo si nadie la confirma. / Un proceso de tratamiento retiene este archivo. La reserva caduca en %n segundos si nadie la confirma. / Un proceso de tratamiento retiene este archivo. La reserva caduca en %n segundos si nadie la confirma. |
| `Rules and limits` | Regeln und Grenzen | Reglas y límites |
| `Excluded folders` | Ausgeschlossene Ordner | Carpetas excluidas |
| `Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups` | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, keine Platzhalter und keine Muster. Beispiel: Backups | Comparación por prefijo sobre la ruta tal como la muestran las listas de esta página, sin comodines ni patrones. Ejemplo: Backups |
| `Add exclusion` | Ausschluss hinzufügen | Añadir exclusión |
| `Remove exclusion %s` | Ausschluss %s entfernen | Quitar la exclusión %s |
| `No folder is excluded.` | Kein Ordner ist ausgeschlossen. | No hay ninguna carpeta excluida. |
| `Largest file to read` | Größte zu lesende Datei | Archivo más grande que se lee |
| `Files above this size are recorded as skipped (too large) and never read.` | Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen. | Los archivos por encima de este tamaño se anotan como omitidos (demasiado grandes) y no se leen nunca. |
| `The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container.` | Das Backend dieser Instanz liest höchstens %s MB. Für mehr FINDLING_MAX_FILE_BYTES in den App-Einstellungen von AppAPI anheben, was den Container neu startet. | El servicio de esta instancia lee como mucho %s MB. Para más, suba FINDLING_MAX_FILE_BYTES en los ajustes de aplicación de AppAPI, lo que reinicia el contenedor. |
| `Index Team Folders` | Team Folders indexieren | Indexar Team Folders |
| `Index external storage` | Externen Speicher indexieren | Indexar el almacenamiento externo |
| `External storage can be slow or charged per request. Indexing reads every file once.` | Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal. | El almacenamiento externo puede ser lento o cobrarse por acceso. La indexación lee cada archivo una vez. |
| `The next run applies the new rules. Nothing restarts.` | Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu. | La próxima pasada aplica las nuevas reglas. No se reinicia nada. |
| `Save rules` | Regeln speichern | Guardar reglas |
| `Rules saved. The next run applies them.` | Regeln gespeichert. Der nächste Lauf übernimmt sie. | Reglas guardadas. La próxima pasada las aplica. |
| `The rules were not saved. Nothing changed.` | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | Las reglas no se guardaron. No ha cambiado nada. |
| `Enter a size between %1$s and %2$s MB.` | Eine Größe zwischen %1$s und %2$s MB eingeben. | Introduzca un tamaño entre %1$s y %2$s MB. |
| `Enter a folder path.` | Einen Ordnerpfad eingeben. | Introduzca una ruta de carpeta. |
| `This path is already excluded.` | Dieser Pfad ist bereits ausgeschlossen. | Esta ruta ya está excluida. |
| `Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.` | Einen Eintrag zu entfernen wirkt innerhalb von %1$s Stunden, wenn der nächste Abgleichlauf diese Dateien wieder aufnimmt. Mit "%2$s" sofort übernehmen. | Quitar una entrada surte efecto en un plazo de %1$s horas, cuando la próxima pasada de comparación vuelva a recoger esos archivos. Ejecute "%2$s" para aplicarlo de inmediato. |
| `Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %1$s entfernt außerdem %2$s bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | ¿Quitar el contenido indexado? Excluir %1$s retira además del índice %2$s documentos ya indexados bajo esa ruta. Los archivos en sí quedan intactos en el disco. |
| `Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | ¿Quitar el contenido indexado? Excluir %s retira además del índice los documentos ya indexados bajo esa ruta. Los archivos en sí quedan intactos en el disco. |
| `at least %s` | mindestens %s | al menos %s |
| `Exclude and remove` | Ausschließen und entfernen | Excluir y quitar |
| `Keep files indexed` | Dateien indexiert lassen | Mantener los archivos indexados |
| `Search` | Suchen | Buscar |
| `Search term` | Suchbegriff | Término de búsqueda |
| `invoice 2026` | Rechnung 2026 | factura 2026 |
| `Search file names only` | Nur Dateinamen durchsuchen | Buscar solo en los nombres de archivo |
| `Results for "%s"` | Treffer für „%s“ | Resultados de «%s» |
| `Search results` | Suchergebnisse | Resultados de la búsqueda |
| `%1$s in %2$s` | %1$s in %2$s | %1$s en %2$s |
| `last opened` | zuletzt geöffnet | abierto por última vez |
| `Show all results` | Alle Treffer anzeigen | Mostrar todos los resultados |
| `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | Abre la página de resultados de Findling |
| `Previous page` | Vorherige Seite | Página anterior |
| `Next page` | Nächste Seite | Página siguiente |
| `Page %s` | Seite %s | Página %s |
| `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | Hay más resultados. Acote la búsqueda para verlos. |
| `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | Busque en el contenido de sus archivos |
| `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | Escriba una palabra de un documento. Findling busca el texto dentro de sus archivos, incluidos los PDF escaneados. |
| `No file contains "%s"` | Keine Datei enthält „%s“ | Ningún archivo contiene «%s» |
| `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | Pruebe con otra palabra, con parte de una palabra compuesta, o revise la ortografía. |
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen. | Otros archivos contienen esta palabra, pero ninguno que usted pueda abrir. |
| `The search is not answering right now` | Die Suche antwortet gerade nicht | La búsqueda no responde en este momento |
| `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | Findling no pudo contactar con su servicio. Sus archivos no han cambiado. Inténtelo de nuevo en un momento, y avise a su administración si sigue así. |
| `Try again` | Erneut versuchen | Intentar de nuevo |
| `Findling is not ready to search` | Findling ist nicht suchbereit | Findling no está listo para buscar |
| `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | Las dos mitades de Findling informan de versiones distintas. Su administración tiene que actualizar ambas a la vez. |
| `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | El índice todavía se está construyendo, por eso pueden faltar resultados. |
| `File type` | Dateityp | Tipo de archivo |
| `PDF` | PDF | PDF |
| `Documents` | Dokumente | Documentos |
| `Spreadsheets` | Tabellen | Hojas de cálculo |
| `Presentations` | Präsentationen | Presentaciones |
| `Images` | Bilder | Imágenes |
| `Text` | Text | Texto |
| `Time range` | Zeitraum | Periodo |
| `Today` | Heute | Hoy |
| `Last 7 days` | Letzte 7 Tage | Últimos 7 días |
| `Last 30 days` | Letzte 30 Tage | Últimos 30 días |
| `This year` | Dieses Jahr | Este año |
| `Remove filter %s` | Filter %s entfernen | Quitar el filtro %s |
| `Reset all filters` | Alle Filter zurücksetzen | Restablecer todos los filtros |
| `Sort by` | Sortieren nach | Ordenar por |
| `Relevance` | Relevanz | Relevancia |
| `Last modified` | Zuletzt geändert | Última modificación |
| `Oldest first` | Älteste zuerst | Más antiguos primero |
| `Modified on %s` | Geändert am %s | Modificado el %s |
| `%1$s in %2$s, modified on %3$s` | %1$s in %2$s, geändert am %3$s | %1$s en %2$s, modificado el %3$s |
| `No results with the active filters` | Keine Treffer mit den aktiven Filtern | No hay resultados con los filtros activos |
| `Remove a filter or widen the time range.` | Entfernen Sie einen Filter oder erweitern Sie den Zeitraum. | Quite un filtro o amplíe el periodo. |
| `Reset filters` | Filter zurücksetzen | Restablecer filtros |

## Ausnahmen für das Vollständigkeitsgate G2

Gate G2, heute `test_every_catalogue_value_carries_a_wording_of_its_language`, fordert, dass
kein Wert leer und keiner mit dem englischen Quellstring identisch ist. Genau zwei Schlüssel
sind es im Spanischen absichtlich. Das ist eine benannte Liste und ausdrücklich **keine**
Toleranzschwelle: eine Schwelle würde einen vergessenen Wortlaut genauso mitdecken wie einen
gewollten, eine Liste deckt nur, was in ihr steht. Die Liste darf wachsen, die Zahl zwei ist
keine Grenze, sondern das Ergebnis des Zählens, und jeder Eintrag trägt seinen Grund bei sich.

- `Findling`: Eigenname der App, in jeder Sprache dasselbe Wort. Er steht als Schlüssel in
  `de.json` und muss deshalb in `es.json` stehen, hat aber keinen eigenen Wortlaut.
- `PDF`: Eigenname eines Dateiformats, in jeder Sprache dieselbe Abkürzung.

Die Liste ist nicht geraten worden. Das Gate lief einmal mit leerem Mapping für `es` und
meldete vier Funde, zwei Schlüssel über zwei Dateien; beide sind hier benannt, und für keinen
weiteren Schlüssel war der gleiche Wortlaut das Ergebnis. Sie ist kürzer als die französische
(fünf Einträge), weil `Page %s`, `Documents` und `Images` im Spanischen echte eigene Wortlaute
haben: `Página %s`, `Documentos`, `Imágenes`.

Dieselben zwei Schlüssel mit denselben Gründen stehen in
`VALUES_THAT_MAY_EQUAL_THEIR_KEY["es"]` in `backend/tests/test_admin_ui_contract.py`. Doku und
Gate dürfen hier nicht auseinanderlaufen: die Doku sagt, was erlaubt ist, das Gate hält es.

## Maschinelle Prüfungen

Gefahren am 25.09.2026 über die beiden erzeugten Dateien, nicht per Augenmaß:

| Prüfung | Ergebnis |
|---|---|
| Schlüsselmenge `es.json` gleich `de.json`, in derselben Reihenfolge | ja, 202 von 202, fehlend 0 |
| Schlüsselmenge `es.js` gleich `es.json` (Objektvergleich über den `register`-Rumpf) | ja, identisch |
| Jeder Schlüssel aus `es.json` kommt in dieser Datei vor | fehlend: 0 |
| Platzhalter-Parität Schlüssel gegen Wert, über alle 40 Schlüssel mit Direktiven, Pluralschlüssel an `_::_` geteilt | 0 Abweichungen |
| Pluralschlüssel mit genau drei Formen | 5 von 5 |
| Form 1 und Form 2 wortgleich | 5 von 5 |
| Pluralschlüsselmenge gleich der deutschen | ja |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, mit `nplurals=3` | ja, in beiden Dateien |
| U+2019 (typographischer Apostroph) | 0 |
| U+2014 und U+2013 (Gedankenstriche) | 0 |
| U+00A0 und U+202F (geschützte Leerzeichen) | 0 |
| Nackte Prozentzeichen, also `%` ohne erkannte Direktive | 0 in Schlüsseln und in allen Formen |
| Pipe-Zeichen (der senkrechte Strich, mit dem Nextcloud Pluralformen verbindet) | 0 in Schlüsseln und in allen Formen |
| Wert identisch mit dem englischen Quellstring | 2, beide oben benannt: `Findling` und `PDF` |
| LF, UTF-8 ohne BOM, abschließender Zeilenumbruch | beide Dateien, byteweise geprüft |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |

Was keine Maschine prüfen kann, ist die Sprache. Das ist der Gegenstand des Abschnitts
darunter.

## Abnahme

**Erzeugt am 25.09.2026, Plan 20-04.** Die spanischen Wortlaute dieser Tabelle sind maschinell
entstanden und anschließend gegen die Gates gefahren, die der Abschnitt "Maschinelle Prüfungen"
aufzählt: Schlüsselmenge, Gleichstand der beiden Dateien, Platzhalterparität, Formenzahl,
Pluralregel, Prozentdisziplin, Pipe-Zeichen, Prosa-Scan auf Gedankenstriche und Symbolzeichen,
Vollständigkeit mit benannter Ausnahmeliste.

**Dieser Katalog ist von keinem Muttersprachler gelesen worden.** Das ist keine offene
Aufgabe, die jemand vergessen hat, sondern der gesperrte Entscheid E-17-5, Option a: die vier
neuen Sprachen entstehen maschinell und werden über das offene Community-Review korrigiert, das
jede App im Nextcloud App Store hat. Wer einen Fehler findet, meldet ihn als Issue im
Repositorium `street1983nk/nextcloud-search` oder schickt eine Änderung an dieser Tabelle; die
nächste Ausgabe nimmt ihn mit. Ein Muttersprachler-Gate ist ausdrücklich **nicht** gewählt
worden und wird hier auch nicht nachträglich eingeführt.

**Die Auslieferung wartet darauf nicht.** Das ist die Abwägung hinter dem Entscheid: ein
spanischer Katalog mit einzelnen unrunden Sätzen ist für einen spanischen Nutzer besser als
eine englische Oberfläche, und die Fehler, die eine Maschine macht, sind sichtbar und
korrigierbar. Der Unterschied zum französischen Katalog ist an dieser Stelle ausdrücklich
festgehalten: `docs/l10n-french.md` trägt eine Abnahme durch den Owner, einen französischen
Muttersprachler, datiert auf den 11.09., 19.09. und 24.09.2026. Diese Datei trägt eine Stufe
weniger, und sie sagt es, damit niemand die beiden für gleich abgenommen hält.

**Stand dieser Datei:** alle 202 Zeilen sind am 25.09.2026 entstanden, keine ist später
hinzugekommen, und keine ist abgenommen. Kommt später ein Schlüssel dazu, gehört er in diese
Tabelle und in einen datierten Nachtrag darunter, aus demselben Grund, aus dem
`docs/l10n-french.md` seine Nachträge führt: eine Datei darf keine ungelesene Zeile
stillschweigend mittragen.
