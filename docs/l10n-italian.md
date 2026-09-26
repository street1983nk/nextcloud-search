# Italienische Wortlaute, vollständig

Diese Datei ist die Quelle der beiden italienischen Katalogdateien `php/l10n/it.json` und
`php/l10n/it.js`. Sie trägt die italienischen Wortlaute für **alle** Schlüssel der Adminseite
und der Ergebnisseite, in einer Tabelle, damit ein Leser sie in einem Durchgang prüfen kann und
nicht als Diff über zwei Dateien. Aus dieser Tabelle sind beide Dateien mechanisch entstanden,
ohne zweite Textrunde.

Was für **alle** Sprachdateien dieser Phase gilt, steht nicht hier, sondern einmal in
`docs/l10n-catalogues.md`: warum Nextcloud zehn Dateien und nicht fünf braucht (Abschnitt 1),
welche Regionalvarianten der Kern führt und welche Findling ausliefert (Abschnitt 2), die
wörtlichen Pluralregeln mit ihrer Herkunft (Abschnitt 3) und die Messung, aus der die Wahl der
Formen folgt (Abschnitt 4). Diese Datei verweist dorthin, statt den Beweis ein zweites Mal zu
führen.

Eine Besonderheit des Italienischen gehört an den Anfang, weil sie eine Entscheidung erspart:
**der Kern kennt für Italienisch keine Regionalvariante.** Die Dateiliste in Abschnitt 1 von
`docs/l10n-catalogues.md` führt neben `es` noch `es_EC` und `es_MX` und neben `pt_PT` noch
`pt_BR`, für Italienisch aber genau `it.json` und `it.js`. Der Abschnitt "Die benannte Grenze",
den die spanische Datei braucht, hat hier also keinen Gegenstand: es gibt nichts wegzulassen.

## Die Schlüsselmenge, aus der Datei gezählt

Nicht aus einem Dokument übernommen, sondern am 25.09.2026 mit `json.load` über
`php/l10n/de.json` und `php/l10n/it.json` gezählt:

| Größe | Wert |
|---|---:|
| Schlüssel in `de.json` | **202** |
| Schlüssel in `it.json` | **202** |
| davon mit printf-Direktiven (`%s`, `%1$s`, `%n`) | **40** |
| davon mit Direktiven, ohne die Pluralschlüssel | **35** |
| davon mit Pluralformen (Wert ist eine Liste) | **5** |
| Zeilen in der Tabelle unten | **202** |

Die beiden Direktiven-Zeilen sind zwei Messungen derselben Sache: die zweite zählt die
Schlüssel mit Platzhaltern **ohne** die fünf Pluralschlüssel, deren `%n` ebenfalls eine
Direktive ist. Beide Zahlen stehen hier, damit die nächste Zählung nicht bei einer der beiden
für falsch gehalten wird.

Die Tabelle unten führt **202** Zeilen und nicht 201: wie in `docs/l10n-spanish.md` und anders
als in `docs/l10n-french.md` steht auch `Findling` darin, mit sich selbst als Wortlaut. Er ist
zugleich der erste Eintrag der Ausnahmeliste weiter unten.

## Wortwahl

Damit die Prüfung eine Entscheidung je Begriff ist und nicht 202 Einzelfälle. Die Linie folgt
den französischen und spanischen Entscheiden aus `docs/l10n-french.md` und
`docs/l10n-spanish.md`, weil die drei Kataloge dieselben Sätze übersetzen und eine dritte,
abweichende Linie nur die Pflege verteuert hätte.

| Englisch | Italienisch | Warum |
|---|---|---|
| the backend | il servizio | Derselbe Entscheid wie im Französischen (`le service`) und im Spanischen (`el servicio`). Der Nutzer sieht einen Dienst, der antwortet oder nicht antwortet, und kein Fremdwort. Wo der Eigenname gemeint ist, bleibt er stehen: `l'applicazione esterna "Findling Backend"` |
| run (Lauf, Abgleichlauf, Hintergrundlauf) | passata, passata di confronto, passata in background | `passata` ist das Wort für einen einzelnen Durchgang über einen Bestand und trägt dasselbe Bild wie `pasada` und `passage`. `esecuzione` ist das schwerere Wort für dieselbe Sache, `ciclo` verspricht eine Regelmäßigkeit, die der Abgleichlauf nicht hat |
| background job | processo in background | Die Wortwahl der italienischen Nextcloud-Oberfläche. Von `processo di elaborazione` unterscheidet es sich in der Ergänzung, und beide Begriffe stehen nie im selben Satz |
| worker | processo di elaborazione | Nach dem französischen `processus de traitement` und dem spanischen `proceso de tratamiento`. `lavoratore` wäre der Mensch, `worker` der Anglizismus, und beide sagen dem Verwaltungsnutzer weniger als die Umschreibung |
| index (Substantiv) | l'indice | Mit Artikel und Apostroph, wie es im Satz steht. `indice` ist im Italienischen unmissverständlich, anders als im Spanischen braucht es keinen Akzent zur Unterscheidung |
| index (Verb), indexing | indicizzare, l'indicizzazione | Und nicht `indexare`, das kein italienisches Wort ist; `indicizzare` ist die Form, die die Nextcloud-Oberfläche selbst führt |
| coverage | copertura | Die Zahl, die sagt, welcher Anteil der Dateien durchsuchbar ist |
| file | file | Das Italienische hat das englische Wort übernommen und bildet keinen Plural: `un file`, `i file`. `archivio` bezeichnet den Aufbewahrungsort und nicht die einzelne Datei |
| storage | spazio di archiviazione, archiviazione esterna | Die Wortwahl der italienischen Nextcloud-Oberfläche. Sie ist der Grund für einen Eintrag im Vokabular-Gate, siehe den Abschnitt "Maschinelle Prüfungen" |
| searchable, findable | si possono trovare con la ricerca, si possono trovare per significato | Zwei Hälften derselben Aussage, deshalb dieselbe Verbform |
| text recognition | riconoscimento del testo | OCR bleibt als Abkürzung stehen, wo der Quellstring sie führt |
| Team Folders | Team Folders | Eigenname der Nextcloud-Funktion, in der italienischen Oberfläche unübersetzt |
| remedy (die Abhilfe, oft nur `None.`) | `Nessuna.` | Weiblich, weil es sich auf `la soluzione` bezieht, und deshalb nicht `Nessuno.` |

