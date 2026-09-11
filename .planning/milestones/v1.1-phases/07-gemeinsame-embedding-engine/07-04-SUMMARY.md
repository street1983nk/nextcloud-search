---
phase: 07-gemeinsame-embedding-engine
plan: 04
subsystem: api
tags: [embeddings, admin-ui, status, diagnostics, l10n]

# Dependency graph
requires:
  - phase: 07-gemeinsame-embedding-engine
    provides: "Plan 07-03: der faule Bau der zweiten Spur, der aendert, was 'kalt' fuer einen laufenden Container bedeutet, und embed/model.py::artifacts_present"
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: "embed/engine.py::shared_model als Halter, und die drei Antworten des Ladewegs (_absent, _load_failed_at, loaded)"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "der Block findling-semantic der Verwaltungsseite, die drei Urteile von AdminViewService::backend() und Gate C in test_admin_ui_contract.py"
provides:
  - "findling.embed.engine.engine_state: der Zustand der Engine als eines von fuenf Woertern, ohne Bau und ohne Laden"
  - "ENGINE_STATES: die geschlossene Menge der fuenf Zustaende, von beiden Haelften gegen dieselbe Quelle gehalten"
  - "embed/model.py: artifacts_absent und load_cooling_down als nebenwirkungsfreie Lesezugaenge"
  - "StatusResponse.engineState, gespeist in _volume(), also auch ohne Zustandsdatenbank"
  - "AdminViewService::engineState(): das Urteil ueber das Wort, statisch und pruefbar"
  - "Die Zeile findling-semantic-engine auf der Seite, mit sechs Saetzen und in beiden Haelften gleich"
  - "Drei neue Gates in test_admin_ui_contract.py: die Kennungen, die Abbildung Wort zu Satz, die sechs Saetze im Katalog"
affects: [phase-10-messung, phase-11-audit]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Auskunft ueber einen Zustand darf den Zustand nicht veraendern: die Frage baut nichts und laedt nichts"
    - "Die Reihenfolge der Verdikte steht als Kommentar neben der Auswertung, weil sie nicht die Reihenfolge der Felder ist"
    - "Ein Wort aus einer geschlossenen Menge ist das Protokoll, der Satz dahinter gehoert der lesenden Haelfte"
    - "Ein Wert von jenseits der Grenze wird verworfen und nie gecastet, auch wenn er nur ein Wort ist"
    - "Der dritte Zustand 'hat nichts gemeldet' bleibt von 'kalt' getrennt, damit eine Aktualisierung in der falschen Reihenfolge nichts behauptet"

key-files:
  created:
    - .planning/phases/07-gemeinsame-embedding-engine/07-04-SUMMARY.md
  modified:
    - backend/src/findling/embed/engine.py
    - backend/src/findling/embed/model.py
    - backend/src/findling/api/status.py
    - backend/tests/test_embed_engine.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_admin_ui_contract.py
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js
    - php/tests/Unit/AdminViewServiceTest.php
    - docs/admin-page.md

key-decisions:
  - "Fuenf Zustaende und ein sechster Satz: loaded, cold, disabled, missing, waiting_for_retry, plus 'nicht gemeldet' auf der lesenden Haelfte"
  - "Die Auswertung fragt bei leerem Halter die Artefakte, statt 'kalt' zu antworten: seit 07-03 baut keine Haelfte die Engine vor der ersten Zeile, ein Container ohne Modell haette sonst lebenslang 'kalt' gemeldet (Rule 2)"
  - "Das Urteil auf der PHP-Seite ist eine eigene statische Methode und nicht text(): ein Zustand hat keine ehrliche Kuerzung, und nur eine statische Methode ist ohne Nextcloud pruefbar"
  - "Kein zweiter Fortschrittsbalken: die Deckung ist eine Zahl, der Zustand ist eine Lage, also eine Klartextzeile"
  - "Die geschlossene Menge wird im Gate aus findling.embed.engine importiert und nicht ein zweites Mal buchstabiert"

metrics:
  tasks: 2
  tasks_skipped: 0
  commits: 3
  duration: "rund 1,5 Stunden"
  completed: 2026-09-08
