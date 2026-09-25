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

**Stand dieser Datei: beide Spalten sind gefüllt.** Die Spalte PT_PT stammt aus Plan 20-07, die
Spalte PT_BR aus Plan 20-08, beide vom 25.09.2026, und jede trägt im Abschnitt "Abnahme" ihren
eigenen datierten Vorbehalt. Die Tabelle unten führt damit vier Spalten.

## Die Schlüsselmenge, aus der Datei gezählt

Nicht aus einem Dokument übernommen, sondern am 25.09.2026 mit `json.load` über
`php/l10n/de.json`, `php/l10n/pt_PT.json` und `php/l10n/pt_BR.json` gezählt; die Zeilen unter
den drei Schlüsselzahlen gelten für beide portugiesischen Dateien gleich:

| Größe | Wert |
|---|---:|
| Schlüssel in `de.json` | **202** |
| Schlüssel in `pt_PT.json` | **202** |
| Schlüssel in `pt_BR.json` | **202** |
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
Entscheide, die die Pläne 20-07 und 20-08 verlangen, stehen in den ersten sechs Zeilen, je
Varietät getrennt entschieden; die weiteren betreffen jeweils Dutzende Zeilen und gehörten
deshalb ebenso getroffen.

| Englisch | PT_PT | PT_BR | Warum |
|---|---|---|---|
| the backend | o serviço | o serviço | Derselbe Entscheid wie im Französischen (`le service`), Spanischen (`el servicio`), Italienischen (`il servizio`) und Niederländischen (`de dienst`), und in beiden Varietäten derselbe. Der Nutzer sieht einen Dienst, der antwortet oder nicht antwortet. `o backend` wäre sagbar, benennt aber ein Bauteil und keine Zusage. Wo der Eigenname gemeint ist, bleibt er stehen: `a aplicação externa "Findling Backend"` gegen `o aplicativo externo "Findling Backend"` |
| run (Lauf, Abgleichlauf, Hintergrundlauf) | a passagem, a passagem de comparação, a passagem em segundo plano | a execução, a execução de comparação, a execução em segundo plano | **Hier entscheiden die Varietäten verschieden.** `passagem` ist in Portugal ein Durchgang über einen Bestand und trägt dasselbe Bild wie `passage`, `pasada`, `passata` und `doorloop`. In Brasilien klingt `passagem` nach Fahrkarte oder Durchfahrt; für einen Lauf eines Programms sagt die brasilianische Oberfläche `execução`, und `a próxima execução` ist dort die gewöhnliche Fügung |
| worker | o processo de tratamento | o processo de indexação | **Ebenfalls verschieden entschieden.** Das europäische `processo de tratamento` folgt der romanischen Linie (`processus de traitement`, `proceso de tratamiento`). Im Brasilianischen ist `tratamento` für Datenverarbeitung ungewöhnlich; `processo de indexação` sagt dem Nutzer, was der Prozess tut, und kollidiert nicht mit `tarefa em segundo plano`. `trabalhador` wäre in beiden Varietäten der Mensch |
| index (Substantiv) | o índice | o índice | Ein gewöhnliches portugiesisches Wort, im Plural `índices`, in beiden Varietäten gleich |
| index (Verb), indexing | indexar, a indexação | indexar, a indexação | Die Formen, die beide portugiesischen Nextcloud-Oberflächen selbst führen |
| coverage | a cobertura | a cobertura | Die Zahl, die sagt, welcher Anteil der Dateien durchsuchbar ist. Wie im Spanischen, in beiden Varietäten gleich |
| file | o ficheiro, Plural `ficheiros` | o arquivo, Plural `arquivos` | **Der wichtigste Varietätenentscheid dieser Datei.** Das Wort steht in beiden Katalogen 60 mal (gezählt über alle Formen, ohne Groß- und Kleinschreibung), es ist also die Stelle, an der sich die beiden Kataloge am deutlichsten unterscheiden |
| user | o utilizador | o usuário | Der Katalog führt das Wort an einer Stelle, und diese eine Stelle ist die zweite Probe der Varietät |
| screen, page of an app | a página | a tela | Die dritte Probe, und sie hat einen Gegenstand, nur einen anderen als erwartet: kein Schlüssel spricht von einem Bildschirm, aber zwei sprechen von "dieser Seite" der Verwaltung. Die brasilianische Oberfläche nennt die Ansicht einer App `tela`, die europäische sagt dort `página` und gerade **nicht** `ecrã`. Wo eine Seite im Sinne der Seitenzählung gemeint ist (`Página anterior`, `Página %s`), sagen beide `página` |
| downloading | a transferir | baixando | **Kommt in beiden Katalogen nicht vor**, weil kein Satz von einem Download spricht. Die Zeile steht hier, damit der erste solche Satz nicht in der falschen Varietät hereinkommt |
| password | a palavra-passe | a senha | Ein Varietätenwort, das der Katalog wirklich führt, zweimal |
| trash bin | a reciclagem | a lixeira | Die Wortwahl der jeweiligen Nextcloud-Oberfläche für denselben Ort |
| log | o registo | o registro | Das Brasilianische schreibt das Wort mit dem zweiten r |
| spreadsheets | as folhas de cálculo | as planilhas | Anders als im Niederländischen ist dieser Dateityp-Filter in beiden Varietäten übersetzt und steht **nicht** in der Ausnahmeliste |
| full text hits | resultados de texto integral | resultados de texto completo | `texto integral` ist die europäische Fügung für die Volltextsuche, `texto completo` die brasilianische |
| container | o contentor | o contêiner | Das europäische Wort ist ein portugiesisches, das brasilianische die eingebürgerte Entlehnung mit Zirkumflex |
| settings | as definições | as configurações | Die Wortwahl der jeweiligen Nextcloud-Oberfläche |
| app | a aplicação | o aplicativo | Ebenso, samt dem Menüpunkt `Aplicações` gegen `Aplicativos` |
| save | guardar | salvar | Das Verb der Schaltfläche `Guardar regras` gegen `Salvar regras` |
| is answering, is running | está a responder, a funcionar | está respondendo, funcionando | Die Verlaufsform: Portugal bildet sie mit `a` und Infinitiv, Brasilien mit dem Gerundium. Sie steht in beiden Katalogen an rund einem Dutzend Stellen |
| background job | a tarefa em segundo plano | a tarefa em segundo plano | Die Wortwahl beider Oberflächen |
| storage | o armazenamento, o armazenamento externo | o armazenamento, o armazenamento externo | Der Vorgang und der Ort tragen dasselbe Wort; durchgezählt werden `armazenamentos` |
| folder | a pasta | a pasta | Und nicht `diretório`: beide Oberflächen sagen `pasta` |
| searchable, findable | pode ser pesquisado, encontrável pelo significado | pode ser pesquisado, encontrável pelo significado | Zwei Hälften derselben Aussage. Ein Eigenschaftswort `pesquisável` gibt es, es klingt aber technischer als der Satz, in dem es steht |
| text recognition | o reconhecimento de texto | o reconhecimento de texto | OCR bleibt als Abkürzung stehen, wo der Quellstring sie führt |
| Team Folders | Team Folders | Team Folders | Eigenname der Nextcloud-Funktion, unübersetzt, mit portugiesischem Artikel davor (`as Team Folders`) |
| remedy (die Abhilfe, oft nur `None.`) | `Nenhuma.` | `Nenhuma.` | Weibliche Form, weil das weggelassene Hauptwort die Abhilfe ist (`nenhuma solução`). Dasselbe Muster wie das spanische `Ninguna.` |
| invoice (Platzhalter im Suchfeld) | fatura | nota fiscal | Das Beispiel soll wie eine echte Suche aussehen, und in Brasilien heißt das Dokument, das man sucht, `nota fiscal` |

**Die vier Proben aus Plan 20-07, jetzt vollständig.** Sie sind der Gegenstand, an dem sich
zeigt, dass die zwei portugiesischen Kataloge wirklich zwei sind und nicht einer mit zwei
Dateinamen:

| Bedeutung | PT_PT | PT_BR | in den Katalogen |
|---|---|---|---|
| file | `ficheiro` | `arquivo` | je 60 mal |
| user | `utilizador` | `usuário` | je 1 mal |
| screen | `ecrã` (dort, wo die Seite gemeint ist: `página`) | `tela` | `tela` 2 mal, `ecrã` 0 mal |
| downloading | `a transferir` | `baixando` | kommt nicht vor |

