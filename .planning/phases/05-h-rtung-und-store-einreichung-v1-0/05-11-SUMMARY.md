---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 11
subsystem: admin-diagnose
tags: [pkg-05, di-04-03, di-04-04, statusseite, quittierung, versionsmarken, in-02, in-03, a8]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: die Fehlerliste mit Gruppen und Beispielpfaden, die geschlossene Label-Tabelle und die Pro-Datei-Diagnose
  - phase: 02-suche-und-index
    provides: die Quittierung mit ihrer Fehlerliste, MAX_LIST_LENGTH und die Transaktionsgrenze
  - phase: 03-aktualit-t-und-ocr
    provides: die OCR-Spur und die Uebergabe ueber skipped(no_text_layer)
provides:
  - Skip-Verdikte je fileid in der Quittierung, mit Grundcode und ohne Pfad, Titel oder Text
  - die vier Container-Gruende als eigene Gruppen der Fehlerliste, mit anklickbaren Beispielpfaden
  - Neustempeln der Versionsmarken nach einem abgeschlossenen Neuaufbau, plus das Anheben der Generation, das den Neuaufbau ueberhaupt erst zu einem macht
  - skipped(mime_not_allowed) ausserhalb des Nenners des Deckungsgrads
  - zwei neue Gates ueber die Statusseite (Prozent-Trennzeichen, Schluesselgleichheit der Uebersetzungen)
affects: [Phase-Review, D-19, D-20, PKG-05, 05-19 Store-Screenshots]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Ein Verdikt reist als fileid plus Code; die empfangende Haelfte wird zuerst gebaut, die sendende danach
    - Zwei Zahlen, die eine Absprache sind, werden verglichen statt kopiert (Container-Deckel gegen MAX_LIST_LENGTH)
    - Ein unsichtbares Zeichen wird als Escape geschrieben, damit die Absprache im Diff lesbar ist
    - Eine Marke wird nach einem Neuaufbau gestempelt und nie beim Seeden; die Grenze der Erkennung steht im Docstring

key-files:
  created: []
  modified:
    - php/lib/Controller/QueueController.php
    - php/lib/Service/QueueService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Command/IndexCommand.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js
    - backend/src/findling/nc/client.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/index/open.py
    - backend/src/findling/store/repo.py
    - backend/tests/test_poller.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_index_open.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_acl_prefilter.py

key-decisions:
  - "Die Skip-Liste ist nach fileid geschluesselt, die Fehlerliste bleibt nach queueId: eine gescheiterte Zeile muss vor dem Loeschen uebersetzt werden, eine uebersprungene reist ohnehin in derselben Quittierung mit"
  - "Eine an die OCR-Spur uebergebene Datei meldet KEIN Verdikt: skipped(no_text_layer) ist kein Endzustand, und indexed wird in diese Tabelle nie geschrieben, also koennte niemand die Zeile je zuruecknehmen"
  - "Der Container kuerzt seine eigene Liste am Deckel der Gegenseite und meldet die Kuerzung; die PHP-Haelfte lehnt eine zu lange Liste ab, genau wie bei der Fehlerliste"
  - "Ein Drift hebt die lokale Generation an, einmal je Drift und nicht einmal je Start: ohne das Anheben ist occ findling:index --restart wirkungslos, weil jede Datei als unveraendert gilt"
  - "Abgeschlossen heisst: keine lebende Datei traegt mehr ein Verdikt einer aelteren Generation. Gemessen nur bei leerer Warteschlange, mit benannter Grenze fuer eventlos geloeschte Dateien"
  - "index_version wird beim Stempeln ausdruecklich NICHT zurueckgeschrieben, weil die Marke eine Untergrenze ist und die lokale Generation nach einem Neuaufbau darueber steht"
  - "A8/Bug-L4: nicht geschlossen und nicht schliessbar; --status beschriftet den Block als Nextcloud-Sicht und nennt die Haelfte, die die Dokumente zaehlt"
  - "IN-03 war ein Fehlbefund des Reviews; behoben wurde die Unsichtbarkeit der Absprache, nicht ein Unterschied"

