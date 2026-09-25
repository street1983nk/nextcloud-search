# Katalogdateien der Phase 20: Ladepfad, Pluralregeln und die Wahl der Formen

Dieses Dokument ist der gemeinsame Beweis aller Sprachdateien der Phase 20. Die vier
Sprachdokumente, die danach entstehen (`docs/l10n-spanish.md`, `docs/l10n-italian.md`,
`docs/l10n-dutch.md`, `docs/l10n-portuguese.md`), verweisen hierher, statt denselben Beweis
viermal zu führen. Dort steht, was die jeweilige Sprache eigen hat: die Wortlaute, ihre
Ausnahmen und der datierte Review-Vorbehalt.

Alles unten ist gemessen und nicht erinnert. Die Messungen liefen am **25.09.2026** gegen zwei
laufende Instanzen:

| Instanz | Container | Version | Rolle |
|---|---|---|---|
| Ziel-Nextcloud der Entwicklung | `findling-nextcloud` | 34.0.3 | `php/` ist als `custom_apps/findling` gebunden, jede Datei ist sofort live |
| zweite Instanz des Versionsfensters | `nc35-nc` | 35.0.0 | Gegenprobe, weil das Fenster NC 33 bis 35 ist |

Der Grund für die zweite Instanz: die Pluralregeln stammen aus den Kerndateien einer fremden
Codebasis. Eine Regel, die in 34 gilt und in 35 anders lautet, wäre ein Befund und keine Wahl
zwischen zwei Messungen.

---

## 1. Warum zehn Dateien und nicht fünf

Nextcloud baut den Katalogdateinamen aus dem Sprachcode **ohne jede Kürzung**. In
`lib/private/L10N/Factory.php` hängt `getL10nFilesForApp()` schlicht `.json` an den Code an,
und `validateLanguage()` davor prüft jede Stufe erneut mit `languageExists()`. Nirgends wird
`pt_PT` zu `pt` verkürzt. Die `LanguageIterator`-Kürzung, die einen einzigen `pt`-Katalog
erlauben würde, gilt für Benachrichtigungen und Mails, nicht für den Dateiladepfad der
App-Kataloge.

Das ist nicht aus dem Quelltext geschlossen, sondern gefragt worden. Die Sonde legt eine echte
`php/l10n/pt.json` an (Wert `Findling` zu `PROBE_PT`) und stellt dann drei Fragen je Sprachcode.
Ergebnis vom 25.09.2026 auf `findling-nextcloud`:

| angefragte Sprache | `languageExists('findling', code)` | `getLanguageCode()` | `t('Findling')` |
|---|---|---|---|
| `pt` | yes | `pt` | `PROBE_PT` |
| `pt_PT` | **no** | **`en`** | `Findling` |
| `pt_BR` | **no** | **`en`** | `Findling` |
| `es` | no | `en` | `Findling` |
| `it` | no | `en` | `Findling` |
| `nl` | no | `en` | `Findling` |
| `fr` | yes | `fr` | `Findling` |
| `de_DE` | yes | `de_DE` | `Findling` |

`findAvailableLanguages('findling')` meldete während der Sonde `en,de,de_DE,fr,pt` und ohne sie
`en,de,de_DE,fr`. Dass `fr` und `de_DE` bei `t('Findling')` das englische Wort zeigen, ist kein
Fehlschlag: `Findling` ist der Name der App und in allen Sprachen dasselbe Wort, geführt als
benannte Ausnahme des Vollständigkeitsgates.

Die entscheidende Zeile ist die zweite und die dritte: **ein Nutzer auf `pt_PT` oder `pt_BR`
landet auf `en`, obwohl ein `pt`-Katalog danebenliegt.** Und niemand kann auf `pt` stehen, denn
der Kern kennt diesen Code gar nicht:

```
$ docker exec findling-nextcloud sh -c 'ls /var/www/html/core/l10n/ | grep -E "^(es|it|nl|pt)"'
es.js  es.json  es_EC.js  es_EC.json  es_MX.js  es_MX.json
it.js  it.json  nl.js  nl.json
pt_BR.js  pt_BR.json  pt_PT.js  pt_PT.json
```

Kein `pt`. Also braucht Portugiesisch zwei Codes und vier Dateien, und die Phase liefert
insgesamt **zehn** Dateien, alle unter `php/l10n/`:

```
php/l10n/es.json     php/l10n/es.js
php/l10n/it.json     php/l10n/it.js
php/l10n/nl.json     php/l10n/nl.js
php/l10n/pt_PT.json  php/l10n/pt_PT.js
php/l10n/pt_BR.json  php/l10n/pt_BR.js
```

Die ExApp bekommt keine. Sie hat kein App-Verzeichnis in der Nextcloud, ihre einzigen
übersetzten Texte sind Store-Metadaten in `backend/appinfo/info.xml`, und jeder Satz, den der
Container über sich selbst sagen lässt, reist als Code und wird auf der PHP-Seite in Worte
gefasst.

**Zum Nachfahren**, die ganze Sonde, einschließlich Aufräumen:

```bash
docker exec findling-nextcloud sh -c 'ls /var/www/html/core/l10n/ | grep -E "^(es|it|nl|pt)"'

# Probekatalog anlegen. php/ ist in den Container gebunden, die Datei liegt damit im Repo.
printf '%s\n' '{ "translations": { "Findling": "PROBE_PT" }, "pluralForm": "nplurals=2; plural=(n != 1);" }' > php/l10n/pt.json

# Sondenskript (Inhalt siehe unten) in den Container legen und ausfuehren.
docker exec -i findling-nextcloud sh -c 'cat > /var/www/html/probe.php' < /tmp/probe.php
MSYS_NO_PATHCONV=1 docker exec -u www-data findling-nextcloud php /var/www/html/probe.php

# Aufraeumen, und zwar beides.
rm -f php/l10n/pt.json
docker exec findling-nextcloud rm -f /var/www/html/probe.php
git status --short   # muss leer sein
```

Der Inhalt von `/tmp/probe.php`:

```php
<?php
require_once '/var/www/html/lib/base.php';
$f = \OCP\Server::get(\OCP\L10N\IFactory::class);
echo "verfuegbar: " . implode(',', $f->findAvailableLanguages('findling')) . "\n";
foreach (['pt','pt_PT','pt_BR','es','it','nl','fr','de_DE'] as $lang) {
    $l = $f->get('findling', $lang);
    printf("%-7s exists=%-4s code=%-6s t(Findling)=%s\n",
        $lang, $f->languageExists('findling',$lang)?'yes':'no',
        $l->getLanguageCode(), $l->t('Findling'));
}
```

`MSYS_NO_PATHCONV=1` gehört unter Windows-Git-Bash vor jedes `docker exec` mit absolutem
Containerpfad, sonst baut MSYS den Pfad in einen Windows-Pfad um und die Datei wird nicht
gefunden. Und weil `php/` in den Container gebunden ist, liegt die Probedatei im Repo und muss
danach weg, auf beiden Seiten. Das abschließende `git status --short` ist kein Schmuck, sondern
die Abnahme.

## 2. Die benannte Grenze: es_EC und es_MX werden nicht ausgeliefert

Der Kern liefert neben `es` auch `es_EC` und `es_MX`, siehe die Dateiliste oben. Findling
liefert sie **nicht**. Ein Nutzer, der in seinen persönlichen Einstellungen Spanisch (Mexiko)
wählt, sieht Findling auf Englisch, aus demselben Mechanismus wie in Abschnitt 1: kein
`es_MX.json` im App-Verzeichnis, also fällt `validateLanguage()` auf `en` zurück.

Das ist eine Entscheidung und keine Lücke. Sie ist dieselbe wie für `fr_CA`, festgehalten im
Kopf von `backend/tests/test_admin_ui_contract.py`. Drei Gründe:

1. **Der Wortlaut wäre derselbe.** Unter den 202 Sätzen der Adminseite und der Ergebnisseite
   ist keiner, in dem sich das mexikanische vom europäischen Spanisch unterscheiden würde.
   Vier zusätzliche Dateien mit identischem Inhalt sind vier zusätzliche Dateien, die
   auseinanderlaufen können.
2. **Der Gleichstand kostet.** Jede Datei ist eine weitere Zeile im Gleichstandsgate und ein
   weiterer Ort, an dem ein neuer Schlüssel nachgezogen werden muss.
3. **Portugiesisch liegt anders.** `pt_PT` und `pt_BR` unterscheiden sich in genau den Wörtern,
   die auf dieser Seite vorkommen (ficheiro gegen arquivo, utilizador gegen usuário, ecrã
   gegen tela). Dort sind zwei Dateien eine Notwendigkeit, hier wären sie eine Kopie.