Die Proben sind nicht nur hier aufgeschrieben, sondern ein Gate. Die Schlüssel, deren zwei
Wortlaute sich unterscheiden **müssen**, stehen als benannte Liste
`PORTUGUESE_WORDINGS_THAT_MUST_DIFFER` in `backend/tests/test_admin_ui_contract.py`, jeder mit
seinem Wortpaar, und `test_the_two_portuguese_catalogues_are_two` fällt, sobald einer dieser
Schlüssel in beiden Dateien denselben Wortlaut trägt. Die Liste ist dieselbe wie hier, damit Doku
und Gate nicht auseinanderlaufen:

| Schlüssel | Wortpaar |
|---|---|
| `File contents` | `ficheiros` gegen `arquivos` |
| `Files` | `Ficheiros` gegen `Arquivos` |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | `utilizadores` gegen `usuários` |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | `página` gegen `tela` |
| `Password protected` | `palavra-passe` gegen `senha` |
| `In the trash bin` | `reciclagem` gegen `lixeira` |
| `The backend could not start Tesseract. Check the log of the External App.` | `registo` gegen `registro` |
| `Spreadsheets` | `Folhas de cálculo` gegen `Planilhas` |
| `The model is in memory, the semantic search is answering.` | `está a responder` gegen `está respondendo` |
| `The semantic half is switched off in the settings of the container.` | `definições do contentor` gegen `configurações do contêiner` |
| `Save rules` | `Guardar` gegen `Salvar` |

Eine Liste und ausdrücklich **keine** Mindestzahl unterschiedlicher Werte: eine Zahl wäre mit
beliebigen zufälligen Abweichungen erfüllbar, während die Alltagswörter europäisch blieben. Und
kein Textgleichheits-Gate in irgendeiner Richtung: 72 der 202 Werte sind in beiden Varietäten
gleich, gemessen am 25.09.2026, und das ist richtig, wo die Sprache gleich ist. Die Gegenprobe
ist gefahren: mit einer Kopie von `pt_PT.json` an der Stelle von `pt_BR.json` meldet das Gate
elf Funde, einen je Schlüssel der Liste.

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

**Der brasilianische Katalog folgt demselben Muster, mit der brasilianischen Anrede.** Wo Deutsch
den Infinitiv führt, steht auch dort der Infinitiv (`Recriá-lo com "occ findling:index --restart"`),
wo Deutsch siezt, die Befehlsform der dritten Person (`Aumente o valor em "Maior arquivo a ler".`,
`Refine a pesquisa para vê-los.`). Wo ein Satz den Nutzer als Person nennt, steht `você`
(`os arquivos que você pediu para o Findling não tocar`, `nenhum que você possa abrir`), wo der
europäische Katalog `lhe` und die Umschreibung mit `sua` führt. Die Schaltflächen tragen auch
hier den Infinitiv: `Salvar regras`, `Adicionar exclusão`, `Tentar de novo`.

## Typografie

Jede Regel unten ist maschinell geprüft, das Ergebnis steht im Abschnitt "Maschinelle
Prüfungen".

- **Kein typographischer Apostroph** (U+2019), nirgends. Das Portugiesische setzt den Apostroph
  im Alltag kaum, dieser Katalog kommt ohne eine einzige Apostrophstelle aus, und die Regel
  steht trotzdem hier, weil eine maschinelle Übersetzung das Zeichen gern aus dem englischen
  Quelltext mitschleppt. Gezählt über alle vier portugiesischen Dateien und über dieses
  Dokument: 0 Vorkommen.
- **Echte Akzente sind Pflicht.** `ç`, `ã`, `õ`, `é`, `í`, `ó` stehen so da, wie die Sprache sie
  schreibt, und werden nicht durch ASCII ersetzt. Das ist nicht dieselbe Frage wie die
  Projektregel für Umlaute: die verbietet Umlaute in Bezeichnern und Code, nicht in den
  ausgelieferten Wortlauten einer Sprache. Der Bindestrich in `palavra-passe` und in
  `recém-ligados` ist der gewöhnliche ASCII-Bindestrich (U+002D).
- **Die enklitischen Pronomen tragen ihren Bindestrich.** `recolhe-o`, `aplica-as`,
  `carregá-lo`, `vai-se preenchendo`. Das ist europäisches Portugiesisch und zugleich ein
  Unterschied zum brasilianischen, das die Pronomen gern voranstellt (`o recolhe`). Wer die
  Bindestriche für Tippfehler hält, liest hier, dass sie keine sind. Der brasilianische Katalog
  stellt das Pronomen deshalb vor das Verb oder baut den Satz um (`e o carrega novamente`,
  `vai pegá-lo`); wo das Pronomen am Infinitiv hängt, trägt es auch dort den Bindestrich.
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
- **Im brasilianischen Katalog steht der Suchbegriff in doppelten Anführungszeichen**, also
  `“%s”` (U+201C und U+201D): `Resultados para “%s”`, `Nenhum arquivo contém “%s”`. Das ist
  die brasilianische Schreibweise; Winkelanführungszeichen sind in Brasilien ungewöhnlich. Beide
  Zeichen stehen nicht auf der Sperrliste dieser Datei, der deutsche Bestand führt das erste
  davon ohnehin (`„%s“`). Bezeichner und Befehle stehen auch hier in geraden
  ASCII-Anführungszeichen.
- **Die Platzhalter sind die des Schlüssels**, in Art und Zahl. `%1$s in %2$s` bleibt
  `%1$s em %2$s` und wird niemals `%s em %s`.
- **Ein literales Prozentzeichen wird `%%` geschrieben.** Der Grund ist gemessen und nicht
  befürchtet: Nextcloud reicht jeden Katalogwert durch `vsprintf`, ein nacktes `%` wirft dort
  einen `ValueError`, und die Seite bleibt weiß. Für das Portugiesische ist das keine
  Formalie, denn die Sprache setzt das Zeichen mit Leerzeichen davor ("50 %"), und genau dieses
  Leerzeichen macht die Direktive unkenntlich. **In keinem der beiden Kataloge steht ein
  einziges Prozentzeichen dieser Art**, auch kein verdoppeltes: wo der deutsche Satz "100 Prozent"
  sagt, sagen beide portugiesischen `cem por cento`. Umformulieren war billiger als retten. Die
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

**`pt_BR`: dieselbe Regel, dieselben drei Formen, und die Kerndatei macht es anders.** Die Regel
für `pt_BR` ist zeichengleich die von `pt_PT` oben und steht so in `php/l10n/pt_BR.json`, in
`php/l10n/pt_BR.js`, in `docs/l10n-catalogues.md`, Abschnitt 3, und in `PLURAL_FORM_OF["pt_BR"]`.
Die fünf Pluralwerte tragen drei Formen, Form 1 und Form 2 wortgleich als gewöhnlicher Plural
(`%n minuto / %n minutos / %n minutos`), und `FORM_COUNT_OF["pt_BR"]` ist 3.

Die Kerndatei der Nextcloud selbst, `core/l10n/pt_BR.json`, schreibt auf Index 1 die
**Millionenform** (`"%n de resultados"`), und zwar in allen neun Pluralwerten. Auf der PHP-Seite
ist das gemessen worden und nicht hergeleitet: der Kern rendert dem brasilianischen Nutzer bei n
gleich 2 den Satz `2 de resultados`. **Findling folgt ihr ausdrücklich nicht.** Keiner der fünf
Pluralschlüssel (Minuten, Stunden, Tage, weitere Treffer, Sperrsekunden) zählt je eine Million,
und dieselbe PHP-Tabelle, die dem Kern `2 de resultados` beschert, würde Findling bei jeder Zahl
über eins einen falschen Satz bescheren. Der Beweis steht in `docs/l10n-catalogues.md`,
Abschnitt 4, und wird hier nicht neu geführt. Die benannte Abweichung bei n gleich 0 hat `pt_BR`
nicht, wie der Absatz darüber sagt.

In der Tabelle unten stehen die Formen eines Pluralschlüssels durch ` / ` getrennt in einer
Zelle, zuerst der Singular, wie es der französische, spanische, italienische und
niederländische Bestand machen. Die deutsche Spalte führt dort zwei Formen, die beiden
portugiesischen je drei.

## Die Tabelle

Alle vier Spalten sind aus `php/l10n/de.json`, `php/l10n/pt_PT.json` und `php/l10n/pt_BR.json`
erzeugt und nicht abgetippt; die Reihenfolge ist die der Dateien. Die Spaltennamen sind ASCII, weil sie
Vertragsbezeichner sind und die Projektregel echte Umlaute der deutschen Prosa vorbehält. Der
Schlüssel ist der englische Quellstring: er steht wörtlich so im Template, läuft dort durch
`$l->t()` und ist in jeder Katalogdatei der Schlüssel der Übersetzung.