patterns-established:
  - "Reihenfolge beim Erweitern eines Kanals: erst die empfangende Haelfte, dann die sendende, weil ein Sender ohne Empfaenger eine stille Datenverlustquelle ist"
  - "Was zwischen den Haelften vereinbart ist, wird von einem Test aus der fremden Quelle gelesen und verglichen, nie abgeschrieben"
  - "Ein Zaehler, der bisher strukturell nought war und lebendig wird, zieht jede Rechnung nach sich, die ihn bisher folgenlos addiert hat"

requirements-completed: [PKG-05]

# Metrics
duration: 80min
completed: 2026-09-03
---

# Phase 5 Plan 11: Skip-Verdikte, Fehlerlistengruppen und ein Banner, das sein Versprechen haelt Summary

**Der Container meldet seine eigenen Verdikte jetzt je fileid an die Nextcloud-Haelfte, sodass die Fehlerliste alle vier Gruende gruppiert statt nur die halbe Wahrheit, und der Reindex-Banner verschwindet durch genau den Befehl, den seine Abhilfe nennt, weil ein Drift die Generation anhebt und ein abgeschlossener Neuaufbau die Marken neu stempelt.**

## Performance

- **Duration:** ca. 80 min
- **Tasks:** 3 von 3
- **Files modified:** 18 (0 neu)
- **Commits:** 3 Aufgaben-Commits plus dieser Abschluss

## Accomplishments

- **Ein drittes Feld in der Quittierung, und es traegt nichts als Zahlen und Codes.** `DELETE /queues/documents` nimmt neben `files` und `failed` jetzt `skipped` an, eine Liste von `{fileId, reason}`. Derselbe Deckel (`MAX_LIST_LENGTH`, 256), dieselbe Ablehnung eines unbekannten Codes, dieselbe Transaktion wie die Fehlerliste. Der Container kuerzt seine eigene Liste vorher am selben Deckel und sagt, wie viele Verdikte er dabei verloren hat, weil eine Ablehnung der Gegenseite die ganze Quittierung kosten wuerde.
- **Die vier Gruende, die nur der Container kennt, sind in der Fehlerliste angekommen.** Verschluesselt, kein Textlayer, leerer Text und Bild ohne erkennbare Schrift standen bisher nur in der Pro-Datei-Diagnose; die Aggregation fehlte, nicht das Wissen. Da die Gruppierung `findling_file_state` liest und alle vier schon ein Label und einen Abhilfesatz hatten, entstehen die Gruppen von selbst, sobald die Zeilen da sind. Auf dem lokalen Stack mit dem echten Referenzkorpus gemessen: sieben Gruppen, darunter alle vier, jede mit anklickbaren Beispielpfaden.
- **Eine an die OCR-Spur uebergebene Datei meldet kein Verdikt, und das ist der Kern der Sache.** `skipped(no_text_layer)` mit eingeschaltetem OCR ist der Uebergabepunkt und kein Endzustand. Wuerde er gemeldet, stuende jeder Scan der Instanz dauerhaft unter "Kein Text im Dokument", denn `indexed` ist die Zahl des Containers und wird in diese Tabelle nie geschrieben, also koennte die Zeile niemand zuruecknehmen. Im Korpuslauf ist genau das messbar: keine Gruppe `no_text_layer`, wohl aber die Endzustaende, in denen die Scans wirklich gelandet sind.
- **Der Reindex-Banner haelt sein Versprechen, und dafuer mussten zwei Loecher zu.** Das erste war das benannte: nichts stempelte die Marken nach einem Neuaufbau. Das zweite fiel beim Bauen auf und machte das erste gefaehrlich: der Neuaufbau baute gar nichts neu, weil `is_unchanged` Inhalts-Hash und Generation vergleicht und eine Analyse-Drift keines von beiden bewegt. Jetzt hebt ein Drift die lokale Generation an, womit jedes gespeicherte Verdikt auf einen Schlag veraltet ist und die vom Banner verlangte Crawl-Runde die Dokumente wirklich wieder liest.
- **Abgeschlossen ist genau bestimmt und die Grenze steht im Docstring.** Nicht das Ende des Befehls und nicht die leere Warteschlange, sondern: keine lebende Datei traegt mehr ein Verdikt einer aelteren Generation. Gefragt wird nur bei leerer Warteschlange und nur so lange, bis die Antwort einmal ja lautet. Die Grenze: eine in Nextcloud eventlos geloeschte Datei haelt die Zahl oben, bis der naechtliche Abgleich sie zu einem Grabstein macht, also kann der Stempel eine Nacht zu spaet kommen. Das ist die Richtung, in die man zu spaet sein darf (T-05-48).
- **Drei kleine Widersprueche der Seite sind weg, einer davon war keiner.** IN-02, die Uebersetzung eines Satzes, den die Seite nicht anzeigt, ist aus beiden Katalogen entfernt, und ein Gate haelt deren Schluesselmengen ab jetzt zusammen. IN-03 war ein Fehlbefund: Vorlage und Skript benutzten schon seit Plan 04-03 beide U+00A0, nur stand es im Skript als Zeichen und liest sich in fast jedem Editor als gewoehnliches Leerzeichen. Behoben wurde die Unsichtbarkeit: beide Seiten schreiben jetzt das Escape, ein Kommentar sagt welches und warum, und ein Gate vergleicht sie.
- **Der Deckungsgrad rechnet wieder das, was neben ihm steht.** `skipped(mime_not_allowed)` war bis heute strukturell nought, weil es niemand schrieb. Mit dem Skip-Kanal wird die Zahl echt, und der Satz neben der Prozentzahl behauptet woertlich, diese Dateien staenden nicht im Nenner. Sie tun es jetzt nicht mehr; ohne diese Zeile haette eine Instanz mit einem einzigen Video fuer immer bei 99 Prozent gestanden.