**Die Anrede folgt Zeile für Zeile dem deutschen Bestand.** Das Deutsche wechselt innerhalb
dieses Katalogs zwischen der unpersönlichen Infinitivanweisung ("Den Wert unter ... erhöhen.")
und der Sie-Form ("Grenzen Sie die Suche ein."). Das Italienische kann beides ebenso, also
steht dort, wo Deutsch den Infinitiv führt, der italienische Infinitiv (`Aumentare il valore in
"File più grande da leggere".`) und dort, wo Deutsch siezt, die höfliche Form auf `-i`
(`Restringa la ricerca per vederli.`). Der Vorteil ist nachprüfbar: der Wechsel ist keine
Nachlässigkeit dieser Datei, sondern eine Eigenschaft der Quelle, und wer ihn eines Tages
vereinheitlichen will, findet die Stellen im deutschen Katalog und nicht hier.

Die Schaltflächen und kurzen Beschriftungen tragen die italienische Oberflächenkonvention, also
die kurze Befehlsform: `Cerca`, `Salva le regole`, `Aggiungi esclusione`, `Mostra i percorsi di
esempio`. Das ist dieselbe Trennung, die das Deutsche zwischen "Regeln speichern" und
"Versuchen Sie es noch einmal" macht.

## Typografie

Jede Regel unten ist maschinell geprüft, das Ergebnis steht im Abschnitt "Maschinelle
Prüfungen".

- **Der Apostroph ist ausnahmslos der gerade ASCII-Apostroph** (U+0027), nie der
  typographische (U+2019). Das ist im Italienischen die wichtigste Regel dieses Katalogs und
  nicht eine Formalie wie im Spanischen: die Elision ist hier alltäglich (`l'indice`,
  `un'analisi`, `c'è`, `dell'applicazione`, `d'ambiente`, `Quest'anno`), und genau an diesen
  Stellen schleppt eine maschinelle Übersetzung am zuverlässigsten U+2019 ein. Der Katalog
  enthält 0 davon, gezählt über beide Dateien und über dieses Dokument.
- **Echte Akzente sind Pflicht und werden nie durch einen nachgestellten Apostroph ersetzt.**
  Also `è`, `può`, `più`, `già`, `perché`, `così`, `né`, `metà`, `sé`, `perciò`, und niemals
  `e'` oder `piu'`. Die Ersatzschreibweise ist in italienischen Texten verbreitet, wo eine
  Tastatur fehlt; in einer ausgelieferten Oberfläche ist sie ein sichtbarer Mangel. Ein eigenes
  Abnahmekriterium sucht die Zeichenfolge `e'` und findet sie nicht.
- **Der Akut auf `perché` und der Gravis auf `è`** sind zwei verschiedene Zeichen und keine
  Geschmacksfrage: `perchè` ist falsch geschrieben, `perché` richtig. Betroffen sind alle
  Sätze mit `perché`, `né`, `poiché`.
- **Kein geschütztes Leerzeichen**, weder U+00A0 noch das schmale U+202F. Sie sind unsichtbar,
  und ein Katalog voll unsichtbarer Zeichen ist ein Katalog, dessen Diff niemand liest.
- **Kein Gedankenstrich**, weder U+2014 noch U+2013. Das ist die Regel des Repositoriums und
  wird vom Prosa-Scanner über jede Katalogdatei gehalten.
- **Anführung des Suchbegriffs mit `«` und `»`**, ohne Leerzeichen innen, also `«%s»`. Für
  Bezeichner der Oberfläche und für Befehle bleibt es beim geraden ASCII-Anführungszeichen,
  genau wie im deutschen, französischen und spanischen Bestand:
  `"occ findling:index --restart"`, `"Cartelle escluse"`.
- **Keine umgekehrten Satzzeichen.** Anders als das Spanische öffnet das Italienische Fragen
  ohne `¿`. Die beiden Rückfragen vor dem Entfernen indexierter Inhalte beginnen deshalb
  schlicht mit `Rimuovere i contenuti indicizzati?`.
- **Die Platzhalter sind die des Schlüssels**, in Art und Zahl. `%1$s in %2$s` bleibt
  `%1$s in %2$s` und wird niemals `%s in %s`.
- **Ein literales Prozentzeichen wird `%%` geschrieben.** Der Grund ist gemessen und nicht
  befürchtet: Nextcloud reicht jeden Katalogwert durch `vsprintf`, ein nacktes `%` wirft dort
  einen `ValueError`, und die Seite bleibt weiß. **In diesem Katalog steht kein einziges
  Prozentzeichen dieser Art**, auch kein verdoppeltes: wo der deutsche Satz "100 Prozent" sagt,
  sagt der italienische `il cento per cento`. Umformulieren war hier billiger als retten, und
  der Satz liest sich besser als mit `%%`. Die Schreibregel steht trotzdem hier, denn die
  nächste Zeile, die eine Zahl mit Prozentzeichen braucht, kommt bestimmt.

## Pluralformen

Die italienische Regel lautet

```
nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
```

und steht wörtlich so als `"pluralForm"` in `php/l10n/it.json` und als vierter Parameter von
`OC.L10N.register` in `php/l10n/it.js`. Sie ist aus `docs/l10n-catalogues.md`, Abschnitt 3,
übernommen und nicht nachgetippt; dort steht auch, dass NC 34.0.3 und NC 35.0.0 für Italienisch
dieselbe Zeichenkette führen. Sie ist zeichengleich mit der spanischen Regel, und das ist eine
Eigenschaft der beiden Sprachen und kein Kopierfehler.

**Die fünf Pluralwerte tragen drei Formen, und Form 1 und Form 2 sind wortgleich.** Der Grund
steht gemessen in `docs/l10n-catalogues.md`, Abschnitt 4, und wird hier nicht neu entschieden:
PHP liest die deklarierte Regel gar nicht und erreicht Form 2 nie, der Browser wertet die Regel
aus und wählt bei n gleich 2 den Index 2. Stünden dort verschiedene Wörter, liefe dieselbe
Zeile derselben Seite im Server-HTML anders als nach dem ersten Poll. Die Millionenform auf
Index 1 ist damit ausdrücklich nicht geschrieben.

Ein italienischer Zusatz dazu: `%n giorno` gegen `%n giorni` und `%n ora` gegen `%n ore` sind
regelmäßige Plurale, `e %n altro` gegen `e %n altri` ebenfalls. Der deutsche Bestand schreibt
bei `_and %n more_::_and %n more_` zweimal dasselbe Wort ("und %n weitere"), weil das Deutsche
dort keinen Unterschied macht; das Italienische macht ihn, also stehen hier drei Formen mit
zwei verschiedenen Wortlauten.