Kein Wert und kein Schlüssel kann ein Pipe-Zeichen enthalten, dafür sorgt `scan_pipe_character`
aus Plan 20-03. Diese Tabelle kann also nicht an einem Wortlaut zerbrechen.

**Die Tabelle trägt vier Spalten, und die vierte ist gefüllt.** Plan 20-07 hat sie mit drei
Spalten angelegt und die vierte nicht leer vorgehalten; Plan 20-08 hat sie mit den
brasilianischen Wortlauten danebengesetzt, in einem Durchgang und mechanisch, nachdem dieselbe
Erzeugung die dreispaltige Fassung zeichengleich reproduziert hatte (204 von 204 Zeilen).

| Schluessel | DE | PT_PT | PT_BR |
|---|---|---|---|
| `Findling` | Findling | Findling | Findling |
| `File contents` | Dateiinhalte | Conteúdo dos ficheiros | Conteúdo dos arquivos |
| `Search coverage` | Deckungsgrad der Suche | Cobertura da pesquisa | Cobertura da pesquisa |
| `%1$s of %2$s indexable files are searchable` | %1$s von %2$s indexierbaren Dateien sind durchsuchbar | %1$s de %2$s ficheiros indexáveis podem ser encontrados pela pesquisa | %1$s de %2$s arquivos indexáveis podem ser encontrados pela pesquisa |
| `The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.` | Der Anteil ist im Moment nicht berechenbar, weil das Backend nicht antwortet. %s Dateien dieser Instanz sind indexierbar. | A proporção não pode ser calculada neste momento porque o serviço não responde. %s ficheiros desta instância são indexáveis. | A proporção não pode ser calculada no momento porque o serviço não responde. %s arquivos desta instância são indexáveis. |
| `Deliberately left out: %s` | Bewusst ausgelassen: %s | Deixados de fora de propósito: %s | Deixados de fora de propósito: %s |
| `Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.` | Diese Dateien sind zu groß, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen. Sie stehen nicht im Nenner darüber, damit der Deckungsgrad 100 Prozent erreichen kann. | Esses ficheiros são demasiado grandes, de um tipo que o Findling não lê, ou excluídos por uma regra. Não estão no denominador acima, de modo que a cobertura pode chegar a cem por cento. | Esses arquivos são grandes demais, de um tipo que o Findling não lê, ou excluídos por uma regra. Eles não entram no denominador acima, de modo que a cobertura pode chegar a cem por cento. |
| `Provisional figure, %1$s of %2$s storages have been counted through.` | Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt. | Valor provisório, foram contados %1$s de %2$s armazenamentos. | Valor provisório, %1$s de %2$s armazenamentos já foram contados. |
| `Findable by meaning` | Auffindbar nach Bedeutung | Encontrável pelo significado | Encontrável pelo significado |
| `%1$s of %2$s indexable files can also be found by meaning` | %1$s von %2$s indexierbaren Dateien sind auch nach Bedeutung auffindbar | %1$s de %2$s ficheiros indexáveis também podem ser encontrados pelo significado | %1$s de %2$s arquivos indexáveis também podem ser encontrados pelo significado |
| `The semantic share cannot be worked out right now. The backend does not answer, or it does not report this figure yet.` | Der semantische Anteil ist im Moment nicht berechenbar. Das Backend antwortet nicht, oder es meldet diese Zahl noch nicht. | A proporção semântica não pode ser calculada neste momento. O serviço não responde, ou ainda não comunica este valor. | A proporção semântica não pode ser calculada no momento. O serviço não responde, ou ainda não informa este valor. |
| `The model is in memory, the semantic search is answering.` | Das Modell liegt im Speicher, die semantische Suche antwortet. | O modelo está em memória, a pesquisa semântica está a responder. | O modelo está na memória, a pesquisa semântica está respondendo. |
| `The model is read when it is first needed. That is the normal state.` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | O modelo é carregado na primeira vez que é preciso. Esse é o estado normal. | O modelo é carregado na primeira vez em que é necessário. Esse é o estado normal. |
| `The semantic half is switched off in the settings of the container.` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | A metade semântica está desligada nas definições do contentor. | A metade semântica está desativada nas configurações do contêiner. |
| `There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.` | In diesem Abbild liegt kein Modell. Die Suche liefert weiterhin Volltexttreffer, die semantische Hälfte bleibt leer. | Nesta imagem não há nenhum modelo. A pesquisa continua a responder com resultados de texto integral, a metade semântica fica vazia. | Não há nenhum modelo nesta imagem. A pesquisa continua respondendo com resultados de texto completo, a metade semântica fica vazia. |
| `Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.` | Das Laden des Modells ist einmal gescheitert und wird in Kürze erneut versucht. Bis dahin liefert die Suche Volltexttreffer. | O carregamento do modelo falhou uma vez e será tentado de novo em breve. Até lá a pesquisa responde com resultados de texto integral. | O carregamento do modelo falhou uma vez e será tentado novamente em breve. Até lá a pesquisa responde com resultados de texto completo. |
| `The model was released to save memory. The next search answers with full text hits and loads it again in the background.` | Das Modell wurde zum Sparen freigegeben. Die nächste Suche antwortet mit Volltexttreffern und lädt es im Hintergrund nach. | O modelo foi libertado para poupar memória. A pesquisa seguinte responde com resultados de texto integral e volta a carregá-lo em segundo plano. | O modelo foi liberado para economizar memória. A próxima pesquisa responde com resultados de texto completo e o carrega novamente em segundo plano. |
| `This container does not report the state of the model yet.` | Dieser Container meldet den Zustand des Modells noch nicht. | Este contentor ainda não comunica o estado do modelo. | Este contêiner ainda não informa o estado do modelo. |
| `The full text search covers every indexed document. The semantic search covers the beginning of each document, and this second figure fills up after the first index has finished.` | Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem Erstindex nach. | A pesquisa de texto integral abrange todos os documentos indexados. A pesquisa semântica abrange o início de cada documento, e este segundo valor vai-se preenchendo depois de terminar a primeira indexação. | A pesquisa de texto completo abrange todos os documentos indexados. A pesquisa semântica abrange o início de cada documento, e este segundo valor vai sendo preenchido depois que a primeira indexação termina. |
| `Up to date, last checked %s` | Aktuell, letzte Prüfung %s | Atualizado, última verificação %s | Atualizado, última verificação %s |
| `Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.` | Die Indexierung kommt seit %s nicht voran. In dieser Zeit hat weder ein Hintergrundauftrag noch das Backend etwas fertiggestellt. | A indexação não avança há %s. Nesse tempo nem uma tarefa em segundo plano nem o serviço terminaram nada. | A indexação não avança há %s. Nesse tempo nem uma tarefa em segundo plano nem o serviço concluíram nada. |
| `No background job of this app has run yet. Background jobs may not be running.` | Noch kein Hintergrundauftrag dieser App ist gelaufen. Möglicherweise laufen die Hintergrundaufträge nicht. | Ainda não foi executada nenhuma tarefa em segundo plano desta aplicação. É possível que as tarefas em segundo plano não estejam a funcionar. | Nenhuma tarefa em segundo plano deste aplicativo foi executada ainda. É possível que as tarefas em segundo plano não estejam funcionando. |
| `Indexing is running.` | Die Indexierung läuft. | A indexação está em curso. | A indexação está em andamento. |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | Die Zahlen konnten nicht aktualisiert werden. Die Werte unten sind die letzten, die diese Seite bekommen hat. | Não foi possível atualizar os números. Os valores abaixo são os últimos que esta página recebeu. | Não foi possível atualizar os números. Os valores abaixo são os últimos que esta tela recebeu. |
| `_%n minute_::_%n minutes_` | %n Minute / %n Minuten | %n minuto / %n minutos / %n minutos | %n minuto / %n minutos / %n minutos |
| `_%n hour_::_%n hours_` | %n Stunde / %n Stunden | %n hora / %n horas / %n horas | %n hora / %n horas / %n horas |
| `_%n day_::_%n days_` | %n Tag / %n Tage | %n dia / %n dias / %n dias | %n dia / %n dias / %n dias |
| `Waiting in the queue` | Wartet in der Warteschlange | À espera na fila | Aguardando na fila |
| `Being processed` | Wird gerade verarbeitet | A ser processado | Sendo processado |
| `Indexed` | Indexiert | Indexado | Indexado |
| `Skipped` | Übersprungen | Ignorado | Ignorado |
| `Failed` | Fehlgeschlagen | Falhado | Falhou |
| `Excluded` | Ausgeschlossen | Excluído | Excluído |
| `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst. | Os ficheiros excluídos não contam para a cobertura. São os ficheiros que o Findling não toca por indicação sua. | Os arquivos excluídos não contam para a cobertura. São os arquivos que você pediu para o Findling não tocar. |
| `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter. | Resta pouco espaço em disco. A indexação está em pausa para que o índice se mantenha intacto. A pesquisa continua a funcionar. | Resta pouco espaço em disco. A indexação está pausada para que o índice continue intacto. A pesquisa continua funcionando. |
| `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer. | O índice foi construído com uma análise de texto mais antiga. Reconstruí-lo com "occ findling:index --restart", caso contrário continuarão a faltar resultados. | O índice foi criado com uma análise de texto mais antiga. Recriá-lo com "occ findling:index --restart", caso contrário alguns resultados continuarão faltando. |
| `Findling is rebuilding its index so that the newly switched on languages can be searched. %1$s of %2$s documents have been carried over. Search keeps answering while this runs, and there is nothing to start or to restart.` | Findling baut seinen Index neu auf, damit die neu eingeschalteten Sprachen durchsucht werden können. %1$s von %2$s Dokumenten sind übertragen. Die Suche antwortet währenddessen weiter, und es gibt nichts zu starten oder neu zu starten. | O Findling está a reconstruir o seu índice para que os idiomas recém-ligados possam ser pesquisados. Já foram migrados %1$s de %2$s documentos. A pesquisa continua a responder entretanto, e não há nada para iniciar nem para reiniciar. | O Findling está recriando o seu índice para que os idiomas recém-ativados possam ser pesquisados. %1$s de %2$s documentos já foram migrados. A pesquisa continua respondendo enquanto isso, e não há nada para iniciar nem para reiniciar. |
| `Findling wants to rebuild its index for the newly switched on languages and there is not enough room: %s more are needed next to what the index already uses. Free that much, or set the environment variable FINDLING_REBUILD_FALLBACK=fullreindex to have the backend read the files again instead. Either way the backend only tries again after a restart of the container.` | Findling möchte seinen Index für die neu eingeschalteten Sprachen neu aufbauen, und es ist nicht genug Platz: %s fehlen zusätzlich zu dem, was der Index bereits belegt. Geben Sie so viel frei, oder setzen Sie die Umgebungsvariable FINDLING_REBUILD_FALLBACK=fullreindex, damit das Backend die Dateien stattdessen neu liest. In beiden Fällen versucht es das Backend erst nach einem Neustart des Containers erneut. | O Findling quer reconstruir o seu índice para os idiomas recém-ligados e não há espaço suficiente: são precisos mais %s além do que o índice já ocupa. Liberte essa quantidade, ou defina a variável de ambiente FINDLING_REBUILD_FALLBACK=fullreindex para que o serviço volte a ler os ficheiros em vez disso. Em qualquer dos casos o serviço só tenta de novo depois de reiniciar o contentor. | O Findling quer recriar o seu índice para os idiomas recém-ativados e não há espaço suficiente: são necessários mais %s além do que o índice já ocupa. Libere esse espaço, ou defina a variável de ambiente FINDLING_REBUILD_FALLBACK=fullreindex para que o serviço leia os arquivos novamente em vez disso. Em qualquer caso o serviço só tenta de novo depois de reiniciar o contêiner. |
| `Languages of the index: %1$s switched on, %2$s with text in the index.` | Sprachen des Index: %1$s eingeschaltet, %2$s mit Text im Index. | Idiomas do índice: %1$s ligados, %2$s com texto no índice. | Idiomas do índice: %1$s ativados, %2$s com texto no índice. |
| `No numbers yet` | Noch keine Zahlen | Ainda sem valores | Ainda sem valores |
| `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` | Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen. | A primeira passagem de indexação ainda não terminou. O Findling arrancou sozinho, não há nada a configurar. | A primeira execução de indexação ainda não terminou. O Findling iniciou sozinho, não há nada para configurar. |
| `The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.` | Die beiden Hälften von Findling melden unterschiedliche Versionen: diese App ist %1$s, das Backend ist %2$s. Solange sie nicht zusammenpassen, antwortet die Suche ohne Ergebnisse, weil eine falsche Antwort ohne Hinweis schlimmer wäre. Beide Hälften auf dieselbe Version bringen. | As duas metades do Findling comunicam versões diferentes: esta aplicação é %1$s, o serviço é %2$s. Enquanto não coincidirem, a pesquisa responde sem resultados, porque uma resposta errada sem aviso seria pior. Ponha ambas as metades na mesma versão. | As duas metades do Findling informam versões diferentes: este aplicativo é %1$s, o serviço é %2$s. Enquanto elas não coincidirem, a pesquisa responde sem resultados, porque uma resposta errada sem aviso seria pior. Coloque as duas metades na mesma versão. |
| `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` | Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist. | O serviço do Findling não responde. Os números abaixo são os últimos que esta aplicação registou. Verifique em Aplicações se a aplicação externa "Findling Backend" está instalada e em funcionamento. | O serviço do Findling não responde. Os números abaixo são os últimos que este aplicativo registrou. Verifique em Aplicativos se o aplicativo externo "Findling Backend" está instalado e em execução. |
| `Estimate for the first index` | Schätzung für den Erstindex | Estimativa para a primeira indexação | Estimativa para a primeira indexação |
| `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | %1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index. | %1$s ficheiros, %2$s deles precisam de OCR. Cerca de %3$s e cerca de %4$s de índice. | %1$s arquivos, %2$s deles precisam de OCR. Cerca de %3$s e cerca de %4$s de índice. |
| `%1$s files, %2$s of them need OCR.` | %1$s Dateien, davon %2$s mit OCR. | %1$s ficheiros, %2$s deles precisam de OCR. | %1$s arquivos, %2$s deles precisam de OCR. |
| `%1$s to %2$s` | %1$s bis %2$s | %1$s a %2$s | %1$s a %2$s |
| `Counting the files, this takes a moment.` | Die Dateien werden gezählt, das dauert einen Moment. | Os ficheiros estão a ser contados, isto demora um momento. | Contando os arquivos, isso leva um momento. |
| `Startup value, being measured.` | Startwert, wird gemessen. | Valor inicial, a ser medido. | Valor inicial, sendo medido. |
| `The space needed is measured as soon as the first documents are in the index.` | Der Platzbedarf wird gemessen, sobald die ersten Dokumente im Index sind. | O espaço necessário é medido assim que os primeiros documentos estiverem no índice. | O espaço necessário é medido assim que os primeiros documentos estiverem no índice. |
| `The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.` | Der Index braucht voraussichtlich mehr Platz, als auf diesem Datenträger frei ist. Die Indexierung pausiert, bevor der Datenträger voll wird, und die Suche funktioniert weiter. | Prevê-se que o índice precise de mais espaço do que o que está livre neste volume. A indexação faz uma pausa antes de o volume encher, e a pesquisa continua a funcionar. | A previsão é de que o índice precise de mais espaço do que este volume tem livre. A indexação é pausada antes de o volume encher, e a pesquisa continua funcionando. |
| `Findling does not wait for a confirmation. The first index has already started.` | Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits. | O Findling não espera por nenhuma confirmação. A primeira indexação já começou. | O Findling não espera por nenhuma confirmação. A primeira indexação já começou. |
| `Files that were not indexed` | Nicht indexierte Dateien | Ficheiros que não foram indexados | Arquivos que não foram indexados |
| `Files that were not indexed, grouped by reason` | Nicht indexierte Dateien, nach Grund gruppiert | Ficheiros que não foram indexados, agrupados por motivo | Arquivos que não foram indexados, agrupados por motivo |
| `Every file was indexed. Nothing was skipped and nothing failed.` | Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen. | Todos os ficheiros foram indexados. Nada foi ignorado e nada falhou. | Todos os arquivos foram indexados. Nada foi ignorado e nada falhou. |
| `Reason` | Grund | Motivo | Motivo |
| `Files` | Dateien | Ficheiros | Arquivos |
| `State` | Zustand | Estado | Estado |
| `Show example paths` | Beispielpfade anzeigen | Mostrar caminhos de exemplo | Mostrar caminhos de exemplo |
| `Hide example paths` | Beispielpfade verbergen | Ocultar caminhos de exemplo | Ocultar caminhos de exemplo |
| `_and %n more_::_and %n more_` | und %n weitere / und %n weitere | e mais %n / e mais %n / e mais %n | e mais %n / e mais %n / e mais %n |
| `File no longer exists (ID %s)` | Datei existiert nicht mehr (ID %s) | O ficheiro já não existe (ID %s) | O arquivo não existe mais (ID %s) |
| `%s (in the trash bin)` | %s (im Papierkorb) | %s (na reciclagem) | %s (na lixeira) |
| `Indexed, text truncated` | Indexiert, Text gekürzt | Indexado, texto cortado | Indexado, texto cortado |
| `Unknown reason (%s)` | Unbekannter Grund (%s) | Motivo desconhecido (%s) | Motivo desconhecido (%s) |
| `This app does not know this code. It may come from a newer version of the backend.` | Diese App kennt diesen Code nicht. Er kann von einer neueren Fassung des Backends kommen. | Esta aplicação não conhece este código. Pode vir de uma versão mais recente do serviço. | Este aplicativo não conhece este código. Ele pode vir de uma versão mais recente do serviço. |
| `Text truncated` | Text gekürzt | Texto cortado | Texto cortado |
| `The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.` | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. | O início do documento pode ser pesquisado, o resto não. Os documentos muito longos são cortados de propósito. | O início do documento pode ser pesquisado, o resto não. Documentos muito longos são cortados de propósito. |
| `Too large` | Zu groß | Demasiado grande | Grande demais |
| `Raise the value under "Largest file to read".` | Den Wert unter "Größte zu lesende Datei" erhöhen. | Aumente o valor em "Maior ficheiro a ler". | Aumente o valor em "Maior arquivo a ler". |
| `File type not supported` | Dateityp nicht unterstützt | Tipo de ficheiro não suportado | Tipo de arquivo não suportado |
| `None. Findling reads PDF, Office, OpenDocument, text and images.` | Keine. Findling liest PDF, Office, OpenDocument, Text und Bilder. | Nenhuma. O Findling lê PDF, Office, OpenDocument, texto e imagens. | Nenhuma. O Findling lê PDF, Office, OpenDocument, texto e imagens. |
| `Password protected` | Passwortgeschützt | Protegido por palavra-passe | Protegido por senha |
| `None. Without the password the content cannot be read.` | Keine. Ohne Passwort ist der Inhalt nicht lesbar. | Nenhuma. Sem a palavra-passe não é possível ler o conteúdo. | Nenhuma. Sem a senha não é possível ler o conteúdo. |
| `No text in the document` | Kein Text im Dokument | Sem texto no documento | Sem texto no documento |
| `None. The document carries neither a text layer nor recognisable writing.` | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. | Nenhuma. O documento não tem camada de texto nem escrita reconhecível. | Nenhuma. O documento não tem camada de texto nem escrita reconhecível. |
| `No text content` | Kein Textinhalt | Sem conteúdo de texto | Sem conteúdo de texto |
| `None. The file is readable but carries no text.` | Keine. Die Datei ist lesbar, enthält aber keinen Text. | Nenhuma. O ficheiro pode ser lido, mas não tem texto. | Nenhuma. O arquivo pode ser lido, mas não tem texto. |
| `Spreadsheet too large` | Tabelle zu groß | Folha de cálculo demasiado grande | Planilha grande demais |
| `None. Very large spreadsheets are skipped so the container does not fall over.` | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. | Nenhuma. As folhas de cálculo muito grandes são ignoradas para que o contentor não caia. | Nenhuma. Planilhas muito grandes são ignoradas para que o contêiner não caia. |
| `File no longer present` | Datei nicht mehr vorhanden | O ficheiro já não está presente | O arquivo não está mais presente |
| `None. The file was already deleted or moved when it was read.` | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. | Nenhuma. O ficheiro já tinha sido apagado ou movido quando foi lido. | Nenhuma. O arquivo já tinha sido apagado ou movido quando foi lido. |
| `Image without recognisable writing` | Bild ohne erkennbare Schrift | Imagem sem escrita reconhecível | Imagem sem escrita reconhecível |
| `None.` | Keine. | Nenhuma. | Nenhuma. |
| `Excluded by a rule` | Durch Regel ausgeschlossen | Excluído por uma regra | Excluído por uma regra |
| `Remove the matching entry under "Excluded folders".` | Den passenden Eintrag unter "Ausgeschlossene Ordner" entfernen. | Retire a entrada correspondente em "Pastas excluídas". | Remova a entrada correspondente em "Pastas excluídas". |
| `File is empty` | Datei ist leer | O ficheiro está vazio | O arquivo está vazio |
| `None. The file has 0 bytes.` | Keine. Die Datei hat 0 Byte. | Nenhuma. O ficheiro tem 0 bytes. | Nenhuma. O arquivo tem 0 bytes. |
| `File damaged` | Datei beschädigt | Ficheiro danificado | Arquivo danificado |
| `Check the file outside of Nextcloud and upload it again.` | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. | Verifique o ficheiro fora do Nextcloud e volte a carregá-lo. | Verifique o arquivo fora do Nextcloud e envie-o novamente. |
| `Document structure faulty` | Dokumentstruktur fehlerhaft | Estrutura do documento defeituosa | Estrutura do documento com defeito |
| `Open the document in the program it came from and save it again.` | Das Dokument im Ursprungsprogramm öffnen und neu speichern. | Abra o documento no programa de onde veio e volte a guardá-lo. | Abra o documento no programa de origem e salve-o novamente. |
| `Character set not recognised` | Zeichensatz nicht erkannt | Conjunto de caracteres não reconhecido | Conjunto de caracteres não reconhecido |
| `Save the file as UTF-8 and upload it again.` | Die Datei als UTF-8 speichern und neu hochladen. | Guarde o ficheiro como UTF-8 e volte a carregá-lo. | Salve o arquivo como UTF-8 e envie-o novamente. |
| `Timed out while reading` | Zeitüberschreitung beim Lesen | Tempo de espera esgotado durante a leitura | Tempo esgotado durante a leitura |
| `The next run tries again.` | Wird beim nächsten Lauf erneut versucht. | A próxima passagem tenta de novo. | A próxima execução tenta de novo. |
| `Not enough memory while reading` | Zu wenig Speicher beim Lesen | Memória insuficiente durante a leitura | Memória insuficiente durante a leitura |
| `The next run tries again. If it happens again, lower the size cap.` | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung den Größen-Cap senken. | A próxima passagem tenta de novo. Se voltar a acontecer, baixe o limite de tamanho. | A próxima execução tenta de novo. Se acontecer outra vez, reduza o limite de tamanho. |
| `File was not retrievable` | Datei war nicht abrufbar | Não foi possível obter o ficheiro | Não foi possível obter o arquivo |
| `Stuck repeatedly` | Mehrfach hängen geblieben | Encravado várias vezes | Travou várias vezes |
| `Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.` | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. | O Findling não volta a tentar este ficheiro. Use a consulta para verificar se ele abre fora do Nextcloud. | O Findling não tenta mais este arquivo. Use a consulta para verificar se ele abre fora do Nextcloud. |
| `Text recognition failed` | Texterkennung fehlgeschlagen | O reconhecimento de texto falhou | O reconhecimento de texto falhou |
| `Text recognition not available` | Texterkennung nicht verfügbar | Reconhecimento de texto não disponível | Reconhecimento de texto indisponível |
| `The backend could not start Tesseract. Check the log of the External App.` | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. | O serviço não conseguiu iniciar o Tesseract. Verifique o registo da aplicação externa. | O serviço não conseguiu iniciar o Tesseract. Verifique o registro do aplicativo externo. |
| `Look up one file` | Einzelne Datei prüfen | Consultar um ficheiro | Consultar um arquivo |
| `Path or file ID` | Pfad oder Datei-ID | Caminho ou ID do ficheiro | Caminho ou ID do arquivo |
| `A path as Nextcloud stores it, or the numeric ID from the list above.` | Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben. | Um caminho tal como o Nextcloud o guarda, ou o número da lista acima. | Um caminho como o Nextcloud o armazena, ou o número da lista acima. |
| `Look up file` | Datei prüfen | Consultar ficheiro | Consultar arquivo |
| `Looking up a single file needs JavaScript. Everything above stays complete without it.` | Die Einzelprüfung braucht JavaScript. Alles darüber bleibt auch ohne vollständig lesbar. | A consulta de um único ficheiro precisa de JavaScript. Tudo o que está acima continua completo sem ele. | A consulta de um único arquivo precisa de JavaScript. Tudo o que está acima continua completo sem ele. |
| `No file at this path, and no file with this ID.` | Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID. | Não há nenhum ficheiro neste caminho, nem nenhum ficheiro com este ID. | Não há nenhum arquivo neste caminho, nem nenhum arquivo com este ID. |
| `Not seen yet` | Noch nicht gesehen | Ainda não visto | Ainda não visto |
| `State unknown right now` | Zustand im Moment unbekannt | Estado desconhecido neste momento | Estado desconhecido no momento |
| `File ID: %s` | Datei-ID: %s | ID do ficheiro: %s | ID do arquivo: %s |
| `Last checked %s` | Zuletzt geprüft: %s | Última verificação: %s | Última verificação: %s |
| `The lookup did not work. Nothing about this file has changed.` | Die Prüfung hat nicht funktioniert. An dieser Datei hat sich nichts geändert. | A consulta não funcionou. Neste ficheiro nada mudou. | A consulta não funcionou. Nada mudou neste arquivo. |
| `The state of this file is unknown right now because the backend does not answer.` | Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet. | O estado deste ficheiro é desconhecido neste momento porque o serviço não responde. | O estado deste arquivo é desconhecido no momento porque o serviço não responde. |
| `This file has not reached the queue. The next comparison run picks it up.` | Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab. | Este ficheiro ainda não chegou à fila. A próxima passagem de comparação recolhe-o. | Este arquivo ainda não chegou à fila. A próxima execução de comparação vai pegá-lo. |
| `It was indexed before and is recorded again on the next comparison run.` | Sie war vorher indexiert und wird beim nächsten Abgleichlauf neu erfasst. | Estava indexado antes e volta a ser registado na próxima passagem de comparação. | Ele estava indexado antes e volta a ser registrado na próxima execução de comparação. |
| `This file was indexed and has since been deleted. It is out of the index with it.` | Diese Datei war indexiert und ist inzwischen gelöscht. Damit ist sie auch aus dem Index heraus. | Este ficheiro estava indexado e entretanto foi apagado. Com isso também saiu do índice. | Este arquivo estava indexado e depois foi apagado. Com isso ele também saiu do índice. |
| `In the trash bin` | Im Papierkorb | Na reciclagem | Na lixeira |
| `Restore the file. The next comparison run picks it up.` | Die Datei wiederherstellen. Der nächste Abgleichlauf holt sie ab. | Restaure o ficheiro. A próxima passagem de comparação recolhe-o. | Restaure o arquivo. A próxima execução de comparação vai pegá-lo. |
| `Storage is not indexed` | Speicherort wird nicht indexiert | O armazenamento não é indexado | O armazenamento não é indexado |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | Findling liest die Heimatverzeichnisse der Nutzer. Team Folders und externer Speicher sind eigene Einstellungen. | O Findling lê as pastas pessoais dos seus utilizadores. As Team Folders e o armazenamento externo são definições próprias. | O Findling lê as pastas pessoais dos seus usuários. As Team Folders e o armazenamento externo têm configurações próprias. |
| `This is a folder` | Das ist ein Ordner | Isto é uma pasta | Isto é uma pasta |
| `Enter the path of a file. A folder has no state of its own.` | Den Pfad einer Datei eingeben. Ein Ordner hat keinen eigenen Zustand. | Indique o caminho de um ficheiro. Uma pasta não tem estado próprio. | Informe o caminho de um arquivo. Uma pasta não tem estado próprio. |
| `Attempts so far: %s` | Bisherige Versuche: %s | Tentativas até agora: %s | Tentativas até agora: %s |
| `The next background run picks this file up (%s).` | Der nächste Hintergrundlauf holt diese Datei ab (%s). | A próxima passagem em segundo plano recolhe este ficheiro (%s). | A próxima execução em segundo plano vai pegar este arquivo (%s). |
| `The content of this file is searchable.` | Der Inhalt dieser Datei ist durchsuchbar. | O conteúdo deste ficheiro pode ser pesquisado. | O conteúdo deste arquivo pode ser pesquisado. |
| `_A worker holds this file. The claim runs out in %n second if nothing acknowledges it._::_A worker holds this file. The claim runs out in %n seconds if nothing acknowledges it._` | Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunde aus, wenn ihn niemand quittiert. / Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunden aus, wenn ihn niemand quittiert. | Um processo de tratamento tem este ficheiro reservado. A reserva expira em %n segundo se ninguém a confirmar. / Um processo de tratamento tem este ficheiro reservado. A reserva expira em %n segundos se ninguém a confirmar. / Um processo de tratamento tem este ficheiro reservado. A reserva expira em %n segundos se ninguém a confirmar. | Um processo de indexação está com este arquivo reservado. A reserva expira em %n segundo se ninguém a confirmar. / Um processo de indexação está com este arquivo reservado. A reserva expira em %n segundos se ninguém a confirmar. / Um processo de indexação está com este arquivo reservado. A reserva expira em %n segundos se ninguém a confirmar. |
| `Rules and limits` | Regeln und Grenzen | Regras e limites | Regras e limites |
| `Excluded folders` | Ausgeschlossene Ordner | Pastas excluídas | Pastas excluídas |
| `Prefix match on the path as the lists on this page show it, no wildcards and no patterns. Example: Backups` | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, keine Platzhalter und keine Muster. Beispiel: Backups | Comparação por prefixo sobre o caminho tal como as listas desta página o mostram, sem caracteres universais nem padrões. Exemplo: Backups | Comparação por prefixo do caminho como as listas desta tela o mostram, sem curingas nem padrões. Exemplo: Backups |
| `Add exclusion` | Ausschluss hinzufügen | Adicionar exclusão | Adicionar exclusão |
| `Remove exclusion %s` | Ausschluss %s entfernen | Retirar a exclusão %s | Remover a exclusão %s |
| `No folder is excluded.` | Kein Ordner ist ausgeschlossen. | Não há nenhuma pasta excluída. | Nenhuma pasta está excluída. |
| `Largest file to read` | Größte zu lesende Datei | Maior ficheiro a ler | Maior arquivo a ler |
| `Files above this size are recorded as skipped (too large) and never read.` | Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen. | Os ficheiros acima deste tamanho são registados como ignorados (demasiado grandes) e nunca são lidos. | Arquivos acima deste tamanho são registrados como ignorados (grandes demais) e nunca são lidos. |
| `The backend of this instance reads at most %s MB. For more, raise FINDLING_MAX_FILE_BYTES in the app settings of AppAPI, which restarts the container.` | Das Backend dieser Instanz liest höchstens %s MB. Für mehr FINDLING_MAX_FILE_BYTES in den App-Einstellungen von AppAPI anheben, was den Container neu startet. | O serviço desta instância lê no máximo %s MB. Para mais, aumente FINDLING_MAX_FILE_BYTES nas definições de aplicação do AppAPI, o que reinicia o contentor. | O serviço desta instância lê no máximo %s MB. Para mais, aumente FINDLING_MAX_FILE_BYTES nas configurações de aplicativo do AppAPI, o que reinicia o contêiner. |
| `Index Team Folders` | Team Folders indexieren | Indexar as Team Folders | Indexar as Team Folders |
| `Index external storage` | Externen Speicher indexieren | Indexar o armazenamento externo | Indexar o armazenamento externo |
| `External storage can be slow or charged per request. Indexing reads every file once.` | Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal. | O armazenamento externo pode ser lento ou cobrado por acesso. A indexação lê cada ficheiro uma vez. | O armazenamento externo pode ser lento ou cobrado por acesso. A indexação lê cada arquivo uma vez. |
| `The next run applies the new rules. Nothing restarts.` | Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu. | A próxima passagem aplica as novas regras. Não reinicia nada. | A próxima execução aplica as novas regras. Nada é reiniciado. |
| `Save rules` | Regeln speichern | Guardar regras | Salvar regras |
| `Rules saved. The next run applies them.` | Regeln gespeichert. Der nächste Lauf übernimmt sie. | Regras guardadas. A próxima passagem aplica-as. | Regras salvas. A próxima execução vai aplicá-las. |
| `The rules were not saved. Nothing changed.` | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | As regras não foram guardadas. Nada mudou. | As regras não foram salvas. Nada mudou. |
| `Enter a size between %1$s and %2$s MB.` | Eine Größe zwischen %1$s und %2$s MB eingeben. | Indique um tamanho entre %1$s e %2$s MB. | Informe um tamanho entre %1$s e %2$s MB. |
| `Enter a folder path.` | Einen Ordnerpfad eingeben. | Indique um caminho de pasta. | Informe um caminho de pasta. |
| `This path is already excluded.` | Dieser Pfad ist bereits ausgeschlossen. | Este caminho já está excluído. | Este caminho já está excluído. |
| `Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.` | Einen Eintrag zu entfernen wirkt innerhalb von %1$s Stunden, wenn der nächste Abgleichlauf diese Dateien wieder aufnimmt. Mit "%2$s" sofort übernehmen. | Retirar uma entrada produz efeito dentro de %1$s horas, quando a próxima passagem de comparação voltar a recolher esses ficheiros. Execute "%2$s" para aplicar de imediato. | Remover uma entrada faz efeito em até %1$s horas, quando a próxima execução de comparação pegar esses arquivos de novo. Execute "%2$s" para aplicar imediatamente. |
| `Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %1$s entfernt außerdem %2$s bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Retirar o conteúdo indexado? Excluir %1$s retira também do índice %2$s documentos já indexados sob esse caminho. Os próprios ficheiros ficam intactos no disco. | Remover o conteúdo indexado? Excluir %1$s também remove do índice %2$s documentos já indexados nesse caminho. Os próprios arquivos continuam intactos no disco. |
| `Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | Retirar o conteúdo indexado? Excluir %s retira também do índice os documentos já indexados sob esse caminho. Os próprios ficheiros ficam intactos no disco. | Remover o conteúdo indexado? Excluir %s também remove do índice os documentos já indexados nesse caminho. Os próprios arquivos continuam intactos no disco. |
| `at least %s` | mindestens %s | pelo menos %s | pelo menos %s |
| `Exclude and remove` | Ausschließen und entfernen | Excluir e retirar | Excluir e remover |
| `Keep files indexed` | Dateien indexiert lassen | Manter os ficheiros indexados | Manter os arquivos indexados |
| `Search` | Suchen | Pesquisar | Pesquisar |
| `Search term` | Suchbegriff | Termo de pesquisa | Termo de pesquisa |
| `invoice 2026` | Rechnung 2026 | fatura 2026 | nota fiscal 2026 |
| `Search file names only` | Nur Dateinamen durchsuchen | Pesquisar apenas nos nomes dos ficheiros | Pesquisar apenas nos nomes dos arquivos |
| `Results for "%s"` | Treffer für „%s“ | Resultados para «%s» | Resultados para “%s” |
| `Search results` | Suchergebnisse | Resultados da pesquisa | Resultados da pesquisa |
| `%1$s in %2$s` | %1$s in %2$s | %1$s em %2$s | %1$s em %2$s |
| `last opened` | zuletzt geöffnet | aberto pela última vez | aberto por último |
| `Show all results` | Alle Treffer anzeigen | Mostrar todos os resultados | Mostrar todos os resultados |
| `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | Abre a página de resultados do Findling | Abre a página de resultados do Findling |
| `Previous page` | Vorherige Seite | Página anterior | Página anterior |
| `Next page` | Nächste Seite | Página seguinte | Próxima página |
| `Page %s` | Seite %s | Página %s | Página %s |
| `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | Existem mais resultados. Restrinja a pesquisa para os ver. | Há mais resultados. Refine a pesquisa para vê-los. |
| `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | Pesquise no conteúdo dos seus ficheiros | Pesquise no conteúdo dos seus arquivos |
| `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | Escreva uma palavra de um documento. O Findling pesquisa o texto dentro dos seus ficheiros, incluindo os PDF digitalizados. | Digite uma palavra de um documento. O Findling pesquisa o texto dentro dos seus arquivos, inclusive em PDFs digitalizados. |
| `No file contains "%s"` | Keine Datei enthält „%s“ | Nenhum ficheiro contém «%s» | Nenhum arquivo contém “%s” |
| `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | Experimente outra palavra, uma parte de uma palavra composta, ou verifique a ortografia. | Tente outra palavra, uma parte de uma palavra composta, ou verifique a ortografia. |
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen. | Outros ficheiros contêm esta palavra, mas nenhum que lhe seja permitido abrir. | Outros arquivos contêm esta palavra, mas nenhum que você possa abrir. |
| `The search is not answering right now` | Die Suche antwortet gerade nicht | A pesquisa não está a responder neste momento | A pesquisa não está respondendo no momento |
| `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | O Findling não conseguiu contactar o seu serviço. Os seus ficheiros não mudaram. Tente de novo daqui a pouco, e avise a sua administração se continuar assim. | O Findling não conseguiu contatar o seu serviço. Seus arquivos não foram alterados. Tente de novo daqui a pouco, e avise a administração se continuar assim. |
| `Try again` | Erneut versuchen | Tentar de novo | Tentar de novo |
| `Findling is not ready to search` | Findling ist nicht suchbereit | O Findling não está pronto para pesquisar | O Findling não está pronto para pesquisar |
| `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | As duas metades do Findling comunicam versões diferentes. A sua administração tem de atualizar ambas ao mesmo tempo. | As duas metades do Findling informam versões diferentes. A administração precisa atualizar as duas ao mesmo tempo. |
| `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | O índice ainda está a ser construído, por isso podem faltar resultados. | O índice ainda está sendo criado, por isso podem faltar resultados. |
| `File type` | Dateityp | Tipo de ficheiro | Tipo de arquivo |
| `PDF` | PDF | PDF | PDF |
| `Documents` | Dokumente | Documentos | Documentos |
| `Spreadsheets` | Tabellen | Folhas de cálculo | Planilhas |
| `Presentations` | Präsentationen | Apresentações | Apresentações |
| `Images` | Bilder | Imagens | Imagens |
| `Text` | Text | Texto | Texto |
| `Time range` | Zeitraum | Período | Período |
| `Today` | Heute | Hoje | Hoje |
| `Last 7 days` | Letzte 7 Tage | Últimos 7 dias | Últimos 7 dias |
| `Last 30 days` | Letzte 30 Tage | Últimos 30 dias | Últimos 30 dias |
| `This year` | Dieses Jahr | Este ano | Este ano |
| `Remove filter %s` | Filter %s entfernen | Retirar o filtro %s | Remover o filtro %s |
| `Reset all filters` | Alle Filter zurücksetzen | Repor todos os filtros | Redefinir todos os filtros |
| `Sort by` | Sortieren nach | Ordenar por | Ordenar por |
| `Relevance` | Relevanz | Relevância | Relevância |
| `Last modified` | Zuletzt geändert | Última modificação | Última modificação |
| `Oldest first` | Älteste zuerst | Mais antigos primeiro | Mais antigos primeiro |
| `Modified on %s` | Geändert am %s | Modificado em %s | Modificado em %s |
| `%1$s in %2$s, modified on %3$s` | %1$s in %2$s, geändert am %3$s | %1$s em %2$s, modificado em %3$s | %1$s em %2$s, modificado em %3$s |
| `No results with the active filters` | Keine Treffer mit den aktiven Filtern | Sem resultados com os filtros ativos | Nenhum resultado com os filtros ativos |
| `Remove a filter or widen the time range.` | Entfernen Sie einen Filter oder erweitern Sie den Zeitraum. | Retire um filtro ou alargue o período. | Remova um filtro ou amplie o período. |
| `Reset filters` | Filter zurücksetzen | Repor filtros | Redefinir filtros |

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
kein Wert leer und keiner mit dem englischen Quellstring identisch ist. Die Ausnahmen stehen je
Sprachcode in einer eigenen Liste, und dieses Dokument führt deshalb **zwei**: eine für `pt_PT`,
eine für `pt_BR`. Das ist jeweils eine benannte Liste und ausdrücklich **keine**
Toleranzschwelle: eine Schwelle würde einen vergessenen Wortlaut genauso mitdecken wie einen
gewollten, eine Liste deckt nur, was in ihr steht. Die Listen dürfen wachsen, die Zahl zwei ist
keine Grenze, sondern das Ergebnis des Zählens, und jeder Eintrag trägt seinen Grund bei sich.