## Task Commits

1. **Task 1: das Skip-Verdikt ueberquert die Grenze** - `3b26227` (feat)
2. **Task 2: die Gruppen und die drei Positionen der Seite** - `042a1f2` (feat)
3. **Task 3: der Neuaufbau stempelt, und --status sagt, wessen Sicht es ist** - `6dc7954` (feat)

## Files Created/Modified

- `php/lib/Controller/QueueController.php` (+95) - dritter Parameter `$skipped`, neuer Validator `skipList()` mit demselben Deckel und derselben geschlossenen Codeliste wie `failureList()`, `queueId()` in `positiveId()` umbenannt, weil es jetzt auch fileids prueft. Der Docblock erklaert, was jede der drei Listen bedeutet und was ausdruecklich in keiner steht.
- `php/lib/Service/QueueService.php` (+56) - `acknowledge()` nimmt die Skips und schreibt sie in derselben Transaktion; eine Quittierung, die nur aus Skips besteht, ist zulaessig.
- `php/lib/Service/AdminViewService.php` (+40) - `mime_not_allowed` einmal gezaehlt, aus dem Nenner genommen und an `coverage()` weitergereicht; der Docblock von Stufe zwei der Diagnose sagt jetzt, warum die Live-Regel vor der gespeicherten Zeile steht, obwohl es die Zeile inzwischen gibt.
- `php/lib/Command/IndexCommand.php` (+30) - `--status` beschriftet die Endzustaende als Nextcloud-Sicht und nennt die Haelfte, die `indexed` zaehlt (A8); `restart()` sagt im Docblock, wo dieser Befehl endet und die andere Haelfte anfaengt.
- `php/templates/admin.php` (+12) und `php/js/admin.js` (+11) - IN-03, das Escape und die Begruendung auf beiden Seiten.
- `php/l10n/de.json`, `php/l10n/de.js` (je -1) - IN-02.
- `backend/src/findling/nc/client.py`, `backend/src/findling/nc/queue.py` (+66) - der dritte Listenparameter bis auf den Draht, `MAX_ACK_LIST` und `_capped_skips()`.
- `backend/src/findling/worker/poller.py` (+70) - `_skip_verdicts()` leitet die Liste aus den fertigen Verdikten ab statt sie an acht Aufrufstellen einzusammeln; `_open_state()` startet einen Neuaufbau bei Drift; `_stamp_if_rebuilt()` haengt am leeren Durchgang.
- `backend/src/findling/index/open.py` (+120) - `start_rebuild_on_drift()`, `stamp_after_rebuild()`, `REBUILD_MARK` und der Fingerabdruck, der einen Neustart mitten im Neuaufbau von einer zweiten Aenderung des Codes unterscheidet.
- `backend/src/findling/store/repo.py` (+25) - `verdicts_older_than()`, das Mass eines unfertigen Neuaufbaus.
- Tests: `test_poller.py` (+14 Faelle), `test_queue_client.py` (+6), `test_index_open.py` (+10), `test_admin_ui_contract.py` (+3), `test_acl_prefilter.py` (Signatur des Fakes).