---

# Phase 7 Plan 04: Der Zustand der Engine, sichtbar auf der Seite, Zusammenfassung

Erfolgskriterium 3 der Phase war halb erfüllt: die Suche fiel bei fehlender
Engine auf Volltext zurück, aber der Admin sah davon nichts. Der Container
meldet jetzt `engineState` als eines von fünf Wörtern, die Seite macht daraus
einen von sechs Sätzen, und die Frage nach dem Zustand baut keine Instanz und
lädt kein Modell.

## Was ein Admin jetzt unterscheiden kann

Vorher stand auf der Seite "0 Prozent auffindbar nach Bedeutung", und das war in
drei völlig verschiedenen Lagen wahr. Jetzt steht darunter ein Satz:

| Meldung | Satz auf der Seite | Was zu tun ist |
|---|---|---|
| `loaded` | Das Modell liegt im Speicher, die semantische Suche antwortet. | nichts |
| `cold` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | warten |
| `disabled` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | Schalter prüfen |
| `missing` | In diesem Abbild liegt kein Modell. | Abbild mit Modell einsetzen |
| `waiting_for_retry` | Das Laden ist einmal gescheitert und wird in Kürze erneut versucht. | fünf Minuten warten |
| kein Feld | Dieser Container meldet den Zustand des Modells noch nicht. | beide Hälften auf denselben Stand bringen |

Die sechste Zeile ist der Container, der älter ist als diese Änderung. Sie
bleibt aus demselben Grund von "kalt" getrennt, aus dem `embedded` auf der
PHP-Seite `null` ist und nicht 0: eine Aktualisierung in der falschen
Reihenfolge darf keinen Zustand behaupten, den niemand gemeldet hat (T-07-03).

## Wie der Zustand zustande kommt

`engine_state()` liest den Halter unter demselben Lock, unter dem
`shared_model()` ihn schreibt, und der eine Unterschied ist der ganze Zweck:
ein leerer Halter wird mit einem Zustand beantwortet und nicht gefüllt. Die
zwei neuen Lesezugänge auf `EmbeddingModel` machen genau die Felder sichtbar,
die `_load()` heute schon führt, und erfinden keinen neuen Zustand:

- `artifacts_absent` gibt die dauerhaft gemerkte Abwesenheit heraus, ohne noch
  einmal hinzusehen.
- `load_cooling_down` vergleicht den Zeitstempel des gescheiterten Öffnens
  gegen `LOAD_RETRY_SECONDS`. `_load()` stellt seither dieselbe Frage über
  diese Eigenschaft, damit die Regel eine Heimat hat und nicht zwei
  Schreibweisen.

Die Reihenfolge der Auswertung steht als Kommentar daneben, weil sie nicht die
Reihenfolge der Felder ist: abgeschaltet schlägt alles, dann fehlt, dann
Karenzzeit, dann geladen, dann kalt. Ohne den ersten Schritt meldet ein
Container mit abgeschalteter Einbettung "kalt" und sieht aus wie einer, der
gleich anfängt.

## Die Kosten der Auskunft

Keine, die jemand bezahlt. Die Frage baut keine Instanz und lädt kein Modell,
und ein Testfall wird rot, wenn `load_count()` dabei steigt oder wenn der Halter
hinterher etwas trägt, das er vorher nicht hatte (T-07-04). Das ist kein
Formalismus: die Seite fragt im Sekundentakt, solange sie offen ist, und eine
Statusantwort, die dabei lädt, würde die 118 MB melden, die sie gerade selbst
verursacht hat.

## Beide Hälften der Seite

Das Wort ist das Protokoll, der Satz gehört der lesenden Hälfte. Der Container
schickt nie einen Text, den ein Admin liest; die Abbildung von einem der fünf
Wörter auf einen Satz steht im Template und im Skript und sonst nirgends. Damit
kann nichts, was von jenseits der Grenze kommt, die Formulierung dieser Seite
werden.

Drei neue Gates halten das Paar zusammen, und alle drei sind mit einem
Rotbeweis belegt:

| Gate | Was es hält | Rotbeweis |
|---|---|---|
| `test_every_half_of_the_page_carries_the_state_of_the_engine` | `engineState` im Dienst, `findling-semantic-engine` in Template und Skript | eine Hälfte ohne die Kennung ergibt Befunde, eine unbekannte Datei ebenfalls |
| `test_both_halves_of_the_page_map_the_same_state_to_the_same_sentence` | dieselbe Abbildung Wort zu Satz, und die Wörter sind die des Containers | ein umbenannter Zustand und ein umformulierter Satz brechen die Gleichheit, beides gefahren |
| `test_the_six_sentences_of_the_engine_line_are_in_the_german_catalogue` | alle sechs Sätze in `de.json`, der sechste auch in beiden Hälften | ein fehlender Satz erscheint als Befund mit Datei und Wortlaut |

Die geschlossene Menge wird im Gate aus `findling.embed.engine` importiert und
nicht ein zweites Mal buchstabiert. Eine zweite Schreibweise einer geschlossenen
Menge ist eine zweite Sache, die man vergessen kann.

## Abweichungen vom Plan

**1. [Rule 2 - fehlende Zusage] Bei leerem Halter wird die Artefaktfrage gestellt, statt "kalt" zu antworten**

- **Gefunden in:** Task 1, beim Entwurf der Auswertung.
- **Sache:** Der Plan schreibt "ist `_ENGINE` leer, ist die Antwort 'kalt'".
  Seit Plan 07-03 baut aber keine der beiden Hälften die Engine vor der ersten
  Zeile, die sie braucht: die eifrige Hälfte des Arbeiters prüft nur die
  Artefakte und gibt bei fehlendem Modell nie eine Zeile heraus, und die
  Suchseite baut den Halter erst bei der ersten semantischen Suche. Ein
  Container ohne Modell hätte damit lebenslang "kalt" gemeldet, und "kalt"
  liest sich als "das Modell wird beim ersten Bedarf geladen, das ist der
  Normalfall". Genau die Unterscheidung, die dieser Plan herstellen soll, wäre
  im wichtigsten Fall unmöglich geblieben, und die zweite Zusage der
  must_haves wäre nicht erfüllt.
- **Lösung:** Ist im Halter keine Instanz für dieses Verzeichnis oder hat sie
  noch nicht geladen, entscheidet die öffentliche `artifacts_present` aus Plan
  07-03: Artefakte da heisst "kalt", Artefakte weg heisst "fehlt". Das sind zwei
  `stat`-Aufrufe, kein Bau und kein Byte Speicher, und der Kommentar an der
  Stelle sagt, warum die Frage dort steht. Die acht Verhaltensweisen des Plans
  sind unverändert Testfälle: "noch nie eine Instanz gebaut" wird mit
  vorhandenen Artefakten gefahren, was die ehrliche Lesart dieses Satzes ist.
- **Commit:** 79ec47d

**2. [Rule 1 - eine Regel, zwei Schreibweisen] `_load()` fragt die Karenzzeit über die neue Eigenschaft**

- **Gefunden in:** Task 1, beim Bau von `load_cooling_down`.
- **Sache:** Der Vergleich gegen `LOAD_RETRY_SECONDS` hätte danach an zwei
  Stellen gestanden, in `_load()` und in der Eigenschaft. Zwei Schreibweisen
  einer Regel stimmen am Tag ihrer Entstehung überein und driften am Tag, an
  dem eine von beiden korrigiert wird.
- **Lösung:** `_load()` stellt die Frage jetzt über die Eigenschaft. Kein
  Verhalten geändert; die drei vorhandenen Fälle des Ladewegs
  (fehlendes Verzeichnis, geworfenes Öffnen, Karenzzeit) sind unangetastet und
  grün.
- **Commit:** 79ec47d

**3. [Entwurfsentscheidung, keine Regel] Das Urteil auf der PHP-Seite ist eine eigene statische Methode**

- **Sache:** Der Plan nennt "dasselbe Urteil wie `note`". `text()` ist privat
  und kürzt einen Satz; ein Zustand hat keine ehrliche Kürzung, und ein
  privates Urteil ist ohne eine ganze Nextcloud nicht prüfbar, während der
  Plan ausdrücklich einen PHP-Testfall verlangt.