Wer das später anders entscheidet, findet den Grund hier und muss ihn widerlegen, statt eine
vergessene Datei zu vermuten.

## 3. Die Pluralregeln, wörtlich

Gelesen am 25.09.2026 aus `/var/www/html/core/l10n/<code>.json`, Feld `pluralForm`, in **beiden**
Instanzen. Die Zeichenketten sind übernommen und nicht nachgetippt.

```
Sprachcode  nplurals  NC 34.0.3 == NC 35.0.0  pluralForm, woertlich aus core/l10n/<code>.json
es          3         ja                      nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
it          3         ja                      nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
nl          2         ja                      nplurals=2; plural=(n != 1);
pt_PT       3         ja                      nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
pt_BR       3         ja                      nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
fr          3         ja                      nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
de          2         ja                      nplurals=2; plural=(n != 1);
de_DE       2         ja                      nplurals=2; plural=(n != 1);
```

**Beide Instanzen führen für alle acht Codes dieselbe Zeichenkette**, Zeichen für Zeichen. Es
gibt also keinen Versionsbefund, der zwischen NC 34 und NC 35 entschieden werden müsste. Der
Befehl, der das beantwortet:

```bash
for c in findling-nextcloud nc35-nc; do
  echo "=== $c ==="
  docker exec "$c" sh -c 'cd /var/www/html/core/l10n && for f in es it nl pt_PT pt_BR fr de de_DE; do
    printf "%s|" "$f"
    php -r "echo json_decode(file_get_contents(\$argv[1].\".json\"),true)[\"pluralForm\"], PHP_EOL;" "$f"
  done'
done
```

**Eine Zeile fällt auf: `fr`.** Der Kern führt Französisch mit `nplurals=3`, Findlings
ausgelieferte `fr.json` steht seit Plan 11-08 auf `nplurals=2; plural=(n > 1);`. Das ist **kein
Fehler, der hier zu beheben wäre**: die französische Zwei-Formen-Variante ist in beiden Hälften
korrekt (Singular bei n gleich 0 und n gleich 1, Plural ab 2), der Owner hat die französischen
Wortlaute am 11.09., 19.09. und 24.09.2026 in dieser Form abgenommen, und ein Umbau auf drei
Formen wäre eine Wortlautänderung ohne Nutzen. Die Zeile ist aber der Grund, warum das Gate ein
**Mapping je Sprachcode** braucht und keine zwei festen Konstanten: `fr` bleibt bei zwei Formen,
während `es` auf drei geht.

Was die Konstante `PLURAL_FORM_OF` in `backend/tests/test_admin_ui_contract.py` deshalb trägt,
ist **die Regel, die Findling ausliefert**, und die ist für sieben von acht Codes die Kernregel
und für `fr` die eigene:

```
de     nplurals=2; plural=(n != 1);
de_DE  nplurals=2; plural=(n != 1);
fr     nplurals=2; plural=(n > 1);
es     nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
it     nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
nl     nplurals=2; plural=(n != 1);
pt_PT  nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
pt_BR  nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;
```

Dieser Block ist die Vorlage für die Konstante, und die Konstante ist zeichengleich mit ihm. Er
ist maßgeblich, falls die beiden Blöcke je auseinanderlaufen: der zweite sagt, was in den
Dateien steht, der erste sagt, woher es stammt.

Die Zahl der Formen je Sprachcode steht daneben in `FORM_COUNT_OF` und wird **nicht** aus
`nplurals=` geparst. Eine geparste Zahl hinge an derselben Zeichenkette, die das Gate prüft,
und eine falsche Regel baute sich damit ihre eigene Erwartung.

**Niederländisch ist zeichengleich mit Deutsch.** `nplurals=2; plural=(n != 1);` steht in
beiden. Das ist keine Nachlässigkeit, sondern die Regel beider Sprachen, und es ist die Falle
dieses Gates: eine Prüfung, die pauschal meldet "diese Datei trägt die deutsche Regel", wäre
für `nl` dauerhaft rot. Das Gate prüft deshalb sprachbewusst, und die gestellte Gegenprobe im
Testrumpf hält genau diesen Fall fest.

## 4. Warum drei Formen deklariert und Form 1 und Form 2 wortgleich geschrieben werden