## Decisions Made

- **Die Skip-Liste ist nach fileid geschluesselt, die Fehlerliste bleibt nach queueId.** Kein Stilbruch, sondern zwei verschiedene Lagen: eine gescheiterte Zeile muss in eine fileid uebersetzt werden, bevor sie geloescht wird, waehrend eine uebersprungene Datei in derselben Quittierung ohnehin in `files` mitreist und die Zustandstabelle nach fileid geschluesselt ist.
- **Die Liste wird auf der Containerseite gekuerzt und auf der Nextcloud-Seite abgelehnt.** Der Plan verlangte an einer Stelle Kuerzung mit Meldung und an einer anderen dieselbe Ablehnung wie bei der Fehlerliste. Beides ist erfuellt, indem jede Haelfte die Regel bekommt, die zu ihrer Rolle passt: die Gegenseite lehnt konsequent ab, wie sie es fuer jede Liste tut, und der Sender sorgt dafuer, dass es nie dazu kommt, und sagt es, falls er dabei etwas verliert. Ein Test liest den Deckel aus der PHP-Quelle und vergleicht ihn mit dem der Python-Seite.
- **Ein unbekannter Code endet als 400 fuer die ganze Quittierung, ein nicht existierendes Paar wird gezaehlt und weggeworfen.** Das ist die bestehende Arbeitsteilung: der Controller prueft gegen die flache Codeliste und lehnt eine defekte Liste ganz ab, `FileStateService::record` beurteilt das Paar und zaehlt die Ablehnung. Live gemessen: `skipped(unicorn)` ergibt 400, `skipped(corrupt)` ergibt 200 mit `recorded: 0`, keine Zeile und eine Warnung im Protokoll.
- **Das Anheben der Generation gehoert zu diesem Plan, obwohl es nicht darin steht.** Ohne es waere der Stempel eine Luege: alle Zeilen tragen bereits die aktuelle Generation, das Mass "nichts Altes mehr da" waere sofort erfuellt, und ein voellig unveraenderter Index wuerde fuer aktuell erklaert. Genau der Fall, den T-05-48 verbietet.
- **Der Fingerabdruck der erwarteten Marken statt eines Zaehlers.** Ein Container, der bei jedem Start anhebt, wuerde auf einer Box, die nachts neu startet, jeden Tag die Arbeit des Vortags entwerten. Der Fingerabdruck unterscheidet "dieser Neuaufbau laeuft schon" von "der Code hat sich schon wieder geaendert" und kostet eine Meta-Zeile.
- **Gefragt wird nur bei leerer Warteschlange, und nur bis zum ersten Ja.** Eine Zaehlung ueber die ganze Dateitabelle zwischen zwei Stapeln waere auf einer Box mit fuenfzigtausend Dokumenten spuerbar. Am leeren Durchgang kostet sie eine Abfrage je Leerlauf-Runde, und ein Merker im Prozess beendet auch das, sobald die Marken einmal als aktuell erkannt wurden.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Neuaufbau baute nichts neu, also haette der Stempel einen unveraenderten Index fuer aktuell erklaert**

