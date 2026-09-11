---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 07
subsystem: ci
tags: [deploy-harp, upgrade, d-04, d-05, index, rel-01, store-install]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-02, die Ratsche backend/tests/test_upgrade_compatibility.py mit GOLD_V1_0_3
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-04, der Release-Asset-Modus und der gemessene Abstand zu timeout-minutes 45
  - phase: 06.1-launch-haertung-vor-der-store-abgabe
    provides: die Store-Install-Strecke, die sechs Store-Deinstallationszusagen und der overview.sh-Helfer der Driftprobe
provides:
  - "deploy-harp.yml faehrt einen Upgrade-Block: v1.0.3 aus den Release-Assets, Referenzkorpus indexiert, Upgrade auf den HEAD-Stand, sechs Zusicherungen"
  - "Erfolgskriterium 2 der Phase 11 steht mit einer Laufnummer statt mit einer Code-Lesung (Lauf 34546421219)"
  - "der Ende-zu-Ende-Beleg zu D-04: fuenf Marken, Trefferzahlen, Dokumentzahlen und Arbeitsvorrat sind vor und nach dem Upgrade paarweise gleich"
  - "der nicht gefahrene Reindex-Zweig von D-05 ist im Workflow benannt, nicht verschwiegen"
affects: [11-10, 11-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Sonde, zwei Lesungen: upgrade-probe.sh wird einmal geschrieben und von der Vorher- und der Nachher-Feststellung gesourct, damit zwei Zustaende und nicht zwei Messungen verglichen werden"
    - "Der Zustand einer Installation als ein JSON-Dokument (Begriffe, Marken, Zaehler, Menue, Banner), danach Vergleich je Schluessel mit eigener Fehlermeldung"
    - "Die fuenf Marken werden im Container selbst gelesen (docker exec python -m findling.tools.index_status), nicht ueber die signierte /status-Route"
    - "Ein Block, der ohne Aussage gruen werden koennte, laeuft in diesem Modus gar nicht: die if-Bedingung schliesst release_tag aus, statt v1.0.3 mit v1.0.3 zu vergleichen"

key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml

key-decisions:
  - "Der Block liegt hinter den sechs Store-Deinstallationszusagen und nicht zwischen Store install 7 und ihnen: die Zusagen brauchen die Store-Installation unversehrt, ein Upgrade mitten darin haette ihnen den Gegenstand weggenommen"
  - "Genau ein Ast (stable34, ubuntu-24.04). Ein Upgrade-Pfad ist eine Aussage ueber die App und nicht ueber die Serverversion; jeder Schritt traegt beide Matrixwerte in seiner eigenen if-Bedingung, weil diese Datei keine Blockbedingung kennt"
  - "Dritte Bedingung env.RELEASE_TAG == '': mit gesetzter Eingabe hat die Store-Strecke die Archive genau dieses Tags installiert, die neue Haelfte waeren dieselben Bytes wie die alte, und der Beweis waere gruen ohne gemessen zu haben"
  - "Der Aufraeumschritt Store upgrade 0 entfernt das Volumen des Store-Durchgangs mit docker und nie ueber die Datenflagge von occ; die Flagge ist im ganzen Block nicht einmal ausgeschrieben, damit ein grep darueber leer bleibt (T-11-26)"
  - "Die neue Container-Haelfte wird mit info-citest.xml registriert (das Abbild dieses Commits aus der lokalen Registratur) und nicht mit STORE_INFO_XML: backend/appinfo/info.xml nennt bis Plan 11-11 weiterhin image-tag 1.0.3, also genau das Abbild, das die alte Haelfte schon faehrt, und die Container-Haelfte des Upgrades waere ein Nulltausch"
  - "Der Schritt prueft ausdruecklich, dass altes und neues Abbild verschieden sind; ein Nulltausch faellt damit auf, statt sechs Zusicherungen gruen zu faerben"
  - "occ upgrade bekommt beide Zweige: bewegt sich die Version, muss installed_version nachziehen; bewegt sie sich nicht (Stand vor 11-11), steht das als ::notice im Protokoll statt als Schoenrederei"
  - "Das Reindex-Banner wird dort gelesen, wo es entschieden wird (backend.reindexRequired der Admin-Uebersicht), und der overview.sh-Helfer der Driftprobe wird wiederverwendet statt nachgebaut"

patterns-established:
  - "Vorher- und Nachher-Feststellungen bekommen eine gemeinsame Sonde und ein gemeinsames JSON-Schema; die Zusicherungen laufen alle, statt beim ersten Unterschied abzubrechen"
  - "Jede Zusicherung ueber Unveraendertheit braucht mindestens eine Zusicherung ueber eine Aenderung neben sich, sonst waere ein Upgrade, das gar nichts getan hat, das gruenste Ergebnis"

requirements-completed: []

# Metrics
duration: 55min
completed: 2026-09-11
---

# Phase 11 Plan 07: Der Upgrade-Beweis 1.0.3 auf den HEAD-Stand Summary

**Der letzte der neun Haertungspfade der Owner-Regel vom 06.09.2026, den CI nicht fuhr, wird jetzt gefahren: eine Installation aus den echten v1.0.3-Release-Assets indexiert den 39-Datei-Korpus, wird auf den Stand dieses Commits gebracht, und Trefferzahlen, Dokumentzahlen, Arbeitsvorrat und alle fuenf Indexmarken sind danach Ziffer fuer Ziffer dieselben (Lauf 34546421219, erster Anlauf gruen).**

## Performance

- **Duration:** rund 55 min, davon rund 13 min CI-Wartezeit, keine Box-Minute
- **Started:** 2026-09-11T00:05:00Z
- **Completed:** 2026-09-11T01:00:00Z
- **Tasks:** 2 von 2
- **Files modified:** 1 geaendert, 0 neu

## Was der Beweis konkret zeigt

Dieselbe Installation, zweimal gelesen, mit derselben Sonde. Links der echte
v1.0.3-Bestand, rechts derselbe Bestand nach dem Upgrade:

| Groesse | vor dem Upgrade | nach dem Upgrade |
|---|---|---|
| Treffer `Belehrung` | 1 | 1 |
| Treffer `Auszug` | 1 | 1 |
| Treffer `Erinnerung` | 1 | 1 |
| `docs` im tantivy-Index | 29 | 29 |
| `indexed` (Container) | 29 | 29 |
| `skipped` / `failed` (Container) | 7 / 6 | 7 / 6 |
| `skipped` / `failed` (Nextcloud) | 7 / 6 | 7 / 6 |
| Arbeitsvorrat `scheduled` / `running` | 0 / 0 | 0 / 0 |
| `schemaVersion` | `1` | `1` |
| `indexVersion` | `1` | `1` |
| `analyzerVersion` | `1` | `1` |
| `wordlistHash` | `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0` | dasselbe |
| `tantivyVersion` | `tantivy v0.26.0, index_format v7` | dasselbe |
| Reindex-Banner | aus | aus |
| `start_rebuild_on_drift`-Zeile | , | keine, in 41 Protokollzeilen |
| Navigationseintrag | **fehlt** (`dashboard files`) | **da** (`dashboard files findling`) |

Der Index ist also nicht nur "irgendwie noch da": er ist **derselbe**. Der
Container, der nach dem Upgrade auf dem Volumen hochkommt, ist ein anderes
Abbild (`localhost:5000/findling_backend:citest` statt
`ghcr.io/street1983nk/findling_backend:1.0.3`, im Schritt geprueft), und er
findet dieselben drei Dokumente ueber dieselben drei Begriffe, zaehlt dieselben
29 Dokumente und stempelt keine Marke um.

Die drei Begriffe sind keine beliebigen Woerter. Jeder von ihnen hat eine
gemessene Aussage in `backend/tests/test_corpus_terms.py`: `Belehrung` steht im
ganzen Korpus nur in `Rechtsmittelbelehrung` in
`15-schweiz-baubewilligung.pdf`, `Auszug` nur in `Grundbuchsauszug` in
`16-oesterreich-mitteilung.pdf`, `Erinnerung` nur in `Zahlungserinnerung` in
`30-nur-ein-bild.pdf`, und alle drei sitzen auf **gescannten** Seiten. Ein
Treffer ist damit die ganze Kette: OCR, Kompositazerlegung, Index, Suche. Die
Vorher-Feststellung besteht darauf, dass jeder der drei genau eine Datei
zurueckbringt, sonst waere eine unveraenderte Zahl nach dem Upgrade die
unveraenderte Abwesenheit eines Treffers.

Die sechste Zusicherung ist die Gegenprobe zu den fuenf anderen: der
Navigationseintrag aus Plan 09-06 war vorher nicht da und ist nachher da. Ohne
sie waere ein Upgrade, das gar nichts bewirkt hat, das gruenste aller
Ergebnisse. Dass der v1.0.3-Bestand ihn wirklich nicht kennt, wird nicht
geglaubt, sondern im entpackten Archiv geprueft (`grep '<navigations>'` muss
leer sein), bevor irgendetwas installiert wird.

## Der Weg, den der Block geht

1. **Store upgrade 0** raeumt den Store-Durchgang weg: `app_api:app:unregister`
   ohne Flagge, dann das Volumen mit `docker volume rm` beim Namen. Die
   Datenflagge kommt im ganzen Block nicht vor, nicht einmal als Zeichenkette
   in einem Kommentar, damit ein `grep` darueber leer bleibt (T-11-26).
2. **Store upgrade 1** laedt `findling.tar.gz` und `findling_backend.tar.gz`
   vom GitHub-Release `v1.0.3`, ueber genau den URL-Weg, den `store-submit.yml`
   dem Store nennt, mit `sha256sum` im Protokoll. Die Begleit-App traegt die
   echte Release-Signatur, die Container-Haelfte wird mit der `info.xml` aus
   dem Archiv registriert, also gegen `ghcr.io/street1983nk/findling_backend:1.0.3`.
3. **Store upgrade 2** legt den 39-Datei-Korpus in das Konto des gewoehnlichen
   Nutzers, `occ files:scan --all`, `occ findling:index --restart`, und faehrt
   dann die Warteform dieses Jobs: `php -f cron.php` in einer Schleife, die
   Bedingung aus zwei unabhaengigen Quellen (Arbeitsvorrat aus Nextcloud,
   Urteile aus dem Container), kein fester Schlaf. **Vier cron-Runden, rund
   18 s von 900 s Budget.**
4. **Store upgrade 3** schreibt die Sonde und die Vorher-Feststellung nach
   `upgrade-before.json`.
5. **Store upgrade 4** tauscht die Begleit-App (Verzeichnis weg, Archiv dieses
   Commits hin, `occ upgrade`) und danach den Container (`unregister` ohne
   Flagge, `register` mit dem neuen `image-tag` auf demselben Volumen), und
   wartet ueber die Kanarienvogel-Suche darauf, dass der neue Container wieder
   antwortet.
6. **Store upgrade 5** schreibt `upgrade-after.json` und faehrt die sechs
   Zusicherungen, jede einzeln, jede mit einer Fehlermeldung, die sagt, was sie
   bedeutet. Alle sechs laufen auch dann, wenn eine faellt.

Beide JSON-Dateien, die Statusausgaben, das Urteil von `occ upgrade`, die
Admin-Uebersicht und das Containerprotokoll wandern in das Log-Artefakt
`harp-logs-stable34`.

## Der nicht gefahrene Zweig (D-05)

Er steht als Kommentarblock ueber Store upgrade 5, und er ist eine Aussage und
keine Luecke. D-05 verlangt, dass ein **noetiger** Reindex sichtbar anlaeuft,
und die Mechanik dafuer ist auf beiden Seiten da:
`findling.index.open.start_rebuild_on_drift` hebt die lokale Generation und
schreibt die Zeile, nach der dieser Schritt sucht, der Container meldet
`reindexRequired`, und `php/templates/admin.php` hebt den Absatz
`findling-banner-reindex` mit `occ findling:index --restart` als Abhilfe.

Dieser Test faehrt den Zweig nicht, weil D-04 sagt, dass sich zwischen 1.0.x
und dieser Fassung keine Marke bewegt, und weil
`backend/tests/test_upgrade_compatibility.py` genau das gegen den Code haelt.
Was hier zugesichert wird, ist die **Abwesenheit** des Driftsignals. Bewegt
sich je eine Marke wirklich, faellt Zusicherung 2 **vor** den beiden
Abwesenheitszusicherungen, und die Frage danach gehoert dem Owner und nicht
einer Testbearbeitung. Das ist derselbe Satz, den die Ratsche aus 11-02 traegt.

## Laufzeit gegen `timeout-minutes: 45`

| Ast | Laufzeit | Upgrade-Block |
|---|---|---|
| stable33, 8.2, ubuntu-24.04 | 12 min 31 s | uebersprungen |
| **stable34, 8.2, ubuntu-24.04** | **12 min 39 s** | **gefahren, 1 min 32 s** |
| stable34, 8.2, ubuntu-24.04-arm | 10 min 25 s | uebersprungen |
| stable35, 8.3, ubuntu-24.04 (tolerant) | 11 min 55 s | uebersprungen |

Der Ast, der den Block faehrt, ist der laengste, und er liegt **32 min 21 s**
unter dem Deckel. `timeout-minutes: 45` bleibt unveraendert; der Wert musste
nicht angefasst werden. Zum Vergleich der Stand vor dieser Aenderung: Lauf
34530207632, derselbe Ast ohne den Block, **11 min 56 s**. Die Differenz von
43 s ist kleiner als die Summe der Blockschritte von 1 min 32 s, weil die
uebrigen Schritte von Lauf zu Lauf um eine aehnliche Groesse schwanken. Beide
Zahlen stehen hier, damit niemand die kleinere fuer eine Messung des Blocks
haelt: die belastbare Zahl ist die Summe der sechs Schritte, und der Abstand
zum Deckel traegt sie dreissigfach. In der Wanduhrzeit des ganzen Laufs faellt
sie ohnehin nicht auf, weil die Aeste parallel fahren.

Die Einzelzeiten des Blocks: Store upgrade 0 eine Sekunde, 1 rund 34 s
(Download plus Registrierung des 1.0.3-Containers), 2 rund 18 s (vier
cron-Runden), 3 zwei Sekunden, 4 rund 34 s (Dateitausch, `occ upgrade`, zweite
Registrierung, Bereitschaftsprobe), 5 drei Sekunden.

## Praezisierungen gegenueber dem Plan

Keine Abweichung von einer Aufgabe, aber vier Stellen, an denen der Plan eine
Entscheidung offenliess und der Code sie treffen musste:

1. **Der Versionsschritt fehlt noch, und das steht im Protokoll.** Der Plan
   spricht vom "lokal gebauten v1.1.0-Archiv". `php/appinfo/info.xml` und
   `backend/appinfo/info.xml` tragen heute beide weiterhin **1.0.3**; der
   Versionsbump ist Plan 11-11 (Welle 7). `occ upgrade` antwortete deshalb
   `No upgrade required.` mit Rueckgabewert 0, und `installed_version` blieb
   bei 1.0.3. Der Schritt hat **beide** Zweige: bewegt sich die Version, muss
   `installed_version` nachziehen, sonst ist es ein Fehler; bewegt sie sich
   nicht, steht ein `::notice` im Protokoll, das den Zustand benennt. Ab 11-11
   laeuft der erste Zweig, ohne dass die Datei angefasst werden muss. Fuer den
   Gegenstand des Beweises ist das folgenlos: der Index liegt im Volumen des
   Containers, und die sechs Zusicherungen messen das Volumen. Der
   Navigationseintrag erscheint trotzdem, weil Nextcloud die `info.xml` ueber
   Pfad **und Mtime** zwischenspeichert, also die neue Datei neu liest.
2. **Die dritte `if`-Bedingung.** Mit gesetztem `release_tag` haette der Block
   v1.0.3 gegen v1.0.3 verglichen. Statt ihn laufen und nichts messen zu
   lassen, laeuft er in diesem Modus gar nicht. Die beiden vom Plan geforderten
   Matrixwerte stehen unveraendert in jeder Bedingung.
3. **Ein Schritt mehr, als der Plan nummeriert.** `Store upgrade 0` raeumt den
   Store-Durchgang weg, nach dem Vorbild von `Store install 0` und
   `Store install 2`. Ohne ihn haette die 1.0.3-Installation das Volumen der
   letzten Registrierung des Store-Durchgangs geerbt, und die Zahlen der
   Vorher-Feststellung haetten zwei moegliche Quellen gehabt.
4. **Die harte Speichergrenze aus `scripts/ops/aws_box.sh`** ist im Schritt
   benannt und nicht nachgezogen, weil dieser Job gegen keine misst und
   nirgends eine setzt. Der Kommentar sagt, an welcher Stelle sie nachgezogen
   werden muesste, sobald das einmal anders ist.

## Task Commits

1. **Task 1:** `9d7b407` , `ci(11-07): die Vorher-Feststellung auf dem v1.0.3-Bestand` (UPGRADE_FROM_TAG, UPGRADE_DRAIN_BUDGET_SECONDS, Store upgrade 0 bis 3, die geteilte Sonde)
2. **Task 2:** `0844bf0` , `ci(11-07): das Upgrade fahren und die Gleichheit zusichern` (Store upgrade 4 und 5, D-05 im Kommentar, Beweisdateien in das Log-Artefakt)

Gepusht: `6ca13e1..0844bf0` auf `origin/main` (mit den sechs offen gebliebenen
Commits aus 11-06).

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | **2012 passed, 15 skipped** (Grundlinie unveraendert) |
| `uv run python -m pytest tests/test_workflow_pins.py tests/test_lockstep_versions.py -q` | 37 passed, vor jedem Commit |
| `uv run python -m pytest tests/test_upgrade_compatibility.py -q` | gruen (die Ratsche aus 11-02, unveraendert) |
| `uv run ruff check .` / `format --check .` | All checks passed / 121 files already formatted |
| `uv run ruff check --config pyproject.toml ../scripts` / `format --check` | All checks passed / 10 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | leer |
| `yaml.safe_load(deploy-harp.yml)` | gueltig, vor jedem Commit |
| `grep -c "Store upgrade"` | 5, gefordert mindestens 3 |
| `grep -c "releases/download"` im Block | 1 ueber `UPGRADE_FROM_TAG`, plus die Variable mit Begruendung |
| `--rm-data` in den sechs Upgrade-Schritten | **0**, per YAML-Parser je Schritt geprueft |
| `if`-Bedingungen der sechs Schritte | alle sechs nennen `stable34` **und** `ubuntu-24.04` |
| Schrittnamen gegen `5e61a66` | **keine** umbenannt, keine entfernt, sechs hinzugefuegt |

`actionlint` steht auf diesem Rechner nicht zur Verfuegung; die Pruefung lief
ueber `yaml.safe_load` plus eine Strukturpruefung ueber Namen, Bedingungen und
Schrittkoerper. Die eigentliche Validierung war der gruene Lauf.

## CI nach dem Push

| Lauf | Ausloeser | Ergebnis |
|---|---|---|
| **34546421219** | Push `0844bf0` | **success**, alle vier Aeste |

Die Upgrade-Schritte je Ast, aus der API gelesen:

| Ast | Store upgrade 0 bis 5 |
|---|---|
| stable33, 8.2, ubuntu-24.04 | skipped, skipped, skipped, skipped, skipped, skipped |
| **stable34, 8.2, ubuntu-24.04** | **success, success, success, success, success, success** |
| stable34, 8.2, ubuntu-24.04-arm | skipped, skipped, skipped, skipped, skipped, skipped |
| stable35, 8.3, ubuntu-24.04 | skipped, skipped, skipped, skipped, skipped, skipped |

Genau ein Ast faehrt den Block, drei ueberspringen ihn. Andere Workflows hat
der Push nicht angestossen, weil die Pfadfilter der uebrigen Dateien auf
`.github/workflows/deploy-harp.yml` nicht greifen.

## Was das fuer die naechsten Plaene heisst

- **11-10 (Audits):** Erfolgskriterium 2 der Phase ist belegt und braucht keine
  Code-Lesung mehr. Die Belegstelle ist Lauf **34546421219**, Ast
  `stable34, 8.2, ubuntu-24.04`, Schritte `Store upgrade 0` bis
  `Store upgrade 5`.
- **11-11 (Versionsbump und Einreichung):** Sobald beide `info.xml` und der
  `image-tag` auf 1.1.0 stehen, faehrt derselbe Block ohne eine Zeile
  Aenderung den **anderen** Zweig: `occ upgrade` fuehrt dann ein echtes
  App-Update aus, und der Schritt besteht darauf, dass `installed_version`
  nachzieht. Der Lauf danach ist der Beweis "1.0.3 auf 1.1.0" im Wortsinn.
  Zweitens: sobald `ghcr.io/street1983nk/findling_backend:1.1.0` existiert,
  kann die neue Container-Haelfte auf `STORE_INFO_XML` umgestellt werden, falls
  das jemand will; noetig ist es nicht, weil der Block ohnehin prueft, dass
  altes und neues Abbild verschieden sind.
- **REL-01 bleibt offen.** Der Upgrade-Pfad ist belegt, die Freigabe selbst
  nicht; das Haken setzt 11-11.

## Self-Check: PASSED

- `.github/workflows/deploy-harp.yml` vorhanden, gueltiges YAML, 47 Schritte
- Commit `9d7b407` vorhanden
- Commit `0844bf0` vorhanden, identisch mit `origin/main`
- Lauf `34546421219` auf `success`, sechs Upgrade-Schritte `success` auf genau
  einem Ast