Für `es`, `it`, `pt_PT` und `pt_BR` tragen die fünf Pluralwerte **drei** Formen, und die zweite
und die dritte sind wortgleich. Das ist kein Schlendrian, sondern das Ergebnis einer Messung.

**PHP liest die deklarierte `pluralForm` überhaupt nicht.** `L10N::load()` übernimmt nur
`$json['translations']`; `L10NString::__toString()` verbindet die Formen mit dem senkrechten
Strich, ersetzt `%n` durch `%count%` und übergibt das an Symfonys `IdentityTranslator`, der
**über den Sprachcode** wählt. Die deklarierte Regel wirkt nur im Browser.

Nebenbefund derselben Quelle, wichtig für jede spätere Sonde: die Auswahl greift nur, wenn der
Wert ein `%n` trägt. Ohne `%n` bleibt die Parameterliste leer, und der Übersetzer gibt die mit
dem senkrechten Strich verbundene Kette unverändert zurück. Eine Probe mit den Formen `FORM0`,
`FORM1` und `FORM2` misst deshalb gar nichts; die Probe unten benutzt `%n FORM0` und so fort.

Gemessen am 25.09.2026 mit Probekatalogen dieser Bauart, gefragt über `IFactory` im Container
`findling-nextcloud`:

| Sprache | PHP bei n=0 | n=1 | n=2 | n=5 | n=1000000 |
|---|---|---|---|---|---|
| `es` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `it` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `nl` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `pt_PT` | FORM1 | FORM0 | FORM1 | FORM1 | FORM1 |
| `pt_BR` | **FORM0** | FORM0 | FORM1 | FORM1 | FORM1 |

**PHP erreicht FORM2 nie.** Die Gegenprobe dazu ist die deklarierte Regel selbst, ausgewertet
wie der Browser sie auswertet (`bundle.pluralFunction(count)` im gebündelten
`@nextcloud/l10n`):

| Sprache | JS bei n=0 | n=1 | n=2 | n=5 | n=1000000 |
|---|---|---|---|---|---|
| `es` | 2 | 0 | 2 | 2 | 1 |
| `it` | 2 | 0 | 2 | 2 | 1 |
| `nl` | 1 | 0 | 1 | 1 | 1 |
| `pt_PT` | 0 | 0 | 2 | 2 | 1 |
| `pt_BR` | 0 | 0 | 2 | 2 | 1 |

Bei n gleich 2 wählt PHP Index 1 und JS Index 2. Stünden dort verschiedene Wörter, liefe die
Seite beim ersten Render anders als nach dem ersten Poll: `2 de dias` im Server-HTML, `2 dias`
im Browser, in derselben Zeile derselben Seite. **Form 1 und Form 2 wortgleich als normalen
Plural zu setzen ist die einzige Wahl, die beide Seiten gleich antworten lässt**, und sie
erfüllt Erfolgskriterium 3 trotzdem, weil drei Formen deklariert sind.

**Der Kern selbst läuft in diese Falle, und das ist der Grund, ihm hier nicht zu folgen.**
Gezählt am 25.09.2026 über `core/l10n/<code>.json` auf `findling-nextcloud`:

| Kerndatei | Plural-Einträge | mit drei Formen | davon Form 1 gleich Form 2 |
|---|---:|---:|---:|
| `core/l10n/es.json` | 6 | 6 | **6** |
| `core/l10n/it.json` | 6 | 6 | **6** |
| `core/l10n/pt_PT.json` | 8 | 8 | 6 |
| `core/l10n/pt_BR.json` | 9 | 9 | **0** |

`pt_BR` schreibt konsequent die Millionenform auf Index 1, zum Beispiel
`"_%n result_::_%n results_": ["%n resultado", "%n de resultados", "%n resultados"]`. Die Folge
ist auf der PHP-Seite messbar, und sie ist gemessen worden, nicht hergeleitet. Gefragt wurde
`$l->n('%n result', '%n results', $n)` gegen den **Kernkatalog** `core` derselben Instanz:

```
pt_BR  n=1  1 resultado      n=2  2 de resultados      n=5  5 de resultados
```

Der Kern rendert dem brasilianischen Nutzer serverseitig `2 de resultados`. **Dieser Falle
folgt Findling nicht.**

## 5. Die verbleibende benannte Abweichung bei n=0