- **Found during:** Task 3, beim Bestimmen von "abgeschlossen"
- **Issue:** `Store.is_unchanged` vergleicht Inhalts-Hash UND Generation. Eine Analyse-Drift bewegt `wordlist_hash`, `analyzer_version` oder `tantivy_version`, aber nie `index_version`. Also lieferte die vom Banner verlangte Crawl-Runde fuer jede Datei "unveraendert", die Zeile wurde ohne ein gelesenes Byte quittiert, und jede Zeile trug weiterhin die aktuelle Generation. Ein Stempel auf dieser Grundlage haette den Index der alten Textanalyse fuer aktuell erklaert und dem Admin die einzige Zeile genommen, die ihm sagte, warum Treffer fehlen.
- **Fix:** `start_rebuild_on_drift()` in `backend/src/findling/index/open.py`, aufgerufen beim Oeffnen der Zustandsdatenbank. Hebt die lokale Generation einmal je Drift an und merkt sich per Fingerabdruck, worauf hin gebaut wird.
- **Files modified:** `backend/src/findling/index/open.py`, `backend/src/findling/worker/poller.py`
- **Commit:** `6dc7954`

**2. [Rule 1 - Bug] Ein lebendig gewordener Zaehler haette den Deckungsgrad auf 99 Prozent eingefroren**

- **Found during:** Task 2, beim Lesen von `coverage()`
- **Issue:** `deliberatelyLeftOut` addiert `countByReason('skipped', 'mime_not_allowed')`, und der Satz daneben sagt woertlich, diese Dateien staenden nicht im Nenner, damit der Deckungsgrad hundert Prozent erreichen kann. Der Nenner zog sie nie ab; folgenlos, solange der Zaehler strukturell nought war, weil auf dieser Seite niemand diesen Grund schrieb. Mit Task 1 wird er echt, und ohne Gegenmassnahme haette eine Instanz mit einem einzigen Video oder Archiv fuer immer bei 99 Prozent gestanden und auf eine Datei gewartet, die niemand je indexieren wird.
- **Fix:** Der Zaehler wird einmal in `overview()` erhoben, vom Nenner abgezogen und an `coverage()` weitergereicht, damit die Zahl im Nenner und die Zahl im Satz dieselbe ist. Live gemessen: filesSeen 10, overCap 1, excluded 2, mime_not_allowed 1 ergibt indexable 6 und deliberatelyLeftOut 4, und `estimate.files` folgt derselben Zahl.
- **Files modified:** `php/lib/Service/AdminViewService.php`
- **Commit:** `042a1f2`

**3. [Rule 2 - Fehlende kritische Funktionalitaet] Ein Verdikt fuer eine an OCR uebergebene Datei waere dauerhaft falsch gewesen**

- **Found during:** Task 1, beim Entwurf des Kanals
- **Issue:** Der naive Weg meldet jedes `skipped`-Verdikt. `skipped(no_text_layer)` ist aber der Uebergabepunkt an die OCR-Spur und kein Endzustand, und weil `indexed` in `findling_file_state` grundsaetzlich nicht geschrieben wird, kann diese Zeile nie wieder verschwinden. Jeder Scan und jedes Bild der Instanz haetten dauerhaft unter "Kein Text im Dokument" in der Fehlerliste gestanden, obwohl OCR sie erfolgreich indexiert hat.
- **Fix:** `_skip_verdicts()` schliesst die uebergebenen fileids aus, dieselbe Regel, der die `done`-Liste schon folgt. Zwei Tests halten beide Richtungen: mit eingeschaltetem OCR reist nichts, mit ausgeschaltetem reist dasselbe Verdikt, weil es dann endgueltig ist.
- **Files modified:** `backend/src/findling/worker/poller.py`, `backend/tests/test_poller.py`
- **Commit:** `3b26227`

