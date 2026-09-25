# Portugiesische Wortlaute, vollständig

Diese Datei ist die Quelle der portugiesischen Katalogdateien von Findling. Sie trägt die
portugiesischen Wortlaute für **alle** Schlüssel der Adminseite und der Ergebnisseite, in einer
Tabelle, damit ein Leser sie in einem Durchgang prüfen kann und nicht als Diff über mehrere
Dateien. Aus dieser Tabelle sind die Katalogdateien mechanisch entstanden, ohne zweite
Textrunde.

Was für **alle** Sprachdateien dieser Phase gilt, steht nicht hier, sondern einmal in
`docs/l10n-catalogues.md`: warum Nextcloud zehn Dateien und nicht fünf braucht (Abschnitt 1),
welche Regionalvarianten der Kern führt und welche Findling ausliefert (Abschnitt 2), die
wörtlichen Pluralregeln mit ihrer Herkunft (Abschnitt 3), die Messung, aus der die Wahl der
Formen folgt (Abschnitt 4), und die benannte Abweichung bei n gleich 0 (Abschnitt 5). Diese
Datei verweist dorthin, statt den Beweis ein zweites Mal zu führen.

**Diese eine Datei trägt zwei Sprachcodes, und das ist kein Zwillingspaar.** Portugiesisch ist
die einzige Sprache dieses Baums, die zwei Codes braucht: `pt_PT` für das europäische und
`pt_BR` für das brasilianische Portugiesisch. Der Kern von Nextcloud 34 und 35 führt beide
nebeneinander und kein `pt` dazwischen; die Dateiliste steht in Abschnitt 1 von
`docs/l10n-catalogues.md`.

Der naheliegende Vergleich ist `de` und `de_DE`, und er ist der falsche. Die beiden deutschen
Codes tragen **dieselben** Wortlaute, und ein Gate in `backend/tests/test_admin_ui_contract.py`
hält diese Textgleichheit fest. Für Portugiesisch gilt das Gegenteil: `pt_PT` und `pt_BR` sind
zwei Wortlautsätze und nicht einer, der zweimal abgelegt wird. Ein Textgleichheits-Gate für das
portugiesische Paar wird deshalb ausdrücklich **nicht** gebaut; es würde eine der beiden
Varietäten dauerhaft in den falschen Wörtern festhalten.

**Stand dieser Datei: die Spalte PT_PT ist gefüllt, die Spalte PT_BR kommt in Plan 20-08.** Bis
dahin führt die Tabelle unten drei Spalten. Eine leere vierte Spalte wird nicht angelegt: eine
leere Zelle sieht aus wie eine vergessene Übersetzung, und genau das ist sie nicht.

## Die Schlüsselmenge, aus der Datei gezählt

Nicht aus einem Dokument übernommen, sondern am 25.09.2026 mit `json.load` über
`php/l10n/de.json` und `php/l10n/pt_PT.json` gezählt:

| Größe | Wert |
|---|---:|
| Schlüssel in `de.json` | **202** |
| Schlüssel in `pt_PT.json` | **202** |
| davon mit printf-Direktiven (`%s`, `%1$s`, `%n`) | **40** |
| davon mit Direktiven, ohne die Pluralschlüssel | **35** |
| davon mit Pluralformen (Wert ist eine Liste) | **5** |
| Formen je Pluralschlüssel | **3** |
| Zeilen in der Tabelle unten | **202** |

Die vorletzte Zeile trennt diese Sprache vom Niederländischen und stellt sie neben das Spanische
und das Italienische: `docs/l10n-dutch.md` trägt dort eine **2**. Warum drei Formen deklariert
werden, obwohl PHP die dritte nie erreicht, steht in Abschnitt 4 von `docs/l10n-catalogues.md`
und weiter unten im Abschnitt "Pluralformen".

Die Tabelle unten führt **202** Zeilen und nicht 201: wie in den drei anderen Sprachdateien
dieser Phase und anders als in `docs/l10n-french.md` steht auch `Findling` darin, mit sich
selbst als Wortlaut. Er ist zugleich der erste Eintrag der Ausnahmeliste weiter unten.

## Wortwahl

Damit die Prüfung eine Entscheidung je Begriff ist und nicht 202 Einzelfälle. Die fünf
Entscheide, die der Plan verlangt, stehen in den ersten fünf Zeilen; die weiteren betreffen
jeweils Dutzende Zeilen und gehörten deshalb ebenso getroffen.

| Englisch | Portugiesisch (PT_PT) | Warum |
|---|---|---|
| the backend | o serviço | Derselbe Entscheid wie im Französischen (`le service`), Spanischen (`el servicio`), Italienischen (`il servizio`) und Niederländischen (`de dienst`). Der Nutzer sieht einen Dienst, der antwortet oder nicht antwortet. `o backend` wäre sagbar, benennt aber ein Bauteil und keine Zusage. Wo der Eigenname gemeint ist, bleibt er stehen: `a aplicação externa "Findling Backend"` |
| run (Lauf, Abgleichlauf, Hintergrundlauf) | a passagem, a passagem de comparação, a passagem em segundo plano | `passagem` ist ein Durchgang über einen Bestand und trägt dasselbe Bild wie `passage`, `pasada`, `passata` und `doorloop`. `execução` wäre das schwerere Wort für dieselbe Sache, `ronda` verspricht eine Regelmäßigkeit, die der Abgleichlauf nicht hat |
| worker | o processo de tratamento | Nach dem französischen `processus de traitement` und dem spanischen `proceso de tratamiento`. `trabalhador` wäre der Mensch, `worker` der Anglizismus, und beide sagen dem Verwaltungsnutzer weniger als die Umschreibung |
| index (Substantiv) | o índice | Ein gewöhnliches portugiesisches Wort, im Plural `índices`. Es braucht keine Umschreibung |
| index (Verb), indexing | indexar, a indexação | Die Formen, die die portugiesische Nextcloud-Oberfläche selbst führt |
| coverage | a cobertura | Die Zahl, die sagt, welcher Anteil der Dateien durchsuchbar ist. Wie im Spanischen |
| file | o ficheiro, Plural `ficheiros` | **Der wichtigste Varietätenentscheid dieser Datei.** Europäisches Portugiesisch sagt `ficheiro`, brasilianisches `arquivo`. Das Wort kommt in diesem Katalog 56 mal vor, es ist also die Stelle, an der sich die beiden Kataloge am deutlichsten unterscheiden werden |
| user | o utilizador | Europäisches Portugiesisch; brasilianisches Portugiesisch sagt `usuário`. Der Katalog führt das Wort an einer Stelle, und diese eine Stelle ist die zweite Probe der Varietät |
| screen | o ecrã | Europäisches Portugiesisch; brasilianisches Portugiesisch sagt `tela`. **In diesem Katalog kommt das Wort nicht vor**, weil kein Schlüssel von einem Bildschirm spricht. Es steht hier trotzdem, weil es die dritte der vier Proben aus Plan 20-07 ist und weil der nächste Schlüssel, der einen Bildschirm nennt, sonst als `tela` hereinkäme |
| downloading | a transferir | Europäisches Portugiesisch; brasilianisches Portugiesisch sagt `baixando`. **Kommt in diesem Katalog ebenfalls nicht vor**, aus demselben Grund und mit derselben Wirkung für später |
| password | a palavra-passe | Europäisches Portugiesisch; brasilianisches Portugiesisch sagt `senha`. Ein fünftes Varietätenwort, das der Plan nicht aufzählt und das der Katalog wirklich führt |
| trash bin | a reciclagem | Die Wortwahl der portugiesischen Nextcloud-Oberfläche; brasilianisch heißt derselbe Ort `lixeira` |
| log | o registo | Europäisches Portugiesisch; brasilianisches Portugiesisch schreibt `registro`, mit dem zweiten r |
| spreadsheets | as folhas de cálculo | Europäisches Portugiesisch; brasilianisches Portugiesisch sagt `planilhas`. Anders als im Niederländischen ist dieser Dateityp-Filter also übersetzt und steht **nicht** in der Ausnahmeliste |
| full text hits | resultados de texto integral | `texto integral` ist die übliche portugiesische Fügung für die Volltextsuche; `texto completo` wäre verständlich und ist die brasilianische Wahl |
| background job | a tarefa em segundo plano | Die Wortwahl der Oberfläche. Von `processo de tratamento` unterscheidet sie sich deutlich genug, und beide Begriffe stehen nie im selben Satz |
| storage | o armazenamento, o armazenamento externo | Der Vorgang und der Ort tragen dasselbe Wort; durchgezählt werden `armazenamentos` |
| folder | a pasta | Und nicht `diretório`: die Oberfläche, in der diese Sätze stehen, sagt `pasta` |
| searchable, findable | pode ser pesquisado, encontrável pelo significado | Zwei Hälften derselben Aussage. Ein Eigenschaftswort `pesquisável` gibt es, es klingt aber technischer als der Satz, in dem es steht |
| text recognition | o reconhecimento de texto | OCR bleibt als Abkürzung stehen, wo der Quellstring sie führt |
| Team Folders | Team Folders | Eigenname der Nextcloud-Funktion, unübersetzt, mit portugiesischem Artikel davor (`as Team Folders`) |
| remedy (die Abhilfe, oft nur `None.`) | `Nenhuma.` | Weibliche Form, weil das weggelassene Hauptwort die Abhilfe ist (`nenhuma solução`). Dasselbe Muster wie das spanische `Ninguna.` |