In der Tabelle unten stehen die Formen eines Pluralschlüssels durch ` / ` getrennt in einer
Zelle, zuerst der Singular, wie es der französische und der spanische Bestand machen. Die
deutsche Spalte trägt zwei Formen und die italienische drei; dass die zweite und die dritte
italienische Form gleich lauten, ist der Entscheid oben und kein Fehler dieser Tabelle.

## Die Tabelle

Alle drei Spalten sind aus `php/l10n/de.json` und `php/l10n/it.json` erzeugt und nicht
abgetippt; die Reihenfolge ist die der Dateien. Die Spaltennamen sind ASCII, weil sie
Vertragsbezeichner sind und die Projektregel echte Umlaute der deutschen Prosa vorbehält. Der
Schlüssel ist der englische Quellstring: er steht wörtlich so im Template, läuft dort durch
`$l->t()` und ist in jeder Katalogdatei der Schlüssel der Übersetzung.

Kein Wert und kein Schlüssel kann ein Pipe-Zeichen enthalten, dafür sorgt `scan_pipe_character`
aus Plan 20-03. Diese Tabelle kann also nicht an einem Wortlaut zerbrechen.

| Schluessel | DE | IT |
|---|---|---|
| `Findling` | Findling | Findling |
| `File contents` | Dateiinhalte | Contenuto dei file |
| `Search coverage` | Deckungsgrad der Suche | Copertura della ricerca |
| `%1$s of %2$s indexable files are searchable` | %1$s von %2$s indexierbaren Dateien sind durchsuchbar | %1$s file indicizzabili su %2$s si possono trovare con la ricerca |
| `The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.` | Der Anteil ist im Moment nicht berechenbar, weil das Backend nicht antwortet. %s Dateien dieser Instanz sind indexierbar. | In questo momento la quota non si può calcolare, perché il servizio non risponde. %s file di questa istanza sono indicizzabili. |
| `Deliberately left out: %s` | Bewusst ausgelassen: %s | Esclusi di proposito: %s |
| `Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.` | Diese Dateien sind zu groß, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen. Sie stehen nicht im Nenner darüber, damit der Deckungsgrad 100 Prozent erreichen kann. | Questi file sono troppo grandi, di un tipo che Findling non legge, oppure esclusi da una regola. Non rientrano nel denominatore qui sopra, in modo che la copertura possa raggiungere il cento per cento. |
| `Provisional figure, %1$s of %2$s storages have been counted through.` | Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt. | Cifra provvisoria, sono stati contati %1$s spazi di archiviazione su %2$s. |
| `Findable by meaning` | Auffindbar nach Bedeutung | Si può trovare per significato |
| `%1$s of %2$s indexable files can also be found by meaning` | %1$s von %2$s indexierbaren Dateien sind auch nach Bedeutung auffindbar | %1$s file indicizzabili su %2$s si possono trovare anche per significato |
| `The semantic share cannot be worked out right now. The backend does not answer, or it does not report this figure yet.` | Der semantische Anteil ist im Moment nicht berechenbar. Das Backend antwortet nicht, oder es meldet diese Zahl noch nicht. | In questo momento la quota semantica non si può calcolare. Il servizio non risponde, oppure non comunica ancora questa cifra. |
| `The model is in memory, the semantic search is answering.` | Das Modell liegt im Speicher, die semantische Suche antwortet. | Il modello è in memoria, la ricerca semantica risponde. |
| `The model is read when it is first needed. That is the normal state.` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | Il modello viene caricato la prima volta che serve. Questo è lo stato normale. |
| `The semantic half is switched off in the settings of the container.` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | La metà semantica è disattivata nelle impostazioni del contenitore. |
| `There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.` | In diesem Abbild liegt kein Modell. Die Suche liefert weiterhin Volltexttreffer, die semantische Hälfte bleibt leer. | In questa immagine non c'è nessun modello. La ricerca continua a rispondere con i risultati del testo completo, la metà semantica resta vuota. |
| `Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.` | Das Laden des Modells ist einmal gescheitert und wird in Kürze erneut versucht. Bis dahin liefert die Suche Volltexttreffer. | Il caricamento del modello non è riuscito una volta e viene ritentato a breve. Fino ad allora la ricerca risponde con i risultati del testo completo. |
| `The model was released to save memory. The next search answers with full text hits and loads it again in the background.` | Das Modell wurde zum Sparen freigegeben. Die nächste Suche antwortet mit Volltexttreffern und lädt es im Hintergrund nach. | Il modello è stato rilasciato per risparmiare memoria. La prossima ricerca risponde con i risultati del testo completo e lo ricarica in secondo piano. |
| `This container does not report the state of the model yet.` | Dieser Container meldet den Zustand des Modells noch nicht. | Questo contenitore non comunica ancora lo stato del modello. |
| `The full text search covers every indexed document. The semantic search covers the beginning of each document, and this second figure fills up after the first index has finished.` | Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem Erstindex nach. | La ricerca a testo completo copre tutti i documenti indicizzati. La ricerca semantica copre l'inizio di ogni documento, e questa seconda cifra si completa dopo la fine del primo indice. |
| `Up to date, last checked %s` | Aktuell, letzte Prüfung %s | Aggiornato, ultimo controllo %s |
| `Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.` | Die Indexierung kommt seit %s nicht voran. In dieser Zeit hat weder ein Hintergrundauftrag noch das Backend etwas fertiggestellt. | L'indicizzazione non avanza da %s. In questo tempo né un processo in background né il servizio hanno portato a termine qualcosa. |
| `No background job of this app has run yet. Background jobs may not be running.` | Noch kein Hintergrundauftrag dieser App ist gelaufen. Möglicherweise laufen die Hintergrundaufträge nicht. | Nessun processo in background di questa applicazione è ancora stato eseguito. È possibile che i processi in background non siano in funzione. |
| `Indexing is running.` | Die Indexierung läuft. | L'indicizzazione è in corso. |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | Die Zahlen konnten nicht aktualisiert werden. Die Werte unten sind die letzten, die diese Seite bekommen hat. | Non è stato possibile aggiornare i numeri. Le cifre qui sotto sono le ultime che questa pagina ha ricevuto. |
| `_%n minute_::_%n minutes_` | %n Minute / %n Minuten | %n minuto / %n minuti / %n minuti |
| `_%n hour_::_%n hours_` | %n Stunde / %n Stunden | %n ora / %n ore / %n ore |
| `_%n day_::_%n days_` | %n Tag / %n Tage | %n giorno / %n giorni / %n giorni |
| `Waiting in the queue` | Wartet in der Warteschlange | In attesa nella coda |
| `Being processed` | Wird gerade verarbeitet | In elaborazione |
| `Indexed` | Indexiert | Indicizzato |
| `Skipped` | Übersprungen | Saltato |
| `Failed` | Fehlgeschlagen | Non riuscito |
| `Excluded` | Ausgeschlossen | Escluso |
| `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst. | I file esclusi non rientrano nella cifra di copertura. Sono i file che Findling non tocca, perché così è stato stabilito. |
| `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter. | Resta poco spazio su disco. L'indicizzazione è in pausa, perché l'indice resti intatto. La ricerca continua a funzionare. |
| `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer. | L'indice è stato costruito con un'analisi del testo più vecchia. Ricostruirlo con "occ findling:index --restart", altrimenti continueranno a mancare dei risultati. |
| `Findling is rebuilding its index so that the newly switched on languages can be searched. %1$s of %2$s documents have been carried over. Search keeps answering while this runs, and there is nothing to start or to restart.` | Findling baut seinen Index neu auf, damit die neu eingeschalteten Sprachen durchsucht werden können. %1$s von %2$s Dokumenten sind übertragen. Die Suche antwortet währenddessen weiter, und es gibt nichts zu starten oder neu zu starten. | Findling sta ricostruendo il suo indice, perché si possano cercare le lingue appena attivate. Sono stati trasferiti %1$s documenti su %2$s. Nel frattempo la ricerca continua a rispondere, e non c'è nulla da avviare o da riavviare. |
| `Findling wants to rebuild its index for the newly switched on languages and there is not enough room: %s more are needed next to what the index already uses. Free that much, or set the environment variable FINDLING_REBUILD_FALLBACK=fullreindex to have the backend read the files again instead. Either way the backend only tries again after a restart of the container.` | Findling möchte seinen Index für die neu eingeschalteten Sprachen neu aufbauen, und es ist nicht genug Platz: %s fehlen zusätzlich zu dem, was der Index bereits belegt. Geben Sie so viel frei, oder setzen Sie die Umgebungsvariable FINDLING_REBUILD_FALLBACK=fullreindex, damit das Backend die Dateien stattdessen neu liest. In beiden Fällen versucht es das Backend erst nach einem Neustart des Containers erneut. | Findling vuole ricostruire il suo indice per le lingue appena attivate e non c'è spazio sufficiente: servono %s in più rispetto a quanto l'indice occupa già. Liberi questa quantità, oppure imposti la variabile d'ambiente FINDLING_REBUILD_FALLBACK=fullreindex, perché il servizio rilegga invece i file. In entrambi i casi il servizio riprova solo dopo un riavvio del contenitore. |
| `Languages of the index: %1$s switched on, %2$s with text in the index.` | Sprachen des Index: %1$s eingeschaltet, %2$s mit Text im Index. | Lingue dell'indice: %1$s attivate, %2$s con testo nell'indice. |
| `No numbers yet` | Noch keine Zahlen | Ancora nessuna cifra |
| `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` | Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen. | La prima passata di indicizzazione non è ancora terminata. Findling è partito da solo, non c'è nulla da configurare. |
| `The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.` | Die beiden Hälften von Findling melden unterschiedliche Versionen: diese App ist %1$s, das Backend ist %2$s. Solange sie nicht zusammenpassen, antwortet die Suche ohne Ergebnisse, weil eine falsche Antwort ohne Hinweis schlimmer wäre. Beide Hälften auf dieselbe Version bringen. | Le due metà di Findling comunicano versioni diverse: questa applicazione è %1$s, il servizio è %2$s. Finché non coincidono, la ricerca risponde senza risultati, perché una risposta sbagliata senza avviso sarebbe peggio. Portare entrambe le metà alla stessa versione. |
| `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` | Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist. | Il servizio di Findling non risponde. I numeri qui sotto sono gli ultimi che questa applicazione ha registrato. In Applicazioni controllare che l'applicazione esterna "Findling Backend" sia installata e avviata. |
| `Estimate for the first index` | Schätzung für den Erstindex | Stima per il primo indice |
| `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | %1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index. | %1$s file, di cui %2$s con OCR. Circa %3$s e circa %4$s di indice. |
| `%1$s files, %2$s of them need OCR.` | %1$s Dateien, davon %2$s mit OCR. | %1$s file, di cui %2$s con OCR. |
| `%1$s to %2$s` | %1$s bis %2$s | da %1$s a %2$s |
| `Counting the files, this takes a moment.` | Die Dateien werden gezählt, das dauert einen Moment. | I file vengono contati, ci vuole un momento. |
| `Startup value, being measured.` | Startwert, wird gemessen. | Valore iniziale, in corso di misurazione. |
| `The space needed is measured as soon as the first documents are in the index.` | Der Platzbedarf wird gemessen, sobald die ersten Dokumente im Index sind. | Lo spazio necessario viene misurato non appena i primi documenti sono nell'indice. |
| `The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.` | Der Index braucht voraussichtlich mehr Platz, als auf diesem Datenträger frei ist. Die Indexierung pausiert, bevor der Datenträger voll wird, und die Suche funktioniert weiter. | Si prevede che l'indice abbia bisogno di più spazio di quanto ne sia libero su questo volume. L'indicizzazione si ferma prima che il volume si riempia, e la ricerca continua a funzionare. |
| `Findling does not wait for a confirmation. The first index has already started.` | Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits. | Findling non aspetta nessuna conferma. Il primo indice è già iniziato. |
| `Files that were not indexed` | Nicht indexierte Dateien | File non indicizzati |
| `Files that were not indexed, grouped by reason` | Nicht indexierte Dateien, nach Grund gruppiert | File non indicizzati, raggruppati per motivo |
| `Every file was indexed. Nothing was skipped and nothing failed.` | Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen. | Tutti i file sono stati indicizzati. Non è stato saltato nulla e non è fallito nulla. |
| `Reason` | Grund | Motivo |
| `Files` | Dateien | File |
| `State` | Zustand | Stato |
| `Show example paths` | Beispielpfade anzeigen | Mostra i percorsi di esempio |
| `Hide example paths` | Beispielpfade verbergen | Nascondi i percorsi di esempio |
| `_and %n more_::_and %n more_` | und %n weitere / und %n weitere | e %n altro / e %n altri / e %n altri |
| `File no longer exists (ID %s)` | Datei existiert nicht mehr (ID %s) | Il file non esiste più (ID %s) |
| `%s (in the trash bin)` | %s (im Papierkorb) | %s (nel cestino) |
| `Indexed, text truncated` | Indexiert, Text gekürzt | Indicizzato, testo troncato |
| `Unknown reason (%s)` | Unbekannter Grund (%s) | Motivo sconosciuto (%s) |
| `This app does not know this code. It may come from a newer version of the backend.` | Diese App kennt diesen Code nicht. Er kann von einer neueren Fassung des Backends kommen. | Questa applicazione non conosce questo codice. Può provenire da una versione più recente del servizio. |
| `Text truncated` | Text gekürzt | Testo troncato |
| `The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.` | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. | L'inizio del documento si può cercare, il resto no. I documenti molto lunghi vengono tagliati di proposito. |
| `Too large` | Zu groß | Troppo grande |
| `Raise the value under "Largest file to read".` | Den Wert unter "Größte zu lesende Datei" erhöhen. | Aumentare il valore in "File più grande da leggere". |
| `File type not supported` | Dateityp nicht unterstützt | Tipo di file non supportato |
| `None. Findling reads PDF, Office, OpenDocument, text and images.` | Keine. Findling liest PDF, Office, OpenDocument, Text und Bilder. | Nessuna. Findling legge PDF, Office, OpenDocument, testo e immagini. |
| `Password protected` | Passwortgeschützt | Protetto da password |
| `None. Without the password the content cannot be read.` | Keine. Ohne Passwort ist der Inhalt nicht lesbar. | Nessuna. Senza la password il contenuto non si può leggere. |
| `No text in the document` | Kein Text im Dokument | Nessun testo nel documento |
| `None. The document carries neither a text layer nor recognisable writing.` | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. | Nessuna. Il documento non contiene né uno strato di testo né scrittura riconoscibile. |
| `No text content` | Kein Textinhalt | Nessun contenuto di testo |
| `None. The file is readable but carries no text.` | Keine. Die Datei ist lesbar, enthält aber keinen Text. | Nessuna. Il file si può leggere, ma non contiene testo. |
| `Spreadsheet too large` | Tabelle zu groß | Foglio di calcolo troppo grande |
| `None. Very large spreadsheets are skipped so the container does not fall over.` | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. | Nessuna. I fogli di calcolo molto grandi vengono saltati, perché il contenitore non vada in crisi. |
| `File no longer present` | Datei nicht mehr vorhanden | File non più presente |
| `None. The file was already deleted or moved when it was read.` | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. | Nessuna. Al momento della lettura il file era già stato eliminato o spostato. |
| `Image without recognisable writing` | Bild ohne erkennbare Schrift | Immagine senza scrittura riconoscibile |
| `None.` | Keine. | Nessuna. |
| `Excluded by a rule` | Durch Regel ausgeschlossen | Escluso da una regola |
| `Remove the matching entry under "Excluded folders".` | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. | Rimuovere la voce corrispondente in "Cartelle escluse". |
| `Not readable for the users asked` | Für die gefragten Nutzer nicht lesbar | Non leggibile per gli utenti interpellati |
| `The file is still there. Check the advanced permissions of the Team Folder: Findling reads a file only as a user who may open it and asks the first 20 of its users in alphabetical order.` | Die Datei ist noch vorhanden. Die erweiterten Berechtigungen des Team Folders prüfen: Findling liest eine Datei nur als Nutzer, der sie öffnen darf, und fragt die ersten 20 ihrer Nutzer in alphabetischer Reihenfolge. | Il file esiste ancora. Controllare le autorizzazioni avanzate del Team Folder: Findling legge un file solo per conto di un utente che può aprirlo e interpella i primi 20 dei suoi utenti in ordine alfabetico. |
| `File is empty` | Datei ist leer | Il file è vuoto |
| `None. The file has 0 bytes.` | Keine. Die Datei hat 0 Byte. | Nessuna. Il file ha 0 byte. |
| `File damaged` | Datei beschädigt | File danneggiato |
| `Check the file outside of Nextcloud and upload it again.` | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. | Controllare il file fuori da Nextcloud e caricarlo di nuovo. |
| `Document structure faulty` | Dokumentstruktur fehlerhaft | Struttura del documento difettosa |
| `Open the document in the program it came from and save it again.` | Das Dokument im Ursprungsprogramm öffnen und neu speichern. | Aprire il documento nel programma da cui proviene e salvarlo di nuovo. |
| `Character set not recognised` | Zeichensatz nicht erkannt | Set di caratteri non riconosciuto |
| `Save the file as UTF-8 and upload it again.` | Die Datei als UTF-8 speichern und neu hochladen. | Salvare il file come UTF-8 e caricarlo di nuovo. |
| `Timed out while reading` | Zeitüberschreitung beim Lesen | Tempo scaduto durante la lettura |
| `The next run tries again.` | Wird beim nächsten Lauf erneut versucht. | La prossima passata riprova. |
| `Not enough memory while reading` | Zu wenig Speicher beim Lesen | Memoria insufficiente durante la lettura |
| `The next run tries again. If it happens again, lower the size cap.` | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken. | La prossima passata riprova. Se succede di nuovo, abbassare il limite di dimensione. |
| `File was not retrievable` | Datei war nicht abrufbar | Non è stato possibile recuperare il file |
| `Stuck repeatedly` | Mehrfach hängen geblieben | Bloccato più volte |
| `Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.` | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. | Findling non riprova più con questo file. Con la verifica controllare se si apre fuori da Nextcloud. |
| `Text recognition failed` | Texterkennung fehlgeschlagen | Riconoscimento del testo non riuscito |
| `Text recognition not available` | Texterkennung nicht verfügbar | Riconoscimento del testo non disponibile |
| `The backend could not start Tesseract. Check the log of the External App.` | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. | Il servizio non è riuscito ad avviare Tesseract. Controllare il registro dell'applicazione esterna. |
| `Look up one file` | Einzelne Datei prüfen | Verificare un singolo file |
| `Path or file ID` | Pfad oder Datei-ID | Percorso o ID del file |
| `A path as Nextcloud stores it, or the numeric ID from the list above.` | Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben. | Un percorso così come lo conserva Nextcloud, oppure il numero dell'elenco qui sopra. |
| `Look up file` | Datei prüfen | Verifica il file |
| `Looking up a single file needs JavaScript. Everything above stays complete without it.` | Die Einzelprüfung braucht JavaScript. Alles darüber bleibt auch ohne vollständig lesbar. | La verifica di un singolo file richiede JavaScript. Tutto quello che sta sopra resta leggibile per intero anche senza. |
| `No file at this path, and no file with this ID.` | Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID. | Nessun file in questo percorso, e nessun file con questo ID. |
| `Not seen yet` | Noch nicht gesehen | Non ancora visto |
| `State unknown right now` | Zustand im Moment unbekannt | Stato sconosciuto in questo momento |
| `File ID: %s` | Datei-ID: %s | ID del file: %s |
| `Last checked %s` | Zuletzt geprüft: %s | Ultimo controllo: %s |
| `The lookup did not work. Nothing about this file has changed.` | Die Prüfung hat nicht funktioniert. An dieser Datei hat sich nichts geändert. | La verifica non ha funzionato. Per questo file non è cambiato nulla. |
| `The state of this file is unknown right now because the backend does not answer.` | Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet. | In questo momento lo stato di questo file è sconosciuto, perché il servizio non risponde. |
| `This file has not reached the queue. The next comparison run picks it up.` | Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab. | Questo file non è ancora arrivato nella coda. La prossima passata di confronto lo prende in carico. |
| `It was indexed before and is recorded again on the next comparison run.` | Sie war vorher indexiert und wird beim nächsten Abgleichlauf neu erfasst. | Era indicizzato prima e viene registrato di nuovo alla prossima passata di confronto. |
| `This file was indexed and has since been deleted. It is out of the index with it.` | Diese Datei war indexiert und ist inzwischen gelöscht. Damit ist sie auch aus dem Index heraus. | Questo file era indicizzato e nel frattempo è stato eliminato. Con questo è uscito anche dall'indice. |
| `In the trash bin` | Im Papierkorb | Nel cestino |
| `Restore the file. The next comparison run picks it up.` | Die Datei wiederherstellen. Der nächste Abgleichlauf holt sie ab. | Ripristinare il file. La prossima passata di confronto lo prende in carico. |
| `Storage is not indexed` | Speicherort wird nicht indexiert | Questo spazio di archiviazione non viene indicizzato |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | Findling liest die Heimatverzeichnisse der Nutzer. Team Folders und externer Speicher sind eigene Einstellungen. | Findling legge le cartelle personali degli utenti. Team Folders e l'archiviazione esterna sono impostazioni a parte. |
| `This is a folder` | Das ist ein Ordner | Questa è una cartella |
| `Enter the path of a file. A folder has no state of its own.` | Den Pfad einer Datei eingeben. Ein Ordner hat keinen eigenen Zustand. | Inserire il percorso di un file. Una cartella non ha uno stato proprio. |
| `Attempts so far: %s` | Bisherige Versuche: %s | Tentativi finora: %s |
| `The next background run picks this file up (%s).` | Der nächste Hintergrundlauf holt diese Datei ab (%s). | La prossima passata in background prende in carico questo file (%s). |
| `The content of this file is searchable.` | Der Inhalt dieser Datei ist durchsuchbar. | Il contenuto di questo file si può cercare. |
| `_A worker holds this file. The claim runs out in %n second if nothing acknowledges it._::_A worker holds this file. The claim runs out in %n seconds if nothing acknowledges it._` | Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunde aus, wenn ihn niemand quittiert. / Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunden aus, wenn ihn niemand quittiert. | Un processo di elaborazione trattiene questo file. La riserva scade tra %n secondo, se nessuno la conferma. / Un processo di elaborazione trattiene questo file. La riserva scade tra %n secondi, se nessuno la conferma. / Un processo di elaborazione trattiene questo file. La riserva scade tra %n secondi, se nessuno la conferma. |
| `Rules and limits` | Regeln und Grenzen | Regole e limiti |
| `Excluded folders` | Ausgeschlossene Ordner | Cartelle escluse |
| `Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups` | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, keine Platzhalter und keine Muster. Beispiel: Backups | Confronto per prefisso sul percorso, così come lo mostrano gli elenchi di questa pagina, senza caratteri jolly e senza modelli. Esempio: Backups |
| `Add exclusion` | Ausschluss hinzufügen | Aggiungi esclusione |
| `Remove exclusion %s` | Ausschluss %s entfernen | Rimuovi l'esclusione %s |
| `No folder is excluded.` | Kein Ordner ist ausgeschlossen. | Nessuna cartella è esclusa. |
| `Largest file to read` | Größte zu lesende Datei | File più grande da leggere |
| `Files above this size are recorded as skipped (too large) and never read.` | Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen. | I file sopra questa dimensione vengono annotati come saltati (troppo grandi) e non vengono mai letti. |
| `The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container.` | Das Backend dieser Instanz liest höchstens %s MB. Für mehr FINDLING_MAX_FILE_BYTES in den App-Einstellungen von AppAPI anheben, was den Container neu startet. | Il servizio di questa istanza legge al massimo %s MB. Per leggerne di più, aumentare FINDLING_MAX_FILE_BYTES nelle impostazioni dell'applicazione di AppAPI, cosa che riavvia il contenitore. |
| `Index Team Folders` | Team Folders indexieren | Indicizza Team Folders |
| `Index external storage` | Externen Speicher indexieren | Indicizza l'archiviazione esterna |
| `External storage can be slow or charged per request. Indexing reads every file once.` | Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal. | L'archiviazione esterna può essere lenta o a pagamento per ogni accesso. L'indicizzazione legge ogni file una volta sola. |
| `The next run applies the new rules. Nothing restarts.` | Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu. | La prossima passata applica le nuove regole. Non si riavvia nulla. |
| `Save rules` | Regeln speichern | Salva le regole |
| `Rules saved. The next run applies them.` | Regeln gespeichert. Der nächste Lauf übernimmt sie. | Regole salvate. La prossima passata le applica. |
| `The rules were not saved. Nothing changed.` | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | Le regole non sono state salvate. Non è cambiato nulla. |
| `Enter a size between %1$s and %2$s MB.` | Eine Größe zwischen %1$s und %2$s MB eingeben. | Inserire una dimensione tra %1$s e %2$s MB. |
| `Enter a folder path.` | Einen Ordnerpfad eingeben. | Inserire il percorso di una cartella. |
| `This path is already excluded.` | Dieser Pfad ist bereits ausgeschlossen. | Questo percorso è già escluso. |
| `Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.` | Einen Eintrag zu entfernen wirkt innerhalb von %1$s Stunden, wenn der nächste Abgleichlauf diese Dateien wieder aufnimmt. Mit "%2$s" sofort übernehmen. | Rimuovere una voce ha effetto entro %1$s ore, quando la prossima passata di confronto riprende quei file. Con "%2$s" applicarlo subito. |
| `Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %1$s entfernt außerdem %2$s bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Rimuovere i contenuti indicizzati? Escludere %1$s toglie dall'indice anche %2$s documenti già indicizzati sotto quel percorso. I file in sé restano intatti sul disco. |
| `Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Rimuovere i contenuti indicizzati? Escludere %s toglie dall'indice anche i documenti già indicizzati sotto quel percorso. I file in sé restano intatti sul disco. |
| `at least %s` | mindestens %s | almeno %s |
| `Exclude and remove` | Ausschließen und entfernen | Escludi e rimuovi |
| `Keep files indexed` | Dateien indexiert lassen | Mantieni i file indicizzati |
| `Search` | Suchen | Cerca |
| `Search term` | Suchbegriff | Termine di ricerca |
| `invoice 2026` | Rechnung 2026 | fattura 2026 |
| `Search file names only` | Nur Dateinamen durchsuchen | Cerca solo nei nomi dei file |
| `Results for "%s"` | Treffer für „%s“ | Risultati per «%s» |
| `Search results` | Suchergebnisse | Risultati della ricerca |
| `%1$s in %2$s` | %1$s in %2$s | %1$s in %2$s |
| `last opened` | zuletzt geöffnet | aperto l'ultima volta |
| `Show all results` | Alle Treffer anzeigen | Mostra tutti i risultati |
| `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | Apre la pagina dei risultati di Findling |
| `Previous page` | Vorherige Seite | Pagina precedente |
| `Next page` | Nächste Seite | Pagina successiva |
| `Page %s` | Seite %s | Pagina %s |
| `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | Ci sono altri risultati. Restringa la ricerca per vederli. |
| `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | Cerchi nel contenuto dei suoi file |
| `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | Scriva una parola presa da un documento. Findling cerca il testo dentro i suoi file, compresi i PDF scansionati. |
| `No file contains "%s"` | Keine Datei enthält „%s“ | Nessun file contiene «%s» |
| `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | Provi con un'altra parola, con una parte di una parola composta, oppure controlli l'ortografia. |
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen. | Altri file contengono questa parola, ma nessuno di quelli che può aprire. |
| `The search is not answering right now` | Die Suche antwortet gerade nicht | In questo momento la ricerca non risponde |
| `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | Findling non è riuscito a contattare il suo servizio. I suoi file non sono cambiati. Riprovi tra un momento e avvisi l'amministrazione, se la situazione resta questa. |
| `Try again` | Erneut versuchen | Riprova |
| `Findling is not ready to search` | Findling ist nicht suchbereit | Findling non è pronto per la ricerca |
| `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | Le due metà di Findling comunicano versioni diverse. L'amministrazione deve aggiornarle entrambe insieme. |
| `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | L'indice è ancora in costruzione, perciò possono mancare dei risultati. |
| `File type` | Dateityp | Tipo di file |
| `PDF` | PDF | PDF |
| `Documents` | Dokumente | Documenti |
| `Spreadsheets` | Tabellen | Fogli di calcolo |
| `Presentations` | Präsentationen | Presentazioni |
| `Images` | Bilder | Immagini |
| `Text` | Text | Testo |
| `Time range` | Zeitraum | Periodo |
| `Today` | Heute | Oggi |
| `Last 7 days` | Letzte 7 Tage | Ultimi 7 giorni |
| `Last 30 days` | Letzte 30 Tage | Ultimi 30 giorni |
| `This year` | Dieses Jahr | Quest'anno |
| `Remove filter %s` | Filter %s entfernen | Rimuovi il filtro %s |
| `Reset all filters` | Alle Filter zurücksetzen | Reimposta tutti i filtri |
| `Sort by` | Sortieren nach | Ordina per |
| `Relevance` | Relevanz | Rilevanza |
| `Last modified` | Zuletzt geändert | Ultima modifica |
| `Oldest first` | Älteste zuerst | Prima i più vecchi |
| `Modified on %s` | Geändert am %s | Modificato il %s |
| `%1$s in %2$s, modified on %3$s` | %1$s in %2$s, geändert am %3$s | %1$s in %2$s, modificato il %3$s |
| `No results with the active filters` | Keine Treffer mit den aktiven Filtern | Nessun risultato con i filtri attivi |
| `Remove a filter or widen the time range.` | Entfernen Sie einen Filter oder erweitern Sie den Zeitraum. | Rimuova un filtro o allarghi il periodo. |
| `Reset filters` | Filter zurücksetzen | Reimposta i filtri |