**4. [Rule 2 - Fehlende kritische Funktionalitaet] Ein Docblock behauptete etwas, das dieser Plan unwahr macht**

- **Found during:** Task 2
- **Issue:** Stufe zwei der Pro-Datei-Diagnose begruendete ihre Live-Berechnung damit, dass `mime_not_allowed` nie geschrieben wird. Ab jetzt schreibt der Container es. Die Reihenfolge der Stufen bleibt richtig, die Begruendung nicht.
- **Fix:** Der Absatz sagt jetzt, dass die Regel von heute vor der Zeile von gestern kommt und dass beide denselben Code und denselben Satz liefern, wo sie zusammentreffen. Live gegengeprueft: der Klick auf jede der sechs Gruppen liefert dasselbe Paar aus Zustand und Grund wie die Gruppe.
- **Files modified:** `php/lib/Service/AdminViewService.php`
- **Commit:** `042a1f2`

### Findings ohne Codeaenderung

**IN-03 war ein Fehlbefund des Phase-4-Reviews.** Das Review nennt `php/js/admin.js` mit `+ ' %'` gegen `"\u{00A0}%"` in der Vorlage. Gemessen: die Zeile traegt seit Commit `57fb0ec` (Plan 04-03) das Byte U+00A0 und war nie ein gewoehnliches Leerzeichen. Beide Seiten stimmten also ueberein, und die Prozentzahl hat ihre Form beim ersten Poll nie geaendert. Was wirklich fehlte, war die Lesbarkeit der Absprache: als Zeichen geschrieben sieht sie in fast jedem Editor und in fast jedem Diff wie ein Leerzeichen aus, was den Fehlbefund erst erzeugt hat. Beide Seiten schreiben jetzt das Escape, tragen den Grund als Kommentar und werden von einem Gate verglichen.

**A8, Bug-L4 aus dem Phase-2-Audit: nicht geschlossen, und nicht schliessbar.** `occ findling:index --status` liest `FileStateService::counts()`, und diese Tabelle fuehrt `indexed` nicht: die Aufteilung der Wahrheit aus Phase 4 macht den Container zur einzigen Quelle fuer indexierte Dokumente, und keiner der drei Schreiber dieser Seite erzeugt je eine `indexed`-Zeile. Die Zahl ist strukturell nought und bleibt es. Korrigiert wurde deshalb die Beschriftung, wie der Plan es als Alternative vorsieht: der Block heisst jetzt "End states as Nextcloud recorded them", und zwei Zeilen darunter sagen, dass `indexed` vom Backend gezaehlt wird und wo beide Sichten nebeneinander stehen. Live gesehen im Lauf unten.

## Live gemessen, protokolliert

Auf einem eigenen, isolierten Stack (Wegwerf-Kopie von `scripts/dev/compose.yaml`,
Projektname `findling-wt0511`, Container `findling-wt0511-nc`, Port 8111,
absoluter Bind auf das `php` dieses Worktrees; Host-Prozess auf Port 10111).
Nextcloud 34.0.3, `findling 0.3.0 enabled`, ExApp `findling_backend` registriert.
Der Alltagsstack `findling-nextcloud` des Owners lief die ganze Zeit unberuehrt
weiter. Der Stack wurde danach mit `down -v` restlos entfernt.

**1. Die Quittierung, gegen die echten Dienste im echten Nextcloud.**