**Die vier Proben aus Plan 20-07 an einer Stelle.** Sie sind der Gegenstand, an dem Plan 20-08
zeigen wird, dass die zwei portugiesischen Kataloge wirklich zwei sind und nicht einer mit zwei
Dateinamen:

| Bedeutung | PT_PT (diese Datei) | PT_BR (Plan 20-08) | in diesem Katalog |
|---|---|---|---|
| file | `ficheiro` | `arquivo` | 56 mal |
| user | `utilizador` | `usuário` | 1 mal |
| screen | `ecrã` | `tela` | kommt nicht vor |
| downloading | `a transferir` | `baixando` | kommt nicht vor |

Die beiden letzten Zeilen sind ehrlich gemeint: zwei der vier Proben haben in diesem Katalog
keinen Gegenstand. Die Abnahme unten prüft deshalb positiv auf `ficheiro` und `utilizador` und
negativ auf alle drei brasilianischen Formen, und die Prüfung auf `ecrã` gegen `tela` wird erst
dann eine echte, wenn ein Schlüssel dazukommt, der von einem Bildschirm spricht.

**Die Anrede folgt Zeile für Zeile dem deutschen Bestand.** Das Deutsche wechselt innerhalb
dieses Katalogs zwischen der unpersönlichen Infinitivanweisung ("Den Wert unter ... erhöhen.")
und der Sie-Form ("Grenzen Sie die Suche ein."). Das Portugiesische kann beides ebenso, also
steht dort, wo Deutsch den Infinitiv führt, der portugiesische Infinitiv
(`Reconstruí-lo com "occ findling:index --restart"`) und dort, wo Deutsch siezt, die höfliche
Form der dritten Person (`Aumente o valor em "Maior ficheiro a ler".`,
`Restrinja a pesquisa para os ver.`). Das ist derselbe Entscheid wie im Italienischen und im
Niederländischen: der Wechsel bleibt eine Eigenschaft der Quelle statt eine Nachlässigkeit der
Übersetzung, und wer ihn vereinheitlichen will, findet die Stellen im deutschen Katalog und
nicht hier.

Die Schaltflächen und kurzen Beschriftungen tragen die portugiesische Oberflächenkonvention,
also den Infinitiv statt der Befehlsform: `Guardar regras`, `Adicionar exclusão`,
`Mostrar caminhos de exemplo`, `Tentar de novo`.

## Typografie

Jede Regel unten ist maschinell geprüft, das Ergebnis steht im Abschnitt "Maschinelle
Prüfungen".

- **Kein typographischer Apostroph** (U+2019), nirgends. Das Portugiesische setzt den Apostroph
  im Alltag kaum, dieser Katalog kommt ohne eine einzige Apostrophstelle aus, und die Regel
  steht trotzdem hier, weil eine maschinelle Übersetzung das Zeichen gern aus dem englischen
  Quelltext mitschleppt. Gezählt über beide Dateien und über dieses Dokument: 0 Vorkommen.
- **Echte Akzente sind Pflicht.** `ç`, `ã`, `õ`, `é`, `í`, `ó` stehen so da, wie die Sprache sie
  schreibt, und werden nicht durch ASCII ersetzt. Das ist nicht dieselbe Frage wie die
  Projektregel für Umlaute: die verbietet Umlaute in Bezeichnern und Code, nicht in den
  ausgelieferten Wortlauten einer Sprache. Der Bindestrich in `palavra-passe` und in
  `recém-ligados` ist der gewöhnliche ASCII-Bindestrich (U+002D).
- **Die enklitischen Pronomen tragen ihren Bindestrich.** `recolhe-o`, `aplica-as`,
  `carregá-lo`, `vai-se preenchendo`. Das ist europäisches Portugiesisch und zugleich ein
  Unterschied zum brasilianischen, das die Pronomen gern voranstellt (`o recolhe`). Wer die
  Bindestriche für Tippfehler hält, liest hier, dass sie keine sind.
- **Kein geschütztes Leerzeichen**, weder U+00A0 noch das schmale U+202F. Sie sind unsichtbar,
  und ein Katalog voll unsichtbarer Zeichen ist ein Katalog, dessen Diff niemand liest.
- **Kein Gedankenstrich**, weder U+2014 noch U+2013. Das ist die Regel des Repositoriums und
  wird vom Prosa-Scanner über jede Katalogdatei gehalten.
- **Der Suchbegriff steht in Winkelanführungszeichen**, also `«%s»`, ohne Leerzeichen innen:
  `Resultados para «%s»`, `Nenhum ficheiro contém «%s»`. Das ist die portugiesische
  Buchtypografie und dieselbe Schreibweise wie im spanischen und italienischen Katalog dieses
  Baums; der französische setzt Leerzeichen innen, der niederländische gerade ASCII-Zeichen,
  und beide Entscheide sind dort begründet. Bezeichner der Oberfläche und Befehle stehen
  dagegen in geraden ASCII-Anführungszeichen, genau wie im deutschen Bestand:
  `"occ findling:index --restart"`, `"Pastas excluídas"`, `"Maior ficheiro a ler"`.
- **Die Platzhalter sind die des Schlüssels**, in Art und Zahl. `%1$s in %2$s` bleibt
  `%1$s em %2$s` und wird niemals `%s em %s`.