## Ausnahmen für das Vollständigkeitsgate G2

Gate G2, heute `test_every_catalogue_value_carries_a_wording_of_its_language`, fordert, dass
kein Wert leer und keiner mit dem englischen Quellstring identisch ist. Genau drei Schlüssel
sind es im Italienischen absichtlich. Das ist eine benannte Liste und ausdrücklich **keine**
Toleranzschwelle: eine Schwelle würde einen vergessenen Wortlaut genauso mitdecken wie einen
gewollten, eine Liste deckt nur, was in ihr steht. Die Liste darf wachsen, die Zahl drei ist
keine Grenze, sondern das Ergebnis des Zählens, und jeder Eintrag trägt seinen Grund bei sich.

- `Findling`: Eigenname der App, in jeder Sprache dasselbe Wort. Er steht als Schlüssel in
  `de.json` und muss deshalb in `it.json` stehen, hat aber keinen eigenen Wortlaut.
- `%1$s in %2$s`: zwei Platzhalter und die Präposition dazwischen, die das Italienische genau
  so schreibt wie das Englische. Es ist derselbe Schlüssel, den auch die deutsche Liste führt,
  und aus demselben Grund. Der verwandte Schlüssel `%1$s in %2$s, modified on %3$s` steht
  **nicht** hier, weil sein zweiter Teil italienisch ist (`modificato il %3$s`).