- Vier Warteschlangenzeilen, quittiert mit vier Skip-Verdikten: `status=200`,
  `{"acknowledged":4,"recorded":4}`, danach in `findling_file_state`
  `8001=skipped(encrypted), 8002=skipped(no_text_layer), 8003=skipped(empty_text), 8004=skipped(image_not_ocrable)`
  und null Warteschlangenzeilen uebrig. Die Gruppierung meldet vier Gruppen.
- Unbekannter Code `unicorn`: `status=400`, nichts gespeichert.
- Nicht existierendes Paar `skipped(corrupt)`: `status=200`, `recorded: 0`, keine
  Zeile, und im Protokoll `Findling: rejected a file state that is not in the
  closed list`. Kein Pfad in irgendeiner Zeile des Protokolls.
- Liste mit 300 Eintraegen: `status=400`.
- Aufruf mit nur zwei Argumenten, also die Form von gestern: `status=200`,
  `{"acknowledged":1,"recorded":0}`.
- Dieselbe fileid ein zweites Mal beurteilt: eine Zeile, neuer Grund.
- `php -l` ueber alle 36 PHP-Dateien der App: ausschliesslich "No syntax errors
  detected".

**2. Die Fehlerliste nach einem Lauf ueber das echte Referenzkorpus.** Die 33
Dateien aus `testdata/corpus` liegen im Heimatverzeichnis eines Nutzers, der
Crawl hat sie eingereiht, der echte Container hat sie gelesen. Die Seite zeigt
danach **sieben Gruppen**, jede mit echten Beispielpfaden:

```
failed(ocr_unavailable)   x20  Text recognition not available      | Photos/Birdie.jpg, ...
failed(corrupt)            x9  File damaged                        | Korpus/24-abgeschnittener-trailer.pdf, ...
skipped(image_not_ocrable) x3  Image without recognisable writing   | Korpus/05-picture.png, Korpus/22-icon.png
failed(empty_file)         x1  File is empty                        | Korpus/06-zero-bytes.pdf
skipped(mime_not_allowed)  x1  File type not supported              | Buchhaltung/Lohnlauf.mp4
skipped(empty_text)        x1  No text content                      | Scans/Leerseite.txt
skipped(encrypted)         x1  Password protected                   | Korpus/07-password-protected.pdf
```

Vier davon sind die Gruende, die nur der Container entscheidet, und keine davon
gab es vor diesem Plan. Es gibt **keine** Gruppe `no_text_layer`: die Scans
wurden an die OCR-Spur uebergeben und sind dort in ihrem echten Endzustand
gelandet, was genau der Ausschluss aus Abweichung 3 ist. Deckungsgrad in
demselben Lauf: `indexed 53`, `indexable 93`, `deliberatelyLeftOut 4`,
`percent 56`.

**3. Ein Klick pro Gruppe fuellt die Pro-Datei-Diagnose mit demselben Grund.**
Fuer alle sechs Gruppen eines vorgelagerten Laufs gegenueber gestellt, jeweils
Zustand und Code der Gruppe gegen Zustand und Code der Diagnose: sechs von sechs
`SAME`, mit denselben Worten im Label.

**4. Die ganze Kette des Reindex-Banners, ohne einen Eingriff von Hand.**

1. Ausgangsstand: `reindexRequired: false`, `indexed/docs 41/41`, das
   Banner-Markup traegt `hidden`.
2. Wortliste im Datentraeger geaendert, also eine andere Textanalyse, und der
   Container neu gestartet. Protokoll: `WARNING the index was built by different
   code; raised the generation to 2 so the next crawl rebuilds it`. Meta:
   `index_version 2`, `wordlist_hash` noch der alte, `rebuild_for b47c78ed53cb0a37`,
   **54 veraltete Zeilen**. Die Seite: `reindexRequired: true` und
   `<p class="findling-banner findling-banner--warning" id="findling-banner-reindex">`
   **ohne** `hidden`.
