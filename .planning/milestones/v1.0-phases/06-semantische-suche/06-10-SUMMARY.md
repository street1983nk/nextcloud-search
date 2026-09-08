---
phase: 06-semantische-suche
plan: 10
subsystem: quality
tags: [gates, fallstrick-1, offline, kriterium-3, grep-hygiene, d-20, d-17b, t-06-47, t-06-51]

# Dependency graph
requires:
  - phase: 06-semantische-suche
    provides: "06-06: die eine Suchroute mit der Verschmelzung oberhalb des einen Vorfilters, und die zwei Aufrufstellen von prefilter_visible"
  - phase: 06-semantische-suche
    provides: "06-08: der zweite Ausschnittsweg, der die Zahl 2 zum ersten Mal unter Druck gehalten hat"
  - phase: 06-semantische-suche
    provides: "06-09: _sides als die eine Stelle beider Ranglisten, und origins ausschliesslich in api/diagnose.py"
  - phase: 06-semantische-suche
    provides: "06-03: die Telemetriezeile von onnxruntime als fehlgeschlagener lokaler Schreibversuch, weitergereicht an den Offline-Test"
  - phase: 05-betriebsbeweis
    provides: "der Job search-parity, sechs Rechteszenarien ueber die eine Suchroute, in diesem Plan unveraendert"
provides:
  - "backend/tests/test_semantic_boundary.py: zwoelf quellcode-lesende Zusicherungen mit Tokenizer-Hygiene"
  - "backend/tests/probe_image_search.py: der Rumpf der zwei Abbild-Schritte, in zwei Betriebsarten"
  - "der Offline-Schritt in docker.yml, beide Architekturen, mit Kontrolllauf"
  - "der Modell-weg-Schritt in docker.yml, mit eigenem Rotnachweis gegen einen leeren Index"
  - "die Umschreibung im Integrationslauf, mit lexikalischem Kontrolllauf und einer Wartefrist aus der gemessenen Rate"
  - "docs/testing.md: die dreizehn Gates der Phase, jedes mit seiner Grenze"
  - "docs/embeddings.md Abschnitt 7: der Betriebsablauf beider Spuren"
affects: [06-11 Lasttest, 06-12 Store-Abgabe]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine zaehlende Zusicherung laeuft ueber tokenisierten Quelltext statt ueber Zeilen, damit sie an ihrem eigenen Erklaertext nicht scheitern kann"
    - "Ein CI-Schritt bekommt seinen Rumpf als Datei unter tests/, damit er lint-, typ- und lokal pruefbar ist statt als Heredoc im Arbeitsablauf zu leben"
    - "Ein Gate ueber eine Abwesenheit traegt eine Antivakuitaetsklausel: die Menge dessen, was es ueberhaupt sieht, wird mitgeprueft"
    - "Ein Artefakt, das in einen CI-Lauf geholt wird und Code ausfuehrt, wird gegen eine aufgeschriebene Pruefsumme verglichen und nicht nur gezaehlt"

key-files:
  created:
    - backend/tests/test_semantic_boundary.py
    - backend/tests/probe_image_search.py
  modified:
    - .github/workflows/docker.yml
    - .github/workflows/integration.yml
    - docs/testing.md
    - docs/embeddings.md
    - README.md