- **Ein literales Prozentzeichen wird `%%` geschrieben.** Der Grund ist gemessen und nicht
  befürchtet: Nextcloud reicht jeden Katalogwert durch `vsprintf`, ein nacktes `%` wirft dort
  einen `ValueError`, und die Seite bleibt weiß. Für das Portugiesische ist das keine
  Formalie, denn die Sprache setzt das Zeichen mit Leerzeichen davor ("50 %"), und genau dieses
  Leerzeichen macht die Direktive unkenntlich. **In diesem Katalog steht kein einziges
  Prozentzeichen dieser Art**, auch kein verdoppeltes: wo der deutsche Satz "100 Prozent" sagt,
  sagt der portugiesische `cem por cento`. Umformulieren war billiger als retten. Die
  Schreibregel steht trotzdem hier, denn die nächste Zeile, die eine Zahl mit Prozentzeichen
  braucht, kommt bestimmt.
- **Kein Pipe-Zeichen.** Nextcloud verbindet die Pluralformen damit; ein Wert, der es trägt,
  zerlegt sich selbst. `scan_pipe_character` aus Plan 20-03 hält das über jede Katalogdatei.

## Pluralformen

Die Regel für `pt_PT` lautet

```
nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
```

und steht wörtlich so als `"pluralForm"` in `php/l10n/pt_PT.json` und als vierter Parameter von
`OC.L10N.register` in `php/l10n/pt_PT.js`. Sie ist aus `docs/l10n-catalogues.md`, Abschnitt 3,
übernommen und nicht nachgetippt; dort steht auch, dass NC 34.0.3 und NC 35.0.0 für
Portugiesisch dieselbe Zeichenkette führen, und zwar für beide Codes dieselbe.

**Die fünf Pluralwerte tragen drei Formen, und Form 1 und Form 2 sind wortgleich.** Das sieht
nach einer vergessenen Zeile aus und ist keine. Der Grund steht ausgeführt in Abschnitt 4 von
`docs/l10n-catalogues.md` und in zwei Sätzen hier: PHP wertet die Regel nicht aus, sondern
benutzt eine eigene Tabelle und erreicht Index 2 nie; der Browser wertet die deklarierte Regel
aus und wählt bei n gleich 2 den Index 2. Wer nur zwei Formen deklarierte, ließe den Browser
nach einem Index greifen, den es nicht gibt; wer Form 1 und Form 2 verschieden schriebe,
bekäme auf Server und Browser verschiedene Sätze für dieselbe Zahl. Zwei gleiche Formen sind
der Preis dafür, dass beide Seiten dasselbe zeigen. `FORM_COUNT_OF["pt_PT"]` ist 3, und die
Zahl steht im Gate als eigene Zahl und wird nicht aus `nplurals=` geparst.

**Die benannte Abweichung bei n gleich 0.** `docs/l10n-catalogues.md`, Abschnitt 5, hält sie
fest, und `pt_PT` ist die einzige der vier Sprachen dieser Phase, die sie hat: bei null wählt
die Browserseite den **Singular** (der Vorderzweig `(n == 0 || n == 1) ? 0` der Regel oben),
die PHP-Seite den **Plural**. Die Messung berichtigt hier eine naheliegende Erwartung, denn
`pt_BR` weicht **nicht** ab, obwohl es dieselbe Regelzeichenkette führt: die Tabelle, die PHP
benutzt, behandelt die Null im brasilianischen Portugiesisch wie den Singular und im
europäischen wie den Plural.

Wie weit die Abweichung reicht, ist ausgezählt und nicht geschätzt: höchstens bis zur
Sekundenzeile der Dateisperre (`_A worker holds this file. ... %n second ..._`). Die drei
Zeitspannen Minuten, Stunden und Tage laufen über `max(1, ...)`-Schwellen und können nie mit 0
gerendert werden, und `e mais %n` wird nur gerendert, wenn der Rest größer als 0 ist. Bleibt
eine Sperre, deren Restlaufzeit auf 0 Sekunden gerundet ist: der Server schriebe dort
`%n segundos`, das Skript nach dem ersten Poll `%n segundo`. Ein portugiesischer Nutzer sieht
in dieser einen Zeile in dieser einen Sekunde eine andere Endung. Das ist eine dokumentierte
Grenze und keine offene Aufgabe; sie zu beseitigen hieße, eine Seite bei jeder anderen Anzahl
falsch zu bedienen.

In der Tabelle unten stehen die Formen eines Pluralschlüssels durch ` / ` getrennt in einer
Zelle, zuerst der Singular, wie es der französische, spanische, italienische und
niederländische Bestand machen. Die deutsche Spalte führt dort zwei Formen, die portugiesische
drei.

## Die Tabelle

Alle drei Spalten sind aus `php/l10n/de.json` und `php/l10n/pt_PT.json` erzeugt und nicht
abgetippt; die Reihenfolge ist die der Dateien. Die Spaltennamen sind ASCII, weil sie
Vertragsbezeichner sind und die Projektregel echte Umlaute der deutschen Prosa vorbehält. Der
Schlüssel ist der englische Quellstring: er steht wörtlich so im Template, läuft dort durch
`$l->t()` und ist in jeder Katalogdatei der Schlüssel der Übersetzung.

Kein Wert und kein Schlüssel kann ein Pipe-Zeichen enthalten, dafür sorgt `scan_pipe_character`
aus Plan 20-03. Diese Tabelle kann also nicht an einem Wortlaut zerbrechen.

**Diese Tabelle trägt heute drei Spalten. Plan 20-08 hebt sie auf vier**, indem er die Spalte
PT_BR mit den brasilianischen Wortlauten danebensetzt. Eine leere vierte Spalte steht hier
bewusst nicht: eine leere Zelle sieht aus wie eine vergessene Übersetzung, und wer diese Datei
zwischen den beiden Plänen liest, soll sehen, was fertig ist, und nicht 202 Lücken.

