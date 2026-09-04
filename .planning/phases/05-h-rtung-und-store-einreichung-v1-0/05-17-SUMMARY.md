---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 17
subsystem: packaging
tags: [store, info-xml, i18n, xsd, privacy, donation, versioning, textual-gate]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: den Uninstall-Vertrag und die Absichtsmarke aus Plan 05-02, an denen der Privacy-Absatz nichts zu ändern hatte
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: das Lockstep-Gate aus Plan 05-07, das bewusst keine Zahl nennt und deshalb diesen Bump nicht behindert
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die gemessene Kernaussage aus Plan 05-14, wortwörtlich zitiert statt neu formuliert
provides:
  - D-12 erfüllt für den Textteil: beide Store-Einträge tragen Name, Kurzbeschreibung und Beschreibung in Englisch, Deutsch und Französisch
  - Sec-L1 geschlossen: der gespeicherte Dokumenttext steht jetzt in beiden Beschreibungen, in allen drei Sprachen, und zusätzlich in der Privacy-Liste des README
  - D-11 erfüllt: beide Hälften und der image-tag stehen auf 1.0.0, mit fortgeschriebenem Versionskommentar auf beiden Seiten
  - D-27 erfüllt: ein donation-Element mit dem Link des Schwesterprojekts, in beiden Einträgen
  - Ein Textgate über beide info.xml und README, das die Übersetzungs-Nachzieh-Regel, die Schemakanten und die Typografie mechanisch prüft
  - docs/store-listing.md als die eine Quelle der sechs Texte, mit Längenzählung je Kurzbeschreibung