key-decisions:
  - "Die Grep-Hygiene laeuft ueber tokenize und nicht ueber einen Zeilenfilter: ein Zeilenfilter faengt Kommentarzeilen und laesst Docstrings stehen, und genau dort stehen alle fuenf Nennungen von prefilter_visible in store/vectors.py"
  - "Die zwei Aufrufstellen werden zusaetzlich benannt (_permit und snippets_for), weil eine blosse Zwei auch von zwei falschen Stellen erfuellt waere"
  - "Der Rumpf der zwei Abbild-Schritte ist eine Datei unter backend/tests/ und kein Heredoc in docker.yml; die Modell-weg-Betriebsart braucht kein Modell und ist deshalb lokal gefahren worden, bevor sie committet wurde"
  - "Der Modell-weg-Fixture traegt keinen Vektorbestand, weil das der Zustand eines Volumens ist, dessen zweite Spur nie ein Modell hatte; damit ist degraded von der fehlenden vierten Ursache getrieben und nicht von unbeschriebenen Versionsmarken, die der Fixture ausdruecklich setzt"
  - "Der Integrationslauf holt das Modell aus dem veroeffentlichten Abbild statt es von einem Modell-Hub zu ziehen, und vergleicht seine sha256 gegen die dreimal gemessene aus Plan 06-03"
  - "Die Umschreibung im Integrationslauf behauptet nicht den ersten Rang, sondern die Anwesenheit des Dokuments, und der Kontrolllauf ohne Zweitspur traegt die Aussage; die Rangqualitaet ist der Messbericht und der Offline-Schritt"
  - "Der Schritt-NAME in docker.yml traegt das Wort degraded, weil die Verifikationszeile des Plans str(d['jobs']) liest und ein YAML-Kommentar dort nicht vorkommt"

patterns-established:
  - "Ein Gate, dessen Aussage eine Abwesenheit ist, bringt seinen eigenen Rotnachweis gegen einen kuenstlichen Quelltext mit"
  - "Zu jedem Abbild-Schritt gehoert ein Kontrolllauf, der belegt, dass die gemessene Eigenschaft nicht ohnehin gilt"

requirements-completed: [SEM-01, SEM-02]

# Metrics
duration: 32min
completed: 2026-09-05
---

# Phase 6 Plan 10: Prüf-Gates Summary

**Die drei Sätze dieser Phase, die man nicht glauben, sondern nur prüfen kann, sind ab jetzt Prüfungen: es gibt keinen zweiten Ausgang, und das ist ein Test, der an seinem eigenen Erklärtext nicht scheitern kann; das gebaute Abbild fährt eine semantische Suche mit abgeklemmtem Netzwerk; und mit leerem Modellverzeichnis liefert dasselbe Abbild Volltexttreffer plus die Marke degraded statt einer leeren Antwort. Der Paritätstest aus Phase 5 ist unverändert, und docs/testing.md sagt für jedes der dreizehn Gates, was es nicht beweist.**

## Performance

- **Duration:** rund 32 min
- **Started:** 2026-09-05T09:28:00Z
- **Completed:** 2026-09-05T10:00:00Z
- **Tasks:** 3 von 3
- **Files modified:** 7 (2 neu, 5 geändert)
- **Tests:** 1.350 bestanden, 13 übersprungen (vorher 1.338), also 12 neue Fälle

## Accomplishments

- **Die Grep-Hygiene ist das eigentliche Ergebnis von Task 1, und sie war keine Formalie.** `store/vectors.py` nennt `prefilter_visible` fünfmal und ruft es keinmal, und alle fünf Nennungen stehen in Docstrings, die die Richtung erklären, in der der Vorfilter fragt. Ein Zeilenfilter über `#` hätte keine einzige davon gefangen; die Zusicherung "kommt dort überhaupt nicht vor" wäre sofort rot gewesen, und zwar an dem Text, der sie begründet. Gezählt wird deshalb über `tokenize`: nur NAME- und OP-Token, also weder Kommentare noch Docstrings noch Zeichenkettenliterale. Zwei Fälle belegen die Hygiene an einer künstlichen Datei, deren naiver Zähler siebenmal anschlägt und deren hygienischer einmal.
- **Die Zahl 2 reicht nicht, also stehen die zwei Stellen mit Namen da.** `test_the_two_call_sites_are_the_candidate_round_and_the_snippet_cut` liest den Baum mit `ast` und verlangt `["_permit", "snippets_for"]`. Zwei Aufrufe an zwei falschen Stellen wären von der Zahl allein nicht zu unterscheiden gewesen. Beide Zusicherungen haben ihren Rotnachweis: derselbe Quelltext plus eine Funktion mit einem dritten Aufruf ergibt 3, und die neue Stelle wird beim Namen genannt.
- **Der Routenscan bringt seine Antivakuitätsklausel mit.** Er zählt nicht nur die verbotenen Pfade, sondern auch alle deklarierten, und vergleicht sie gegen die fünf, die es gibt. Ein Parser, der Dekoratoren nicht mehr sieht, meldet sonst null Verstöße über null Routen und sieht kerngesund aus, während die zweite Route direkt daneben steht.
- **Der Modell-weg-Schritt ist lokal gefahren worden, bevor er committet wurde.** Er braucht kein Modell, also läuft er auf der Entwicklungsmaschine: Referenzlauf ohne Semantik `[1]` bei `degraded false`, Lauf mit eingeschaltetem Einbetten und leerem Modellverzeichnis `[1]` bei `degraded true`, und der eingebaute Rotnachweis gegen einen absichtlich leeren Index meldet sich wie verlangt. Der Kontrolllauf des Offline-Schritts ist ebenfalls lokal belegt: die Umschreibung findet ohne Vektorbestand nichts.
- **Der Paritätstest ist unverändert, und das ist nachgerechnet.** Alle Hunks von `git diff` liegen zwischen den ursprünglichen Zeilen 914 und 1301, also innerhalb von `index-search-e2e` (788 bis 1318). Der Job `search-parity` beginnt bei Zeile 1789 und ist von keiner Zeile berührt.