| Schluessel | DE | PT_PT |
|---|---|---|
| `Findling` | Findling | Findling |
| `File contents` | Dateiinhalte | Conteúdo dos ficheiros |
| `Search coverage` | Deckungsgrad der Suche | Cobertura da pesquisa |
| `%1$s of %2$s indexable files are searchable` | %1$s von %2$s indexierbaren Dateien sind durchsuchbar | %1$s de %2$s ficheiros indexáveis podem ser encontrados pela pesquisa |
| `The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.` | Der Anteil ist im Moment nicht berechenbar, weil das Backend nicht antwortet. %s Dateien dieser Instanz sind indexierbar. | A proporção não pode ser calculada neste momento porque o serviço não responde. %s ficheiros desta instância são indexáveis. |
| `Deliberately left out: %s` | Bewusst ausgelassen: %s | Deixados de fora de propósito: %s |
| `Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.` | Diese Dateien sind zu groß, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen. Sie stehen nicht im Nenner darüber, damit der Deckungsgrad 100 Prozent erreichen kann. | Esses ficheiros são demasiado grandes, de um tipo que o Findling não lê, ou excluídos por uma regra. Não estão no denominador acima, de modo que a cobertura pode chegar a cem por cento. |
| `Provisional figure, %1$s of %2$s storages have been counted through.` | Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt. | Valor provisório, foram contados %1$s de %2$s armazenamentos. |
| `Findable by meaning` | Auffindbar nach Bedeutung | Encontrável pelo significado |
| `%1$s of %2$s indexable files can also be found by meaning` | %1$s von %2$s indexierbaren Dateien sind auch nach Bedeutung auffindbar | %1$s de %2$s ficheiros indexáveis também podem ser encontrados pelo significado |
| `The semantic share cannot be worked out right now. The backend does not answer, or it does not report this figure yet.` | Der semantische Anteil ist im Moment nicht berechenbar. Das Backend antwortet nicht, oder es meldet diese Zahl noch nicht. | A proporção semântica não pode ser calculada neste momento. O serviço não responde, ou ainda não comunica este valor. |
| `The model is in memory, the semantic search is answering.` | Das Modell liegt im Speicher, die semantische Suche antwortet. | O modelo está em memória, a pesquisa semântica está a responder. |
| `The model is read when it is first needed. That is the normal state.` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | O modelo é carregado na primeira vez que é preciso. Esse é o estado normal. |
| `The semantic half is switched off in the settings of the container.` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | A metade semântica está desligada nas definições do contentor. |
| `There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.` | In diesem Abbild liegt kein Modell. Die Suche liefert weiterhin Volltexttreffer, die semantische Hälfte bleibt leer. | Nesta imagem não há nenhum modelo. A pesquisa continua a responder com resultados de texto integral, a metade semântica fica vazia. |
| `Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.` | Das Laden des Modells ist einmal gescheitert und wird in Kürze erneut versucht. Bis dahin liefert die Suche Volltexttreffer. | O carregamento do modelo falhou uma vez e será tentado de novo em breve. Até lá a pesquisa responde com resultados de texto integral. |
| `The model was released to save memory. The next search answers with full text hits and loads it again in the background.` | Das Modell wurde zum Sparen freigegeben. Die nächste Suche antwortet mit Volltexttreffern und lädt es im Hintergrund nach. | O modelo foi libertado para poupar memória. A pesquisa seguinte responde com resultados de texto integral e volta a carregá-lo em segundo plano. |
| `This container does not report the state of the model yet.` | Dieser Container meldet den Zustand des Modells noch nicht. | Este contentor ainda não comunica o estado do modelo. |
| `The full text search covers every indexed document. The semantic search covers the beginning of each document, and this second figure fills up after the first index has finished.` | Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem Erstindex nach. | A pesquisa de texto integral abrange todos os documentos indexados. A pesquisa semântica abrange o início de cada documento, e este segundo valor vai-se preenchendo depois de terminar a primeira indexação. |
| `Up to date, last checked %s` | Aktuell, letzte Prüfung %s | Atualizado, última verificação %s |
| `Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.` | Die Indexierung kommt seit %s nicht voran. In dieser Zeit hat weder ein Hintergrundauftrag noch das Backend etwas fertiggestellt. | A indexação não avança há %s. Nesse tempo nem uma tarefa em segundo plano nem o serviço terminaram nada. |
| `No background job of this app has run yet. Background jobs may not be running.` | Noch kein Hintergrundauftrag dieser App ist gelaufen. Möglicherweise laufen die Hintergrundaufträge nicht. | Ainda não foi executada nenhuma tarefa em segundo plano desta aplicação. É possível que as tarefas em segundo plano não estejam a funcionar. |
| `Indexing is running.` | Die Indexierung läuft. | A indexação está em curso. |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | Die Zahlen konnten nicht aktualisiert werden. Die Werte unten sind die letzten, die diese Seite bekommen hat. | Não foi possível atualizar os números. Os valores abaixo são os últimos que esta página recebeu. |
| `_%n minute_::_%n minutes_` | %n Minute / %n Minuten | %n minuto / %n minutos / %n minutos |
| `_%n hour_::_%n hours_` | %n Stunde / %n Stunden | %n hora / %n horas / %n horas |
| `_%n day_::_%n days_` | %n Tag / %n Tage | %n dia / %n dias / %n dias |
| `Waiting in the queue` | Wartet in der Warteschlange | À espera na fila |
| `Being processed` | Wird gerade verarbeitet | A ser processado |
| `Indexed` | Indexiert | Indexado |
| `Skipped` | Übersprungen | Ignorado |
| `Failed` | Fehlgeschlagen | Falhado |
| `Excluded` | Ausgeschlossen | Excluído |
| `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst. | Os ficheiros excluídos não contam para a cobertura. São os ficheiros que o Findling não toca por indicação sua. |
| `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter. | Resta pouco espaço em disco. A indexação está em pausa para que o índice se mantenha intacto. A pesquisa continua a funcionar. |
| `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer. | O índice foi construído com uma análise de texto mais antiga. Reconstruí-lo com "occ findling:index --restart", caso contrário continuarão a faltar resultados. |
| `Findling is rebuilding its index so that the newly switched on languages can be searched. %1$s of %2$s documents have been carried over. Search keeps answering while this runs, and there is nothing to start or to restart.` | Findling baut seinen Index neu auf, damit die neu eingeschalteten Sprachen durchsucht werden können. %1$s von %2$s Dokumenten sind übertragen. Die Suche antwortet währenddessen weiter, und es gibt nichts zu starten oder neu zu starten. | O Findling está a reconstruir o seu índice para que os idiomas recém-ligados possam ser pesquisados. Já foram migrados %1$s de %2$s documentos. A pesquisa continua a responder entretanto, e não há nada para iniciar nem para reiniciar. |
| `Findling wants to rebuild its index for the newly switched on languages and there is not enough room: %s more are needed next to what the index already uses. Free that much, or set the environment variable FINDLING_REBUILD_FALLBACK=fullreindex to have the backend read the files again instead. Either way the backend only tries again after a restart of the container.` | Findling möchte seinen Index für die neu eingeschalteten Sprachen neu aufbauen, und es ist nicht genug Platz: %s fehlen zusätzlich zu dem, was der Index bereits belegt. Geben Sie so viel frei, oder setzen Sie die Umgebungsvariable FINDLING_REBUILD_FALLBACK=fullreindex, damit das Backend die Dateien stattdessen neu liest. In beiden Fällen versucht es das Backend erst nach einem Neustart des Containers erneut. | O Findling quer reconstruir o seu índice para os idiomas recém-ligados e não há espaço suficiente: são precisos mais %s além do que o índice já ocupa. Liberte essa quantidade, ou defina a variável de ambiente FINDLING_REBUILD_FALLBACK=fullreindex para que o serviço volte a ler os ficheiros em vez disso. Em qualquer dos casos o serviço só tenta de novo depois de reiniciar o contentor. |
| `Languages of the index: %1$s switched on, %2$s with text in the index.` | Sprachen des Index: %1$s eingeschaltet, %2$s mit Text im Index. | Idiomas do índice: %1$s ligados, %2$s com texto no índice. |
| `No numbers yet` | Noch keine Zahlen | Ainda sem valores |
| `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` | Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen. | A primeira passagem de indexação ainda não terminou. O Findling arrancou sozinho, não há nada a configurar. |
| `The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.` | Die beiden Hälften von Findling melden unterschiedliche Versionen: diese App ist %1$s, das Backend ist %2$s. Solange sie nicht zusammenpassen, antwortet die Suche ohne Ergebnisse, weil eine falsche Antwort ohne Hinweis schlimmer wäre. Beide Hälften auf dieselbe Version bringen. | As duas metades do Findling comunicam versões diferentes: esta aplicação é %1$s, o serviço é %2$s. Enquanto não coincidirem, a pesquisa responde sem resultados, porque uma resposta errada sem aviso seria pior. Ponha ambas as metades na mesma versão. |
| `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` | Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist. | O serviço do Findling não responde. Os números abaixo são os últimos que esta aplicação registou. Verifique em Aplicações se a aplicação externa "Findling Backend" está instalada e em funcionamento. |
| `Estimate for the first index` | Schätzung für den Erstindex | Estimativa para a primeira indexação |
| `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | %1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index. | %1$s ficheiros, %2$s deles precisam de OCR. Cerca de %3$s e cerca de %4$s de índice. |
| `%1$s files, %2$s of them need OCR.` | %1$s Dateien, davon %2$s mit OCR. | %1$s ficheiros, %2$s deles precisam de OCR. |
| `%1$s to %2$s` | %1$s bis %2$s | %1$s a %2$s |
| `Counting the files, this takes a moment.` | Die Dateien werden gezählt, das dauert einen Moment. | Os ficheiros estão a ser contados, isto demora um momento. |
| `Startup value, being measured.` | Startwert, wird gemessen. | Valor inicial, a ser medido. |
| `The space needed is measured as soon as the first documents are in the index.` | Der Platzbedarf wird gemessen, sobald die ersten Dokumente im Index sind. | O espaço necessário é medido assim que os primeiros documentos estiverem no índice. |
| `The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.` | Der Index braucht voraussichtlich mehr Platz, als auf diesem Datenträger frei ist. Die Indexierung pausiert, bevor der Datenträger voll wird, und die Suche funktioniert weiter. | Prevê-se que o índice precise de mais espaço do que o que está livre neste volume. A indexação faz uma pausa antes de o volume encher, e a pesquisa continua a funcionar. |
| `Findling does not wait for a confirmation. The first index has already started.` | Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits. | O Findling não espera por nenhuma confirmação. A primeira indexação já começou. |
| `Files that were not indexed` | Nicht indexierte Dateien | Ficheiros que não foram indexados |
| `Files that were not indexed, grouped by reason` | Nicht indexierte Dateien, nach Grund gruppiert | Ficheiros que não foram indexados, agrupados por motivo |
| `Every file was indexed. Nothing was skipped and nothing failed.` | Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen. | Todos os ficheiros foram indexados. Nada foi ignorado e nada falhou. |
| `Reason` | Grund | Motivo |
| `Files` | Dateien | Ficheiros |
| `State` | Zustand | Estado |
| `Show example paths` | Beispielpfade anzeigen | Mostrar caminhos de exemplo |
| `Hide example paths` | Beispielpfade verbergen | Ocultar caminhos de exemplo |
| `_and %n more_::_and %n more_` | und %n weitere / und %n weitere | e mais %n / e mais %n / e mais %n |
| `File no longer exists (ID %s)` | Datei existiert nicht mehr (ID %s) | O ficheiro já não existe (ID %s) |
| `%s (in the trash bin)` | %s (im Papierkorb) | %s (na reciclagem) |
| `Indexed, text truncated` | Indexiert, Text gekürzt | Indexado, texto cortado |
| `Unknown reason (%s)` | Unbekannter Grund (%s) | Motivo desconhecido (%s) |
| `This app does not know this code. It may come from a newer version of the backend.` | Diese App kennt diesen Code nicht. Er kann von einer neueren Fassung des Backends kommen. | Esta aplicação não conhece este código. Pode vir de uma versão mais recente do serviço. |
| `Text truncated` | Text gekürzt | Texto cortado |
| `The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.` | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. | O início do documento pode ser pesquisado, o resto não. Os documentos muito longos são cortados de propósito. |
| `Too large` | Zu groß | Demasiado grande |
| `Raise the value under "Largest file to read".` | Den Wert unter "Größte zu lesende Datei" erhöhen. | Aumente o valor em "Maior ficheiro a ler". |
| `File type not supported` | Dateityp nicht unterstützt | Tipo de ficheiro não suportado |
| `None. Findling reads PDF, Office, OpenDocument, text and images.` | Keine. Findling liest PDF, Office, OpenDocument, Text und Bilder. | Nenhuma. O Findling lê PDF, Office, OpenDocument, texto e imagens. |
| `Password protected` | Passwortgeschützt | Protegido por palavra-passe |
| `None. Without the password the content cannot be read.` | Keine. Ohne Passwort ist der Inhalt nicht lesbar. | Nenhuma. Sem a palavra-passe não é possível ler o conteúdo. |
| `No text in the document` | Kein Text im Dokument | Sem texto no documento |
| `None. The document carries neither a text layer nor recognisable writing.` | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. | Nenhuma. O documento não tem camada de texto nem escrita reconhecível. |
| `No text content` | Kein Textinhalt | Sem conteúdo de texto |
| `None. The file is readable but carries no text.` | Keine. Die Datei ist lesbar, enthält aber keinen Text. | Nenhuma. O ficheiro pode ser lido, mas não tem texto. |
| `Spreadsheet too large` | Tabelle zu groß | Folha de cálculo demasiado grande |
| `None. Very large spreadsheets are skipped so the container does not fall over.` | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. | Nenhuma. As folhas de cálculo muito grandes são ignoradas para que o contentor não caia. |
| `File no longer present` | Datei nicht mehr vorhanden | O ficheiro já não está presente |
| `None. The file was already deleted or moved when it was read.` | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. | Nenhuma. O ficheiro já tinha sido apagado ou movido quando foi lido. |
| `Image without recognisable writing` | Bild ohne erkennbare Schrift | Imagem sem escrita reconhecível |
| `None.` | Keine. | Nenhuma. |
| `Excluded by a rule` | Durch Regel ausgeschlossen | Excluído por uma regra |
| `Remove the matching entry under "Excluded folders".` | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. | Retire a entrada correspondente em "Pastas excluídas". |
| `File is empty` | Datei ist leer | O ficheiro está vazio |
| `None. The file has 0 bytes.` | Keine. Die Datei hat 0 Byte. | Nenhuma. O ficheiro tem 0 bytes. |
| `File damaged` | Datei beschädigt | Ficheiro danificado |
| `Check the file outside of Nextcloud and upload it again.` | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. | Verifique o ficheiro fora do Nextcloud e volte a carregá-lo. |
| `Document structure faulty` | Dokumentstruktur fehlerhaft | Estrutura do documento defeituosa |
| `Open the document in the program it came from and save it again.` | Das Dokument im Ursprungsprogramm öffnen und neu speichern. | Abra o documento no programa de onde veio e volte a guardá-lo. |
| `Character set not recognised` | Zeichensatz nicht erkannt | Conjunto de caracteres não reconhecido |
| `Save the file as UTF-8 and upload it again.` | Die Datei als UTF-8 speichern und neu hochladen. | Guarde o ficheiro como UTF-8 e volte a carregá-lo. |
| `Timed out while reading` | Zeitüberschreitung beim Lesen | Tempo de espera esgotado durante a leitura |
| `The next run tries again.` | Wird beim nächsten Lauf erneut versucht. | A próxima passagem tenta de novo. |
| `Not enough memory while reading` | Zu wenig Speicher beim Lesen | Memória insuficiente durante a leitura |
| `The next run tries again. If it happens again, lower the size cap.` | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken. | A próxima passagem tenta de novo. Se voltar a acontecer, baixe o limite de tamanho. |
| `File was not retrievable` | Datei war nicht abrufbar | Não foi possível obter o ficheiro |
| `Stuck repeatedly` | Mehrfach hängen geblieben | Encravado várias vezes |
| `Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.` | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. | O Findling não volta a tentar este ficheiro. Use a consulta para verificar se ele abre fora do Nextcloud. |
| `Text recognition failed` | Texterkennung fehlgeschlagen | O reconhecimento de texto falhou |
| `Text recognition not available` | Texterkennung nicht verfügbar | Reconhecimento de texto não disponível |
| `The backend could not start Tesseract. Check the log of the External App.` | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. | O serviço não conseguiu iniciar o Tesseract. Verifique o registo da aplicação externa. |
| `Look up one file` | Einzelne Datei prüfen | Consultar um ficheiro |
| `Path or file ID` | Pfad oder Datei-ID | Caminho ou ID do ficheiro |
| `A path as Nextcloud stores it, or the numeric ID from the list above.` | Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben. | Um caminho tal como o Nextcloud o guarda, ou o número da lista acima. |
| `Look up file` | Datei prüfen | Consultar ficheiro |
| `Looking up a single file needs JavaScript. Everything above stays complete without it.` | Die Einzelprüfung braucht JavaScript. Alles darüber bleibt auch ohne vollständig lesbar. | A consulta de um único ficheiro precisa de JavaScript. Tudo o que está acima continua completo sem ele. |
| `No file at this path, and no file with this ID.` | Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID. | Não há nenhum ficheiro neste caminho, nem nenhum ficheiro com este ID. |
| `Not seen yet` | Noch nicht gesehen | Ainda não visto |
| `State unknown right now` | Zustand im Moment unbekannt | Estado desconhecido neste momento |
| `File ID: %s` | Datei-ID: %s | ID do ficheiro: %s |
| `Last checked %s` | Zuletzt geprüft: %s | Última verificação: %s |
| `The lookup did not work. Nothing about this file has changed.` | Die Prüfung hat nicht funktioniert. An dieser Datei hat sich nichts geändert. | A consulta não funcionou. Neste ficheiro nada mudou. |
| `The state of this file is unknown right now because the backend does not answer.` | Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet. | O estado deste ficheiro é desconhecido neste momento porque o serviço não responde. |
| `This file has not reached the queue. The next comparison run picks it up.` | Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab. | Este ficheiro ainda não chegou à fila. A próxima passagem de comparação recolhe-o. |
| `It was indexed before and is recorded again on the next comparison run.` | Sie war vorher indexiert und wird beim nächsten Abgleichlauf neu erfasst. | Estava indexado antes e volta a ser registado na próxima passagem de comparação. |
| `This file was indexed and has since been deleted. It is out of the index with it.` | Diese Datei war indexiert und ist inzwischen gelöscht. Damit ist sie auch aus dem Index heraus. | Este ficheiro estava indexado e entretanto foi apagado. Com isso também saiu do índice. |
| `In the trash bin` | Im Papierkorb | Na reciclagem |
| `Restore the file. The next comparison run picks it up.` | Die Datei wiederherstellen. Der nächste Abgleichlauf holt sie ab. | Restaure o ficheiro. A próxima passagem de comparação recolhe-o. |
| `Storage is not indexed` | Speicherort wird nicht indexiert | O armazenamento não é indexado |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | Findling liest die Heimatverzeichnisse der Nutzer. Team Folders und externer Speicher sind eigene Einstellungen. | O Findling lê as pastas pessoais dos seus utilizadores. As Team Folders e o armazenamento externo são definições próprias. |
| `This is a folder` | Das ist ein Ordner | Isto é uma pasta |
| `Enter the path of a file. A folder has no state of its own.` | Den Pfad einer Datei eingeben. Ein Ordner hat keinen eigenen Zustand. | Indique o caminho de um ficheiro. Uma pasta não tem estado próprio. |
| `Attempts so far: %s` | Bisherige Versuche: %s | Tentativas até agora: %s |
| `The next background run picks this file up (%s).` | Der nächste Hintergrundlauf holt diese Datei ab (%s). | A próxima passagem em segundo plano recolhe este ficheiro (%s). |
| `The content of this file is searchable.` | Der Inhalt dieser Datei ist durchsuchbar. | O conteúdo deste ficheiro pode ser pesquisado. |
| `_A worker holds this file. The claim runs out in %n second if nothing acknowledges it._::_A worker holds this file. The claim runs out in %n seconds if nothing acknowledges it._` | Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunde aus, wenn ihn niemand quittiert. / Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunden aus, wenn ihn niemand quittiert. | Um processo de tratamento tem este ficheiro reservado. A reserva expira em %n segundo se ninguém a confirmar. / Um processo de tratamento tem este ficheiro reservado. A reserva expira em %n segundos se ninguém a confirmar. / Um processo de tratamento tem este ficheiro reservado. A reserva expira em %n segundos se ninguém a confirmar. |
| `Rules and limits` | Regeln und Grenzen | Regras e limites |
| `Excluded folders` | Ausgeschlossene Ordner | Pastas excluídas |
| `Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups` | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, keine Platzhalter und keine Muster. Beispiel: Backups | Comparação por prefixo sobre o caminho tal como as listas desta página o mostram, sem caracteres universais nem padrões. Exemplo: Backups |
| `Add exclusion` | Ausschluss hinzufügen | Adicionar exclusão |
| `Remove exclusion %s` | Ausschluss %s entfernen | Retirar a exclusão %s |
| `No folder is excluded.` | Kein Ordner ist ausgeschlossen. | Não há nenhuma pasta excluída. |
| `Largest file to read` | Größte zu lesende Datei | Maior ficheiro a ler |
| `Files above this size are recorded as skipped (too large) and never read.` | Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen. | Os ficheiros acima deste tamanho são registados como ignorados (demasiado grandes) e nunca são lidos. |
| `The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container.` | Das Backend dieser Instanz liest höchstens %s MB. Für mehr FINDLING_MAX_FILE_BYTES in den App-Einstellungen von AppAPI anheben, was den Container neu startet. | O serviço desta instância lê no máximo %s MB. Para mais, aumente FINDLING_MAX_FILE_BYTES nas definições de aplicação do AppAPI, o que reinicia o contentor. |
| `Index Team Folders` | Team Folders indexieren | Indexar as Team Folders |
| `Index external storage` | Externen Speicher indexieren | Indexar o armazenamento externo |
| `External storage can be slow or charged per request. Indexing reads every file once.` | Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal. | O armazenamento externo pode ser lento ou cobrado por acesso. A indexação lê cada ficheiro uma vez. |
| `The next run applies the new rules. Nothing restarts.` | Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu. | A próxima passagem aplica as novas regras. Não reinicia nada. |
| `Save rules` | Regeln speichern | Guardar regras |
| `Rules saved. The next run applies them.` | Regeln gespeichert. Der nächste Lauf übernimmt sie. | Regras guardadas. A próxima passagem aplica-as. |
| `The rules were not saved. Nothing changed.` | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | As regras não foram guardadas. Nada mudou. |
| `Enter a size between %1$s and %2$s MB.` | Eine Größe zwischen %1$s und %2$s MB eingeben. | Indique um tamanho entre %1$s e %2$s MB. |
| `Enter a folder path.` | Einen Ordnerpfad eingeben. | Indique um caminho de pasta. |
| `This path is already excluded.` | Dieser Pfad ist bereits ausgeschlossen. | Este caminho já está excluído. |
| `Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.` | Einen Eintrag zu entfernen wirkt innerhalb von %1$s Stunden, wenn der nächste Abgleichlauf diese Dateien wieder aufnimmt. Mit "%2$s" sofort übernehmen. | Retirar uma entrada produz efeito dentro de %1$s horas, quando a próxima passagem de comparação voltar a recolher esses ficheiros. Execute "%2$s" para aplicar de imediato. |
| `Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %1$s entfernt außerdem %2$s bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Retirar o conteúdo indexado? Excluir %1$s retira também do índice %2$s documentos já indexados sob esse caminho. Os próprios ficheiros ficam intactos no disco. |
| `Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Retirar o conteúdo indexado? Excluir %s retira também do índice os documentos já indexados sob esse caminho. Os próprios ficheiros ficam intactos no disco. |
| `at least %s` | mindestens %s | pelo menos %s |
| `Exclude and remove` | Ausschließen und entfernen | Excluir e retirar |
| `Keep files indexed` | Dateien indexiert lassen | Manter os ficheiros indexados |
| `Search` | Suchen | Pesquisar |
| `Search term` | Suchbegriff | Termo de pesquisa |
| `invoice 2026` | Rechnung 2026 | fatura 2026 |
| `Search file names only` | Nur Dateinamen durchsuchen | Pesquisar apenas nos nomes dos ficheiros |
| `Results for "%s"` | Treffer für „%s“ | Resultados para «%s» |
| `Search results` | Suchergebnisse | Resultados da pesquisa |
| `%1$s in %2$s` | %1$s in %2$s | %1$s em %2$s |
| `last opened` | zuletzt geöffnet | aberto pela última vez |
| `Show all results` | Alle Treffer anzeigen | Mostrar todos os resultados |
| `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | Abre a página de resultados do Findling |
| `Previous page` | Vorherige Seite | Página anterior |
| `Next page` | Nächste Seite | Página seguinte |
| `Page %s` | Seite %s | Página %s |
| `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | Existem mais resultados. Restrinja a pesquisa para os ver. |
| `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | Pesquise no conteúdo dos seus ficheiros |
| `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | Escreva uma palavra de um documento. O Findling pesquisa o texto dentro dos seus ficheiros, incluindo os PDF digitalizados. |
| `No file contains "%s"` | Keine Datei enthält „%s“ | Nenhum ficheiro contém «%s» |
| `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | Experimente outra palavra, uma parte de uma palavra composta, ou verifique a ortografia. |
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen. | Outros ficheiros contêm esta palavra, mas nenhum que lhe seja permitido abrir. |
| `The search is not answering right now` | Die Suche antwortet gerade nicht | A pesquisa não está a responder neste momento |
| `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | O Findling não conseguiu contactar o seu serviço. Os seus ficheiros não mudaram. Tente de novo daqui a pouco, e avise a sua administração se continuar assim. |
| `Try again` | Erneut versuchen | Tentar de novo |
| `Findling is not ready to search` | Findling ist nicht suchbereit | O Findling não está pronto para pesquisar |
| `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | As duas metades do Findling comunicam versões diferentes. A sua administração tem de atualizar ambas ao mesmo tempo. |
| `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | O índice ainda está a ser construído, por isso podem faltar resultados. |
| `File type` | Dateityp | Tipo de ficheiro |
| `PDF` | PDF | PDF |
| `Documents` | Dokumente | Documentos |
| `Spreadsheets` | Tabellen | Folhas de cálculo |
| `Presentations` | Präsentationen | Apresentações |
| `Images` | Bilder | Imagens |
| `Text` | Text | Texto |
| `Time range` | Zeitraum | Período |
| `Today` | Heute | Hoje |
| `Last 7 days` | Letzte 7 Tage | Últimos 7 dias |
| `Last 30 days` | Letzte 30 Tage | Últimos 30 dias |
| `This year` | Dieses Jahr | Este ano |
| `Remove filter %s` | Filter %s entfernen | Retirar o filtro %s |
| `Reset all filters` | Alle Filter zurücksetzen | Repor todos os filtros |
| `Sort by` | Sortieren nach | Ordenar por |
| `Relevance` | Relevanz | Relevância |
| `Last modified` | Zuletzt geändert | Última modificação |
| `Oldest first` | Älteste zuerst | Mais antigos primeiro |
| `Modified on %s` | Geändert am %s | Modificado em %s |
| `%1$s in %2$s, modified on %3$s` | %1$s in %2$s, geändert am %3$s | %1$s em %2$s, modificado em %3$s |
| `No results with the active filters` | Keine Treffer mit den aktiven Filtern | Sem resultados com os filtros ativos |
| `Remove a filter or widen the time range.` | Entfernen Sie einen Filter oder erweitern Sie den Zeitraum. | Retire um filtro ou alargue o período. |
| `Reset filters` | Filter zurücksetzen | Repor filtros |

