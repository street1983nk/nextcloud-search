---
phase: 20-ui-kataloge-es-it-nl-pt
plan: 01
subsystem: l10n
tags: [pluralschluessel, kataloge, gate, nextcloud-l10n, sonde, checkpoint]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: "die sechs Bestandskataloge und die Gates G1 bis G4 in test_admin_ui_contract.py"
  - phase: 18-schema-marken-und-umbauweg
    provides: "die 202 Schluessel, auf denen die harte Zahl des Zwillings-Gates steht"
provides:
  - "Alle sechs Bestandskataloge fuehren die fuenf Pluralschluessel als _<singular>_::_<plural>_, also unter dem Namen, unter dem L10N::n und @nextcloud/l10n sie nachschlagen"
  - "expected_directives_per_form(key): die Teilung eines zusammengesetzten Schluessels an der Marke, eine Erwartung fuer Form 0 und eine fuer jede weitere"
  - "scan_placeholder_parity nennt die Formnummer in der Fundmeldung"
  - "Der Gedaechtnis-Docstring von test_the_german_catalogue_covers_both_german_language_codes traegt den Absatz zur Umbenennung samt Messung"
  - "docs/l10n-french.md: fuenf gehobene Tabellenzeilen und der datierte Nachtrag 25.09.2026 mit dem Satz, dass kein franzoesischer Wortlaut angefasst wurde"