## Task Commits

1. **Task 1: Die Grenzzusicherungen als Testdatei, mit sauberer Grep-Hygiene** - `d6b4dcc` (test)
2. **Task 2: Offline-Nachweis, Modell-weg-Abnahme und die Umschreibung im Integrationslauf** - `e6e9e46` (feat)
3. **Task 3: Die Gate-Landschaft und die Doku-Seiten mitziehen** - `650c92f` (docs)
4. **Die geholte Modelldatei wird geprüft und nicht nur gezählt** - `f8acbb4` (fix)

## Files Created/Modified

- `backend/tests/test_semantic_boundary.py` - zwölf Fälle über sieben Eigenschaften, dazu die zwei Leser (`code_mentions`, `call_sites`) über tokenisiertem Quelltext, `functions_calling` und `route_paths` über `ast`, drei Rotnachweise und zwei Hygienefälle; der Kopf nennt Fallstrick 1 und sagt am Ende, was die Datei nicht beweist
- `backend/tests/probe_image_search.py` - der Rumpf der zwei Abbild-Schritte in den Betriebsarten `offline` und `model-gone`, mit einem eigenen Korpus aus fünf erfundenen deutschen Passagen, dem Bau eines vollständigen Volumens, dem echten Einbettungsweg der zweiten Spur und `api.search.one_round` als der Suchpfad, den auch die Route fährt
- `.github/workflows/docker.yml` - zwei Schritte neben der Probe aus 06-01, beide mit `--network none`, beide auf beiden Architekturen; der Kommentar über dem ersten trägt die ganze Aussage zu HF_HUB_OFFLINE samt der Telemetriezeile aus 06-03
- `.github/workflows/integration.yml` - fünf Einträge im Job-Env, der Modellschritt mit Prüfsummenvergleich, die Warteschleife auf die Zweitspur mit eigener Frist und eigener Fehlermeldung, die zwei Umschreibungsschritte und zwei Dateinamen mehr im Fehlerbericht; kein Zeichen innerhalb von `search-parity`
- `docs/testing.md` - der Abschnitt "The gates of phase 6, and the boundary of each one" mit dreizehn Zeilen und zwei Spalten, dazu die Umschreibung im Integrationslauf in der bestehenden Liste
- `docs/embeddings.md` - Abschnitt 7 "Der Betriebsablauf: zwei Spuren nacheinander, nicht nebeneinander", mit der gemessenen Dauer, ihrer Kommandozeile, der zweiten Statuszahl und dem, was die Dauer nicht ist
- `README.md` - ein Abschnitt "What it finds" mit drei Punkten und dem Satz aus D-17b, mit dem gemessenen Anteil und ohne den Tokendeckel