## Was diese Kataloge nicht leisten

Zwei benannte Grenzen. Beide sind Entscheide dieses Milestones und keine Lücken, und beide
stehen hier, damit sie später nicht wie Fehler aussehen.

**Die Rechtschreibreform wird nicht vereinheitlicht.** Das Abkommen von 1990 hat in Portugal
eine Reihe stummer Mitlaute abgeschafft, und im Alltag stehen die alte und die neue Schreibung
bis heute nebeneinander. Dieser Katalog schreibt durchgehend die heute übliche, reformierte
Form: `atualizar` und nicht `actualizar`, `ativos` und nicht `activos`, `exceto` und nicht
`excepto`. Was er **nicht** leistet, ist ein Gate darüber. Ein portugiesischer Leser, der die
alte Schreibung gewohnt ist, findet hier also eine Entscheidung vor und keinen Fehler; wer sie
umkehren will, kehrt sie in der ganzen Tabelle um und nicht in einer Zeile.

**Es gibt keine getrennten portugiesischen Wortlaute für die Suche selbst, nur für die
Oberfläche.** Der Unterschied zwischen `ficheiro` und `arquivo` steht in den Katalogen dieser
Phase; der Index, die Wortzerlegung und die Trefferbewertung kennen ihn nicht. Ein Nutzer, der
auf europäisches Portugiesisch gestellt ist, sucht mit derselben Textanalyse wie einer auf
brasilianisches. Das ist in `REQUIREMENTS.md` als künftige Arbeit geführt und ausdrücklich
nicht Gegenstand dieses Milestones. Wer an dieser Stelle mehr erwartet, erwartet eine
sprachspezifische Analysekette, und die ist ein eigener Plan mit eigener Messung.