affects: [20-02 (PLURAL_FORM_OF je Sprachcode), 20-03 (Scanner parametrisiert), 20-04 bis 20-08 (zehn neue Kataloge erben das Format)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Katalogformat wird nicht getippt, sondern gegossen, und die Giessform beweist sich zuerst am unveraenderten Bestand: cast(alt) == alt byteweise, danach erst die Aenderung"
    - "Ein Fund, der eine Form betrifft, nennt die Formnummer; sonst liest sich ein Verlust in der zweiten Form wie einer in der ersten"
    - "Die Vorher-Haelfte eines Vorher-Nachher-Belegs wird gemessen und nicht zitiert: die alten Katalogbytes aus HEAD~1 laufen unter einer Wegwerf-App-ID auf derselben Instanz, am selben Tag, mit derselben Frage"

key-files:
  created:
    - .planning/phases/20-ui-kataloge-es-it-nl-pt/20-01-SUMMARY.md
  modified:
    - backend/tests/test_admin_ui_contract.py
    - php/l10n/de.json
    - php/l10n/de.js
    - php/l10n/de_DE.json
    - php/l10n/de_DE.js
    - php/l10n/fr.json
    - php/l10n/fr.js
    - docs/l10n-french.md

key-decisions:
  - "Die Teilung steht in einer eigenen Funktion expected_directives_per_form direkt ueber dem Scanner und nicht im Schleifenrumpf: der Plan verlangt die Teilung an genau einer Stelle, und eine zweite Gestalt derselben Teilung koennte sonst spaeter einwandern"
  - "Die Kataloge sind gegossen und nicht per Hand nachgezogen, aber die Giessform ist zuerst gegen den unveraenderten Bestand byteweise geprueft worden (cast_json und cast_js reproduzieren alle sechs Dateien exakt). Erst danach lief die Umbenennung, und der Diff zeigt in jeder der sechs Dateien genau fuenf Zeilen"
  - "Die Bestandsform der Kataloge schreibt Listenwerte EINZEILIG; json.dumps(indent=4) schreibt sie dreizeilig. Die Giessform faltet die Listen deshalb wieder zusammen. Ohne diesen Schritt haette der Diff 30 statt 5 Zeilen je Datei gezeigt und die Byte-Gegenprobe des Plans waere unerfuellbar gewesen"
  - "Die Vorher-Messung ist neu erhoben und nicht aus der Research uebernommen: die Katalogbytes aus HEAD~1 lagen unter der Wegwerf-App-ID l10nprobe im Container, dieselbe Instanz beantwortet dieselbe Frage einmal alt und einmal neu. Beide Ablagen sind nach dem Lauf entfernt"
  - "KAT-01 bleibt UNGEHAKT. Dieser Plan repariert die Bestandskataloge; die Anforderung verlangt zehn neue Dateien im Gleichstand und wird fruehestens mit 20-08 erfuellt"

requirements-completed: []

# Metrics
duration: 35min
completed: 2026-09-25
---

# Phase 20 Plan 01: Pluralschluessel-Fix der sechs Bestandskataloge Summary

**Die fuenf Pluralschluessel aller sechs Bestandskataloge heissen jetzt `_<singular>_::_<plural>_`,
und damit antwortet die Oberflaeche auf Deutsch und Franzoesisch erstmals bei jeder Anzahl in der
eingestellten Sprache statt ab zwei auf Englisch.**

## Was gebaut wurde

`L10N::n` setzt seinen Suchbegriff aus Singular und Plural zusammen und faellt auf den englischen
Quellstring zurueck, wenn der Katalog diesen zusammengesetzten Namen nicht kennt; das gebuendelte
`@nextcloud/l10n` tut im Browser dasselbe. Findling hat die fuenf Pluralschluessel seit dem ersten
Katalog als blanken Singular gefuehrt. Die Folge war messbar und ist gemessen worden, nicht
hergeleitet.

Der Paritaetsscanner `scan_placeholder_parity` hat die einzige Logikaenderung dieser Phase bekommen.
Ein zusammengesetzter Schluessel traegt jede Direktive zweimal, jede Form aber nur einmal; ein
Vergleich gegen den ganzen Schluessel haette jeden uebersetzten Plural fuer unvollstaendig gehalten.
`expected_directives_per_form` schneidet den Schluessel an der Marke, urteilt die Singularhaelfte
gegen Form 0 und die Pluralhaelfte gegen jede weitere, und laesst einen Schluessel ohne Marke
unveraendert wie bisher lesen.

## Aufgaben und Commits

| Task | Name | Commit | Dateien |
| --- | --- | --- | --- |
| 1 | Der Paritaetsscanner teilt zusammengesetzte Schluessel | `51e0ea4` | `backend/tests/test_admin_ui_contract.py` |
| 2 | Fuenf Schluessel, sechs Kataloge, ein Absatz im Gedaechtnis | `5389009` | sechs Kataloge, `test_admin_ui_contract.py`, `docs/l10n-french.md` |
| 3 | Vorher-Nachher-Beleg an der laufenden Instanz | Checkpoint, siehe unten | keine Codeaenderung |

## Der Beleg: Vorher und Nachher an derselben Instanz

Gefragt wurde `n('%n day', '%n days', $n)` ueber `IFactory` im laufenden Container
`findling-nextcloud`, fuer `de` und `fr`, je n = 1, 2 und 5. Die Vorher-Haelfte ist keine
Wiedergabe der Research vom 24.09., sondern eine eigene Messung vom 25.09.: die Katalogbytes aus
`HEAD~1` (also der Stand vor Task 2) lagen dafuer unter der Wegwerf-App-ID `l10nprobe` im selben
Container, beantwortet von derselben Nextcloud in derselben Minute.

**Vorher** (blanker Pluralschluessel, Stand vor diesem Plan):

```
de  n=1  1 Tag
de  n=2  2 days
de  n=5  5 days
fr  n=1  1 jour
fr  n=2  2 days
fr  n=5  5 days
```

**Nachher** (zusammengesetzter Pluralschluessel, ausgelieferter Stand):

```
de  n=1  1 Tag
de  n=2  2 Tage
de  n=5  5 Tage
fr  n=1  1 jour
fr  n=2  2 jours
fr  n=5  5 jours
```

Die Sondenskripte und die Wegwerf-Ablage sind nach dem Lauf aus dem Container entfernt worden;
im Repo ist keine Probedatei entstanden, `git status --short` ist leer.

## CHECKPOINT: was der Owner pruefen soll

**Typ:** `checkpoint:human-verify`, blockierend. Der Owner war zum Ausfuehrungszeitpunkt nicht
anwesend; die Sichtprobe wird ihm bei Rueckkehr vorgelegt. Der Plan bleibt bis zu seiner Antwort
offen, Phase 20 faehrt erst danach mit 20-02 weiter.

**Warum dieser Checkpoint blockierend ist:** dieser Plan aendert die **bestehenden** deutschen und
franzoesischen Kataloge und geht damit ueber den Auftrag der Phase hinaus, die eigentlich nur vier
neue Sprachen bringen soll. Die Research hat das als offene Frage 1 gefuehrt und die Reparatur in
dieser Phase empfohlen, weil dieselbe Arbeit nach den zehn neuen Dateien sechzehn statt sechs
Dateien kostet.

**Zu pruefen sind drei Dinge:**

1. **Die sechs Zeilen der Nachher-Ausgabe oben.** Erwartet: `de` liefert `1 Tag`, `2 Tage`,
   `5 Tage`, `fr` liefert `1 jour`, `2 jours`, `5 jours`. Nirgends darf `2 days` oder `5 days`
   stehen. Das ist der ganze Beleg; steht dort weiterhin Englisch, waere der Schluessel falsch
   geschrieben und der Plan nicht erfuellt.
2. **Dass die Aenderung der Bestandskataloge gewollt ist.** Kein Wortlaut, weder deutsch noch
   franzoesisch, ist angefasst worden: dieselben Werte, dieselbe Reihenfolge, dieselben zwei Formen.
   Geaendert hat sich ausschliesslich der Schluessel, unter dem sie liegen. Die Owner-Abnahmen der
   franzoesischen Wortlaute vom 11.09., 19.09. und 24.09.2026 bleiben damit vollstaendig gueltig,
   und es ist keine ungelesene Zeile hinzugekommen. `docs/l10n-french.md` traegt diesen Satz als
   datierten Nachtrag.
3. **Ob die Sonde vor seinen Augen nachgefahren werden soll.** Sie ist reine Automatisierung, der
   Owner muss dafuer nichts tun; wer sie dennoch live sehen will, sagt es, dann laeuft sie erneut.

**Resume-Signal:** "approved" bestaetigen, oder die abweichenden Zeilen der Sondenausgabe nennen.

## Abnahmekriterien, nachgemessen

| Kriterium | Ergebnis |
| --- | --- |
| Schluesselzahl in `php/l10n/de.json` | 202 vor und nach der Aenderung |
| Fuenf Listenwerte, jeder beginnt mit einem Unterstrich und traegt die Marke | ja, alle fuenf |
| `grep -c '_::_'` je Katalogdatei | 5 in allen sechs Dateien |
| `cmp de.json de_DE.json`, `cmp de.js de_DE.js` | beide still, die Zwillinge sind zeichengleich |
| LF, UTF-8 ohne BOM, abschliessender Zeilenumbruch | alle sechs Dateien, byteweise geprueft |
| `git diff --stat -- php/l10n/` | genau 5 geaenderte Zeilen je Datei, 30 insgesamt |
| `git diff --name-only -- php/templates php/js php/lib backend/src` | leer, kein Baumhash faellig |
| `grep -c '_::_' backend/tests/test_admin_ui_contract.py` | 7, gefordert waren mindestens 4 |
| `cd backend && uv run pytest -q` | 2877 passed, 15 skipped |
| ruff check, ruff format --check, pyright, vulture | alle gruen (pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, 0 errors) |

**Dass die Scanner-Aenderung tragend ist, ist gemessen und nicht behauptet:** der alte Scanner
haette ueber dem heutigen Baum 30 Funde gemeldet, obwohl jeder Wert stimmt. Die gestellte gruene
Zeile im Gate (`{"_%n day_::_%n days_": ["%n jour", "%n jours"]}`) ist mit der Teilung leer und
waere ohne sie zwei Funde lang.

## Die Paare, aus den Aufrufstellen gelesen

Der Plan hat die fuenf Paare vorgegeben und zugleich angeordnet, im Konfliktfall die Aufrufstelle
gelten zu lassen. Gelesen wurden `php/templates/admin.php:192,195,198,719,723`,
`php/lib/Service/AdminViewService.php:956` und `php/js/admin.js:126,129,131`. Alle fuenf Paare
stimmen woertlich mit dem Plan ueberein, es gab nichts abzubrechen:

| Schluessel neu | Quelle |
| --- | --- |
| `_%n minute_::_%n minutes_` | `admin.php:198`, `admin.js:131` |
| `_%n hour_::_%n hours_` | `admin.php:195`, `admin.js:129` |
| `_%n day_::_%n days_` | `admin.php:192`, `admin.js:126` |
| `_and %n more_::_and %n more_` | `admin.php:719,723`, Singular und Plural sind dort absichtlich derselbe Satz |
| `_A worker holds this file. ... %n second ..._::_... %n seconds ..._` | `AdminViewService.php:956` |

## Abweichungen vom Plan

### Regel 3 (blockierende Kleinigkeit, inline behoben)

**1. [Rule 3 - Blocker] Die Giessform musste die Listenwerte wieder einzeilig falten**

- **Gefunden in:** Task 2
- **Problem:** Das Rezept aus der Research (`json.dumps(..., ensure_ascii=False, indent=4)`)
  reproduziert den Bestand NICHT: der Bestand schreibt Listenwerte einzeilig, `json.dumps` schreibt
  sie dreizeilig. Ungeprueft uebernommen haette die Giessform 30 statt 5 Zeilen je Datei bewegt und
  die vom Plan geforderte Byte-Gegenprobe waere nicht zu erfuellen gewesen.
- **Fix:** Die Giessform faltet Listenwerte wieder auf eine Zeile und wurde ZUERST gegen den
  unveraenderten Bestand geprueft: `cast_json(alt) == alt` und `cast_js(alt) == alt` byteweise fuer
  alle sechs Dateien. Erst danach lief die Umbenennung.
- **Dateien:** keine (Einmal-Lauf, kein Generator im Repo, so wie der Phasen-Entscheid es verlangt)
- **Commit:** `5389009`

### Kleine Abweichung in der Form, nicht in der Sache

Das Abnahmekriterium von Task 1 erwartet die Teilung "innerhalb der Funktion"
`scan_placeholder_parity`, waehrend der Aktionstext desselben Tasks einen Hilfsnamen
`expected_directives_per_form` verlangt, der die Teilung an einer Stelle haelt. Beides zusammen
geht nicht. Gefolgt wurde dem Aktionstext: `key.split("_::_", 1)` steht in der Hilfsfunktion
unmittelbar ueber dem Scanner, `grep -n 'split'` zeigt sie in Zeile 419, und es gibt im ganzen
Baum genau eine Teilung an dieser Marke.

### Was ausdruecklich NICHT geaendert wurde

`KAT-01` bleibt ungehakt. Die Anforderung verlangt zehn neue Katalogdateien im Gleichstand; dieser
Plan repariert den Bestand und erfuellt sie nicht. Der Haken gehoert fruehestens zu 20-08.

Kein Pfad unter `php/templates/`, `php/js/`, `php/lib/` oder `backend/src/findling` ist angefasst
worden, also bewegt sich kein Baumhash und der Fussabdruck von Phase 19 bleibt unberuehrt.

## Authentifizierungs-Tore

Keine.

## Bekannte Stubs

Keine.

## Self-Check: PASSED

Alle neun genannten Dateien liegen im Baum, beide Commit-Hashes (`51e0ea4`, `5389009`) stehen in
der Historie. Kein Eintrag fehlt.


**OWNER-GO 25.09.2026:** Checkpoint abgenommen (Owner-Antwort "weiter" auf die vorgelegte Sichtprobe; Vorher/Nachher-Sonde und Bestandsreparatur de/fr freigegeben). Ausfuehrung laeuft weiter mit Welle 2.