- **Lösung:** `AdminViewService::engineState(mixed): ?string` ist statisch und
  öffentlich, aus demselben Grund wie `coverageShare()` und `progressStamp()`
  es sind, und prüft gegen `ENGINE_STATES`. Verworfen wird, nie gecastet
  (T-07-02).
- **Commit:** c495afc

## TDD-Tore

| Tor | Commit | Nachweis |
|---|---|---|
| RED | a0123f5 | die 14 neuen Fälle sind rot, mit `ImportError: cannot import name 'ENGINE_COLD'` in beiden Suiten |
| GREEN | 79ec47d | 73 Fälle der drei betroffenen Suiten grün, danach 1.695 der ganzen Suite |
| REFACTOR | entfällt | der einzige Umbau ohne Verhaltensänderung (Abweichung 2) gehörte in das GREEN-Tor, weil er die Eigenschaft benutzt, die dort entsteht |

Das RED-Tor ist ein Sammelfehler beim Einlesen und nicht 14 einzelne
Fehlmeldungen: die Konstanten und die Funktion, gegen die die Fälle laufen,
gab es noch nicht. Das ist die gröbste Form von rot und deshalb hier
ausdrücklich benannt.

## Gate-Ergebnisse

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün, 116 Dateien |
| `uv run pytest -q` | 1.699 grün, 15 übersprungen (vorher 1.681) |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | grün |
| `php -l` über die drei geänderten PHP-Dateien | fehlerfrei, PHP 8.5.9 im Container |
| `node --check php/js/admin.js` | fehlerfrei |
| beide Uebersetzungskataloge | 149 Schlüssel, in beiden dieselben |
| `git diff` auf `info.xml` | keine Zeile, keine neue Route, kein neuer Zugriffsgrad |
| Em-Dash und En-Dash in allen geänderten Dateien | keiner |

**Die PHPUnit-Suite selbst läuft hier nicht.** Sie braucht die
`tests/bootstrap.php` von `nextcloud/server` und das ist der `phpunit`-Job von
`php.yml`. Damit die 13 Urteile dieses Plans nicht ungefahren bleiben, sind sie
in einem echten PHP 8.5 gefahren: `AdminViewService.php` in den laufenden
Nextcloud-Container kopiert, per `require` eingelesen und
`AdminViewService::engineState()` mit genau den 13 Eingaben des Testfalls
aufgerufen, darunter `null`, `''`, `'Cold'`, `'<b>cold</b>'`, `3`, `true` und
`['cold']`. Ergebnis: alle 13 wie erwartet, keine Umwandlung. Die Klasse trägt
kein `extends` und kein `implements`, deshalb geht das ohne Autoloader.

## Was offen bleibt

- **Die Zeile hängt am Nenner.** Sie steht im Block `findling-semantic`, wie
  vom Plan gefordert, und der Block ist ausgeblendet, solange die Instanz keine
  indexierbare Datei hat. Auf einer ganz frischen Installation zeigt die Seite
  stattdessen "Noch keine Zahlen". Das ist die Lage, in der der Zustand der
  Engine am wenigsten sagt, aber es ist eine Lücke und sie gehört dem Audit
  der Phase vorgelegt, nicht stillschweigend behoben: eine Zeile aus dem Block
  herauszuziehen wäre eine Änderung am Aufbau der Seite und nicht an dieser
  Zeile.
- **Das Audit-Gate der Phase.** Security-, Bug- und Performance-Audit stehen
  nach diesem Plan noch aus, Befunde ab MEDIUM vor dem Phasenabschluss gefixt
  (Owner-Regel 15.08.2026).
- `.planning/STATE.md` und `.planning/ROADMAP.md` sind unverändert, wie vom
  Plan gefordert. Es wurde nicht gepusht.

## Self-Check: PASSED

Alle 13 geänderten Dateien und die neue Zusammenfassung liegen im Arbeitsbaum,
die drei Commit-Kürzel `a0123f5`, `79ec47d` und `c495afc` stehen in der
Historie des Zweigs `exec/07-04`.