## Ausnahmen für das Vollständigkeitsgate G2

Gate G2, heute `test_every_catalogue_value_carries_a_wording_of_its_language`, fordert, dass
kein Wert leer und keiner mit dem englischen Quellstring identisch ist. Genau zwei Schlüssel
sind es im europäischen Portugiesisch absichtlich. Das ist eine benannte Liste und ausdrücklich
**keine** Toleranzschwelle: eine Schwelle würde einen vergessenen Wortlaut genauso mitdecken wie
einen gewollten, eine Liste deckt nur, was in ihr steht. Die Liste darf wachsen, die Zahl zwei
ist keine Grenze, sondern das Ergebnis des Zählens, und jeder Eintrag trägt seinen Grund bei
sich.

- `Findling`: Eigenname der App, in jeder Sprache dasselbe Wort. Er steht als Schlüssel in
  `de.json` und muss deshalb in `pt_PT.json` stehen, hat aber keinen eigenen Wortlaut.
- `PDF`: Eigenname eines Dateiformats, in jeder Sprache dieselbe Abkürzung.

Die Liste ist nicht geraten worden. Drei Läufe, in dieser Reihenfolge:

| Lauf | Ergebnis |
|---|---|
| kein Eintrag für `pt_PT` in der Tabelle | `AssertionError: languages without a list of exceptions: ['pt_PT']` |
| leeres Mapping `"pt_PT": {}` | vier Funde, zwei Schlüssel über zwei Dateien, erster davon `pt_PT.json: 'Findling' is still the English source string` |
| zwei begründete Einträge | grün, 52 passed |