## Die dreizehn Gates und ihre drei ausdrücklichen Grenzen

Die Tabelle steht in `docs/testing.md`. Die drei Grenzen, die der Plan wörtlich verlangt hat:

| Gate | Grenze, wie sie dort steht |
|---|---|
| Offline-Schritt | beweist, dass kein Netzwerk nötig ist, nicht, dass nie eines versucht wird; die Telemetriezeile von onnxruntime steht als Beispiel daneben |
| `test_semantic_boundary.py` | beweist, dass es im Quelltext keine zweite Route gibt, nicht, dass die vorhandene richtig filtert; dafür stehen `test_acl_prefilter.py`, der PHP-Recheck und `search-parity` |
| Präfixfall in `test_embed_model.py` | beweist einen Rangunterschied, nicht die absolute Qualität; die steht im Messbericht aus Plan 06-03 |

## Decisions Made

- **Tokenizer statt Zeilenfilter.** Der Plan verlangt, dass jede zählende Zusicherung Kommentarzeilen ausfiltert. In diesem Baum reicht das nicht: die fünf Nennungen in `store/vectors.py` stehen in Docstrings, und ein Docstring ist keine Kommentarzeile. `tokenize` beantwortet beides in einem, indem es nur NAME- und OP-Token behält, und der Testfall zur Hygiene fährt beide Formen durch, den `#`-Kommentar und den Docstring plus ein Zeichenkettenliteral.
- **`call_sites` unterscheidet Aufruf von Definition.** Ein `def prefilter_visible(` ist ein NAME gefolgt von einer Klammer und wäre gegen das Budget seiner eigenen Aufrufer gezählt worden. `def` und `class` vor dem Namen beenden die Übereinstimmung deshalb.
- **Der Rumpf der Abbild-Schritte ist eine Datei.** `docker.yml` kennt bereits einen Python-Heredoc (die Provenance-Prüfung, rund 25 Zeilen). Diese zwei Schritte brauchen zusammen rund zweihundert, sie bauen einen Index, einen Zustandsspeicher und einen Vektorbestand und fahren den echten Suchpfad. Als Heredoc wären sie von ruff, pyright und vulture nicht berührt und auf keiner Maschine ausführbar gewesen. Als Datei unter `backend/tests/` folgen sie dem Muster, das `test_vec_extension_probe.py` für genau diesen Zweck erfunden hat ("Two ways to run it, on purpose"), und die zweite Betriebsart ist lokal gefahren.
- **Der Name beginnt nicht mit `test_`.** pytest darf die Datei nicht einsammeln: die Offline-Betriebsart braucht 118 MB Gewichte, die auf keiner Entwicklungsmaschine liegen, und ein übersprungener Test wäre ein Gate, das aussieht, als liefe es. ruff, pyright und vulture sehen die Datei trotzdem, weil sie im `tests`-Pfad liegt.
- **Der Modell-weg-Fixture hat keinen Vektorbestand, und die Versionsmarken sind gesetzt.** Beides zusammen ist der Punkt. Ohne Marken wäre `degraded` schon deshalb wahr, weil eine nie geschriebene Marke als abweichend zählt, und der Schritt hätte die Marke aus dem falschen Grund gesehen. Mit gesetzten Marken und fehlendem Bestand bleibt genau die vierte Ursache aus 06-06 übrig, also die, um die es geht.
- **Die Anwesenheit des Modells wird im Modell-weg-Schritt ausdrücklich verneint.** Der Schritt fragt `resources.query_model().embed_query(...)` und verlangt `available is False`, bevor er irgendetwas anderes tut. Mit einem Modell im Verzeichnis wäre der ganze Schritt eine Prüfung von nichts, und "die Einhängung hat nicht gegriffen" sieht sonst genauso aus wie "der Container hält seine Volltexthälfte".
- **Der Integrationslauf holt das Modell aus dem veröffentlichten Abbild.** Der ExApp läuft dort als nativer Prozess aus `backend/`, hat also onnxruntime und das sqlite-vec-Rad, aber nicht die 118 MB. Ein Griff zu einem Modell-Hub bei jedem Push wäre das Gegenteil dessen, was dieses Produkt verspricht; `measure.yml` geht denselben Weg aus demselben Grund. Die Bytes sind dieselben Bytes, weil `MODEL_REVISION` auf einen Commit festgenagelt ist und `quantize_dynamic` reproduzierbar ist, dreimal gegen dieselbe sha256 belegt.
- **Die Umschreibung im Integrationslauf behauptet Anwesenheit und nicht Rang.** Getragen wird die Aussage vom Kontrolllauf davor: mit abgeschalteter Zweitspur antwortet dieselbe Anfrage leer, also kann alles, was der zweite Lauf findet, nur aus der Vektorhälfte kommen. Ein Rang-1-Anspruch über einen Korpus aus 22 Dokumenten wäre eine Aussage über die Modellqualität an einer Stelle, an der sie nicht gemessen, sondern nur behauptet werden könnte, und ein rotes `main` wäre der Preis. Die Rangfrage beantwortet der Offline-Schritt, dessen Korpus die Probe selbst schreibt, und der Messbericht aus 06-03. `docs/testing.md` sagt das an der Stelle.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktion] Die zwei Abbild-Schritte hatten keinen Rumpf, den der Plan hätte tragen können**