Eine Abweichung bleibt übrig, und sie wird hier benannt statt beseitigt: bei **n gleich 0**
wählt JS für `pt_PT` den **Singular** (Regel `(n == 0 || n == 1) ? 0 : ...`, Index 0), während
PHP den Plural wählt (FORM1). Die Tabellen in Abschnitt 4 zeigen es in der ersten Spalte.

**Betroffen ist `pt_PT`, und zwar als einzige der vier Sprachen.** Die Messung berichtigt hier
eine naheliegende Erwartung: `pt_BR` weicht **nicht** ab, denn Symfonys Regel für `pt_BR`
behandelt die Null wie den Singular und wählt ebenfalls FORM0, genau wie die deklarierte Regel
im Browser. `es` und `it` weichen im Index ab (JS 2 gegen PHP 1), aber nicht im Wortlaut, weil
Form 1 und Form 2 wortgleich sind.

**Wie weit die Abweichung reicht:** höchstens bis zur Sekundenzeile der Dateisperre
(`A worker holds this file. The claim runs out in %n second ...`). Die drei Zeitspannen
(Minuten, Stunden, Tage) laufen über `max(1, ...)`-Schwellen und können nie mit 0 gerendert
werden, und `and %n more` wird nur gerendert, wenn der Rest größer als 0 ist. Bleibt eine
Sperre, deren Restlaufzeit auf 0 Sekunden gerundet ist: der Server schriebe dort die
Pluralform, das Skript nach dem ersten Poll die Singularform. Ein portugiesischer Nutzer sieht
in dieser einen Zeile in dieser einen Sekunde eine andere Endung.

Das ist der Preis der Entscheidung aus Abschnitt 4, er ist bekannt, und er ist kleiner als die
Alternative: eine Seite, die bei jeder Anzahl außer 1 zwischen Server und Browser
auseinanderläuft.

## 6. Der zusammengesetzte Pluralschlüssel

Ein Plural steht in einem Nextcloud-Katalog unter dem Schlüssel `_<singular>_::_<plural>_` und
niemals unter dem blanken Singular. `L10N::n` baut diesen Bezeichner selbst und fällt sonst auf
den englischen Quellstring zurück; das gebündelte `@nextcloud/l10n` tut im Browser dasselbe.

Findling hat die fünf Schlüssel seit dem ersten Katalog blank geführt und deshalb auf Deutsch
und Französisch ab n gleich 2 englisch geantwortet. **Plan 20-01 hat das repariert**, mit
Vorher-Nachher-Beleg an der laufenden Instanz; der Beleg und die fünf Schlüsselpaare stehen in
`.planning/phases/20-ui-kataloge-es-it-nl-pt/20-01-SUMMARY.md` und werden hier nicht wiederholt.

Für die zehn neuen Dateien heißt das nur eines, und darum steht es hier: **das Format ist geerbt
und nicht neu zu entscheiden.**

```json
{
  "translations": {
    "_%n day_::_%n days_": ["%n dia", "%n dias", "%n dias"]
  },
  "pluralForm": "nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;"
}
```

Wer einen Pluralschlüssel blank schreibt, liefert eine halb englische Seite aus. Das
Gleichstandsgate fängt es, weil die Schlüsselmenge dann von der deutschen abweicht.

## 7. Die Schlüsselzahl

Aus der Datei gezählt, nicht aus der Recherche übernommen:

| Größe | Wert | gezählt am |
|---|---:|---|
| Schlüssel in `php/l10n/de.json` | **202** | 25.09.2026 |
| davon Pluralschlüssel (Wert ist eine Liste) | **5** | 25.09.2026 |

```bash
python -c "import json,io;print(len(json.load(io.open('php/l10n/de.json',encoding='utf-8'))['translations']))"
```

Jede der zehn neuen Dateien führt dieselben 202 Schlüssel. Die Zahl wird **am Plantag erneut
gezählt** und nicht aus diesem Dokument abgeschrieben: sie ist zwischen dem 10.09. und dem
24.09.2026 dreimal gestiegen (173, dann 197, dann 199, dann 202), und ein abgeschriebener Wert
ist genau die Art Zahl, die still falsch wird.

Die harte Zahl im Gate steht in
`test_the_german_catalogue_covers_both_german_language_codes`, und der Docstring darüber
verlangt wörtlich, dass wer sie anfasst den nächsten Absatz schreibt. Wer nur die
Schlüssel**namen** ändert, schreibt ihn ebenfalls: der Absatz ist das Gedächtnis dieser Datei.