- `PDF`: Eigenname eines Dateiformats, in jeder Sprache dieselbe Abkürzung.

Die Liste ist nicht geraten worden. Drei Läufe, in dieser Reihenfolge:

| Lauf | Ergebnis |
|---|---|
| kein Eintrag für `it` in der Tabelle | `AssertionError: languages without a list of exceptions: ['it']` |
| leeres Mapping `"it": {}` | sechs Funde, drei Schlüssel über zwei Dateien, erster davon `it.json: 'Findling' is still the English source string` |
| drei begründete Einträge | grün, 52 passed |

Beurteilt wurde je Schlüssel und nicht gezählt. Die Liste ist kürzer als die französische (fünf
Einträge), weil `Page %s`, `Documents` und `Images` im Italienischen eigene Wortlaute haben:
`Pagina %s`, `Documenti`, `Immagini`. Sie ist um einen Eintrag länger als die spanische, weil
das Spanische `%1$s en %2$s` schreibt und damit einen eigenen Wortlaut hat, das Italienische
aber dieselbe Präposition wie das Englische führt.

Dieselben drei Schlüssel mit denselben Gründen stehen in
`VALUES_THAT_MAY_EQUAL_THEIR_KEY["it"]` in `backend/tests/test_admin_ui_contract.py`. Doku und
Gate dürfen hier nicht auseinanderlaufen: die Doku sagt, was erlaubt ist, das Gate hält es.