- **Found during:** Task 2, beim Entwurf des Offline-Schritts
- **Issue:** Die Dateiliste des Plans führt für Task 2 nur die zwei Arbeitsabläufe. Was die zwei Schritte tun sollen, ist "einen kleinen Bestand einbetten und eine semantische Suche gegen ihn fahren" beziehungsweise "eine gewöhnliche Volltextanfrage fahren und dreierlei erwarten". Das sind zusammen rund zweihundert Zeilen Python, die einen Index, einen Zustandsspeicher und einen Vektorbestand bauen. Als Heredoc in `docker.yml` wären sie von keinem Gate dieses Projekts berührt und auf keiner Maschine ausführbar gewesen, also genau die Sorte CI-Code, die erst im roten Lauf gelesen wird.
- **Fix:** `backend/tests/probe_image_search.py`, zwei Betriebsarten, nach dem Muster von `test_vec_extension_probe.py`. Nicht mit `test_` benannt, damit pytest sie nicht einsammelt.
- **Files modified:** backend/tests/probe_image_search.py (neu), .github/workflows/docker.yml
- **Verification:** `ruff check . --no-cache`, `ruff format --check .`, `pyright` und `vulture` decken die Datei ab und sind grün; `uv run python tests/probe_image_search.py model-gone` läuft lokal durch, inklusive des eingebauten Rotnachweises.
- **Committed in:** `e6e9e46`

**2. [Rule 3 - Blockierendes Problem] Der Integrationslauf hat kein Modell**

- **Found during:** Task 2, dritter Teil
- **Issue:** Der Plan verlangt die Umschreibung im Job `index-search-e2e` und eine Warteschleife auf die Zahl `embedded`. Beides setzt voraus, dass die zweite Spur dort überhaupt läuft. Der ExApp läuft in diesem Job als nativer Prozess aus `backend/`, also mit onnxruntime und dem sqlite-vec-Rad, aber ohne die int8-Modelldatei: die ist ein Erzeugnis der Modellstufe von `backend/Dockerfile` und liegt im Abbild und sonst nirgends. `FINDLING_EMBED_MODEL_DIR` zeigt auf `/usr/local/share/findling/model`, das auf einem Läufer nicht existiert, jede Einbettung hätte das ehrliche `embedding_unavailable` gegeben, und der Umschreibungsfall wäre eine Prüfung von nichts gewesen.
- **Fix:** Ein Schritt vor dem Setup holt das Modellverzeichnis mit `docker create` und `docker cp` aus `ghcr.io/street1983nk/findling_backend:dev` und legt es unter `${{ github.workspace }}/findling-model`; `FINDLING_EMBED_MODEL_DIR` steht auf Job-Ebene, damit es auch den Prozess erreicht, den die zusammengesetzte Aktion startet, wie `FINDLING_RECONCILE_ENABLED` im Job darunter. Die Grenze dieses Weges steht als Kommentar an Ort und Stelle.
- **Files modified:** .github/workflows/integration.yml
- **Verification:** Der Schritt lädt als YAML, sein Shell-Rumpf ist syntaktisch geprüft, und `test_workflow_pins.py` ist grün. Ein echter Lauf steht aus, siehe "Offene Verifikation".
- **Committed in:** `e6e9e46`

