---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 05
subsystem: l10n
tags: [l10n, franzoesisch, d-07, fr-gate, 174-schluessel, rel-01, checkpoint]

# Dependency graph
requires:
  - phase: 09-eigene-ergebnisseite
    provides: die 24 vorbereiteten Wortlaute der Ergebnisseite und die fuenf Punkte der Bedingungsliste in docs/l10n-french.md
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-VORENTSCHEIDE.md, Entscheid v1-a vom 10.09.2026, und Plan 11-13, der den 174. Schluessel in die vier deutschen Kataloge geschrieben hat
provides:
  - "eine dreispaltige Tabelle Schluessel / DE / FR ueber 173 Zeilen, aus der php/l10n/fr.json und php/l10n/fr.js mechanisch entstehen"
  - "die vom Owner am 11.09.2026 abgenommene franzoesische Fassung aller 174 Katalogschluessel (D-07, Teil 1 von 2)"
  - "die benannte Ausnahmenliste fuer das Vollstaendigkeitsgate G2 von Plan 11-08: Findling und Page %s"
  - "die franzoesische Pluralregel nplurals=2; plural=(n > 1); als Wortlaut fuer fr.json und den vierten Parameter von OC.L10N.register"
  - "der Befund, dass Findling Schluessel 1 von 174 in de.json ist und deshalb in fr.json und fr.js stehen muss, sonst geht Gate G1 rot"
  - "die aus der Datei gezaehlten Zahlen 174 / 34 / 29 / 5 mit der Erklaerung, warum 34 und 29 dieselbe Sache zweimal messen"