3. `occ findling:index --restart --no-interaction` -> "The crawl was queued.",
   Hintergrundauftraege gelaufen, der Container hat alle 54 Dateien wieder
   gelesen. Dass sie wirklich gelesen wurden und nicht als unveraendert
   quittiert: alle 54 Zeilen tragen danach Generation 2, und nur `record()`
   schreibt die Generation, also stand hinter jeder eine echte Extraktion.
4. Warteschlange leer -> `INFO the rebuild is through at generation 2; the
   version marks are current again`. Meta: `wordlist_hash 158a3d85bc43`,
   `rebuild_for` geleert, **0 veraltete Zeilen**.
5. Seite neu gerendert: `reindexRequired: false`, das Banner-Markup traegt wieder
   `hidden`. Niemand hat etwas gestempelt.

**5. A8 im Lauf gesehen.** `occ findling:index` gibt aus:

```
End states as Nextcloud recorded them
  indexed              0
  skipped              6
  failed               30
  indexed is counted by the backend container and never written here, so it stays 0.
  The admin settings page of Findling shows the counters of both halves side by side.
```

## Verification

- `cd backend && uv run python -m pytest -q`: **932 passed, 11 skipped** (davon 33 neue Faelle dieses Plans)
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run vulture src tests --min-confidence 80`: alle gruen
- Gate B (Routenzahl als Ratsche): unveraendert, dieser Plan legt keine Route an
- Gate C: gruen, plus drei neue Faelle in `test_admin_ui_contract.py`
- Drift-Gate der drei Grundlisten: gruen, dieser Plan fuehrt keinen neuen Code ein
- `grep -c innerHTML php/js/admin.js` = 0
- `grep -c 'Indexing, about' php/l10n/de.json php/l10n/de.js` = 0 und 0, und der Quelltext kommt in Vorlage, Skript und PHP nicht mehr vor
- `php -l` ueber alle 36 PHP-Dateien der App im Container: sauber
- Kein Em-Dash (U+2014) und kein En-Dash (U+2013) in den geaenderten Dateien

## Known Stubs

Keine.

## Deferred Issues

- **DI-05-13:** Der Rueckzug des Pollers bleibt fuer die Statusseite unsichtbar. DI-05-08 war ausdruecklich an diesen Plan adressiert und wird mit einem Argument zurueckgestellt, das es noch nicht kannte: im Hauptfall, der halb entfernten Installation aus D-17, gibt es keine Statusseite mehr, auf der ein Banner stehen koennte. Der verbleibende Fall waere die Anzeige wert, braucht aber ein neues Feld in `backend/src/findling/api/status.py`, die nicht in den `files_modified` dieses Plans steht, und einen Weg, Laufzeitzustand des Pollers in eine Antwort zu bringen, die bisher nur Persistiertes meldet.
- **DI-05-14:** Ein Verdikt in `findling_file_state` wird nie zurueckgenommen. Aelter als dieser Plan und seit Phase 2 fuer alle `failed`-Gruende gueltig; dieser Plan verbreitert ihn um die `skipped`-Gruende und schliesst den einen Fall aus, in dem die Veralterung der Normalfall statt der Ausnahme waere.
- **DI-05-11** (Gruppenwechsel und ACL-Vorfilter) wurde gelesen und beruehrt diesen Plan nicht: er faellt in die Ereigniskette, nicht in die Quittierung.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers des Plans. Die einzige neue
Grenzueberschreitung ist die dritte Liste der Quittierung, und sie ist als
T-05-45 bis T-05-47 geplant, mit Tests belegt und live gemessen. Der neue
Meta-Schluessel `rebuild_for` liegt im Datentraeger des Containers, traegt einen
Hash von Versionsnummern und keine Nutzerdaten.

## Self-Check: PASSED

Alle 20 in dieser Zusammenfassung genannten Dateien liegen im Baum, und die drei
Aufgaben-Commits `3b26227`, `042a1f2` und `6dc7954` stehen im Verlauf
dieses Zweiges.