**Liste für `pt_PT`**, genau zwei Schlüssel:

- `Findling`: Eigenname der App, in jeder Sprache dasselbe Wort. Er steht als Schlüssel in
  `de.json` und muss deshalb in `pt_PT.json` stehen, hat aber keinen eigenen Wortlaut.
- `PDF`: Eigenname eines Dateiformats, in jeder Sprache dieselbe Abkürzung.

**Liste für `pt_BR`**, ebenfalls genau zwei Schlüssel, dieselben und aus demselben Grund:

- `Findling`: Eigenname der App. Er steht als Schlüssel in `de.json` und muss deshalb in
  `pt_BR.json` stehen, hat aber keinen eigenen Wortlaut.
- `PDF`: Eigenname eines Dateiformats, in jeder Sprache dieselbe Abkürzung.

Dass die beiden Listen gleich sind, ist ein Befund und keine Übernahme: die brasilianische ist
eigens gemessen worden, mit denselben drei Läufen wie die europäische. Kein Eintrag ohne Liste:
`AssertionError: languages without a list of exceptions: ['pt_BR']`. Leeres Mapping: vier Funde,
zwei Schlüssel über zwei Dateien, erster davon
`pt_BR.json: 'Findling' is still the English source string`. Zwei begründete Einträge: grün.
Auch das Brasilianische schreibt zwischen den Platzhaltern `em` und sagt `Planilhas`, also fehlen
`%1$s in %2$s` und `Spreadsheets` aus demselben Grund wie im europäischen.