## Maschinelle Prüfungen

Gefahren am 25.09.2026 über die beiden erzeugten Dateien, nicht per Augenmaß:

| Prüfung | Ergebnis |
|---|---|
| Schlüsselmenge `it.json` gleich `de.json`, in derselben Reihenfolge | ja, 202 von 202, fehlend 0 |
| Schlüsselmenge `it.js` gleich `it.json` (Objektvergleich über den `register`-Rumpf) | ja, identisch |
| Jeder Schlüssel aus `it.json` kommt in dieser Datei vor | fehlend: 0 |
| Platzhalter-Parität Schlüssel gegen Wert, über alle 40 Schlüssel mit Direktiven, Pluralschlüssel an `_::_` geteilt | 0 Abweichungen |
| Pluralschlüssel mit genau drei Formen | 5 von 5 |
| Form 1 und Form 2 wortgleich | 5 von 5 |
| Pluralschlüsselmenge gleich der deutschen | ja |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, mit `nplurals=3` | ja, in beiden Dateien |
| U+2019 (typographischer Apostroph) | 0 |
| U+2014 und U+2013 (Gedankenstriche) | 0 |
| U+00A0 und U+202F (geschützte Leerzeichen) | 0 |
| Zeichenfolge `e'` als Ersatz für `è` | 0 |
| Nackte Prozentzeichen, also `%` ohne erkannte Direktive | 0 in Schlüsseln und in allen Formen |
| Pipe-Zeichen (der senkrechte Strich, mit dem Nextcloud Pluralformen verbindet) | 0 in Schlüsseln und in allen Formen |
| Wert identisch mit dem englischen Quellstring | 3, alle drei oben benannt |
| LF, UTF-8 ohne BOM, abschließender Zeilenumbruch | beide Dateien, byteweise geprüft |
| Giessform gegen den unveränderten Bestand, vor der ersten neuen Zeile | 8 von 8 byteweise gleich (`de`, `de_DE`, `fr`, `es`, je `.json` und `.js`) |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped |

**Ein Befund gehört zu dieser Tabelle, weil er nicht am Katalog liegt.** Das Vokabular-Gate in
`backend/tests/test_public_artifacts.py` hält eine Wortstamm-Sperre über alles unter `docs/`
und fällt über dem italienischen Wort für den Speicherort (`archiviazione`), genau wie es in
Plan 20-04 über dem spanischen Wort für Datei gefallen ist. Die Lösung ist dieselbe und die im
Gate vorgesehene: ein benannter Eintrag in `AUSNAHMEN` mit eigenem Grund, keine aufgeweichte
Regex. Umformulieren scheidet aus, weil die IT-Spalte die ausgelieferten Wortlaute von
`it.json` führt und eine Doku, die anders schreibt als die Datei, aufhört deren Quelle zu sein.

Was keine Maschine prüfen kann, ist die Sprache. Das ist der Gegenstand des Abschnitts
darunter.

## Abnahme

**Erzeugt am 25.09.2026, Plan 20-05.** Die italienischen Wortlaute dieser Tabelle sind
maschinell entstanden und anschließend gegen die Gates gefahren, die der Abschnitt "Maschinelle
Prüfungen" aufzählt: Schlüsselmenge, Gleichstand der beiden Dateien, Platzhalterparität,
Formenzahl, Pluralregel, Prozentdisziplin, Pipe-Zeichen, Prosa-Scan auf Gedankenstriche und
Symbolzeichen, Apostroph- und Akzentprüfung, Vollständigkeit mit benannter Ausnahmeliste.