Beurteilt wurde je Schlüssel und nicht gezählt. **Es ist die kürzeste Liste dieses Baums**, so
kurz wie die spanische und kürzer als die italienische (drei), die niederländische (vier) und
die französische (fünf). Der Unterschied zu den drei längeren ist ein einziger Schlüssel, und
er ist eine Eigenschaft der Sprache: `%1$s in %2$s` steht in der deutschen, der italienischen
und der niederländischen Liste, weil diese drei Sprachen die Präposition zwischen den beiden
Platzhaltern genauso schreiben wie das Englische. Das Portugiesische schreibt `em`, also ist
der Schlüssel hier übersetzt und keine Ausnahme. `Spreadsheets` wiederum steht in der
niederländischen Liste und nicht hier, weil das Portugiesische `folhas de cálculo` sagt, wo das
Niederländische das englische Wort führt.

Dieselben zwei Schlüssel mit denselben Gründen stehen in
`VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_PT"]` in `backend/tests/test_admin_ui_contract.py`. Doku
und Gate dürfen hier nicht auseinanderlaufen: die Doku sagt, was erlaubt ist, das Gate hält es.

## Maschinelle Prüfungen

Gefahren am 25.09.2026 über die beiden erzeugten Dateien, nicht per Augenmaß:

| Prüfung | Ergebnis |
|---|---|
| Schlüsselmenge `pt_PT.json` gleich `de.json`, in derselben Reihenfolge | ja, 202 von 202, fehlend 0 |
| Schlüsselmenge `pt_PT.js` gleich `pt_PT.json` (Objektvergleich über den `register`-Rumpf) | ja, identisch |
| Jeder Schlüssel aus `pt_PT.json` kommt in dieser Datei vor | fehlend: 0 |
| Platzhalter-Parität Schlüssel gegen Wert, über alle 40 Schlüssel mit Direktiven, Pluralschlüssel an `_::_` geteilt | 0 Abweichungen |
| Pluralschlüssel mit genau **drei** Formen, Form 1 gleich Form 2 | 5 von 5 |
| Pluralschlüsselmenge gleich der deutschen | ja |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, mit `nplurals=3` | ja, in beiden Dateien |
| `scan_plural_rule` meldet für `pt_PT` mit der eigenen Zeichenkette keinen Fund | ja, `[]` |
| `scan_plural_rule` meldet für `pt_PT` mit der deutschen Zeichenkette zwei Funde | ja |
| `scan_plural_rule` meldet für `pt_PT` mit der **spanischen** Zeichenkette einen Fund | ja, und das ist die schärfere Gegenprobe: die beiden Regeln unterscheiden sich nur im Vorderzweig |
| `php/l10n/pt.json` und `php/l10n/pt.js` vorhanden | nein, beide nicht, und das ist gewollt |
| U+2019 (typographischer Apostroph) | 0 |
| U+2014 und U+2013 (Gedankenstriche) | 0 |
| U+00A0 und U+202F (geschützte Leerzeichen) | 0 |
| Nackte Prozentzeichen, also `%` ohne erkannte Direktive | 0 in Schlüsseln und in allen Formen |
| Verdoppelte Prozentzeichen | 0, der einzige betroffene Satz ist umformuliert |
| Pipe-Zeichen (der senkrechte Strich, mit dem Nextcloud Pluralformen verbindet) | 0 in Schlüsseln und in allen Formen |
| Wert identisch mit dem englischen Quellstring | 2, beide oben benannt |
| `ficheiro` und `utilizador` im Katalog | 56 und 1 |
| `arquivo`, `usuário`, `tela` im Katalog | 0, 0, 0 |
| LF, UTF-8 ohne BOM, abschließender Zeilenumbruch | beide Dateien, byteweise geprüft; der Git-Blob ist reines LF (0 CR) |
| Giessform gegen den unveränderten Bestand, vor der ersten neuen Zeile | 12 von 12 byteweise gleich (`de`, `de_DE`, `fr`, `es`, `it`, `nl`, je `.json` und `.js`) |
| Einträge in `L10N_CATALOGUES` | 14 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped |
| ruff check, ruff format --check, pyright, vulture | alle grün |