Die europäische Liste ist ebenso wenig geraten worden. Drei Läufe, in dieser Reihenfolge:

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
`VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_PT"]` und `VALUES_THAT_MAY_EQUAL_THEIR_KEY["pt_BR"]` in
`backend/tests/test_admin_ui_contract.py`. Doku und Gate dürfen hier nicht auseinanderlaufen: die
Doku sagt, was erlaubt ist, das Gate hält es.

## Maschinelle Prüfungen

Gefahren am 25.09.2026 über die erzeugten Dateien, nicht per Augenmaß: die Spalte PT_PT in
Plan 20-07 über `pt_PT.json` und `pt_PT.js`, die Spalte PT_BR in Plan 20-08 über `pt_BR.json`
und `pt_BR.js`. Die Werte der Spalte PT_PT sind die von damals und nicht nachgezogen; wo sie
sich auf den Baum beziehen (Testzahlen, Tupellänge), gelten sie für den Stand nach 20-07.

| Prüfung | PT_PT | PT_BR |
|---|---|---|
| Schlüsselmenge gleich `de.json`, in derselben Reihenfolge | ja, 202 von 202, fehlend 0 | ja, 202 von 202, fehlend 0 |
| Schlüsselmenge `.js` gleich `.json` (Objektvergleich über den `register`-Rumpf) | ja, identisch | ja, identisch |
| Jeder Schlüssel des Katalogs kommt in dieser Datei vor | fehlend: 0 | fehlend: 0 |
| Platzhalter-Parität Schlüssel gegen Wert, über alle 40 Schlüssel mit Direktiven, Pluralschlüssel an `_::_` geteilt | 0 Abweichungen | 0 Abweichungen |
| Pluralschlüssel mit genau **drei** Formen, Form 1 gleich Form 2 | 5 von 5 | 5 von 5, und **nicht** die Millionenform der Kerndatei |
| Pluralschlüsselmenge gleich der deutschen | ja | ja |
| `pluralForm` zeichengleich mit `docs/l10n-catalogues.md`, mit `nplurals=3` | ja, in beiden Dateien | ja, in beiden Dateien, und gleich `PLURAL_FORM_OF["pt_BR"]` |
| `scan_plural_rule` mit der eigenen Zeichenkette | `[]` | `[]` |
| `scan_plural_rule` mit der deutschen Zeichenkette | zwei Funde | zwei Funde |
| `scan_plural_rule` mit der **spanischen** Zeichenkette | ein Fund | ein Fund |
| `php/l10n/pt.json` und `php/l10n/pt.js` vorhanden | nein, gewollt | nein, gewollt |
| U+2019 (typographischer Apostroph) | 0 | 0 |
| U+2014 und U+2013 (Gedankenstriche) | 0 | 0 |
| U+00A0 und U+202F (geschützte Leerzeichen) | 0 | 0 |
| Nackte Prozentzeichen, also `%` ohne erkannte Direktive | 0 in Schlüsseln und in allen Formen | 0 in Schlüsseln und in allen Formen |
| Verdoppelte Prozentzeichen | 0, der einzige betroffene Satz ist umformuliert | 0, derselbe Satz, ebenso umformuliert |
| Pipe-Zeichen (der senkrechte Strich, mit dem Nextcloud Pluralformen verbindet) | 0 | 0 |
| Wert identisch mit dem englischen Quellstring | 2, beide oben benannt | 2, beide oben benannt |
| Eigene Varietätenwörter im Katalog (Textzählung über die `.json`) | `ficheiro` 56, `utilizador` 1 | `arquivo` 55, `usuário` 1, `tela` 2 |
| Wörter der anderen Varietät im Katalog | `arquivo`, `usuário`, `tela`: 0, 0, 0 | `ficheiro`, `utilizador`, `ecrã`: 0, 0, 0 |
| Werte gleich dem Wert der anderen Varietät | nicht messbar, die zweite Datei gab es noch nicht | 72 von 202, keine davon unter einem Schlüssel von `PORTUGUESE_WORDINGS_THAT_MUST_DIFFER` |
| `test_the_two_portuguese_catalogues_are_two` mit einer Kopie von `pt_PT.json` als `pt_BR.json` | entfällt | rot, elf Funde; danach zurückgesetzt |
| LF, UTF-8 ohne BOM, abschließender Zeilenumbruch | beide Dateien, byteweise geprüft | beide Dateien, byteweise geprüft |
| Giessform gegen den unveränderten Bestand, vor der ersten neuen Zeile | 12 von 12 byteweise gleich | 14 von 14 byteweise gleich (`de`, `de_DE`, `fr`, `es`, `it`, `nl`, `pt_PT`, je `.json` und `.js`) |
| Einträge in `L10N_CATALOGUES` | 14 | 16 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 52 passed | 53 passed |
| `cd backend && uv run pytest -q` | 2879 passed, 15 skipped | 2880 passed, 15 skipped |
| ruff check, ruff format --check, pyright, vulture | alle grün | alle grün |

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