**Dieser Katalog ist von keinem Muttersprachler gelesen worden.** Das ist keine offene
Aufgabe, die jemand vergessen hat, sondern der gesperrte Entscheid E-17-5, Option a: die vier
neuen Sprachen entstehen maschinell und werden über das offene Community-Review korrigiert, das
jede App im Nextcloud App Store hat. Wer einen Fehler findet, meldet ihn als Issue im
Repositorium `street1983nk/nextcloud-search` oder schickt eine Änderung an dieser Tabelle; die
nächste Ausgabe nimmt ihn mit. Ein Muttersprachler-Gate ist ausdrücklich **nicht** gewählt
worden und wird hier auch nicht nachträglich eingeführt.

**Die Auslieferung wartet darauf nicht.** Das ist die Abwägung hinter dem Entscheid: ein
italienischer Katalog mit einzelnen unrunden Sätzen ist für einen italienischen Nutzer besser
als eine englische Oberfläche, und die Fehler, die eine Maschine macht, sind sichtbar und
korrigierbar. Der Unterschied zum französischen Katalog ist an dieser Stelle ausdrücklich
festgehalten: `docs/l10n-french.md` trägt eine Abnahme durch den Owner, einen französischen
Muttersprachler, datiert auf den 11.09., 19.09. und 24.09.2026. Diese Datei trägt eine Stufe
weniger, und sie sagt es, damit niemand die beiden für gleich abgenommen hält.

**Zwei Stellen, an denen ein Muttersprachler zuerst hinsehen sollte.** Sie sind hier benannt,
damit das Review nicht bei null anfängt. Erstens die Wahl von `passata` für den Lauf: sie ist
aus der romanischen Linie übernommen, und ein Muttersprachler könnte `esecuzione` oder `ciclo`
vorziehen. Zweitens der Wechsel zwischen Infinitiv und höflicher Form, der dem deutschen
Bestand folgt und deshalb innerhalb einer Seite wechselt; wer ihn vereinheitlichen will, muss
zuerst den deutschen Katalog vereinheitlichen.

**Stand dieser Datei:** alle 202 Zeilen sind am 25.09.2026 entstanden, keine ist später
hinzugekommen, und keine ist abgenommen. Kommt später ein Schlüssel dazu, gehört er in diese
Tabelle und in einen datierten Nachtrag darunter, aus demselben Grund, aus dem
`docs/l10n-french.md` seine Nachträge führt: eine Datei darf keine ungelesene Zeile
stillschweigend mittragen.