**3. [Rule 2 - Fehlende kritische Funktion] Die geholte Modelldatei erreichte onnxruntime ungeprüft**

- **Found during:** Nach Task 3, beim Durchgehen der neuen Angriffsfläche für die Bedrohungsnotiz
- **Issue:** Der Schritt aus Abweichung 2 zog das Modellverzeichnis über den beweglichen Zeiger `:dev` und druckte die sha256, ohne sie zu vergleichen. onnxruntime führt den Graphen aus dieser Datei aus. Das ist wörtlich der Fall, gegen den `backend/Dockerfile` für jede Datei schreibt, die es holt (T-06-01): ein geholtes Artefakt, das niemand prüft, ist ein geholtes Artefakt, das jeder ersetzen kann.
- **Fix:** Vergleich gegen `8da4c9ba...`, die in Plan 06-03 dreimal gemessene Prüfsumme der ausgelieferten int8-Datei, mit einer Fehlermeldung, die sagt, welche zwei Stellen ein bewusster Modellwechsel mitbewegen muss. Damit wird die Veraltungsfrage des Zugriffs von einem Vorbehalt zu einem Gate.
- **Files modified:** .github/workflows/integration.yml
- **Verification:** YAML lädt, Shell-Syntax geprüft, `test_workflow_pins.py` grün; der Vergleichswert stammt aus `docs/measurements/2026-09-05-modellqualitaet/README.md`.
- **Committed in:** `f8acbb4`

### Abweichungen, die keine Autoreparatur sind, sondern eine Auslegung des Plans

**4. Die zwei Vorfilterstellen liegen in `_permit` und `snippets_for`, nicht in `candidates`**

Der Verhaltensblock von Task 1 sagt "in candidates und in snippets_for". Plan 06-06
hat den Aufruf der Kandidatenrunde bewusst in einen Helfer gezogen, damit zwei
Abschnitte der Schleife nicht zwei Zeilen sind, und das ist genau die Eigenschaft,
die dieses Gate festhalten soll. Die Zusicherung nennt deshalb `_permit` und
`snippets_for` und sagt im Kommentar, warum der umschliessende Name ein anderer ist
als der der Funktion, um die es geht.

**5. Der Umschreibungsfall bringt kein neues Korpusdokument mit**

Der Plan verlangt "mindestens ein Dokument, dessen Umschreibung in der Anfrage
steht". `10-kuendigung.docx` ist bereits eines. Ein zusätzliches Korpusdokument
hätte `EXPECTED_INDEXED`, `EXPECTED_SKIPPED`, `testdata/CORPUS.md` und den
Verdiktzähler des Jobs `readonly-gate` mitbewegt, und keine dieser Stellen steht
in der Dateiliste dieses Plans.

**6. Der Schrittname trägt das Wort `degraded`**

Die Verifikationszeile des Plans liest `str(d['jobs'])` von `docker.yml` und
verlangt darin `network` und `degraded`. Ein YAML-Kommentar kommt in dieser
Zeichenkette nicht vor, weil der Parser ihn verwirft. Der Schritt heisst deshalb
"Criterion 3 in the image, full text hits and the degraded mark" und druckt seine
Erwartung zusätzlich als erste Zeile in den Lauf.

**7. `docs/embeddings.md` bekommt keinen Nachtrag zu Zahlen, die schon ihre Kommandozeile haben**