affects: [05-18-store-medien, release-v1-0-0, phase-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein dreisprachiger Text, der in zwei Dateien gepflegt wird, braucht eine dritte Datei, in der alle Fassungen nebeneinander stehen: die Nachzieh-Regel ist sonst nicht lesbar und nicht prüfbar"
    - "Die englische Fassung eines l10n-Elements steht ohne lang-Attribut, weil die XSD den Wert en als Vorgabe einsetzt und ein ausgeschriebenes lang=en die Eindeutigkeit verletzen würde"
    - "Ein Befund je Ursache und nicht je Folge: ein Sprachcode, den das Schema nicht kennt, darf nicht zusätzlich als drei fehlende Übersetzungen gemeldet werden"
    - "Eine Zahl, die an drei Orten steht, wird nach dem Einebnen der Leerzeichen verglichen: der Zeilenumbruch einer Markdown-Datei ist kein Unterschied in der Aussage"
    - "Der Store-Validierungspfad lässt sich ohne lokale Werkzeuge in einem Wegwerf-Container nachfahren, mit denselben gepinnten Dateien, die der Runner holt"

key-files:
  created:
    - docs/store-listing.md
    - backend/tests/test_store_metadata.py
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - README.md
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Der Name bleibt in allen drei Sprachen derselbe, steht aber trotzdem dreimal da: eine Elementart mit nur einer Sprache wäre von einer, die zwei verloren hat, nicht zu unterscheiden, und die Nachzieh-Regel prüft genau das"
  - "Dieses Repository führt kein Vokabular-Gate; es gilt die Regel des Owners, und der gesperrte Begriff kommt in keiner der sechs Fassungen vor, auch nicht in der englischen, weil kein Text einzelne Dateitypen aufzählt"
  - "Das donation-Element trägt zusätzlich type=paypal, weil die gepinnte XSD den Wert kennt und der Store damit das Ziel benennen kann statt nur eine Adresse zu zeigen"
  - "Kein leeres screenshot-Element, sondern ein Absichtskommentar an seinem Platz in der Sequenz: ein leeres Element beendet den Upload mit einem Serverfehler"
  - "Die Mindestzahl von einem Screenshot je App wird ausdrücklich NICHT in diesem Gate gesetzt; sie kommt mit Plan 05-18, und ein Kommentar sagt das, damit die Lücke nicht als Versehen gelesen wird"
  - "Der Store-Validierungspfad wurde lokal in einem Wegwerf-Abbild nachgefahren, weil die Entwicklungsmaschine weder xsltproc noch xmllint hat und ein Schema-Fehler beim Upload ungleich teurer ist als hier"

patterns-established:
  - "Die Anti-Vakuitätsklausel eines Textgates prüft auch die Datei, die nur gelesen und nicht geparst wird: README.md fällt sonst aus der Prüfung, ohne dass etwas rot wird"
  - "Eine Regel, deren Gegenstand heute null Vorkommen hat, wird so geschrieben, dass sie jedes vorhandene Vorkommen beurteilt, und die Mindestzahl bleibt dem Plan überlassen, der die Gegenstände anlegt"

requirements-completed: [PKG-05]

# Metrics
duration: ca. 1h 40m
completed: 2026-09-04
---

# Phase 5 Plan 17: Die Store-Texte in drei Sprachen und ein Gate darüber Summary

**Beide Store-Einträge tragen jetzt Name, Kurzbeschreibung und Beschreibung in Englisch, Deutsch und Französisch, jede der sechs Beschreibungen benennt den gespeicherten Dokumenttext und zitiert die gemessene Spitze von 429 MB wortwörtlich aus dem Messbericht, beide Hälften und der image-tag stehen auf 1.0.0 mit einem Spendenlink, beide Dateien bestehen den Store-Validierungspfad lokal, und ein neues Gate mit 23 Prüfungen macht die Übersetzungs-Nachzieh-Regel, die Schemakanten und die Typografie mechanisch.**

## Performance

- **Duration:** rund 1 h 40 min
- **Tasks:** 3, alle autonom, kein Checkpoint
- **Files modified:** 6 Dateien, davon 2 neu
- **Gates:** `969 passed, 11 skipped` in der vollen Suite, ruff, ruff format, pyright und vulture sämtlich sauber

## Accomplishments

- **D-12 ist für den Textteil erfüllt, und zwar in der Form, die die XSD verlangt.** Beide `info.xml` tragen `name`, `summary` und `description` je dreimal, in der Reihenfolge der `xs:sequence`, mit der englischen Fassung in einem Element ohne `lang`-Attribut. Das ist keine Bequemlichkeit: die XSD setzt für ein fehlendes Attribut die Vorgabe `en` ein, ein ausgeschriebenes `lang="en"` daneben wäre ein zweiter Eintrag desselben Codes und würde `uniqueNameL10n` verletzen.
- **Sec-L1 ist geschlossen, und zwar an drei Stellen statt an einer.** Der ehrliche Privacy-Absatz der Backend-Fassung war die Vorlage; er steht jetzt in beiden Einträgen und in allen drei Sprachen. Die Prüfung der `README.md` hat dieselbe Lücke ein drittes Mal gefunden: die Privacy-Liste zählte vier Zusagen auf und liess das eine weg, was tatsächlich gespeichert wird. Der Absatz steht jetzt auch dort, siehe Deviations.
- **Die gemessene Zahl steht an drei Orten und wird an drei Orten geprüft.** Der Satz aus Plan 05-14 ist zitiert und nicht neu formuliert, in `README.md` und in beiden englischen Beschreibungen. Das Gate vergleicht ihn nach dem Einebnen der Leerzeichen, weil eine Markdown-Datei anders umbricht als eine `info.xml` und ein Zeilenumbruch nichts über die Aussage sagt. Dazu gehört in jeder Sprache der Zusatz aus dem Bericht: die Maschine war x86, die Wiederholung auf ARM steht aus, und `docs/performance.md` nennt jede Zahl, die sie ersetzen wird.
- **Der Store-Validierungspfad ist lokal nachgefahren, nicht nur behauptet.** Auf der Entwicklungsmaschine gibt es weder `xsltproc` noch `xmllint`. Beides lief in einem Wegwerf-Abbild aus `php:8.2-cli`, gegen genau die beiden Dateien, die der Runner holt: `pre-info.xslt` und `info.xsd` unter `APPSTORE_SHA 5c4373d7`. Ausgabe für beide Dateien: `validates`. Die beiden Findings-Schritte aus `php.yml` wurden im selben Lauf mitgeprüft, weil sie Annahmen über denselben Transformationsweg festhalten.
- **Das neue Gate hat sich beim ersten Lauf selbst korrigiert.** Ein Selbsttest verlangte zwei Befunde für einen Tippfehler und bekam vier. Der Grund war eine echte Schwäche und kein zu strenger Test: ein `de_DE` wurde in die Menge der erwarteten Sprachen aufgenommen und erzeugte damit drei Folgebefunde über fehlende `de_DE`-Übersetzungen. Behoben, mit dem Grund im Code, und die Regel ist dieselbe, die das Lockstep-Gate für sich formuliert: die Gestalt ist der Fehler, der Unterschied ist die Folge, und zwei Zeilen für eine Ursache schicken den Leser auf die Suche nach einem zweiten Problem.
- **Beide Rot-Proben des Plans sind durchgeführt und zurückgenommen.** Ein Gedankenstrich in `README.md` macht `test_no_store_text_carries_a_dash_or_an_emoji` rot mit der Meldung `README.md: carries an em dash`. Ein entferntes `<name lang="de">` in `php/appinfo/info.xml` macht `test_both_info_files_keep_the_schema_edges_and_all_three_languages` rot mit `php/appinfo/info.xml: the name has no entry for lang=de, although another element kind has one`. Beide Änderungen wurden mit `git checkout --` auf die eine betroffene Datei zurückgenommen.

## Task Commits

1. **Task 1: Eine Quelle für drei Sprachen** - `1035a58` (docs)
2. **Task 2: Beide info.xml auf 1.0.0, dreisprachig, mit donation** - `467cf71` (feat)
3. **Task 3: Das Gate über die Store-Texte** - `c9aaa1e` (test)
4. **Task 3, Nachtrag: der gespeicherte Text in der README-Privacy-Liste** - `adba1d6` (docs)
5. **Zwei Befunde ausserhalb des Umfangs notiert** - `2f231e8` (docs)

**Plan-Metadaten:** dieser SUMMARY (docs)

## Files Created/Modified

- `docs/store-listing.md` (neu, 258 Zeilen): je App ein Abschnitt, darin `name`, `summary` und `description` in drei Sprachen, mit der Angabe, in welches Element jeder Text geht, und mit der gezählten Länge jeder Kurzbeschreibung. Davor die Regeln, die für alle sechs Texte gelten, der Befund zum Vokabular, die zitierte Messzahl, und am Ende der Abschnitt, was in den Texten bewusst nicht steht.
- `php/appinfo/info.xml`: Textblock von drei auf neun Elemente, Version `0.3.0` auf `1.0.0`, `donation` zwischen `repository` und `dependencies`, ein Absichtskommentar für die Screenshots aus Plan 05-18. Der Versionskommentar ist nach dem bestehenden Vertrag fortgeschrieben. Unangetastet: `dependencies`, die drei einzeiligen Blöcke und ihre Begründung.
- `backend/appinfo/info.xml`: dieselben vier Änderungen, dazu `image-tag` auf `1.0.0` und der fortgeschriebene Kopfkommentar. Unangetastet: der ganze `external-app`-Block mit fünf Routen und siebzehn Umgebungsvariablen.
- `backend/tests/test_store_metadata.py` (neu, 337 Zeilen): das Gate, mit zehn Regeln, einer Anti-Vakuitätsklausel und dreizehn Selbsttests.
- `README.md`: ein Aufzählungspunkt in der Privacy-Liste.
- `deferred-items.md`: DI-05-24 und DI-05-25.

## Decisions Made

- **Der Name steht dreimal da, obwohl er dreimal derselbe ist.** "Findling" ist ein Eigenname und wird nicht übersetzt. Trotzdem tragen beide Dateien drei `name`-Elemente, denn die Nachzieh-Regel ist eine Aussage über Elementmengen: eine Elementart mit genau einer Sprache wäre von einer, die zwei Sprachen eingebüsst hat, nicht zu unterscheiden. Der eingefrorene Name kommt aus `docs/store-identity.md` und wurde nicht neu erfunden.
- **Zum Vokabular: dieses Repository führt kein Gate dafür.** Gesucht wurde in `backend/tests` und in `scripts/ci`. Es gibt Gate A, Gate B, Gate C, das Lockstep-Gate, das Paritäts-Gate, das Uninstall-Gate und die Prüfung des deutschen Kompositum-Wörterbuchs, aber keine Prüfung gegen eine Liste verbotener Projektbegriffe. Es gilt daher die Regel des Owners für öffentliche Artefakte. Der gesperrte Begriff für einen Aufbewahrungsort kommt in keiner der sechs Fassungen vor: die deutsche und die französische sprechen von einer Sicherung, die englische bräuchte ihn nur als Dateityp-Bezeichnung und kommt ebenfalls ohne aus, weil kein Text einzelne Dateitypen aufzählt. `docs/store-listing.md` selbst nennt ihn ebenfalls nicht, auch nicht in dem Abschnitt, der die Regel erklärt.
- **`type="paypal"` am donation-Element.** Der Plan verlangt den Link. Die gepinnte XSD kennt für `donation` ein optionales `type` mit den Werten `paypal`, `stripe` und `other`. Der Wert ist wahr, er ist im Schema, und er lässt den Store das Ziel benennen statt eine nackte Adresse zu zeigen. Beide Dateien tragen ihn.
- **Kein leeres `screenshot`-Element, und die Mindestzahl gehört nicht in dieses Gate.** Ein leeres Element beendet den Upload mit einem Serverfehler, das ist die teuerste bekannte Falle des Schwesterprojekts. An seinem Platz in der Sequenz steht deshalb ein Kommentar mit der Absicht für Plan 05-18. Das Gate prüft dazu passend jede vorhandene Adresse auf `https` und auf 256 Zeichen und verlangt ausdrücklich keine Mindestzahl; ein Kommentar sagt, warum, damit die Lücke nicht als Versehen gelesen wird.
- **Die Bewertung "kein Querverweis auf den MCP Connector" gilt den sechs Store-Texten.** In `docs/store-listing.md` wird der Ausschluss beim Namen genannt, in einem Abschnitt, der ausdrücklich nicht in eine `info.xml` gehört. Eine Regel, die ihren Gegenstand verschweigt, kann niemand nachprüfen; in den Texten selbst kommt er nicht vor, und das ist es, was D-12 verlangt.
- **Der Bump passiert genau hier.** Beide Versionskommentare sagen jetzt, dass 1.0.0 eine Entscheidung ist und keine Folge: D-11 nennt die Zahl für das Store-Erstrelease, kein Protokoll hat sich geändert, keine Route ist dazugekommen. Der Backend-Kopfkommentar hat dafür seine beiden bestehenden Regeln in die Vergangenheitsform gesetzt und die neue daneben gestellt, weil er ausdrücklich der Ort ist, an dem der nächste Plan nachschlägt, unter welcher Regel er steht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Die Privacy-Liste des README liess den gespeicherten Text weg**

- **Found during:** Task 3, beim vorgesehenen Abgleich der `README.md`
- **Issue:** Die Liste unter "Privacy" nannte vier Zusagen: kein Inhalt verlässt den Server, keine Telemetrie, keine Schreibzugriffe, kein zweites Rechtemodell. Sie liess das eine weg, was tatsächlich gespeichert wird, nämlich den aus jedem indexierten Dokument gewonnenen Text im Datenspeicher der Backend-App. Das ist derselbe Befund, den Sec-L1 gegen die PHP-Store-Beschreibung erhoben hat, in dem öffentlichen Artefakt, das mehr Menschen lesen als beide Store-Einträge zusammen. Eine Datenschutzaussage, die die Aufzählung eröffnet und die einzige Speicherung auslässt, ist irreführend, und zwar unabhängig davon, ob sie wörtlich falsch ist.
- **Fix:** ein fünfter Aufzählungspunkt an zweiter Stelle, direkt hinter der Zusage, die er einschränkt, mit demselben Inhalt wie der Absatz in beiden Store-Beschreibungen und mit dem Hinweis, dass er dort in allen drei Sprachen steht.
- **Files modified:** README.md
- **Verification:** `test_store_metadata.py` bleibt grün, kein Gedankenstrich, kein Emoji, die zitierte Messzahl unverändert
- **Committed in:** `adba1d6`

**2. [Rule 1 - Bug] Das eigene Gate meldete drei Folgebefunde für eine Ursache**

- **Found during:** Task 3, beim ersten Lauf der Selbsttests
- **Issue:** `_missing_translations` bildete die Menge der erwarteten Sprachen aus allen vorgefundenen Codes, also auch aus denen, die das Schema nicht kennt. Ein einziges `de_DE` an einem `summary` erzeugte damit vier Befunde: den falschen Code, das fehlende `de` an derselben Elementart, und zusätzlich ein fehlendes `de_DE` an `name` und an `description`. Drei davon beschreiben Probleme, die es nicht gibt, und alle vier verschwinden mit derselben einen Berichtigung.
- **Fix:** in die Erwartung gehen nur Sprachcodes ein, die das Schema kennt. Der Selbsttest verlangt jetzt genau zwei Befunde und prüft beide namentlich; die Begründung steht im Docstring der Funktion, mit dem Verweis auf dieselbe Regel im Lockstep-Gate.
- **Files modified:** backend/tests/test_store_metadata.py
- **Verification:** `23 passed` über das neue Gate und das Lockstep-Gate
- **Committed in:** `c9aaa1e`

### Nicht behoben, sondern notiert

**3. DI-05-24: `docs/testing.md` kennt das neue Gate nicht, und nichts verlinkt `docs/store-listing.md`**

Die Gate-Tabelle in `docs/testing.md` nennt jedes textuelle Gate mit dem Satz, was es verhindert. Das neue fehlt dort, und die neue Quelldatei der Store-Texte wird von keiner Doku-Seite verlinkt. Beide Dateien stehen nicht in den `files_modified` dieses Plans, und ein paralleler Ausführer arbeitet in derselben Welle.

**4. DI-05-25: Der Store-Validierungspfad hat kein lokales Werkzeug**

Der Pfad wurde für diesen Plan in einem Wegwerf-Abbild nachgefahren, das nicht Teil des Repositories ist und diesen Plan nicht überlebt. Ein Skript unter `scripts/dev/` wäre eine neue Datei ausserhalb des Umfangs, und die Frage Container gegen Abhängigkeit berührt die Bezugsdisziplin, die in dieser Phase unter einem Owner-Gate steht.

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1), 2 als Befund notiert
**Impact on plan:** Kein zusätzlicher Umfang und keine Änderung an Code des Produkts. Beide Behebungen liegen innerhalb der `files_modified` dieses Plans.

