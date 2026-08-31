---
phase: 02-indexkern-und-volltextsuche
plan: 14
subsystem: ci
tags: [e2e, deutsche-suchqualitaet, rechtefall, zeitbudget, zweiter-dialekt, korpus, checkpoint-offen]
status: checkpoint-pending

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-11: POST /search, POST /snippets, GET /status und der Testhaken FINDLING_ARTIFICIAL_DELAY_MS"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-12: zweistufiger Suchpfad in PHP, 1,5 s je Aufruf, 2,5-s-Wanduhr"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-13: findling.tools.index_status und die Warteschleifen des Dauergates"
  - phase: 02-indexkern-und-volltextsuche
    provides: "02-04: Crawl, Warteschlange und Zugriffsliste"
provides:
  - "testdata/corpus 09 bis 12: je ein Traeger fuer einen deutschen Sprachfall, gemessen gegen die echte Wortliste"
  - "integration.yml Job index-search-e2e: sieben Sprachassertions, Rechtefall in beide Richtungen, Zeitbudgetprobe, Endstaende exakt"
  - "setup-test-nc: Dialekteingabe (sqlite oder mysql) und alle drei ExApp-Routen"
  - "docs/dev-setup.md: der Weg vom leeren Rechner zum Inhaltstreffer auf Port 8090"
  - "Gemessener Befund: die Registrierung kannte seit Phase 2 nur eine von drei Routen, /snippets war unerreichbar"
  - "Gemessener Befund: pypdfium2 verbindet Seitenzeilen mit CR LF, das Loeschen verklebte Woerter im Textausschnitt"