Was keine Maschine prüfen kann, ist die Sprache. Das ist der Gegenstand des Abschnitts
darunter.

## Abnahme

**Erzeugt am 25.09.2026, Plan 20-07.** Die europäisch-portugiesischen Wortlaute dieser Tabelle
sind maschinell entstanden und anschließend gegen die Gates gefahren, die der Abschnitt
"Maschinelle Prüfungen" aufzählt: Schlüsselmenge, Gleichstand der beiden Dateien,
Platzhalterparität, Formenzahl, Pluralregel, Prozentdisziplin, Pipe-Zeichen, Prosa-Scan auf
Gedankenstriche und Symbolzeichen, Apostroph- und Akzentprüfung, Vollständigkeit mit benannter
Ausnahmeliste, und dazu die Varietätenprobe positiv wie negativ.

**Dieser Katalog ist von keinem Muttersprachler gelesen worden.** Das ist keine offene Aufgabe,
die jemand vergessen hat, sondern der gesperrte Entscheid E-17-5, Option a: die vier neuen
Sprachen entstehen maschinell und werden über das offene Community-Review korrigiert, das jede
App im Nextcloud App Store hat. Wer einen Fehler findet, meldet ihn als Issue im Repositorium
`street1983nk/nextcloud-search` oder schickt eine Änderung an dieser Tabelle; die nächste
Ausgabe nimmt ihn mit. Ein Muttersprachler-Gate ist ausdrücklich **nicht** gewählt worden und
wird hier auch nicht nachträglich eingeführt.

**Die Auslieferung wartet darauf nicht.** Das ist die Abwägung hinter dem Entscheid: ein
portugiesischer Katalog mit einzelnen unrunden Sätzen ist für einen portugiesischen Nutzer
besser als eine englische Oberfläche, und die Fehler, die eine Maschine macht, sind sichtbar und
korrigierbar. Der Unterschied zum französischen Katalog ist an dieser Stelle ausdrücklich
festgehalten: `docs/l10n-french.md` trägt eine Abnahme durch den Owner, einen französischen
Muttersprachler, datiert auf den 11.09., 19.09. und 24.09.2026. Diese Datei trägt eine Stufe
weniger, und sie sagt es, damit niemand die beiden für gleich abgenommen hält.

**Drei Stellen, an denen ein Muttersprachler zuerst hinsehen sollte.** Sie sind hier benannt,
damit das Review nicht bei null anfängt. Erstens die Wahl von `passagem` für den Lauf und die
daraus gebauten Fügungen `passagem de comparação` und `passagem em segundo plano`: sie sind
regelmäßig gebildet, aber lang, und ein Muttersprachler könnte `execução` oder eine
Umschreibung vorziehen. Zweitens `processo de tratamento` für den Worker, aus der romanischen
Linie übernommen. Drittens der Wechsel zwischen Infinitiv und höflicher Form der dritten
Person, der dem deutschen Bestand folgt und deshalb innerhalb einer Seite wechselt; wer ihn
vereinheitlichen will, muss zuerst den deutschen Katalog vereinheitlichen.

**Was ausdrücklich nicht zur Nachbesserung ansteht:** die drei Formen mit wortgleicher Form 1
und Form 2, und die Abweichung bei n gleich 0. Beides sieht nach einem Fehler aus und ist
keiner; der Abschnitt "Pluralformen" führt es aus, und wer es ändern will, widerlegt zuerst die
Messungen in `docs/l10n-catalogues.md`, Abschnitte 4 und 5.

**Stand dieser Datei:** alle 202 Zeilen der Spalte PT_PT sind am 25.09.2026 entstanden, keine
ist später hinzugekommen, und keine ist abgenommen. Die Spalte PT_BR trägt Plan 20-08 nach, mit
eigenem Datum und eigenem Vorbehalt. Kommt später ein Schlüssel dazu, gehört er in diese
Tabelle und in einen datierten Nachtrag darunter, aus demselben Grund, aus dem
`docs/l10n-french.md` seine Nachträge führt: eine Datei darf keine ungelesene Zeile
stillschweigend mittragen.