## TDD Gate Compliance

Task 3 trägt `tdd="true"`, und der Gegenstand ist ein Gate. Ein Gate ist der Test, es gibt kein Produktionsverhalten daneben, das erst rot und dann grün werden könnte; die Bauform dieses Repositories ersetzt den RED-Schritt deshalb dauerhaft durch Selbsttests gegen inszenierte Proben, dreizehn an der Zahl, je Regel mindestens eine. Der RED-Schritt hat trotzdem zweimal stattgefunden und ist beide Male protokolliert:

| Probe | Erwartung | Ergebnis |
|---|---|---|
| Selbsttest zu `de_DE` beim ersten Lauf | zwei Befunde | vier, siehe Deviation 2, behoben |
| Gedankenstrich an `README.md` angehängt | rot | `README.md: carries an em dash`, zurückgenommen |
| `<name lang="de">` aus `php/appinfo/info.xml` entfernt | rot | `the name has no entry for lang=de, although another element kind has one`, zurückgenommen |

Der Commit dieses Tasks trägt entsprechend das Präfix `test`, und der Nachtrag am README `docs`. Ein `feat`-Commit gehört zu Task 2 und nicht hierher.

## Issues Encountered

- **Die Verifikationsbefehle des Plans zeigen auf den Haupt-Checkout.** Alle drei `<automated>`-Blöcke beginnen mit `cd /c/Users/Student/nextcloud-search`. Ein Wave-Executor arbeitet in seinem Worktree, und dort auszuführen wäre eine Prüfung des falschen Baums gewesen. Sämtliche Kommandos wurden mit dem Worktree-Pfad gefahren, inhaltlich unverändert.
- **`xsltproc` und `xmllint` gibt es auf dieser Maschine nicht.** Der Ausweg war ein Abbild aus dem lokal vorhandenen `php:8.2-cli` mit `xsltproc` und `libxml2-utils`, plus die beiden gepinnten Dateien aus `raw.githubusercontent.com`. Der Befund steht als DI-05-25 in der Liste.
- **Ein doppelter Rückstrich überlebt ein Here-Dokument in dieser Umgebung nicht.** Ein Skript, das `"\\u2014"` als Ersatztext schreiben sollte, ersetzte den Gedankenstrich durch sich selbst, weil `\\` auf dem Weg zu `\` wurde und Ersatztext und Suchtext damit identisch waren. Die Länge der Datei blieb unverändert, was der einzige Hinweis war. Umgangen, indem der Rückstrich als `chr(92)` gebildet wurde. Für spätere Pläne: eine Ersetzung, die Escapes schreibt, gehört in eine Datei und nicht in ein Here-Dokument.
- **Beide `info.xml` liegen mit CRLF im Arbeitsbaum.** Sie wurden binär gelesen und binär geschrieben, damit der Diff die geänderten Stellen zeigt und nicht jede Zeile. Ergebnis: 150 beziehungsweise 147 geänderte Zeilen statt 101 beziehungsweise 282.

## User Setup Required

Keine.

## Next Phase Readiness

**Für Plan 05-18 (Store-Medien):** In beiden `info.xml` steht der Absichtskommentar an der Stelle, an der die `screenshot`-Elemente laut Sequenz hingehören, also zwischen `repository` und `donation`. Das Gate prüft jede eingesetzte Adresse auf `https` und 256 Zeichen; die Regel "mindestens ein Screenshot je App" ist dort ausdrücklich offen gelassen und gehört in denselben Plan, der die Bilder anlegt. Ein leeres Element darf unter keinen Umständen als Platzhalter stehen bleiben.

**Für den Release-Plan (D-26, Tag `v1.0.0`):** Die drei Versionsangaben stehen auf `1.0.0` und stimmen überein, geprüft von `test_lockstep_versions.py` und beim Release zusätzlich von `docker.yml` gegen den git-Tag. Das Abbild `ghcr.io/street1983nk/findling_backend:1.0.0` muss in der Registry existieren, bevor die Freigabe veröffentlicht wird, nicht danach.

**Für den ARM-Volllauf:** Die zitierte Kernaussage nennt x86 ausdrücklich und benennt die ausstehende Wiederholung. Wenn der ARM-Lauf seine Zahl liefert, sind vier Orte anzupassen, und alle vier sind mechanisch verbunden: `README.md`, die beiden englischen Beschreibungen und `docs/store-listing.md`. Das Gate wird rot, sobald einer der ersten drei abweicht; die vierte Datei ist die Quelle und wird von Hand nachgezogen.

**Offen und ausdrücklich nicht hier erledigt:** DI-05-24 und DI-05-25.

## Self-Check: PASSED

| Prüfung | Ergebnis |
|---|---|
| `docs/store-listing.md` | vorhanden, 258 Zeilen |
| `backend/tests/test_store_metadata.py` | vorhanden, 337 Zeilen |
| Commits `1035a58`, `467cf71`, `c9aaa1e`, `adba1d6`, `2f231e8` | alle im Log |
| Store-Validierungspfad, beide Dateien | `validates`, gegen `APPSTORE_SHA 5c4373d7` |
| routes-Finding und settings-Finding aus `php.yml` | beide unverändert wahr |
| `<version>1.0.0</version>` in beiden Dateien, `<image-tag>1.0.0</image-tag>` | vorhanden |
| `grep -c de_DE` über beide `info.xml` | 0 und 0 |
| leeres `screenshot`-Element | keines in beiden Dateien |
| `donation` mit dem Link aus D-27 | in beiden Dateien, an seinem Platz |
| Messsatz wortgleich in `README.md` und beiden englischen Beschreibungen | ja, nach Einebnen der Leerzeichen |
| Kurzbeschreibungen gegen 128 Zeichen | 72, 85, 87, 63, 64, 70 |
| Em-Dash und En-Dash in den fünf geänderten Dateien | keine |
| Emojis | keine |
| Gesperrter Vokabular-Begriff in `docs/store-listing.md` | kein Vorkommen |
| `uv run python -m pytest -q` | 969 passed, 11 skipped |
| `ruff check`, `ruff format --check`, `pyright`, `vulture` | alle sauber |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | nicht angefasst |
| Zweig | `worktree-agent-05-17`, keine fremde Datei angefasst |

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-04*