### Zweiter Vorbehalt: die Spalte PT_BR

Der Vorbehalt oben deckt die Spalte PT_PT und bleibt so stehen, wie er am 25.09.2026 in Plan
20-07 geschrieben wurde. Dieser deckt die Spalte PT_BR. Es sind zwei Vorbehalte, weil es zwei
Kataloge sind, die zu zwei Zeitpunkten entstanden sind; einer erbt nichts vom anderen.

**Erzeugt am 25.09.2026, Plan 20-08.** Die brasilianisch-portugiesischen Wortlaute dieser
Tabelle sind maschinell entstanden, als eigene Spalte geschrieben und ausdrücklich nicht aus der
Spalte PT_PT kopiert und nachbearbeitet. Gefahren wurden die Gates der Spalte PT_BR im Abschnitt
"Maschinelle Prüfungen": Schlüsselmenge, Gleichstand der beiden Dateien, Platzhalterparität,
Formenzahl, Pluralregel samt spanischer und deutscher Gegenprobe, Prozentdisziplin,
Pipe-Zeichen, Prosa-Scan auf Gedankenstriche und Symbolzeichen, Apostroph- und Akzentprüfung,
Vollständigkeit mit eigener, gemessener Ausnahmeliste, die Varietätenprobe positiv wie negativ
und das neue Unterschieds-Gate `test_the_two_portuguese_catalogues_are_two` samt Gegenprobe mit
einer Kopie.