affects: [11-08, 11-09, 11-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Uebersetzung entsteht als Tabelle und wird abgenommen, bevor sie in Katalogdateien gegossen wird: der Owner liest einen Lesevorgang statt vier Diffs"
    - "Die Spalten, die eine Maschine bereits kennt (Schluessel, DE), werden aus der Quelldatei erzeugt und nicht abgetippt; nur die neue Spalte ist Handarbeit"
    - "Eine Ausnahmenliste wird benannt und begruendet, eine Toleranzschwelle waere die Vermeidung derselben Arbeit"
    - "Eine Begriffstabelle vor der Wortlauttabelle macht die Abnahme zu einer Entscheidung je Begriff statt zu 174 Einzelfaellen"
    - "Typografieregeln einer Zielsprache werden am Bestand des Repositoriums festgemacht und nicht am Regelwerk der Sprache, damit ein Diff nicht zwei Schulen mischt"

key-files:
  created: []
  modified:
    - docs/l10n-french.md

key-decisions:
  - "Die Schluesselmenge ist aus php/l10n/de.json gezaehlt und nicht aus der Recherche uebernommen. 174 statt 173 ist kein Befund, sondern Entscheid v1-a; die Datei nennt Plan 11-13 als Herkunft"
  - "Die Datei nennt vier Zahlen statt drei: 34 Schluessel mit printf-Direktiven und 29 ohne die fuenf Pluralschluessel. Beide stehen da, weil die Recherche 29 zaehlt und eine naive Nachzaehlung 34 findet, und die naechste Zaehlung sonst eine der beiden fuer falsch haelt"
  - "backend heisst durchgehend le service, nach dem seit Phase 9 abgenommenen Wortlaut der Ergebnisseite. Wo der Eigenname gemeint ist, bleibt Findling Backend stehen"
  - "run heisst passage und nicht execution, a worker heisst un processus de traitement und nicht un travailleur: die deutsche Vorlage sagt Arbeiter, aber ein franzoesischer Leser denkt dort an eine Person"
  - "Das Register folgt dem Deutschen zeilenweise: die Verwaltungsseite im Infinitiv, die Ergebnisseite im Vouvoiement. Ein einheitliches Register waere eine Textrunde gewesen, die niemand bestellt hat"
  - "Vor : ; ? ! steht ein einfaches Leerzeichen und nicht U+00A0 oder U+202F. Das ist die Form des franzoesischen Bestands (README.fr.md, info.xml) und die einzige, die den Katalog nicht mit unsichtbaren Zeichen fuellt"
  - "Findling steht nicht in der Tabelle, wie der Plan es verlangt, aber mit Wortlaut in der Ausnahmenliste. Beides zusammen ist der einzige Weg, der die Abnahmekriterien und Gate G1 von 11-08 gleichzeitig haelt"
  - "Die drei 173er-Stellen der Datei sind hier bearbeitet und nicht an 11-10 weitergereicht, weil docs/l10n-french.md in files_modified dieses Plans steht. Die beiden historischen Aussagen behalten ihre damalige Zahl und sind als Geschichte kenntlich, die vorwaertsgerichtete Bedingung nennt jetzt 174"

patterns-established:
  - "Der Ausfuehrende zaehlt die Groesse seines Gegenstands aus der Datei, bevor er die Zahl der Recherche zitiert, und schreibt beide hin"
  - "Vor einem Text-Gate steht eine Begriffstabelle, damit der Owner Begriffe entscheidet und nicht Zeilen"

requirements-completed: []

# Metrics
duration: 30min
completed: 2026-09-11
---

# Phase 11 Plan 05: Die vollstaendige franzoesische Uebersetzung und ihre Abnahme Summary

**Die 149 neuen franzoesischen Zeichenketten sind geschrieben, stehen mit den 24 der Ergebnisseite in einer einzigen dreispaltigen Tabelle ueber alle 174 Katalogschluessel, und der Owner hat sie am 11.09.2026 in einem Lesevorgang ohne eine einzige Korrektur abgenommen; 11-08 kann `fr.json` und `fr.js` daraus giessen, ohne eine zweite Textrunde zu eroeffnen.**

## Die Zahlen, aus der Datei gezaehlt

Erster Handgriff, wie der Plan es verlangt, mit `json.load` ueber `php/l10n/de.json`
statt mit den Zahlen der Recherche:

| Groesse | Wert | Recherche vom 10.09. |
|---|---:|---:|
| Schluessel in `de.json` | **174** | 173 |
| mit printf-Direktiven | **34** | |
| mit Direktiven, ohne die Pluralschluessel | **29** | 29 |
| mit Pluralformen (Wert ist eine Liste) | **5** | 5 |
| Zeilen in der Tabelle | **173** | |
| davon woertlich aus Phase 9 | **24** | 24 |
| neu uebersetzt | **149** | 149 |

Die **174 ist keine Abweichung, sondern der Entscheid**: v1-a vom 10.09.2026,
`11-VORENTSCHEIDE.md` Zeile 116, gebaut von Plan 11-13 in Welle 2. Die Datei nennt
diese Herkunft an der Zahl, damit ein spaeterer Leser die gestiegene Zahl nicht fuer
Nachlaessigkeit haelt und wieder senkt.

Die **34 und die 29 sind dieselbe Sache zweimal gemessen**: die Recherche zaehlt die
Schluessel mit Platzhaltern ohne die fuenf Pluralschluessel, deren `%n` ebenfalls eine
Direktive ist. Eine naive Nachzaehlung findet 34 und haelt die 29 fuer falsch. Beide
Zahlen stehen deshalb in der Datei, mit dem Satz, der sie auseinanderhaelt. Das ist
keine Abweichung von 29 und 5, sondern ihre Erklaerung.

## Die Tabelle

173 Zeilen, `| Schluessel | DE | FR |`, in der Reihenfolge von `de.json`. Die Spalten
`Schluessel` und `DE` sind **nicht abgetippt, sondern aus der Datei erzeugt**: ein
Skript liest `php/l10n/de.json` und setzt die Zeilen, nur die FR-Spalte ist Handarbeit.
Damit kann eine Zeile der Tabelle nicht stillschweigend von dem abweichen, was die App
tatsaechlich uebersetzt, und die Pruefung "Reihenfolge identisch mit `de.json`" ist
konstruktiv wahr statt nachtraeglich geprueft.

Der Spaltenname ist ASCII (`Schluessel`), weil er ein Vertragsbezeichner ist; die
Projektregel behaelt echte Umlaute der deutschen Prosa vor, und die Datei sagt das an
der Stelle.

Vor der Tabelle stehen drei Abschnitte, die die Abnahme billig machen:

- **Wortwahl**, eine Begriffstabelle mit zehn Zeilen und je einer Begruendung. Damit
  entscheidet der Owner `le service` einmal und nicht siebenmal.
- **Typografie**, fuenf Regeln, jede am franzoesischen Bestand des Repositoriums
  festgemacht und nicht am Regelwerk der Sprache.
- **Pluralformen**, die franzoesische Regel und der Unterschied, der sie noetig macht.

## Die Sprache, und die drei Entscheidungen darin

Die 24 Wortlaute der Ergebnisseite sind woertlich uebernommen und nicht neu erfunden.
Die 149 neuen sind die Verwaltungsseite: die Verdikt-Labels mit ihren Abhilfen, die
Zustandsnamen, die Regeln und Grenzen, die Einzeldateipruefung.

Drei Entscheidungen sind Entscheidungen und keine Uebersetzungen, deshalb stehen sie in
der Wortwahl-Tabelle und sind vom Owner ausdruecklich bestaetigt worden:

| Englisch | Franzoesisch | Der Grund |
|---|---|---|
| the backend | `le service` | So steht es seit Phase 9 im abgenommenen Wortlaut der Ergebnisseite (`Findling n'a pas pu joindre son service`). Wo der Eigenname gemeint ist, bleibt `l'application externe "Findling Backend"` stehen |
| run, Lauf | `passage` | `execution` ist das schwerere Wort fuer dieselbe Sache. `Abgleichlauf` wird `passage de comparaison`, `Hintergrundlauf` wird `passage en arriere-plan` |
| A worker | `un processus de traitement` | Die deutsche Vorlage sagt `Ein Arbeiter`. Woertlich uebersetzt denkt ein franzoesischer Leser an eine Person, und die Zeile spricht von einem Verarbeitungsprozess, der eine Datei haelt |

Das Register folgt dem Deutschen zeilenweise: wo die Verwaltungsseite im Infinitiv
anweist (`Den Wert unter ... erhoehen.`), steht der franzoesische Infinitiv
(`Augmenter la valeur sous ...`); wo die Ergebnisseite siezt (`Versuchen Sie ...`),
steht das Vouvoiement (`Essayez ...`). Der 174. Schluessel gehoert zur Ergebnisseite und
ist entsprechend gesetzt:

| Englisch | Deutsch | Franzoesisch |
|---|---|---|
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie oeffnen duerfen. | D'autres fichiers contiennent ce mot, mais aucun que vous soyez autorise a ouvrir. |

(Die Akzente stehen in der Datei, diese Zusammenfassung gibt sie zur Sicherheit gegen
Zeichensatzfehler in der Reproduktion nicht wieder.)

## Die Ausnahmenliste fuer G2, und der Befund darin

Gate G2 von Plan 11-08 fordert, dass kein FR-Wert leer und keiner mit dem englischen
Quellstring identisch ist. Genau zwei Schluessel sind es absichtlich, beide benannt und
begruendet, ausdruecklich **keine Toleranzschwelle**:

- `Findling`, Eigenname, in allen drei Sprachen derselbe.
- `Page %s`, im Franzoesischen dasselbe Wort; eine Abweichung waere eine
  Verschlechterung.

**Befund, und er gehoert 11-08:** `docs/l10n-french.md` hat bis heute behauptet,
`Findling` sei "kein Uebersetzungsschluessel und wurde in Plan 09-05 auch nicht als
einer angelegt". Gegen die Datei gehalten stimmt das nicht: `Findling` ist **Schluessel
1 von 174** in `php/l10n/de.json` und traegt dort sich selbst als Wert. Fuer die
Copy-Tabelle der Phase 9 war die Aussage richtig gemeint, fuer den Katalog ist sie
falsch. Die Folge ist keine Nebensache: **`fr.json` und `fr.js` muessen den Schluessel
`Findling` mit dem Wert `Findling` tragen, sonst geht Gate G1 (Schluesselgleichheit
ueber alle sechs Dateien) rot.** Er steht deshalb nicht in der Tabelle, wie der Plan es
verlangt, aber mit Wortlaut in der Ausnahmenliste, und der Befund steht ausgeschrieben
daneben.

## Die drei 173er-Stellen aus der Uebergabe von 11-13

Plan 11-13 hat festgehalten, dass `docs/l10n-french.md` an drei Stellen noch 173 nennt,
und die Bearbeitung bewusst diesem Plan ueberlassen. Die Datei steht in `files_modified`
von 11-05, also sind sie hier bearbeitet und **nicht** an 11-10 weitergereicht worden:

| Stelle | Vorher | Jetzt |
|---|---|---|
| "Die 24 hier sind genau die 24 Schluessel ... (149 auf 173)" | Aussage ueber Phase 9 | steht unter einer Ueberschrift, die sie als Geschichte ausweist, mit "auf die damaligen 173" |
| "Ein Katalog, der 24 von 173 Zeichenketten uebersetzt" | Begruendung der Vertagung | steht unter "Warum vertagt", ausgewiesen als Geschichte, mit "von damals 173" |
| "Massgeblich ist die Schluesselmenge ... heute 173" | vorwaertsgerichtete Bedingung | "zum Zeitpunkt der Uebersetzung: damals 173, zum Zeitpunkt der Uebersetzung **174** (Entscheid V-1a, gebaut von Plan 11-13)" |

Die beiden ersten waren am Tag ihrer Niederschrift wahr und werden deshalb nicht
umgeschrieben, sondern eingeordnet. Die dritte war eine Bedingung fuer die Zukunft und
ist nachgefuehrt.

## Das FR-Gate, Teil 1 von 2

**Abgenommen am 2026-09-11**, die Zeile steht datiert in derselben Datei, die 11-08
giessen wird (T-11-18). Der Owner, franzoesischer Muttersprachler, hat die Tabelle
vollstaendig gelesen und **keine Korrektur genannt**. Die drei Wortwahl-Entscheidungen
oben sind ausdruecklich bestaetigt.

Die Zahl der Tabellenzeilen ist vor und nach der Abnahme **173**, die Schluesselmenge
identisch: keine Korrektur hat einen Schluessel entfernt oder hinzugefuegt, es gibt also
auch keinen Befund dieser Art zu benennen. Die maschinellen Pruefungen sind nach der
Abnahme erneut gefahren worden.

Teil 2 von 2 (Store-Text, `README.fr.md`, die franzoesischen Teile von `info.xml`) steht
aus und ist Gegenstand von Plan 11-09. Die Datei sagt das an der Abnahmezeile, damit
niemand Teil 1 fuer D-07 haelt.

## Maschinelle Pruefungen

Zweimal gefahren, vor und nach der Abnahme, beide Male gegen die **geschriebene Datei**
und nicht gegen das erzeugende Skript, und nicht per Augenmass:

| Pruefung | Ergebnis |
|---|---|
| Jeder Schluessel aus `de.json` kommt in der Datei vor (Verify-Befehl des Plans) | `fehlend: 0`, Exit 0 |
| Tabellenzeilen | 173, vor und nach der Abnahme gleich |
| Schluesselmenge und Reihenfolge identisch mit `de.json` ohne `Findling` | ja |
| Duplikate in der Schluesselspalte | 0 |
| Platzhalter-Paritaet ueber alle 34 Schluessel mit Direktiven, beide Pluralformen einzeln | 0 Abweichungen |
| Pluralschluessel mit genau zwei Formen | 5 von 5 |
| `nplurals=2; plural=(n > 1);` in der Datei | ja |
| U+2019 (typographischer Apostroph) | 0 |
| U+2014 und U+2013 | 0 |
| U+00A0 und U+202F (geschuetzte Leerzeichen) | 0 |
| FR-Wert identisch mit dem englischen Quellstring | 2, beide in der Ausnahmenliste benannt |
| `Findling` in der Schluesselspalte einer Tabellenzeile | nein |
| Zeilen mit ` / ` in der FR-Spalte | genau die 5 Pluralzeilen, also ein verlaesslicher Trenner fuer 11-08 |
| Dateilaenge | 398 Zeilen, `min_lines: 220` |
| Zeilenenden | LF, 0 CRLF (die Datei faellt nicht unter `.gitattributes`, `core.autocrlf` ist `true`) |

**Grundlinie unveraendert.** `uv run python -m pytest -q` in `backend/`: **2012 passed,
15 skipped**. `ruff check .`, `ruff format --check .`, `ruff check --config
pyproject.toml ../scripts`, `ruff format --config pyproject.toml --check ../scripts`,
`pyright` (0 errors, 0 warnings) und `vulture src tests --min-confidence 80` ohne
Befund. Der Plan aendert nur eine Markdown-Datei, und kein Gate liest sie heute
inhaltlich; die Suite ist trotzdem gefahren, weil die Konvention der Phase es verlangt.

## Was gebaut wurde, Task fuer Task

**Task 1, die Tabelle.** Die Zahlen aus der Datei gezaehlt, die bestehende
24-Zeilen-Tabelle durch eine 173-Zeilen-Tabelle ersetzt, die 24 Wortlaute woertlich
uebernommen, 149 neue geschrieben, Wortwahl-, Typografie- und Pluralabschnitt davor, die
Ausnahmenliste mit dem Findling-Befund darunter, die Geschichte der Phase 9 als
Geschichte erhalten und die drei 173er-Stellen eingeordnet. Commit `9e391e6`.

**Task 2, das Gate.** Abnahme ohne Korrektur, Abnahmezeile mit Datum und mit dem
ausdruecklichen "Teil 1 von 2 (Katalog), D-07", die bestaetigten drei Begriffe
namentlich festgehalten, maschinelle Pruefungen erneut gefahren. Commit `2fbd8a1`.

## Deviations from Plan

Keine. Der Plan ist ausgefuehrt wie geschrieben, kein Paket installiert (T-11-SC), keine
Architekturaenderung, keine Auto-Fix-Runde.

Zwei Dinge, die nach Abweichung aussehen und keine sind, beide vom Plan so vorgesehen:
die Schluesselzahl 174 statt 173 ist Entscheid v1-a und ausdruecklich keine Abweichung,
und die Direktivenzahl 34 statt 29 ist dieselbe Messung mit und ohne die
Pluralschluessel. Beides ist in der Datei benannt.

## Threat Flags

Keine. Der Plan fuehrt keine Netzwerkschnittstelle, keinen Auth-Pfad, keinen Dateizugriff
und keine Schemaaenderung ein; er aendert eine Markdown-Datei. Die Dispositionen des
Registers sind bedient, soweit dieser Plan sie bedienen kann:

- **T-11-16** (FR-Werte mit `<` oder `&`): kein FR-Wert traegt `<`, `>` oder `&`. Die
  Werte gehen in 11-08 durch das dortige Gate und in 11-10 durch das Audit unter
  ASVS V5.
- **T-11-17** (verlorener Platzhalter): Paritaet je Zeile maschinell geprueft, 0
  Abweichungen ueber 34 Schluessel, beide Pluralformen einzeln.
- **T-11-18** (Abnahme des Owners): datiert in derselben Datei, die gegossen wird, und
  ausdruecklich als Teil 1 von 2 bezeichnet.
- **T-11-19** (Information Disclosure): accept, unveraendert.

## Uebergaben

- **11-08** giesst aus dieser Tabelle. Drei Dinge sind dafuer festgehalten: die
  FR-Spalte ist der Wert, ` / ` trennt Singular und Plural und kommt in genau den fuenf
  Pluralzeilen vor, und **`Findling` ist der 174. Wert und steht nicht in der Tabelle,
  sondern in der Ausnahmenliste**. Wer nur die Tabelle liest, baut ein `fr.json` mit 173
  Schluesseln und laesst Gate G1 rot werden. Die Pluralregel fuer G4 steht als Wortlaut
  in der Datei, ebenso die zweite G2-Ausnahme `Page %s`.
- **11-09** fuehrt Teil 2 von 2 des FR-Gates. Die Wortwahl-Tabelle dieser Datei ist die
  Vorlage, an der sich Store-Text und `README.fr.md` messen lassen muessen, damit die
  Oberflaeche nicht `le service` sagt, wo der Store-Text von etwas anderem spricht.
- **11-10** bekommt von hier **keinen** offenen Punkt. Die drei 173er-Stellen aus der
  Uebergabe von 11-13 sind in diesem Plan bearbeitet worden und nicht weitergereicht.
- **11-11** setzt den Versionsbump. REL-01 bleibt ungehakt: die Uebersetzung ist
  geschrieben und abgenommen, aber die Kataloge existieren erst nach 11-08 und die
  Abgabe erst danach.

## Self-Check: PASSED