Das Abnahmekriterium verlangt für jede gemessene Zahl Kommandozeile und Messdatum.
Die Seite hatte beides bereits für die Platzkennzahl, für die Scan-Latenz, für die
Modellqualität und für die Modellgrösse; drei Verweise auf Messberichte sind
geprüft und zeigen auf vorhandene Dateien. Neu ist deshalb nur, was fehlte: die
Dauer der zweiten Spur mit ihrer Kommandozeile und ihrem Datum, in Abschnitt 7.

---

**Total deviations:** 3 autorepariert (2 fehlende kritische Funktionen, 1 blockierendes Problem), 4 Auslegungen
**Impact on plan:** Keine Ausweitung des Umfangs. Die drei Autoreparaturen betreffen genau die Eigenschaften, die dieser Plan zusichern soll: dass die zwei Abbild-Schritte einen prüfbaren Rumpf haben, dass die Umschreibung im Integrationslauf etwas misst, und dass das Artefakt, an dem diese Messung hängt, dasselbe ist, das dieses Projekt gemessen hat.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: supply-chain | .github/workflows/integration.yml | Der Job zieht ab jetzt `ghcr.io/street1983nk/findling_backend:dev` und kopiert das Modellverzeichnis heraus, das onnxruntime anschliessend ausführt. Das Bedrohungsregister dieses Plans führt unter T-06-SC nur pip- und uv-Installationen und kennt kein Abbild, das in einen CI-Lauf geholt wird. Der Zugriff ist mit `f8acbb4` gegen die aufgeschriebene sha256 abgesichert (Regel 2), also ist die Lücke geschlossen und nicht offen; die Notiz steht hier, weil die Angriffsfläche neu ist und im Register des naechsten Plans stehen sollte. Was weiterhin offen bleibt: der Zeiger ist ein Tag und kein Digest, also entscheidet die Pruefsumme und nicht die Adresse, und ein zurueckgezogenes Paket macht den Job rot statt still falsch. |

## Issues Encountered

- **`store/vectors.py` nennt den Vorfilter fünfmal, ruft ihn keinmal, und alle fünf Stellen sind Docstrings.** Der erste Entwurf des Hygienefilters ging über Zeilen und hätte die Zusicherung "kommt dort überhaupt nicht vor" an genau dem Text scheitern lassen, der sie erklärt. Das ist die Falle, die der Plan als Auftrag beschreibt, und sie steht in diesem Baum schon da.
- **`ruff format` wollte drei meiner Ausdrücke anders umbrechen.** Alle drei sind umgebaut statt mit einer `noqa`-Direktive versehen worden: eine Listenkomprehension in zwei Anweisungen, eine zweite ebenso, und eine implizite Zeichenkettenverkettung in einer Liste in Klammern (ISC004). Die Prüfung `ruff format --check ..` über das ganze Repositorium meldet weiterhin genau die neun vorbestehenden Markdown-Dateien aus DI-06-01 und keine zehnte.
- **Die AWS-Box ist nicht angefasst worden.** Dieser Plan misst nichts. Die einzigen Zahlen in den neuen Texten stammen aus den Berichten von Welle 0 und aus Plan 06-02, 06-03 und 06-05.

## Offene Verifikation

**Zwei Läufe, die von dieser Maschine aus nicht zu fahren sind, und was statt dessen belegt ist.**

`docker.yml` braucht einen Abbildbau samt Registrierung, `integration.yml` eine
ganze Nextcloud-Installation; beides gibt es hier nicht. Was geprüft ist:

- Beide Dateien laden als YAML, und die Verifikationszeile des Plans läuft durch.
- Alle 94 `run`-Blöcke beider Dateien sind mit `bash -n` syntaktisch geprüft, die neuen eingeschlossen.
- `test_workflow_pins.py` ist grün, es ist keine Action dazugekommen.
- Die Betriebsart `model-gone` der Probe ist lokal gefahren, mit dem erwarteten Ergebnis in allen vier Zeilen.
- Der Kontrolllauf der Betriebsart `offline` ist ebenfalls lokal gefahren: die Umschreibung findet ohne Vektorbestand nichts. Erst danach bricht der lokale Lauf am fehlenden Modell ab, was der erwartete Zustand einer Maschine ohne Abbild ist.
- Die Zählabfrage der Warteschleife (`COUNT(DISTINCT file_id)` über `chunks`) ist gegen eine echte `vectors.db` mit zwei Dokumenten gefahren und antwortet 2, ohne dass die vec0-Erweiterung geladen werden muss.

**Was damit ausdrücklich noch nicht belegt ist**, und es ist die eine Zusicherung
dieses Plans, die ihr erster CI-Lauf beantwortet: ob das Modell im Offline-Schritt
das Zieldokument auf Rang 1 stellt, und ob die zweite Spur im Integrationslauf die
erwarteten 22 Dokumente innerhalb von 300 Sekunden mit Vektoren versieht. Beide
Zahlen sind hergeleitet und nicht geraten (der Korpus der Probe hat fünf
themenfremde Passagen, die Frist ist das Fünfzigfache der gemessenen Modellzeit),
und ein Überschreiten ist nach T-06-51 ein Befund und kein Anlass, die Zahl zu
heben, bis es passt.

## User Setup Required

None. Für den Betrieb ändert sich nichts: keine neue Einstellung, keine neue
Abhängigkeit, kein Eingriff an der PHP-Hälfte. Was ein Betreiber davon hat, steht
in `README.md` und in `docs/embeddings.md` Abschnitt 7.

## Next Phase Readiness

- **Plan 06-11 findet den Betriebsablauf beschrieben vor.** `docs/embeddings.md` Abschnitt 7 nennt beide Spuren, die gemessene Dauer der zweiten und die zweite Statuszahl; was der Lasttest ergänzt, ist die Zahl der Zielbox, die dort ausdrücklich als fehlend markiert ist.
- **Plan 06-12 erbt eine geprüfte Aussage für den Store-Text.** Dass der Container ohne Netzwerkzugang einbettet, ist ab dem ersten grünen `docker.yml`-Lauf ein Schritt und keine Zusage mehr, und `docs/testing.md` sagt daneben, was der Schritt nicht beweist. Der Store-Text selbst ist in diesem Plan unangetastet geblieben, wie der Plan es verlangt.
- **DI-06-02 und DI-06-03 bleiben offen**, unverändert seit 06-09, und sie sind weiterhin ein Blocker für den Tag `v1.0.0` und für keinen der beiden nächsten Pläne.
- **Ein neuer Punkt für das Bedrohungsregister von 06-11**, siehe "Threat Flags": der Integrationslauf holt ab jetzt ein Abbild aus einer Registry.
- **Kein Blocker.**

## Self-Check: PASSED

Beide angelegten Dateien liegen auf der Platte
(`backend/tests/test_semantic_boundary.py`, `backend/tests/probe_image_search.py`),
alle vier Commits (`d6b4dcc`, `e6e9e46`, `650c92f`, `f8acbb4`) stehen in
`git log`. Zusätzlich geprüft: `prefilter_visible` steht unverändert 2 mal in
`index/search.py`, alle Hunks in `integration.yml` liegen innerhalb von
`index-search-e2e` und keiner innerhalb von `search-parity`, die drei
Messberichtsverweise in `docs/embeddings.md` und der Verweis von `README.md` auf
`docs/embeddings.md` zeigen auf vorhandene Dateien, und weder Geviert- noch
Halbgeviertstrich stehen in einer der sieben geänderten Dateien oder in dieser
Zusammenfassung. `pytest` 1.350 bestanden und 13 übersprungen, `ruff check .
--no-cache`, `ruff format --check .`, `pyright` mit 0 Fehlern und `vulture` ohne
Befund, jeweils im CI-Umfang `backend`. Die neun vorbestehenden
Markdown-Formatbefunde oberhalb von `backend` (DI-06-01) sind unverändert.

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-05*