affects: [phase-03-ocr, phase-04-statusseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Suchbegriff steht in genau einer Korpusdatei, sonst prueft eine gruene Assertion nur, dass irgendetwas gefunden wurde"
    - "Zu jeder Ausschlussprobe gehoert die Kontrollprobe ohne den Ausschluss"
    - "Erwartete Endstaende werden exakt geprueft, nicht als 'wenig' beschrieben"
    - "Eine Textbereinigung, auf deren Laenge sich ein Offset stuetzt, ersetzt Zeichen einzeln statt sie zu entfernen"

key-files:
  created:
    - testdata/corpus/09-bescheid.pdf
    - testdata/corpus/10-kuendigung.docx
    - testdata/corpus/11-uebersicht.odt
    - testdata/corpus/12-aktenvermerk.txt
  modified:
    - scripts/dev/build_corpus.py
    - testdata/corpus/README.md
    - .github/workflows/integration.yml
    - .github/actions/setup-test-nc/action.yml
    - php/lib/Text/PlainText.php
    - php/lib/Service/ExAppService.php
    - docs/dev-setup.md
    - docs/testing.md
    - scripts/dev/compose.yaml

key-decisions:
  - "Der Ausschlussfall braucht ein Wort in zwei Dateien: 'Bescheid' steht bewusst in 09 und 10, sonst waere 'bescheid -frist' auch dann gruen, wenn das Minus nichts tut"
  - "Der Dateityp reist als type:pdf und nicht als ext:pdf: das RESEARCH nennt ext:, der gebaute Code kennt type:"
  - "Die Endstaende werden exakt geprueft (9 indexed, 2 skipped, 1 failed) statt 'failed muss null sein': der Korpus enthaelt eine Null-Byte-Datei mit Absicht"
  - "Das Skelettverzeichnis wird abgeschaltet und das Konto des Installateurs geleert: sonst zaehlt der Job Dokumente mit, die niemand gewaehlt hat"
  - "Der zweite Dialekt wandert als Matrixeintrag in die CI und nicht als zweites Compose-Profil auf eine Maschine, die vor dem Push niemand startet"

patterns-established:
  - "Sprachbefunde vor dem CI-Lauf gegen die echte Wortliste messen, in einem Wegwerfcontainer mit /usr/share/dict/ngerman"

requirements-completed: []

# Metrics
duration: 32 min
completed: 2026-09-01
---

# Phase 02 Plan 14: Der Beweis der deutschen Suche Summary

**Vier neue Korpusdateien tragen je einen deutschen Sprachfall, ein dritter CI-Job sucht sie ueber die normale Nextcloud-Suchroute mit sieben Assertions, einem zweiten Nutzer, einer Zeitbudgetprobe und einem zweiten Datenbankdialekt, und zwei Fehler auf genau diesem Weg sind dabei aufgefallen und behoben.**

## Stand: Task 3 wartet auf den Owner

Dieser Plan hat `autonomous: false`. Die Tasks 1 und 2 sind fertig und committet, die Vorarbeit von Task 3 (`docs/dev-setup.md`) ebenfalls. Was fehlt, ist die Sichtprobe des Owners und ihre Beobachtung in diesem Dokument. Die Rueckmeldung dazu steht am Ende dieser Datei unter "Offen".

## Performance

- **Duration:** 32 min bis zum Checkpoint
- **Started:** 2026-09-01T00:47Z
- **Tasks:** 2 von 3 fertig, Task 3 vorbereitet und am Checkpoint angehalten
- **Files created:** 4, **modified:** 9

## Task Commits

1. **Task 1: Referenzkorpus um deutsche Inhalte erweitern** , `2eec453` (test)
2. **Task 2: Index-E2E mit deutschen Assertions, Rechtefall, Zeitbudget und zweitem Dialekt** , `b49d22c` (test)
3. **Task 3 (Vorarbeit): der Weg vom leeren Rechner zum Inhaltstreffer** , `95ab7c2` (docs)

Dazu zwei Fehlerbehebungen, die auf dem Weg lagen und ohne die Task 2 nicht haette gruen werden koennen: `80c3f1f` (Routenliste) und `5d880c6` (Zeilenumbrueche im Textausschnitt). Beide sind unter "Deviations" begruendet.

## Was gemessen wurde, bevor die CI es prueft

Der Plan verlangt, dass jeder Suchbegriff genau eine Datei trifft. Das ist keine Behauptung geblieben. Extraktion, Analysekette und die vollstaendige Suchpipeline liefen lokal gegen die **echte** Wortliste (`/usr/share/dict/ngerman`, 356010 Zeilen, Rezept A, 276496 Eintraege, Digest `b1f64012...` , identisch mit `docs/german-analyzer.md`), in einem Container mit genau diesem Debian-Paket. Der Index wurde aus den zwoelf Korpusdateien gebaut, die Zugriffsliste mit zwei Nutzern gefuellt und `build_query` plus `candidates` aufgerufen, also derselbe Code, den der Container in der CI ausfuehrt.

| Suchzeile | Nutzer mit Zugriff | Nutzer mit einer Freigabe |
|---|---|---|
| `Genehmigung` | `09-bescheid.pdf` | `09-bescheid.pdf` |
| `Frist` | `10-kuendigung.docx` | nichts |
| `Mueller` | `12-aktenvermerk.txt` | nichts |
| `Vertrag` | `11-uebersicht.odt` | nichts |
| `"drei Monate"` | `10-kuendigung.docx` | , |
| `bescheid` (Kontrolle) | `09` **und** `10` | , |
| `bescheid -frist` | `09-bescheid.pdf` | , |
| `type:pdf bescheid` | `09-bescheid.pdf` | , |
| `findling-canary` | nichts (kein Index-Sonderweg) | , |

Die Tokens der Korpusdateien, ebenfalls gemessen:

| Datei | Tokens (Auszug) |
|---|---|
| `09-bescheid.pdf` | `bescheid unt verwalt behord grundstuck verkehr genehm wurd erteilt bescheid kostenfrei` |
| `10-kuendigung.docx` | `bescheid beendig mietverhaltnis kundig frist betragt drei monat quartal end wohnung bes rein ubergeb` |
| `11-uebersicht.odt` | `ubersicht laufend vertrag vertrag fachbereich lieg original ubersicht jahrlich fort geschrieb` |
| `12-aktenvermerk.txt` | `aktenvermerk registratur zustand akt frau mull ruckfrag bitt sekretariat richt` |

Drei Dinge, die diese Messung geklaert hat und die sonst erst der CI-Lauf gezeigt haette:

- `drei` ist **kein** deutsches Stoppwort und ueberlebt die Kette, die Phrase `"drei Monate"` ist also eine echte Wortfolgenpruefung und nicht versehentlich eine Einzeltermsuche.
- Die Umlautvariante wirkt genau wie dokumentiert: `Mueller` allein ergibt `muell` und trifft nichts, erst die Anfrageumschreibung aus 02-09 fuegt `Müller` mit `mull` hinzu, und das trifft.
- Keiner der sieben Begriffe kollidiert mit den acht Dateien der Phase 1. Deren deutsche Woerter zerfallen in `grundstuck ausschuss massnahm strassenbau beitrag satzung zeichensatz erkenn behord deutsch` und beruehren keinen Suchbegriff.

Der Textausschnitt fuer `Genehmigung` lautet gemessen:

```
Bescheid der unteren Verwaltungsbehörde  Die Grundstücksverkehrsgenehmigung wurde erteilt.  Dieser Bescheid ist kostenfrei
```

mit dem Hervorhebungsbereich `[45, 75]` in **Zeichen**, also dem vollstaendigen Kompositum: die Teiltoken erben die Offsets des Originalworts, was das RESEARCH als gewuenschtes Verhalten beschreibt.

Die Endzustaende des Korpus, ebenfalls gegen den echten Code gemessen und nicht geschaetzt:

| Datei | Zustand | Grund |
|---|---|---|
| 01, 03, 04, 08, 09, 10, 11, 12, README.md | indexed | , |
| 02-scan-no-text-layer.pdf | skipped | `no_text_layer` (OCR ist Phase 3) |
| 07-password-protected.pdf | skipped | `encrypted` |
| 06-zero-bytes.pdf | **failed** | `empty_file` |
| 05-picture.png | kein Zustand | vom Crawl nie eingereiht, Mimetyp nicht in der Allowlist |

Daraus die drei Zahlen, die der Job prueft: **9 indexed, 2 skipped, 1 failed**, und `docs == indexed`.

## Der Korpus

| Datei | Bytes | SHA-256 (Anfang) |
|---|---|---|
| `09-bescheid.pdf` | 793 | `2802d3fa` |
| `10-kuendigung.docx` | 1003 | `cd5f422d` |
| `11-uebersicht.odt` | 793 | `d5ed0823` |
| `12-aktenvermerk.txt` | 118 | `421095e8` |

Gesamt 6776 Byte in 12 Dateien plus README, auf der Platte 40 KB (Blockgroesse), weit unter der Grenze von 400 KB. Ein zweiter Lauf von `build_corpus.py` aendert keine Datei; `git status --porcelain testdata/corpus` meldet nach dem Commit nichts.

**Die acht Dateien der Phase 1 haben sich um kein Byte bewegt.** `git diff --stat HEAD -- testdata/corpus` vor dem Commit zeigte ausschliesslich `README.md`, die vier neuen Dateien waren unbeobachtet. `.gitattributes` ist unveraendert; die Regel `testdata/corpus/** -text` deckt die neuen Dateien bereits ab.

**Der Job `readonly-gate` bleibt ohne Anpassung gruen**, und das ist nachgesehen und nicht angenommen: er friert die Dateiliste mit `find ... | sort > filelist.txt` ein, zaehlt mit `wc -l < filelist.txt` und vergleicht die Zusammenfassung des Lesewerkzeugs gegen genau diese Zahl. Nirgends im Job steht eine feste Dateizahl. Dasselbe gilt fuer `resilience.yml`: dort steht `per_copy=$(find ... | wc -l)`, und die Zahl der Kopien wird daraus berechnet. Mit 13 statt 9 Eintraegen je Kopie sinkt die Kopienzahl von 46 auf 32, die Zahl der beurteilten Dateien bleibt mit 384 ueber der Untergrenze von 200.

## Der Job `index-search-e2e`

15 Schritte, zwei Matrixeintraege (`sqlite`, `mysql`), MariaDB 11.4 als Dienstcontainer. Der Ablauf:

1. Skelettverzeichnis abschalten, das Konto des Installateurs leeren, zwei Nutzer anlegen. Ohne das wuerde der Crawl das Handbuch, das Bild und den Vorlagenordner dreier Konten mitzaehlen, und die Zahlen des letzten Schritts waeren Zahlen ueber Dokumente, die niemand gewaehlt hat.
2. Korpus in das Konto des ersten Nutzers, `occ files:scan --all`.
3. Genau eine Datei per OCS-Share-API an den zweiten Nutzer, **vor** dem Crawl, danach erneut scannen. Der Kommentar im Job nennt den Grund: die Zugriffsliste entsteht beim Indexieren, spaetere Freigaben sind Phase 3.
4. `findling:index --restart --no-interaction`, SchedulerJob `--once`, StorageCrawlJob `--stop_after 60`.
5. Warten bis die Warteschlange leer ist und alle zwoelf Dateien einen Zustand haben, mit Zaehlerausgabe je Runde und hartem Zeitlimit.
6. Sieben Sprachassertions, jede mit `jq -e`, eigener Fehlermeldung und einer Pruefung auf Anzahl **und** Titel. Bei der ersten zusaetzlich: die Subline enthaelt `genehmigung` und kein `<`. Der Pfad enthaelt das Wort nicht, also kann diese Zeile nur mit einem echten Textausschnitt gruen werden.
7. Der zweite Nutzer, beide Richtungen: `Genehmigung` liefert ihm genau die freigegebene Datei, `Frist`, `Vertrag` und `Mueller` liefern ihm nichts.
8. Backend neu starten mit `FINDLING_ARTIFICIAL_DELAY_MS=3000`, dieselbe Suche, Wanduhr messen.
9. Endzustaende exakt pruefen und `docs == indexed`.

Bei `failure()` gibt der Job den Dialekt, beide Zaehlerquellen, alle elf Suchantworten, das ExApp-Log und das Nextcloud-Log aus.

Die beiden dokumentierten Sprachgrenzen (`suchte` findet `suchen` nicht, `Mietvertrag` ist ueber `Vertrag` nicht findbar) stehen als Kommentar mit Verweis auf `docs/german-analyzer.md` im Job und sind bewusst keine Assertion.

## Files Created/Modified

- `scripts/dev/build_corpus.py` , vier neue Erzeuger (`build_german_pdf`, `build_german_docx`, `build_odt`, `build_umlaut_name_txt`), ein gemeinsamer reproduzierbarer ZIP-Packer fuer die beiden neuen Archive, und ein Abschnittskommentar, der sagt, warum oberhalb davon keine Zeile angefasst wurde. Der PDF-Erzeuger schreibt cp1252-Bytes und deklariert `/Encoding /WinAnsiEncoding`, mit der Begruendung im Kommentar: pdfium liest die Umlaute gemessen auch ohne, dann haenge der Testfall aber an der Nachsicht des Parsers statt an der Datei.
- `testdata/corpus/README.md` , neue Ueberschrift (zwei Aufgaben), vier Zeilen in der Dateitabelle, eine Tabelle der Sprachfaelle mit den gemessenen Tokens, der Satz zum absichtlich doppelten Wort, die beiden nicht getesteten Grenzen und die Warnung, dass ein hinzugefuegtes **Wort** dieselbe Sorgfalt braucht wie eine hinzugefuegte Datei.
- `.github/workflows/integration.yml` , 456 hinzugefuegte Zeilen, **null** entfernte. Die Jobs `walking-skeleton` und `readonly-gate` sind Zeile fuer Zeile unveraendert.
- `.github/actions/setup-test-nc/action.yml` , fuenf neue Eingaben fuer den Dialekt, `pdo_mysql` und `mysqli` in der Erweiterungsliste, eine Fallunterscheidung im Installationsschritt mit Ausgabe des tatsaechlich installierten `dbtype`, und die berichtigte Routenliste.
- `php/lib/Text/PlainText.php` , Steuerzeichen werden zu einem Leerzeichen statt geloescht.
- `php/lib/Service/ExAppService.php` , Laengenvergleich statt Identitaetsvergleich vor den Hervorhebungen.
- `docs/dev-setup.md` , neuer Abschnitt "Phase 2: from a file on disk to a content hit", sieben Schritte, Port 8090 samt Grund an den Anfang.
- `docs/testing.md` , die beiden geaenderten Zusagen in ihrer neuen Form.
- `scripts/dev/compose.yaml` , der Kommentar sagt jetzt, warum der zweite Dialekt in der CI liegt und nicht als lokales Profil.

## Decisions Made

- **`type:pdf` statt `ext:pdf`.** Der Plan nennt beide Schreibweisen, das RESEARCH nennt `ext:pdf`. Gebaut wurde in 02-09 `TYPE_PREFIX = "type:"`, und `ext` ist der Feldname im Schema, nicht das Praefix in der Suchzeile. Der Job benutzt die Schreibweise, die der Code kennt.
- **Ein Wort in zwei Dateien, mit Absicht.** Der Plan verlangt, dass kein Suchbegriff zufaellig in zwei Dateien steht. `Bescheid` steht in zweien, und zwar nicht zufaellig: eine Ausschlussprobe braucht etwas zum Ausschliessen. Der Job prueft deshalb erst die Kontrolle (`bescheid` liefert zwei) und dann den Ausschluss (`bescheid -frist` liefert eine, und zwar die richtige). Ohne die Kontrolle waere ein wirkungsloses Minus nicht von einem wirksamen zu unterscheiden.
- **Exakte Endzustaende statt `failed == 0`.** Der Plan verlangt `failed` gleich null. Der Korpus enthaelt seit Phase 1 eine Null-Byte-Datei, und `judge()` bewertet die als `failed(empty_file)`; das ist gewollt und der Grund, warum es die Datei gibt. Der Job prueft daher alle drei Zahlen exakt. `failed muss klein sein` haette den Tag verdeckt, an dem ein funktionierendes Dokument zu scheitern beginnt.
- **Das Skelett wird abgeschaltet.** Ein neu angelegtes Konto bekommt Handbuch, Bild und Vorlagenordner, und der Crawl laeuft ueber jede Einhaengung der Instanz. Die Endzustaende waeren damit weder vorhersagbar noch aussagekraeftig. `skeletondirectory` auf leer und das Konto des Installateurs leeren macht die Instanz zu genau dem, was der Job zaehlen will.
- **Der Dienstcontainer laeuft auch im SQLite-Lauf.** Dienstcontainer lassen sich nicht an einen Matrixeintrag binden. Die Alternative waere eine zweite, fast gleiche Jobdefinition gewesen; ein paar Minuten Leerlaufcontainer sind billiger als eine zweite Kopie von fuenfzehn Schritten.
- **Die Zeitschranke der Budgetprobe ist 2900 ms.** Sie muss unterhalb der kuenstlichen Verzoegerung von 3000 ms liegen, sonst waere sie auch ohne Zeitgrenze gruen. Erwartet werden rund 1,5 s bis 2 s, weil die zweite Anfrage in ihre 1,5-s-Grenze laeuft. Zusaetzlich, und zeitunabhaengig, wird geprueft, dass die Subline auf den Pfad zurueckgefallen ist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die ExApp-Registrierung kannte nur eine von drei Routen**

- **Found during:** Task 2, beim Nachlesen des Aufbaus
- **Issue:** `setup-test-nc/action.yml` registrierte genau eine Route (`search`, POST). `backend/appinfo/info.xml` fuehrt seit Phase 2 drei (`search`, `snippets`, `status`). AppAPI behandelt die Routenliste als Allowlist, eine nicht gelistete Route wird abgewiesen. Damit haette **jede** Suche in der CI Treffer geliefert und nie einen Textausschnitt, weil der Ausschnitt aus dem zweiten Aufruf kommt. Der Kommentar an genau dieser Stelle sagt seit Phase 1 voraus, was passiert: "If a later phase adds a route to info.xml and forgets it here, the integration job is what says so." Genau das ist eingetreten.
- **Fix:** Alle drei Routen registriert, `status` mit ADMIN, die anderen beiden mit USER, wie in `info.xml`. Der Kommentar sagt jetzt, dass die Voraussage eingetreten ist und wobei sie aufgefallen ist.
- **Files modified:** `.github/actions/setup-test-nc/action.yml`
- **Verification:** Die JSON-Nutzlast des Registrierungsaufrufs wurde aus der YAML geparst, entschluesselt und ausgegeben: drei Routen, korrektes JSON.
- **Committed in:** `80c3f1f`

**2. [Rule 1 - Bug] Zeilenumbrueche verklebten Woerter im Textausschnitt**

- **Found during:** Task 2, bei der Offline-Messung des Ausschnitts
- **Issue:** `PlainText::bounded` entfernte Steuerzeichen ersatzlos. pypdfium2 verbindet die Zeilen einer Seite mit CR LF, also wurde aus zwei Zeilen `...VerwaltungsbehördeDie Grundstücks...`, ein Wort, das in keinem Dokument steht. Das Abnahmekriterium des Checkpoints lautet woertlich "lesbarer Klartext"; der Kommentar in der Klasse selbst nannte den richtigen Ort fuer die Behebung ("they belong folded into spaces here").
- **Fix:** Ersatz durch ein Leerzeichen statt Loeschung, ein Zeichen fuer ein Zeichen. Weil das laengenerhaltend ist, waere der bisherige Identitaetsvergleich in `filterSnippets` ab sofort fuer jedes mehrzeilige Dokument falsch gewesen und haette dessen Hervorhebungen verworfen; er vergleicht jetzt die Laenge. Beide Stellen tragen den Zusammenhang als Kommentar, in beide Richtungen.
- **Files modified:** `php/lib/Text/PlainText.php`, `php/lib/Service/ExAppService.php`, `docs/testing.md`
- **Verification:** `php -l` ueber alle 17 Dateien in `php:8.2-cli` ohne Befund; die Ersetzung in derselben PHP-Version ausgefuehrt: Ausgabe lesbar, `mb_strlen` vorher gleich nachher.
- **Committed in:** `5d880c6`

**3. [Rule 3 - Blocking] Der Dialekt liess sich ueber die Composite-Action nicht waehlen**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt einen zweiten Matrixeintrag mit `maintenance:install --database=mysql`. Der Installationsschritt liegt in der geteilten Composite-Action und war fest auf `--database=sqlite` verdrahtet. Die Alternative waere gewesen, den halben Aufbau im neuen Job zu wiederholen, also genau die Verdopplung, wegen der die Action existiert.
- **Fix:** Fuenf Eingaben mit Vorgabewerten (`database`, `database-host`, `database-name`, `database-user`, `database-pass`), eine Fallunterscheidung im Installationsschritt und `pdo_mysql`/`mysqli` in der Erweiterungsliste. Die beiden vorhandenen Jobs uebergeben nichts davon und installieren unveraendert gegen SQLite. Der Schritt gibt das tatsaechlich installierte `dbtype` aus, damit ein stiller Rueckfall nicht als bestandene Dialektprobe durchgeht.
- **Files modified:** `.github/actions/setup-test-nc/action.yml`
- **Verification:** YAML geparst, 15 Schritte; die beiden alten Jobs referenzieren die neuen Eingaben nicht.
- **Committed in:** `b49d22c`

**4. [Rule 2 - Missing critical functionality] Das Skelettverzeichnis haette die Zaehlung wertlos gemacht**

- **Found during:** Task 2
- **Issue:** Der Plan beschreibt den Ablauf ab "zwei Nutzer anlegen". Ein neu angelegtes Nextcloud-Konto bekommt aber das Skelett (Handbuch, Bild, Vorlagenordner), und der Crawl laeuft ueber alle Einhaengungen der Instanz, auch ueber das Konto des Installateurs. Die Endzustaende waeren damit weder reproduzierbar noch aussagekraeftig gewesen, und ein englischsprachiges Handbuch im Index ist ausserdem ein zusaetzlicher Treffkandidat fuer jede Assertion.
- **Fix:** Ein Schritt vor dem Anlegen der Nutzer setzt `skeletondirectory` auf leer und leert das Konto des Installateurs, danach ein Scan mit der Ausgabe, wie viele Dateien die Instanz vor dem Korpus haelt.
- **Files modified:** `.github/workflows/integration.yml`
- **Verification:** Der Schritt gibt die Zahl aus, der Lauf belegt sie. Ohne Lauf ist das die schwaechste Stelle dieses Plans, siehe Deviation 5.
- **Committed in:** `b49d22c`

**5. [Rule 3 - Blocking] Die CI-Kriterien sind ohne Push nicht auswertbar**

- **Found during:** alle drei Tasks
- **Issue:** Jedes Task hat als Abnahmekriterium einen `gh run list`-Aufruf mit dem Wert `success`. Dieser Executor pusht nicht, der Orchestrator tut das nach dem Plan. `gh run list` liefert heute `success` fuer `integration.yml` (bei `1768ae0`) und fuer `resilience.yml` (bei `2310d7a`), also fuer den Stand **vor** diesem Plan. Laut Projektregel wird so etwas dokumentiert, nicht simuliert.
- **Fix:** Ersatzpruefungen, die ohne Runner moeglich sind: die vollstaendige Suchpipeline offline gegen die echte Wortliste gemessen (siehe oben), jeder `run`-Block beider geaenderter YAML-Dateien einzeln mit `bash -n` geprueft (24 Bloecke, alle sauber), beide YAML-Dateien mit einem Parser gelesen, die Registrierungsnutzlast als JSON geparst, `php -l` in der CI-Version ueber alle PHP-Dateien.
- **Files modified:** keine
- **Verification:** **Offen bis zum Push des Orchestrators.** Danach `gh run list --workflow=integration.yml --limit 1 --json conclusion -q '.[0].conclusion'` und dasselbe fuer `resilience.yml`.
- **Committed in:** keiner (Pruefschritt)

**6. [Rule 2 - Missing critical functionality] Der Kopfkommentar der Workflow-Datei nannte zwei Jobs**

- **Found during:** Task 2
- **Issue:** Das Abnahmekriterium verlangt, dass der Diff ausschliesslich Hinzufuegungen im neuen Job zeigt. Der Kopfkommentar der Datei beschrieb aber genau zwei Jobs, und eine Dateiueberschrift, die den teuersten Job der Datei verschweigt, schickt den naechsten Leser in die falsche Richtung.
- **Fix:** Ein Absatz **hinzugefuegt**, keine Zeile geaendert. Der Diff bleibt reine Hinzufuegung (`git diff HEAD` zaehlt null entfernte Zeilen), die Hinzufuegung liegt nur nicht im Job.
- **Files modified:** `.github/workflows/integration.yml`
- **Committed in:** `b49d22c`

**7. [Rule 2 - Missing critical functionality] Die lokale Anleitung haette ohne Wortliste geendet**

- **Found during:** Task 3
- **Issue:** Das Entwicklungs-Backend laeuft als Hostprozess, und `findling.index.wordlist` liest `/usr/share/dict/ngerman`. Auf einer Entwicklermaschine gibt es diese Datei nicht, der Poller stirbt in einem `FileNotFoundError`, bevor er die erste Zeile der Warteschlange anfasst. Genau daran ist der erste Lauf des Resilienz-Gates gescheitert. Eine Anleitung ohne diesen Schritt haette den Owner an derselben Stelle stehen lassen.
- **Fix:** Ein Kommando, das das Artefakt in einem Wegwerfcontainer baut und direkt in das Volume schreibt, das der Hostprozess liest. Es ist plattformunabhaengig, weil es den Systempfad nur im Container braucht. Ausgefuehrt und mit der erwarteten Ausgabe im Dokument belegt: 276496 Eintraege, Digest `b1f64012...`, identisch mit `docs/german-analyzer.md`.
- **Files modified:** `docs/dev-setup.md`
- **Verification:** Kommando ausgefuehrt, `.dev/storage/dict/de.txt` und `de.txt.sha256` liegen vor, Digest stimmt. `.dev/` ist gitignoriert.
- **Committed in:** `95ab7c2`

---

**Total deviations:** 7 auto-fixed (2 Bugs, 4 fehlende Notwendigkeiten, 1 blockierendes CI-Kriterium)
**Impact on plan:** Kein Scope-Zuwachs. Die beiden Bugs lagen genau auf dem Weg, den dieser Plan beweisen soll, und beide waeren ohne ihn erst einem Nutzer aufgefallen.

## Acceptance Criteria

### Task 1

| Kriterium | Soll | Ist |
|---|---|---|
| zweiter Lauf aendert keine Datei | leer | `git status --porcelain testdata/corpus` nach dem Commit leer |
| `ls testdata/corpus \| wc -l` | >= 12 | 13 |
| `du -sk testdata/corpus` | < 400 | 40 |
| `grep -c 'Genehmigung' build_corpus.py` | >= 1 | 1 |
| `grep -c 'WinAnsiEncoding' build_corpus.py` | >= 1 | 3 |
| Phase-1-Dateien unveraendert | ja | `git diff --stat HEAD -- testdata/corpus` nannte nur README.md |
| `.gitattributes` | unveraendert | unveraendert |
| `integration.yml` gruen | success | siehe Deviation 5 |

### Task 2

| Kriterium | Soll | Ist |
|---|---|---|
| `grep -c 'index-search-e2e'` | >= 1 | 2 |
| `grep -c 'jq -e'` | >= 12 | 35 |
| `grep -c '...api/v1/shares'` | 1 | 1 |
| `grep -c 'database=mysql'` | >= 1 | 1 |
| `grep -c 'FINDLING_ARTIFICIAL_DELAY_MS'` | >= 1 | 2 |
| `grep -c 'index_status'` | >= 2 | 3 |
| `grep -c 'german-analyzer.md'` | >= 1 | 1 |
| nur Hinzufuegungen | ja | 456 hinzugefuegt, 0 entfernt |
| gemessene Suchdauer mit und ohne Verzoegerung | im SUMMARY | **offen**, siehe unten |
| `integration.yml` gruen | success | siehe Deviation 5 |

### Task 3

Offen, das ist der Checkpoint.

## Die Zahlen, die noch fehlen

Der Plan verlangt die gemessene Gesamtzeit der Suche mit und ohne kuenstliche Verzoegerung im SUMMARY. Nachgetragen aus dem ersten gruenen Lauf (Commit 8048940, beide Matrixeintraege gruen):

- Gewoehnliche Suche end-to-end: **278 ms** (sqlite) bzw. **363 ms** (mysql).
- Budgetprobe mit 3000 ms kuenstlicher Verzoegerung je Excerpt: **1957 ms** (sqlite) bzw. **2049 ms** (mysql), also unter dem Provider-Budget; die 1,5-s-Grenze je Aufruf griff, die Suche selbst blieb antwortfaehig.

Erstlauf-Befund desselben Laufs (behoben in 8048940): die Korpus-Beschreibung `testdata/corpus/README.md` nannte alle Suchbegriffe im Klartext, wurde mitindexiert und machte jeden exakten Trefferzaehler zum Off-by-one. Sie liegt jetzt als `testdata/CORPUS.md` ausserhalb des Korpus, `EXPECTED_INDEXED` ist 8.

## Threat Flags

Keine neue Angriffsflaeche. Die sechs `mitigate`-Dispositionen des Plans:

| Threat ID | Umsetzung |
|---|---|
| T-02-141 (Treffer aus fremden Dateien) | Der zweite Nutzer wird in beide Richtungen geprueft: eine Freigabe findet er, drei Begriffe, die dem ersten Nutzer je eine Datei liefern, liefern ihm nichts. Offline vorab gemessen |
| T-02-142 (Textausschnitt ohne Zugriff) | Der Ausschnitt entsteht erst nach dem Recheck (02-12) und wird im Container zusaetzlich vorgefiltert (02-11). Der Job belegt den Ausschnitt an einem echten Dokument |
| T-02-143 (Assertion aus dem falschen Grund gruen) | Jeder Suchbegriff steht in genau einer Datei, gemessen gegen die echte Wortliste; das eine bewusste Doppelwort traegt die Kontrollprobe des Ausschlusses; jede Assertion prueft Anzahl **und** Titel |
| T-02-144 (veraenderte Phase-1-Dateien) | Kein Byte bewegt, und Gate B vergleicht weiterhin jede Pruefsumme ueber eine dynamisch gezaehlte Liste |
| T-02-145 (langsames Backend blockiert die Suchleiste) | Budgetprobe mit 3000 ms Verzoegerung, Schranke 2900 ms, plus die zeitunabhaengige Pruefung, dass die Subline auf den Pfad zurueckgefallen ist |
| T-02-146 (dialektabhaengiger Upsert) | Zweiter Matrixeintrag mit MariaDB; der installierte Dialekt wird ausgegeben, damit ein stiller Rueckfall nicht als bestanden durchgeht |
| T-02-147 (Suchbegriffe im CI-Log) | unveraendert `accept`: der Korpus ist oeffentliches Testmaterial ohne Nutzerdaten |

## Known Stubs

Keine.

## Issues Encountered

- **Der teuerste Job des Projekts ist von hier aus nicht ausfuehrbar.** Alles, was ohne Runner pruefbar war, wurde geprueft (Deviation 5). Die verbleibende Unsicherheit liegt bei den Dingen, die erst eine echte Nextcloud zeigt: ob die Freigabe ueber die OCS-API in dieser Serverversion genau so antwortet, ob `skeletondirectory` auf leer wirklich jedes Skelett verhindert, und ob MariaDB 11.4 mit `stable34` anstandslos installiert.
- **Der zweite Dialekt ist der wahrscheinlichste rote Lauf.** Das ist der Zweck des Eintrags. Faellt er rot aus, ist die erste Stelle zum Nachsehen der Upsert der Warteschlange, also die offene Frage 4 des RESEARCH.
- **Eine Zahl im Resilienz-Gate haengt am Korpus.** `resilience.yml` rechnet die Kopienzahl aus der Dateizahl je Kopie aus. Die Arithmetik traegt (32 Kopien, 384 beurteilte Dateien gegen eine Untergrenze von 200), aber sie traegt nicht beliebig weit: ein Korpus mit sehr vielen Dateien je Kopie wuerde die Verdopplung dort unnoetig teuer machen.

## User Setup Required

Die Sichtprobe des Checkpoints. Die Schritte stehen kopierfertig in `docs/dev-setup.md` im Abschnitt "Phase 2: from a file on disk to a content hit".

## Offen

**Task 3, Checkpoint `human-verify`.** Der Owner sieht einen echten Inhaltstreffer mit Textausschnitt und macht die Gegenprobe mit dem zweiten Nutzer. Seine Beobachtung gehoert danach in dieses Dokument, zusammen mit den beiden gemessenen Suchzeiten aus dem ersten gruenen Lauf.

## Self-Check: PASSED

- Alle vier neuen Korpusdateien liegen im Arbeitsverzeichnis und sind committet.
- Alle fuenf Commits liegen im Log von `main`: `2eec453`, `80c3f1f`, `5d880c6`, `b49d22c`, `95ab7c2`.
- Keine Loeschung in irgendeinem Commit dieses Plans: `git diff --diff-filter=D HEAD~1 HEAD` war nach jedem Commit leer.
- Keine Aenderung an `STATE.md`, `ROADMAP.md` oder `REQUIREMENTS.md`.
- Nicht gepusht, wie beauftragt.

---
*Phase: 02-indexkern-und-volltextsuche*
*Stand: 2026-09-01, Checkpoint offen*