**Dieser Katalog ist von keinem Muttersprachler gelesen worden.** Es gilt derselbe Entscheid
E-17-5, Option a, wie für die Spalte PT_PT: maschinell erzeugt, korrigiert über das offene
Community-Review des Nextcloud App Store, gemeldet als Issue im Repositorium
`street1983nk/nextcloud-search` oder als Änderung an dieser Tabelle. **Die Auslieferung wartet
darauf nicht**, aus derselben Abwägung: eine brasilianische Oberfläche mit einzelnen unrunden
Sätzen ist für einen brasilianischen Nutzer besser als eine englische, und erst recht besser als
eine europäisch-portugiesische, die er täglich als fremd liest.

**Vier Stellen, an denen ein brasilianischer Muttersprachler zuerst hinsehen sollte.** Erstens
`execução` für den Lauf und die Fügungen `execução de comparação` und `execução em segundo
plano`. Zweitens `processo de indexação` für den Worker, das hier anders entschieden ist als im
europäischen Katalog. Drittens `Excluído` und `Pastas excluídas` für den Ausschluss durch eine
Regel: im brasilianischen Alltag heißt `excluir` auch "löschen", und genau diese Doppeldeutigkeit
soll die Oberfläche nicht tragen, wenn die Dateien auf der Platte unverändert bleiben; die Sätze
um den Ausschluss sagen das jeweils ausdrücklich (`Os próprios arquivos continuam intactos no
disco`), aber ein Muttersprachler kann ein Wort wie `ignorar` oder `deixar de fora` vorziehen.
Viertens `tela` für die Verwaltungsseite, das bewusst gewählt ist und die Probe `ecrã` gegen
`tela` erst zu einer echten macht.

**Was ausdrücklich nicht zur Nachbesserung ansteht:** die drei Formen mit wortgleicher Form 1
und Form 2, obwohl die Kerndatei `core/l10n/pt_BR.json` es anders macht. Der Abschnitt
"Pluralformen" sagt, warum Findling ihr nicht folgt.

**Stand der Spalte PT_BR:** alle 202 Zeilen sind am 25.09.2026 entstanden, keine ist später
hinzugekommen, und keine ist abgenommen. Kommt später ein Schlüssel dazu, bekommt er beide
portugiesischen Wortlaute und einen datierten Nachtrag, und gehört er in eine der Varietätenfragen
dieses Dokuments, gehört er auch in `PORTUGUESE_WORDINGS_THAT_MUST_DIFFER`.
