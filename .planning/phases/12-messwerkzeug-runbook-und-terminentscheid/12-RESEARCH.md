# Phase 12: Messwerkzeug, Runbook und Terminentscheid - Research

**Researched:** 2026-09-14
**Domain:** Messwerkzeug-Bau (Shell/Python-Sonden gegen einen laufenden Container), AWS-EBS-Wiederaufbau aus Snapshot, Betriebs-Runbook, fristgebundener Versionsentscheid
**Confidence:** HIGH fuer alles am eigenen Baum und an der installierten Bibliothek Gemessene, HIGH fuer den NC-35-Releasestand (gh api), MEDIUM fuer die Zeitposten des Deckel-Rechenblatts (aus einem einzigen v1.1-Lauf abgeleitet)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**stable35-Entscheid (HART-03, Frist 16.09.2026)**
- **D-01:** Ist NC 35 am 16.09. final, wird das Versionsfenster GLEICH in v1.2.0 auf max NC 35 gehoben (kein separates 1.1.x nur fuers Fenster).
- **D-02:** Beweisgrundlage der Hebung: NC-35-final-Check PLUS die bestehende deploy-harp-Fremdinstallations-/Upgrade-Strecke gruen gegen stable35. Der Release-Status allein reicht nicht.
- **D-03:** Ist NC 35 am 16.09. noch nicht final: Entscheid dokumentieren (Fenster bleibt), neuen RE-CHECK-Termin setzen (spaetestens vor der Phase-16-Einreichung erneut pruefen); Phase 12 gilt damit als erfuellt.

**Budget-Grundlage der Anfahrt (fuer Phase 15 vorbereitet)**
- **D-04:** Der Wirkungsbeleg-Volllauf laeuft gegen den VOLLKORPUS (52.111 Dokumente), direkt vergleichbar mit v1.0-Baseline und v1.1-Lauf. KEIN Teilkorpus-Werkzeug in Phase 12. Konsequenz: der Deckel-Vorschlag fuer Phase 15 muss realistisch sein (>= 31 h / ~3,59 USD; letzter Volllauf allein 26 h 37 min plus ~3,5 h Ruestzeit).
- **D-05:** Ein Deckel-Rechenblatt (Zeitposten, Kostenposten, Empfehlung) wird FESTER Runbook-Bestandteil: vor jeder Anfahrt wird der Deckel aus den zuletzt gemessenen Posten neu gerechnet; die Owner-Freigabe am Phase-15-Checkpoint bekommt damit eine belegte Zahlbasis.
- **D-06:** Zielinstanz bleibt m7g.large (ARM, Vergleichbarkeit mit Baseline und v1.1; Hetzner-ARM/CAX weiterhin nicht beschaffbar).

**Cron-Intervall-Regel (MESS-06)**
- **D-07:** Das Cron-Intervall wird FESTGENAGELT UND PROTOKOLLIERT: der Anfahrt-Ablauf setzt den Systemcron der Messinstanz explizit auf 5 Minuten und protokolliert den Ist-Zustand (12 statt 5 Minuten kosteten in v1.1 ~5,85 h Leerlauf und verfaelschten den Laufzeitvergleich).
- **D-08:** Durchsetzung FAIL-CLOSED IM SKRIPT: ein Vorpruefschritt im Anfahrt-/Messskript bricht ab, wenn das Intervall nicht stimmt oder nicht protokolliert ist. Eine Runbook-Checkliste allein reicht nicht (menschliche Schritte werden vergessen, das war die v1.1-Falle).

**Runbook-Zuschnitt (MESS-04)**
- **D-09:** Umfang: Hauptpfad ist der WIEDERAUFBAU AUS DEM SNAPSHOT (snap-03f1d1d9ad9262704), der in Phase 15 erstvollzogen wird. Der Neuaufbau-von-null steht nur als Verweis auf die bestehenden Messberichte, wird nicht ausgearbeitet (ungetesteter Text waere Ballast).
- **D-10:** Form: nummerierte Copy-paste-Kommandobloecke mit erwarteten Ausgaben/Pruefpunkten je Schritt. Der Erstvollzug in Phase 15 validiert das Runbook woertlich.
- **D-11:** Abbau und Kostenfuehrung sind PFLICHTTEILE des Runbooks: Abbau-Checkliste (Snapshot pruefen, destroy, Tag-Sweep ueber Regionen), box.env-Kostenpflege und das Deckel-Rechenblatt aus D-05. Der Abbau war schon zweimal die Falle (cmd_destroy-Tag-Sweep; destroy loescht box.env).

### Claude's Discretion
- Technischer Zuschnitt der neuen Fremdbestands-Messgroesse ueber die Diagnose-Route (`ranked_sides`, arbeitet ohne Vorfilter): Skript-Design, ob 98b angepasst oder ersetzt wird, Schwellen-Semantik (Schwelle 64 muss pruefbar werden, alte Deckelung war 26).
- Design des neuen `aws_box.sh`-Unterbefehls fuer Volume-aus-Snapshot (Namensgebung, Parameter, Sicherheitspruefungen).
- Dokumentationsort und Form des stable35-Entscheids (Vermerk in deploy-harp.yml plus Entscheidungsnotiz; Details frei).
- Ob der Cron-Fail-closed-Check als eigenes Skript oder als Schritt in einem bestehenden Anfahrtskript lebt.

### Deferred Ideas (OUT OF SCOPE)
- Teilkorpus-Werkzeug (bewusst verkleinerter Wirkungsbeleg): abgelehnt fuer v1.2 (D-04), bleibt Option fuer spaetere Messkampagnen, falls Kosten je wichtiger werden als Vergleichbarkeit.
- Neuaufbau-von-null-Runbook: nur Verweis (D-09); voll ausarbeiten erst, wenn der Snapshot je geloescht wird (Wiedervorlage nach v1.2).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MESS-04 | Werkzeug und Runbook stehen VOR der bezahlten Anfahrt: Fremdbestands-Vorpruefung misst ueber die Diagnose-Route (`ranked_sides`) statt der gedeckelten OCS-Route; `aws_box.sh` kann Volume-aus-Snapshot (`snap-03f1d1d9ad9262704`); `docs/runbook-messbox.md` als Erstfassung | Abschnitte "Befund 1" (Messgroesse, drei Zaehlwege empirisch geprueft), "Befund 2" (aws_box.sh-Luecke und Tag-Falle), "Befund 3" (Runbook-Quellmaterial und Umfangsschock: die Box existiert nicht mehr) |
| MESS-06 | Cron-Intervall wird vor jedem Messlauf protokolliert; Vergleichbarkeitsbedingungen (Korpus, Werkzeugstand, Instanztyp) stehen im Runbook | Abschnitt "Befund 4" (das Intervall war NOMINAL 5 min und EFFEKTIV 12 min, ein Konfigurationscheck faengt den Befund nicht) |
| HART-03 | stable35-Fenster-Entscheid (RE-CHECK 16.09.2026, Entscheid v2-a) vollzogen und dokumentiert | Abschnitt "Befund 5" (Fenster ist bereits 33-35, es geht um den CI-Flag; NC-35-Stand am 14.09. verifiziert) |
</phase_requirements>

---

## Summary

Diese Phase baut kein Produkt, sondern Werkzeug, Text und einen Entscheid. Die
Recherche hat fuer alle drei Anteile Befunde gefunden, die die vorliegende
Aufgabenbeschreibung an entscheidenden Stellen korrigieren, und zwar nach oben
im Aufwand und nach unten im Risiko. Drei davon sind so gross, dass eine Planung
ohne sie ins Leere baut.

**Erstens: die neue Messgroesse ist einfacher und exakter zu haben, als MESS-04
vermutet.** Die Diagnose-Route `/diagnose` liefert heute keine Zahl, sondern eine
Herkunftsmarke fuer genau eine Datei, und sie wird von der PHP-Seite ohne den
`query`-Parameter gerufen, mit dem diese Marke ueberhaupt erst entsteht. Eine
Trefferzahl ueber den Draht waere ausserdem genau das Zaehl-Orakel, das T-02-93
verbietet. Der Ausweg ist das im Repositorium bereits etablierte Muster einer
In-Container-Sonde (`docker cp` plus `/app/.venv/bin/python`, gefahren in
`94-grundlast.sh`): eine Sonde im Prozess kann `ranked_sides` direkt rufen und
zusaetzlich `Searcher.search(query, 1, count=True).count` lesen. Dieses
`count`-Feld existiert in der installierten tantivy 0.26.0 zur Laufzeit,
obwohl der Typstub es nicht deklariert; es ist am 14.09.2026 gegen die
installierte Fassung gemessen worden und liefert die ungedeckelte Zahl der
Dokumente im Index, die den Begriff tragen. Das ist woertlich die Messgroesse,
die der Bericht vom 10.09. selbst verlangt hat.

**Zweitens: die Messbox existiert nicht mehr.** Plan 11-12 hat am 11.09.2026
Instanz, Datentraeger, Security Group und die Zustandsdatei `box.env`
vollstaendig abgebaut; auf der Entwicklungsmaschine liegt unter
`C:/Users/Student/.findling-loadtest/` nur noch das Verzeichnis
`systemplatte-2026-09/` mit zwei Archivdateien, keine `box.env`. Damit sind
`aws_box.sh start|stop|status|volume|snapshot` allesamt nicht lauffaehig (sie
rufen `require_state`), `cmd_create` verweigert die Erzeugung ausdruecklich, und
der A-Record `loadtest.infranode.dev` zeigt ins Leere. Das Runbook ist also nicht
"Box wecken und messen", sondern "Maschine neu bauen, Systemplatte neu
herrichten, Datentraeger aus dem Snapshot heben, Zustandsdatei neu schreiben".
Der Snapshot traegt Docker-Wurzel, lokale Registry, Korpus und Index; er traegt
NICHT `/home/ubuntu/work` samt Passwortdateien und nicht die Systemplatte.

**Drittens: der stable35-Entscheid ist kleiner als gedacht.** Beide `info.xml`
stehen bereits auf `min-version="33" max-version="35"`. Es ist nichts zu heben.
Der offene Punkt ist der Ast `server-version: stable35` in `deploy-harp.yml` mit
`tolerate-failure: true` plus der 25-zeilige RE-CHECK-Absatz darueber. Und
am 14.09.2026 ist die neueste NC-35-Marke `v35.0.0rc4` (Vorabversion,
10.09.2026), die neueste echte Freigabe `v34.0.4`; der offizielle Zeitplan nennt
den 16.09.2026 mit dem ausdruecklichen Zusatz "date not final".

**Primary recommendation:** Die Phase in vier unabhaengige Straenge schneiden
(Messgroesse, `aws_box.sh`, Runbook, stable35-Entscheid), den stable35-Strang als
ersten und terminlich isolierten Plan fuehren (Frist 16.09., zwei Tage), die neue
Messgroesse als In-Container-Python-Sonde in einem NEUEN Laufverzeichnis unter
`docs/measurements/` bauen und die drei betroffenen Gate-Tests in derselben
Welle mitziehen, weil sie sonst rot werden.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fremdbestands-Messgroesse (Zaehlung im Index) | In-Container-Python-Sonde (ExApp-Prozessraum) | Shell-Skript auf der Box als Fahrer | Der Bestand ist eine Eigenschaft des Tantivy-Index. Jede Zaehlung, die den Containerrand verlaesst, ist das Zaehl-Orakel aus T-02-93; im Prozess gibt es diese Grenze nicht |
| Urteilslogik der zehn Sprachfaelle (dreiwertig) | Shell-Skript im Laufverzeichnis | In-Container-Sonde liefert nur Zahlen | Bestehendes Muster aus `98b-sprachfaelle.sh`; das Skript besitzt die Exit-Codes und die Bilanzzeile, die Sonde besitzt keine Urteile |
| Volume aus Snapshot | `scripts/ops/aws_box.sh` (Entwicklungsmaschine, AWS-API) | keine | `aws_box.sh` ist der einzige Ort, an dem dieses Projekt AWS-Ressourcen anlegt, taggt und in `box.env` verbucht |
| Cron-Durchsetzung fail-closed | Shell-Vorpruefschritt auf der Box | Runbook als Erklaerung | Der Ist-Zustand ist nur auf der Box lesbar; ein Text kann nichts erzwingen (D-08) |
| Deckel-Rechenblatt | `docs/runbook-messbox.md` (Text mit Rechenweg) | `aws_box.sh prices` liefert die Saetze | Die Rechnung ist eine Owner-Entscheidungsvorlage, kein Programm |
| stable35-Entscheid | `.github/workflows/deploy-harp.yml` (CI-Konfiguration) | Entscheidungsnotiz im Repositorium | Der Beweis ist ein CI-Lauf; die Begruendung ist Prosa und gehoert daneben |

---

## Befund 1: Die neue Fremdbestands-Messgroesse

### 1.1 Was heute schiefgeht, mit Zahlen

`docs/measurements/2026-09-werkzeugfixe/README.md` Abschnitt 4 haelt die Messung
vom 10.09.2026 fest [VERIFIED: eigener Baum]:

| Fall | Begriff | Fremdbestand (Seite, Tiefe 64) | Urteil |
|---|---|---|---|
| 1 | Genehmigung | 6, 26 | ROT |
| 2 | Frist | 6, 26 | ROT |
| 4 | Vertrag | 6, 26 | ROT |
| 6 | bescheid | 6, 26 | ROT |
| 7 | type:pdf bescheid | 6, 26 | GRUEN |

Die Gegenprobe `72-fremdbestand.py` hat dieselbe OCS-Route mit den Tiefen
5, 64, 200 und 2000 und mit fuenf Begriffen gefragt, die in keinem der zehn
Faelle vorkommen. Die Antwort lautet fuer jeden Begriff und jede Tiefe 26. Die
Zahl ist damit ein Deckel der Antwort und nicht der Bestand dahinter; sie kann
die Schwelle 64 nie erreichen, und das dreiwertige Urteil faellt auf zweiwertig
zurueck. Das ist DI-10-02/DI-11-01 in einem Satz.

Der Bericht selbst nennt die verlangte Nachfolge-Messgroesse woertlich:
"die Zahl der Dokumente im Index, die den Begriff tragen, statt der Zahl der
Treffer, die die Route herausgibt" [VERIFIED: `docs/measurements/2026-09-werkzeugfixe/README.md`, Abschnitt "Was als Naechstes zu tun ist"].

### 1.2 Warum die Diagnose-Route so, wie sie heute liegt, die Zahl nicht liefert

Drei Befunde, alle am Quellcode belegt [VERIFIED: eigener Baum]:

1. **`/diagnose` gibt keine Zahl aus, sondern eine Marke fuer eine Datei.**
   `backend/src/findling/api/diagnose.py:275` nimmt `fileId` und optional
   `query`; die Antwort traegt `origin` als eines von vier Woertern
   (`lexical`/`semantic`/`both` aus `index/fusion.py::origins` plus `none`).
   Trefferzahlen kommen dort nicht vor.
2. **Die PHP-Seite ruft die Route ohne `query`.**
   `php/lib/Service/AdminViewService.php:715` ruft
   `adminGet('/diagnose', $userId, ['fileId' => $fileId])`. Ohne `query` gibt
   `_report` den Ursprung als `None` weiter, und `response_model_exclude_none`
   laesst das Feld ganz weg. Der Ursprungs-Mechanismus ist ueber PHP und ueber
   `occ findling:diagnose` heute also unerreichbar.
3. **Eine Zahl ueber den Draht ist ausdruecklich verboten.**
   `index/search.py::_sides` gibt `len(hits)` als dritten Wert zurueck und der
   Docstring dort sagt: "The third value ... never leaves `candidates`: ... a raw
   cursor is the counting oracle of T-02-93 the moment it crosses a process
   boundary." `candidates()` wiederholt die Regel an der Stelle, an der `needed`
   gebildet wird. Eine neue Zahl auf `/diagnose` waere ein Bruch dieser Regel,
   mitten im Store-Release-Fenster.

**Konsequenz:** MESS-04 ist erfuellbar, ohne eine einzige Zeile Produktionscode
zu aendern, und das ist der klar sicherere Weg.

### 1.3 Das Fenster von `ranked_sides` und warum es reicht

`index/search.py:296-320` [VERIFIED: eigener Baum]:

```python
def ranked_sides(index, query, *, semantic=None) -> RankedSides:
    resolved = settings()
    searcher = index.searcher()
    window = min(resolved.search_rrf_window, SEARCH_SCAN_MAX)
    ...
```

`SEARCH_RRF_WINDOW = 100` (`config.py:547`), `SEARCH_SCAN_MAX = 10_000`
(`config.py:182`). Das Fenster ist also 100 je Liste. Die Schwelle 64 stammt aus
`php/lib/Search/Provider.php:90` (`MAX_RECHECKS_ABSOLUTE = 64`).

**100 > 64.** Eine Zaehlung ueber `ranked_sides` kann die Schwelle also
ueberschreiten, im Gegensatz zur heutigen 26. Erfolgskriterium 1 der Phase ist
damit woertlich erfuellbar. Die Zahl saettigt allerdings bei 100.

### 1.4 Der bessere dritte Zaehlweg, empirisch geprueft

`tantivy.Searcher.search(query, limit, count=True, ...)` ist im Typstub der
installierten Fassung deklariert, `SearchResult` deklariert dort aber nur
`hits`. Zur Laufzeit existiert `count` trotzdem. Gemessen am 14.09.2026 gegen
`backend/.venv` (tantivy 0.26.0, cp313, win_amd64) [VERIFIED: eigene Probe]:

```
300 Dokumente indexiert, alle tragen den Begriff
hits 10
has count attr: True 300
dir: ['count', 'hits']
```

`SearchResult.count` liefert also die ungedeckelte Zahl der Treffer im Index,
unabhaengig vom `limit`. Das ist exakt "die Zahl der Dokumente im Index, die den
Begriff tragen".

**Folge fuer das Skript-Design:** Die Sonde meldet drei Zahlen je Begriff, und
jede beantwortet eine andere Frage:

| Zahl | Herkunft | Was sie beantwortet | Deckel |
|---|---|---|---|
| `bestand` | `searcher.search(query, 1, count=True).count` | Wie viele Dokumente im ganzen Index tragen den Begriff | keiner unterhalb der Indexgroesse |
| `fenster_lexikalisch` / `fenster_semantisch` | `len(ranked_sides(...).lexical)` bzw. `.semantic` | Wie voll ist das Fusionsfenster, das der Recheck abschreitet | 100 |
| `rang_eigene_datei` | Position der eigenen `file_id` in der fusionierten Liste, oder "nicht im Fenster" | Kommt die eigene Datei ueberhaupt in Reichweite der 64 Rechecks | 100 |

Die Schwellen-Semantik wird damit belastbar: **nicht messbar**, wenn
`rang_eigene_datei` fehlt oder groesser als `MAX_RECHECKS_ABSOLUTE` ist, mit
`bestand` als erklaerender Zahl daneben. Das ist strenger und ehrlicher als ein
reiner Zahlenvergleich gegen 64, und es erklaert die alten roten Faelle direkt:
die Diagnose vom 10.09. hat fuer `Bescheid` Rang 1.925 von 2.000 gemessen.

**Warnung zum Typstub:** `.count` ist im `.pyi` nicht deklariert. Liegt die
Sonde unter `docs/measurements/**/skripte/`, ist das folgenlos (pyright laeuft
dort nicht, siehe Befund 6). Wandert sie nach `scripts/` oder `backend/`, braucht
sie ein gezieltes `# type: ignore` oder einen `getattr`-Zugriff.

### 1.5 Das Transportmuster ist bereits etabliert

`docs/measurements/2026-09-vergleichsmessung-m7g/skripte/94-grundlast.sh:102-113`
[VERIFIED: eigener Baum]:

```sh
sudo docker cp "$GEWICHTE" "$CONTAINER:/tmp/49b-gewichte.py"
sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/49b-gewichte.py
...
sudo docker cp "$WOHER" "$CONTAINER:/tmp/52-woher.py"
sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/52-woher.py
```

Containername: `nc_app_findling_backend` (Vorgabe in `94-grundlast.sh:49`).
Interpreter im Abbild: `/app/.venv/bin/python`. Die Sonde braucht keinen
HTTP-Zugang, kein Passwort und keine Route.

**Kein Vorfilter, kein Recheck:** `ranked_sides` fragt ausdruecklich keinen
Berechtigungs-Vorfilter (Docstring, D-14). Das ist hier korrekt: gemessen wird
der Bestand und nicht die Sicht eines Kontos.

### 1.6 Empfehlung zum Skript-Zuschnitt

- **Neue Datei in einem NEUEN Laufverzeichnis**, nicht Aenderung von `98b`.
  Die Hausregel ist explizit und durch einen Waechter mit sha256 abgesichert:
  "eine gefahrene Messfassung ist Teil des Belegs, und ein Fix entsteht als neue
  Datei in einem neuen Laufverzeichnis" (`DRIVEN_FASSUNG_RULE` in
  `backend/tests/test_measurement_scripts.py`). `98b` ist am 10.09. gefahren
  worden und traegt Rohdaten.
- Vorschlag: `docs/measurements/2026-09-v12-messung/skripte/` mit
  `00-ablauf.md`, `98c-sprachfaelle.sh` und `73-bestand-sonde.py`.
- Abschnitt 0 von `98c` faehrt die Sonde und schreibt `bestand` je Begriff.
  Die Rang-Pruefung kann erst NACH Upload und Indexierung laufen, weil die
  eigene Datei vorher nicht existiert; sie gehoert deshalb als neuer Abschnitt
  3b zwischen Indexierung und Faelle, nicht in Abschnitt 0. Das ist die einzige
  strukturelle Aenderung gegenueber `98b`.
- Exit-Codes von `98b` uebernehmen (15/16/17/18/19/22/23) und fuer den neuen
  Abbruchgrund fortsetzen, statt sie zu verschieben.
- `CI_LAUF` als Pflichteingabe beibehalten (Exit 22 vor dem ersten Fall).

---

## Befund 2: `aws_box.sh` und der Weg vom Snapshot zum Volume

### 2.1 Ist-Zustand

Acht Unterbefehle, Reihenfolge und Zeilen [VERIFIED: `scripts/ops/aws_box.sh`]:

| Unterbefehl | Zeile | Was er tut | `require_state`? |
|---|---|---|---|
| `prices` | 234 | Instanztyp-Fakten und gepinnte Saetze | nein |
| `create` | 266 | erzeugt NICHTS, druckt das Rezept und endet mit `exit 1` | nein |
| `volume` | 320 | erzeugt ein LEERES 60-GB-gp3-Volume, taggt, haengt an | ja |
| `status` | 386 | Zustand, Laufzeit, Kosten | weich |
| `stop` | 478 | anhalten, Laufzeit und Kosten fortschreiben | ja |
| `start` | 547 | wecken, neue Adresse, SSH-Regel nachziehen | ja |
| `snapshot` | 652 | Snapshot des Datentraegers, mit unabhaengiger Nachlese | ja |
| `destroy` | 818 | Instanz, Volume, Security Group, Tag-Sweep, `box.env` weg | ja |

Feste Werte: `REGION='eu-central-1'`, `ZONE='eu-central-1c'`,
`INSTANCE_TYPE='m7g.large'`, `VOLUME_SIZE_GB=60`, `VOLUME_TYPE='gp3'`,
`TAG_KEY='purpose'`, `TAG_VALUE='findling-phase5'`,
`KEEP_TAG_VALUE='findling-corpus-keep'`,
`STATE_FILE="$HOME/.findling-loadtest/box.env"`.

**Die Luecke:** `cmd_volume` ruft `ec2 create-volume` ohne `--snapshot-id`. Es
gibt keinen Weg vom Snapshot zum Volume.

### 2.2 Die drei Fallen, die der neue Unterbefehl abfangen muss

Alle drei stehen bereits als Befund im Repositorium
[VERIFIED: `docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`, Abschnitt 10]:

> aus dem snapshot ein volume: aws ec2 create-volume --snapshot-id
> snap-03f1d1d9ad9262704 --availability-zone <zone> --volume-type gp3. das volume
> traegt danach wieder den tag des snapshots und muss auf purpose=findling-phase5
> umgetaggt werden, wenn es ein spaeteres destroy mitnehmen soll.

1. **Tag-Vererbung.** Ein aus dem Snapshot erzeugtes Volume erbt
   `purpose=findling-corpus-keep`. Der Tag-Sweep von `cmd_destroy` sucht nach
   `purpose=findling-phase5`; ein geerbter Keep-Tag macht das Volume zu einer
   unsichtbaren Dauerrechnung. Der neue Unterbefehl MUSS umtaggen und das
   Ergebnis zurueckliesen.
2. **Zone.** `create-volume --snapshot-id` braucht eine Verfuegbarkeitszone. Das
   Volume muss in `eu-central-1c` liegen, sonst ist es nie an die Box zu haengen
   (`cmd_volume` filtert aus genau diesem Grund schon heute nach Zone).
3. **Groesse.** Der Snapshot stammt von einem 60-GB-Volume mit 51,6 GiB
   geschriebener Bloecke. Ein `--size` unterhalb von 60 wird von der API
   abgelehnt; ohne `--size` uebernimmt AWS die Snapshotgroesse. Beide Wege sind
   vertretbar, der explizite ist der pruefbare.

Zusaetzlich aus dem Muster von `cmd_volume` zu uebernehmen: ein bereits
vorhandenes, nicht angehaengtes Volume mit dem richtigen Tag in der richtigen
Zone wird AUFGENOMMEN statt ein zweites erzeugt (der erste Lauf von `cmd_volume`
hat genau diesen Fehler gemacht und eine Rechnung hinterlassen).

### 2.3 Der Gate-Test, der mitgezogen werden MUSS

`backend/tests/test_ops_scripts.py:264` heisst
`test_the_aws_tool_names_its_eight_subcommands_in_the_usage` und behauptet in
Zeile 279 woertlich [VERIFIED: eigener Baum]:

```python
assert "usage: aws_box.sh <prices|create|volume|status|stop|start|snapshot|destroy>" in text
```

Ein neunter Unterbefehl macht diesen Test rot, wenn er nicht in derselben
Aenderung umbenannt und angepasst wird. Dazu kommen die allgemeinen Gates
(`test_the_script_carries_neither_a_dash_nor_a_carriage_return`,
`test_the_aws_tool_waits_with_the_waiters_and_not_with_a_loop`,
`test_the_box_tool_labels_every_resource_it_creates`).

### 2.4 Namensvorschlag

`restore` oder `volume-from-snapshot`. Empfehlung: **`restore`**, weil es in der
Usage-Zeile kurz bleibt und sich nicht mit dem bestehenden `volume` verwechselt.
Aufrufform: `aws_box.sh restore [<snapshot-id>]`, Vorgabe aus
`CORPUS_SNAPSHOT_ID` in `box.env`, sonst aus einer neuen Konstante mit
`snap-03f1d1d9ad9262704`.

---

## Befund 3: Das Runbook und der Umfangsschock

### 3.1 Die Box ist abgebaut, nicht geparkt

**Dies ist der folgenreichste Befund dieser Recherche.** Der Aufgabentext und
Teile der Recherche-Basis sprechen vom "Wiederaufbau aus dem Snapshot" so, als
sei die Maschine noch da. Sie ist es nicht.

Belege [VERIFIED]:
- `.planning/milestones/v1.1-phases/11-.../11-12-SUMMARY.md` liefert
  "ein destroy, das die Historie nicht mitnehmen kann" und "die vollstaendige
  Kosten- und Schadenshistorie der Box im Repositorium, nachdem box.env
  geloescht ist", `requirements-completed: [REL-01]`, `completed: 2026-09-11`.
- Dateisystem-Probe am 14.09.2026:
  `C:/Users/Student/.findling-loadtest/` enthaelt ausschliesslich
  `systemplatte-2026-09/` mit `home-ubuntu-work.tar.gz` und
  `vergleichsmessung-nebendateien.tar.gz`. **Keine `box.env`.**
- `07-snapshot-und-abbau.txt`: "der A-record loadtest.infranode.dev zeigt seit
  dem abbau ins leere."

**Folgen fuer das Runbook:**

| Unterbefehl | Zustand ohne `box.env` |
|---|---|
| `volume`, `stop`, `start`, `snapshot` | `require_state` bricht ab: "no state file at ..." |
| `destroy` | `require_state`, ausserdem `FINDLING_STATE_BACKUP` als Pflichtpfad |
| `status` | liest weich, faellt auf Suche nach Tag zurueck |
| `create` | verweigert grundsaetzlich (`exit 1`), druckt nur das Rezept |

Das Runbook muss daher mit dem Handaufbau der Maschine beginnen. Das Rezept
steht vollstaendig in `cmd_create` (Security Group mit SSH nur von einer
Adresse plus 80/443, Schluesselpaar, `run-instances` mit
`ami-0e79e661e73ddfac9`, 40 GB gp3 Systemplatte, `mem=4G`-Drop-in in
`/etc/default/grub.d/99-mem4g.cfg`, Reboot, Rueckleseprobe `3.9Gi` / `2` /
`aarch64`). Zusaetzlich zu beschaffen: UDP 443 in der Security Group (DI-05-35,
HTTP/3-Alt-Svc des AIO-Apache), der A-Record und die Neuanlage von `box.env`.

### 3.2 Was im Snapshot liegt und was nicht

[VERIFIED: `07-snapshot-und-abbau.txt`, Abschnitte 4 und 10; `box.env`-Abschrift ebenda]

**Im Snapshot (auf `/mnt/findling`, ext4, per UUID mit `nofail` in der fstab):**
- Docker `data-root` und containerd-Wurzel
- die lokale Registry auf der Box (`localhost:5000`)
- `ncdata`, darin `lasttest/files/loadtest` mit den 50.000 Lastdateien
- der Tantivy-Index und die Vektorablage
- 35 GB von 59 GB belegt, `FullSnapshotSizeInBytes` 51,6 GiB

**NICHT im Snapshot:**
- die Systemplatte insgesamt (40 GB gp3, `DeleteOnTermination=true`)
- `/home/ubuntu/work` samt `.pw/` (Passwoerter fuer `admin` und `lasttest`);
  gesichert als `home-ubuntu-work.tar.gz` ausserhalb des Arbeitsbaums
- die Docker-Daemon-Konfiguration, die `data-root` ueberhaupt erst auf
  `/mnt/findling` zeigen laesst
- der Grub-Drop-in mit `mem=4G`, die fstab-Zeile, der `/etc/hosts`-Pin

Ein Wiederaufbau ist also: Maschine bauen, Systemplatte herrichten, Docker mit
dem richtigen `data-root` konfigurieren BEVOR er startet, Volume aus dem
Snapshot anhaengen und mounten, `home-ubuntu-work.tar.gz` zurueckspielen,
A-Record setzen, `/etc/hosts`-Pin bilden, `app_api:app:disable`/`enable`,
harte Speichergrenze setzen.

### 3.3 Die wiederkehrenden Handgriffe, die `aws_box.sh start` ausdruecklich NICHT erledigt

Aus `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md`
Abschnitt 1, woertlich uebernehmbar [VERIFIED]:

| Offener Punkt | Handgriff |
|---|---|
| A-Record `loadtest.infranode.dev` | auf die neue Adresse setzen. Rueckfall 1: `/etc/hosts`-Pin nach JEDEM Maschinenneustart neu aus `docker inspect` des Apache-Containers bilden (Apache wanderte von `172.18.0.6` auf `172.18.0.4`, der alte Pin liess den Poller 300 s ins Backoff laufen). Rueckfall 2: `curl --resolve` |
| Container nach Maschinenstart nicht bewaffnet (DI-05-36) | `occ app_api:app:disable findling_backend`, dann `occ app_api:app:enable findling_backend`. Der Beweis ist ein GEZAEHLTER Poller-Durchgang im Protokoll, kein abgelesener Zustand |
| Harte Speichergrenze nach jeder Registrierung weg | `docker update --memory=2g --memory-swap=2g`, danach `memory.max` und `memory.swap.max` AUS DER CGROUP zurueckliesen, Erwartungswert `2147483648` |
| Nur EINE Nextcloud auf dem Docker-Dienst | `docker ps` zaehlt vor dem ersten `--rm-data`. Am 07.09.2026 hat eine zweite, frische Nextcloud mit `app_api:app:unregister --rm-data` das Messvolumen der ERSTEN geloescht |
| Git fuer Windows schreibt Pfadargumente um | `/dev/sdf` wurde zu `C:/Program Files/Git/dev/sdf`. `aws_box.sh` schaltet das fuer seinen Prozess ab; jedes neue Skript von dieser Maschine aus muss dasselbe tun |

### 3.4 Die Bestandspruefung als Abbruchbedingung

Aus `2026-09-werkzeugfixe/skripte/00-ablauf.md` Schritt 2 [VERIFIED]:

> Der Index ist intakt und die Box ist die, gegen die Phase 10 gemessen hat:
> **52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen**, 3.9Gi, 2 Kerne,
> aarch64. Stimmt das nicht, endet die Anfahrt hier.

Diese Zeile gehoert woertlich ins Runbook, weil sie die einzige ist, die eine
Anfahrt beendet, bevor sie nennenswert Geld kostet.

### 3.5 Struktur-Vorlage fuer `docs/runbook-messbox.md`

Die beiden bestehenden `00-ablauf.md` sind die Vorlage; die des
Werkzeugfix-Laufs (133 Zeilen) ist die passendere Groessenordnung, die der
Vergleichsmessung (313 Zeilen) liefert die Tiefe. Empfohlene Gliederung, die
D-09 bis D-11 abdeckt:

1. Wofuer dieses Runbook gilt und wofuer nicht (Hauptpfad Wiederaufbau aus
   Snapshot; Neuaufbau von null nur als Verweis auf die drei Messberichte)
2. Das Deckel-Rechenblatt (D-05), VOR der ersten Kommandozeile
3. Vorbedingungen ohne Box-Zeit (CI-Laufnummer, Passwortarchiv, AWS-Anmeldung,
   Owner-Freigabe mit Datum und Deckel)
4. Aufbau in nummerierten Copy-paste-Bloecken mit erwarteter Ausgabe je Schritt
   (D-10): Security Group, Schluessel, Instanz, `mem=4G`, Volume aus Snapshot,
   Mount, Docker-`data-root`, Systemplatten-Rueckspielung, A-Record,
   `/etc/hosts`-Pin, DI-05-36-Bewaffnung, Speichergrenze
5. Zustandspruefung mit Abbruchbedingung (52.111/37/0, 3.9Gi, 2, aarch64)
6. Vergleichbarkeitsbedingungen, protokollpflichtig (Abschnitt 3.6 unten)
7. Messreihenfolge mit Abbruchpfaden und Exit-Codes je Schritt
8. Abbau-Checkliste (D-11): Endmessungen VOR dem Abbau, Snapshot pruefen,
   `FINDLING_STATE_BACKUP` setzen, `destroy`, Tag-Sweep, Kostenueberblick
9. Kostenfuehrung: welche Felder in `box.env` wann fortgeschrieben werden

### 3.6 Die fuenf protokollpflichtigen Vergleichbarkeitsgroessen

Aus PITFALLS Pitfall 16, jede vor dem Lauf ABZULESEN und nicht zu erinnern
[CITED: `.planning/research/PITFALLS.md`, Pitfall 16]:

| Groesse | Woher | Warum |
|---|---|---|
| Zeilenstaende `state.db` (indexiert / uebersprungen / fehlgeschlagen) | `occ findling:index` | Der Snapshot traegt FERTIGE Indizes. Wer ihn einspielt und "Volllauf" startet, misst womoeglich einen Resume ueber 52.000 fertige Zeilen statt eines Neubaus. Beim v1.1-Anstoss lagen bereits 1.653 Dateien im Index |
| Cron-Intervall der Instanz | siehe Befund 4 | 5,85 h Leerlauf in v1.1 |
| Instanztyp und harte Containergrenze | `aws_box.sh status`, cgroup | m7g.large, `2147483648` |
| Zeit seit dem letzten Containerstart | `docker inspect --format '{{.State.StartedAt}}'` | Der Seitencache des Wirts hat die Kaltstart-Reproduktion vom 10.09. vollstaendig erklaert: 1.838 ms gegen 1.598 ms, weil der letzte Start einmal 29 h und einmal Minuten zurueck lag |
| Werkzeugstand (Baumhash) | `40b-baumhash.sh` gegen das Abbild | Ein korrigiertes Lastwerkzeug macht v1.1-Stufenzahlen unvergleichbar (Pitfall 16 Punkt 4) |

---

## Befund 4: Das Cron-Intervall war NOMINAL richtig und EFFEKTIV falsch

### 4.1 Der Beleg

`docs/performance.md:158` [VERIFIED: eigener Baum]:

> der Lauf war 5,85 h von 26,6 h ohne Arbeitsvorrat (194 von 812 Lesungen,
> Baseline: 0,10 h), weil der Zulauf am 5-Minuten-Systemcron hing, der auf der
> Box nur alle rund 12 Minuten eine Scheibe von etwa 870 Zeilen lieferte,
> waehrend die Baseline bis zu 49.601 Zeilen Vorlauf hielt

**Die entscheidende Lesart:** Der Systemcron war auf 5 Minuten eingestellt. Die
tatsaechliche Scheibenauslieferung lag bei rund 12 Minuten. Die Differenz
entsteht zwischen Cron-Takt und `StorageCrawlJob`-Fortschritt, nicht an der
Cron-Konfiguration.

**Konsequenz fuer D-07/D-08, und das ist der wichtigste Befund dieses
Abschnitts:** Ein Vorpruefschritt, der nur die KONFIGURATION liest (etwa
`occ background:cron`, den AIO-Cron-Container oder die crontab), haette am
10.09.2026 GRUEN gemeldet, waehrend der Befund vorlag. Die Durchsetzung muss
daher zweiteilig sein:

1. **Konfigurationszweig (billig, vor dem Lauf):** Cron-Modus und Takt der
   Instanz ablesen und ins Protokoll schreiben. Fehlt der Eintrag, bricht das
   Skript ab (D-08, fail-closed).
2. **Wirkungszweig (der eigentliche Befund):** waehrend des Laufs den Abstand
   zwischen zwei Zulaufscheiben MESSEN und protokollieren. Das Werkzeug dafuer
   existiert bereits: `96d-statusbeobachter.py` schreibt alle 120 s eine
   Statuszeile, `96b-waechter.sh` liest den Arbeitsvorrat. Die Zahl
   "vorrat=0 in N von M Lesungen" ist genau die Groesse, aus der 5,85 h
   berechnet worden sind.

Ein Fail-closed-Check, der nur Zweig 1 abdeckt, erfuellt MESS-06 dem Buchstaben
nach und verfehlt den Befund. Das gehoert in die Planung, nicht in die
Ausfuehrung.

### 4.2 Eine Zahlendifferenz, die der Plan nicht glaetten sollte

PITFALLS Pitfall 16 und `docs/performance.md` nennen "194 von 812 Lesungen".
`docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/00-ende.txt:142-143`
nennt "vorrat=0 in 62 von 325 Lesungen" [VERIFIED: eigener Baum]. Beide Paare
ergeben rund 24 bzw. 19 Prozent und stammen sehr wahrscheinlich aus zwei
verschiedenen Ableseintervallen (Statusbeobachter alle 120 s gegen Waechter alle
300 s). Sie sind kein Widerspruch, aber das Runbook sollte benennen, WELCHE
Reihe die Protokollzahl liefert, sonst entsteht beim naechsten Bericht eine
Scheingenauigkeit. [ASSUMED: die Zuordnung der beiden Reihen zu den beiden
Beobachtern ist nicht ausdruecklich belegt]

### 4.3 Der behobene Teil und der offene Teil

Der Befund ist in v1.1 bereits behoben worden: die Top-up-Route
(`POST /queues/documents/topup`, Budget 20 s, Scheiben-Lock gegen den Cron)
laesst einen Container, dessen Claim leer ausgeht, die naechste Crawl-Scheibe
selbst ausfuehren. Der WIRKUNGSBELEG dazu steht aus und ist der Kern von
Phase 15. Phase 12 baut die Instrumentierung, die diesen Beleg fuehren kann.

---

## Befund 5: Der stable35-Entscheid

### 5.1 Das Versionsfenster ist bereits gehoben

[VERIFIED: eigener Baum]

```
php/appinfo/info.xml:219      <nextcloud min-version="33" max-version="35"/>
backend/appinfo/info.xml:225  <nextcloud min-version="33" max-version="35"/>
```

**D-01 spricht von "auf max NC 35 heben". In den `info.xml` gibt es dabei nichts
zu tun.** Die Formulierung stammt aus `11-CONTEXT.md` D-11 ("Das Versionsfenster
von v1.1.0 bleibt bei max Nextcloud 34"), die durch den spaeteren Vorentscheid
V-2 vom 10.09. in der anderen Lesart bestaetigt worden ist. `deploy-harp.yml`
haelt das woertlich fest:

> Decided on 2026-09-10 by phase 11, decision v2-a ... the declared window of
> v1.1.0 stays at min-version 33 and max-version 35, both info.xml stay as they
> are, this entry stays with tolerate-failure: true, and
> backend/tests/test_lockstep_versions.py stays unchanged.

Der Planer muss diese Diskrepanz auffangen, sonst entsteht ein Plan, dessen
erste Aufgabe bereits erledigt ist.

### 5.2 Was tatsaechlich offen ist

Genau zwei Dinge in `.github/workflows/deploy-harp.yml`:

| Ort | Ist-Zustand | Zielzustand bei NC 35 final |
|---|---|---|
| Matrix-Eintrag `server-version: stable35` (Zeile 217-271) | `tolerate-failure: true`, `php-version: '8.3'`, `runner: ubuntu-24.04` | `tolerate-failure: false`, der Ast wird muss-gruen |
| Der RE-CHECK-Absatz darueber (Zeile 211-270, rund 60 Zeilen Kommentar) | traegt "RE-CHECK DATE: 2026-09-16" und drei aufeinander aufbauende Entscheidungsvermerke | kommt laut eigenem Wortlaut heraus ("On that day this flag and this whole paragraph come out") |

Der Kommentar nennt seine Nachfolge-Adresse selbst: sie lag bei Plan 11-11 und
wandert mit dem Abschluss von Phase 11 weiter. Phase 12 ist die neue Adresse.

Gleichzeitig ist ein Gate zu beachten: `backend/tests/test_lockstep_versions.py`
prueft, dass die CI-Matrix JEDE Version des deklarierten Fensters abdeckt
(`_window_findings(("33","35"), ("33","35"), ["33","34","35"]) == []`, Zeile
387). Der `stable35`-Eintrag darf also nicht entfernt werden, nur sein Flag darf
fallen.

### 5.3 Der Releasestand, verifiziert am 14.09.2026

`gh api repos/nextcloud/server/releases` [VERIFIED: GitHub API, 2026-09-14]:

```
v35.0.0rc4  prerelease=true   2026-09-10T12:53:25Z
v34.0.4     prerelease=false  2026-09-10T13:16:15Z
v33.0.9     prerelease=false  2026-09-10T13:29:56Z
v35.0.0rc3  prerelease=true   2026-09-03T12:29:49Z
```

**NC 35 ist am 14.09.2026 NICHT final.** Neueste 35er-Marke ist rc4 als
Vorabversion, neueste echte Freigabe ist v34.0.4.

Beide Zweige `stable35` existieren weiterhin
(`gh api repos/nextcloud/server/branches/stable35` und
`.../app_api/branches/stable35` antworten mit `stable35`)
[VERIFIED: GitHub API, 2026-09-14], der CI-Ast faellt also nicht auf `master`
zurueck.

Offizieller Zeitplan [CITED: github.com/nextcloud/server/wiki/Maintenance-and-Release-Schedule]:

| Meilenstein NC 35 | Datum |
|---|---|
| RC 1 | 2026-08-25 |
| RC 2 | 2026-08-27 |
| RC 3 | 2026-09-03 |
| RC 4 | 2026-09-10 |
| Final | 2026-09-16, mit dem Zusatz "date not final, but will be pre-conf" |

Der Kadenz nach (rc3 am 03.09., rc4 am 10.09., jeweils mittwochs) waere ein rc5
am 17.09. moeglich; der Zeitplan nennt keinen. Die Wahrscheinlichkeit, dass am
16.09. der D-03-Zweig greift, ist damit real und nicht gering.

### 5.4 Was der D-02-Beweis konkret verlangt

D-02 fordert "NC-35-final-Check PLUS deploy-harp gruen gegen stable35". Der
gruene Ast ist reproduzierbar: der Kommentar haelt fest, dass der Ast am
07.09.2026 im Lauf 34114937751 alleine gruen war. Ein neuer Beweis braucht einen
Lauf von `deploy-harp.yml` auf dem aktuellen Stand. Die Strecke ist
umfangreich (Fremdinstallation, Store-Install, Upgrade-Beweis) und laeuft auf
`push`/`workflow_dispatch`; sie kostet Wartezeit, kein Geld.

Beachten: Befund A aus Plan 11-11 warnt vor den Uninstall-Gate-Schwellen in
derselben Strecke [CITED: `12-CONTEXT.md`, Integration Points]. Ein roter Lauf
am 16.09. ist nach dem eigenen Wortlaut des Kommentars "a finding rather than a
reason to put the flag back".

### 5.5 Empfehlung zur Form des Entscheids

Der Entscheid ist an beiden Tagen zu dokumentieren, egal wie er ausfaellt.
Empfohlen:
- Der Kommentar in `deploy-harp.yml` wird fortgeschrieben (bei D-03: neuer
  RE-CHECK-Termin mit Begruendung und benannter Nachfolge-Adresse in Phase 16;
  bei D-01/D-02: Absatz entfaellt, Flag faellt, Datum und Laufnummer des gruenen
  Beweises stehen an seiner Stelle).
- Eine kurze Entscheidungsnotiz daneben, damit der Entscheid nicht nur in einem
  YAML-Kommentar lebt. `docs/`-Ort frei; `.planning/phases/12-.../` ist die
  naheliegende Adresse, weil dort ohnehin die Phasenunterlagen liegen.
- Der Plan muss BEIDE Zweige vorab ausformulieren, weil am 16.09. keine Zeit fuer
  eine Entwurfsrunde ist.

---

## Befund 6: Wo neue Dateien liegen duerfen, und welche Gates dann greifen

### 6.1 Die Gate-Landschaft fuer Messskripte

`backend/tests/test_measurement_scripts.py` [VERIFIED: eigener Baum]:

| Geltungsbereich | Auswahl | Gates |
|---|---|---|
| **Weit** | `docs/measurements/**/skripte/*` mit Suffix `.py` oder `.sh` | kein Wagenruecklauf (als Bytes gelesen), kein Halbgeviert- und kein Geviertstrich (`DASHES = (chr(0x2014), chr(0x2013))`) |
| **Eng** | `NARROW_SCOPE_DIRS = (RUN_DIR, FIX_RUN_DIR)`, also NUR `2026-09-vergleichsmessung-m7g/skripte` und `2026-09-werkzeugfixe/skripte` | Shebang muss `#!/bin/sh\n` oder `#!/usr/bin/env python3\n` sein, kein Maschinenpfad im Code (`/home/`, `sys.path.insert`, `sys.path.append`, `drillhelfer`, ausgenommen Kommentare und kommentierte Vorgabewerte), kein Passwort auf der Kommandozeile |
| **Waechter** | `2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh` | sha256 `5f9607fc...`, 23479 Bytes, byteweise unveraendert |

**Handlungsbedarf:** Ein neues Laufverzeichnis wird vom WEITEN Bereich
automatisch erfasst, vom ENGEN nicht. `NARROW_SCOPE_DIRS` ist eine fest
verdrahtete Zweiertupel und muss um das neue Verzeichnis ergaenzt werden, sonst
laufen Shebang-, Maschinenpfad- und Passwort-Gate ueber die neuen Skripte NICHT.
Dazu passt `test_the_wide_scope_covers_every_measurement_and_skips_what_is_not_a_script`,
das eine Untermenge behauptet und laut eigenem Docstring "a floor and not an
equality" ist, damit der naechste Lauf ohne Edit aufgenommen wird.

### 6.2 Die CI-Luecke, die ein Plan schliessen sollte

`.github/workflows/python.yml` triggert auf `backend/**`, `scripts/**` und sich
selbst [VERIFIED: eigener Baum, Zeilen 6-25]. **`docs/measurements/**` steht
nicht in der Liste.** Ein Commit, der ausschliesslich ein neues Messskript unter
`docs/measurements/.../skripte/` anlegt, startet `python.yml` nicht, und damit
laufen `test_measurement_scripts.py` und `test_ops_scripts.py` nicht. Die Gates
greifen erst beim naechsten Commit, der `backend/**` oder `scripts/**` beruehrt,
und faerben dann den falschen Commit rot. Das ist derselbe Mechanismus, den der
Kommentar in `python.yml` fuer `scripts/dev/build_corpus.py` beschreibt und
deshalb bereits einmal abgefangen hat.

**Zwei Wege, beide vertretbar:**
- `docs/measurements/**` in die Pfadliste von `python.yml` aufnehmen (eng am
  bestehenden Begruendungsmuster, eine Zeile plus Kommentar).
- Oder in derselben Aenderung ohnehin `backend/tests/test_measurement_scripts.py`
  beruehren (was fuer `NARROW_SCOPE_DIRS` sowieso noetig ist), sodass die Gates
  auf dem Commit laufen. Das ist kein Schutz fuer spaetere Commits.

Empfehlung: **beides**, weil der zweite Weg nur zufaellig traegt.

### 6.3 Ruff, pyright, vulture

`python.yml` linted `backend/.` (also `src` und `tests`) und zusaetzlich
`../scripts` mit derselben Regelmenge, ausdruecklich ohne pyright und ohne
vulture [VERIFIED: `python.yml:76-114`]. `docs/measurements/**` wird von keinem
dieser Werkzeuge erfasst. Eine Python-Sonde dort ist damit frei von Ruff- und
pyright-Zwang, aber auch frei von deren Schutz; die gemeinsame Regel der
Messskripte (keine Maschinenpfade, kein Passwort im Argument) ersetzt das nur
teilweise.

Eine Aenderung an `scripts/ops/aws_box.sh` faellt dagegen unter `scripts/**` und
loest `python.yml` aus; der Ruff-Lauf betrifft sie nicht (Shell), die
`test_ops_scripts.py`-Gates schon.

---

## Befund 7: Das Deckel-Rechenblatt (D-05)

### 7.1 Die belegten Posten aus dem v1.1-Lauf

[VERIFIED: `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitt 16 und 7]

| Posten | Zeit | Quelle |
|---|---|---|
| Anfahrt und Vormessungen | 38 min | v1.1, Abschnitt 16 |
| Volllauf beide Spuren bis zum letzten Vektor | **26 h 37 min 21 s** | Abschnitt 7, Obergrenze gegen die grobe Marke 26 h 41 min 15 s |
| Nachmessungen (zwei vom Owner entschiedene) | ~2 h 50 min | Abschnitt 16 |
| **Tatsaechliche Gesamtlaufzeit** | **31,05 h** | `box.env`, `BOX_LAST_UPTIME_COST_USD` |
| **Tatsaechliche Kosten** | **3,5969 USD netto** | ebenda |

Saetze [VERIFIED: `aws_box.sh:147-152` und Abschnitt 16]:

| Satz | Wert |
|---|---|
| laufend gesamt | 0,115841 USD/h |
| davon Box m7g.large | 0,0978 USD/h |
| davon Speicher gp3 | 0,013041 USD/h |
| davon oeffentliche IPv4-Adresse | 0,0050 USD/h |
| angehalten | 0,3130 USD/Tag |
| Snapshot (dauerhaft) | 2,79 bis 2,99 USD/Monat |

Deckel-Geschichte [VERIFIED]: urspruenglich 30 h / 3,50 USD (Owner 09.09.),
gerissen am 10.09. um 15:20Z, angehoben auf 34 h / 4,00 USD, tatsaechlich
verbraucht 31,05 h / 3,5969 USD. Der Deckel ist also SCHON EINMAL gerissen.

### 7.2 Warum 31 h fuer Phase 15 vermutlich zu knapp ist

Die PITFALLS-Empfehlung von ">= 31 h / ~3,59 USD" entspricht exakt dem, was der
v1.1-Lauf VERBRAUCHT hat. Phase 15 hat aber einen anderen Arbeitsumfang. Das
Rechenblatt muss die Differenzposten ausweisen, statt die alte Summe zu
uebernehmen:

**Posten, die in v1.1 nicht vorkamen:**
- Erstvollzug des Wiederaufbau-Runbooks inklusive Handaufbau der Maschine,
  Systemplatten-Rueckspielung und A-Record (in v1.1 stand die Box bereits)
- Untersuchung der VIER regressiven Laststufen mit je einem Entscheid
- Wiederaufwaerm-Messung der Entladung in vier Auspraegungen
  (warm/kalt x mit/ohne Seitencache), A/B ueber den MEM-01-Schalter
- Sprachfall-Messung mit der NEUEN Messgroesse inklusive Erstvollzug des neuen
  Skripts

**Posten, die guenstiger werden:**
- Der Korpus muss nicht neu erzeugt und nicht neu hochgeladen werden; er kommt
  aus dem Snapshot. In v1.0/v1.1 war das ein eigener, mehrstuendiger Block

**Posten, die gleich bleiben:**
- Der Volllauf selbst. Ob der Top-up-Fix ihn verkuerzt, ist die zu beweisende
  Frage; das Rechenblatt darf die erhoffte Verbesserung NICHT vorwegnehmen.
  Als Planwert gilt 26 h 37 min, nicht ein erhoffter kleinerer Wert. Genau
  dieser Fehler hat den v1.1-Deckel gerissen.

Das Rechenblatt gehoert als TABELLE mit leeren Ist-Spalten ins Runbook, damit
Phase 15 es fuellt und Phase 16 daraus die naechste Rechnung ableiten kann. Die
Freigabe selbst faellt am Phase-15-Checkpoint, nicht hier.

### 7.3 Ein Zusatzposten, den das Rechenblatt nennen muss

`destroy` loescht `box.env`. Die Kostenhistorie existiert danach nur noch in
der committeten Rohdatei. Das ist in v1.1 bereits eingetreten, und die aktuelle
Abwesenheit von `box.env` auf der Entwicklungsmaschine ist der Beleg. Das
Rechenblatt braucht daher eine Zeile "Wohin die Schlusszahlen VOR dem Abbau
geschrieben werden".

---

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---|---|---|---|
| Zahl der Dokumente im Index zu einem Begriff | eine eigene Zaehlschleife ueber Treffer, eine Aggregation, ein zweiter Rangweg | `Searcher.search(query, 1, count=True).count` | Existiert in tantivy 0.26.0, empirisch geprueft, ungedeckelt, ein Aufruf |
| Beide Ranglisten einer Anfrage | `searcher.search` plus Vektorsuche in der Sonde nachbauen | `findling.index.search.ranked_sides(index, query, semantic=...)` | Der Docstring von `_sides` nennt genau diesen Nachbau als den Fehler: "A second way of building either list would answer that question about a search this container never ran, and the difference would show up as a mark that is right most of the time" |
| Anfrage aus einer Suchzeile bauen | eigener Parser, eigene Operator-Behandlung | `findling.query.rewrite.build_query(side.index, text, title_only=False)` | Komposita, Umlautvarianten, Stemmer und Operatoren haengen daran; ein zweiter Weg misst eine andere Suche |
| Auf AWS-Ressourcen warten | eigene Warteschleife mit `sleep` | `aws ec2 wait <waiter>` | Hausregel seit 04.09.2026, in `aws_box.sh` als Kommentar begruendet und in `test_the_aws_tool_waits_with_the_waiters_and_not_with_a_loop` durchgesetzt |
| Bestaetigen, dass eine AWS-Ressource fertig/weg ist | dem Waiter glauben | unabhaengige Nachlese per `describe-*` | "ein Waiter, der zurueckkehrt, sagt nur, dass die API aufgehoert hat pending zu antworten" (Muster aus Plan 11-12) |
| Passwoerter zur Box tragen | Argument, Umgebung ueber `sudo` durchreichen ohne `--preserve-env` | `occ`-Wrapper aus `98b-sprachfaelle.sh` mit `sudo --preserve-env=OC_PASS docker exec -e OC_PASS` | `sudo` raeumt unter `env_reset` die Umgebung, `docker exec` gibt von sich aus nichts weiter. In v1.1 mussten deswegen zwei Skripte WAEHREND des Laufs korrigiert werden |
| Ein Messskript korrigieren, das schon gefahren ist | `98b-sprachfaelle.sh` anfassen | neue Datei in neuem Laufverzeichnis | Waechter mit sha256 und die Hausregel `DRIVEN_FASSUNG_RULE` |
| Kostensaetze holen | die regionale Preisliste herunterladen | die gepinnten Saetze in `aws_box.sh`, Reproduktionsbefehl in `cmd_prices` | Die Liste ist ueber ein Gigabyte gross; der Kommentar nennt das "a trap" |

**Kerngedanke:** Dieses Repositorium hat fuer fast jede Aufgabe dieser Phase
bereits ein Muster mit einer ausgeschriebenen Begruendung. Der teuerste Fehler
waere, ein zweites Verfahren fuer eine Frage zu bauen, die ein bestehendes
bereits beantwortet.

---

## Common Pitfalls

### Pitfall 1: Die Zahl verlaesst den Container

**Was schiefgeht:** Um die Fremdbestandszahl bequem zu bekommen, wird
`/diagnose` um ein Zahlenfeld erweitert oder `AdminViewService` reicht `query`
durch.
**Warum:** Es sieht nach der kleinsten Aenderung aus.
**Vermeidung:** In-Container-Sonde. Kein Produktionscode.
**Warnzeichen:** Im Plan steht eine Aufgabe, die `backend/src/findling/api/` oder
`php/lib/Service/AdminViewService.php` beruehrt.

### Pitfall 2: Das aus dem Snapshot erzeugte Volume bleibt als Rechnung stehen

**Was schiefgeht:** Das Volume erbt `purpose=findling-corpus-keep`, der
Tag-Sweep von `destroy` findet es nicht, es kostet 0,0952 USD je GB-Monat
weiter.
**Warum:** AWS vererbt die Tags des Snapshots, und der Keep-Tag ist genau dafuer
erfunden worden, dem Sweep zu entgehen.
**Vermeidung:** Umtaggen auf `purpose=findling-phase5` als Pflichtschritt IM
Unterbefehl, mit Rueckleseprobe; nicht als Runbook-Zeile.
**Warnzeichen:** Der neue Unterbefehl ruft `create-volume` und danach nur noch
`attach-volume`.

### Pitfall 3: Der Cron-Check prueft die Konfiguration statt der Wirkung

**Was schiefgeht:** Der Vorpruefschritt liest den Cron-Takt, findet 5 Minuten,
meldet gruen, und der Lauf verliert wieder 5,85 Stunden.
**Warum:** Der v1.1-Befund war eine Diskrepanz zwischen Takt und Wirkung, nicht
eine falsche Einstellung.
**Vermeidung:** Beide Zweige aus Befund 4.1.
**Warnzeichen:** Im Plan steht genau ein Cron-Task und er heisst "Intervall
setzen und pruefen".

### Pitfall 4: Der Volllauf ist in Wahrheit ein Resume

**Was schiefgeht:** Der Snapshot traegt den FERTIGEN Index. Wer ihn einspielt und
"Volllauf" startet, misst einen Resume ueber 52.000 fertige Zeilen und meldet
eine grandiose Verbesserung.
**Warum:** Der Snapshot ist als Korpusquelle gedacht, traegt aber Korpus UND
Index.
**Vermeidung:** Der Nullstand wird VOR dem Anstoss mit Zahlen belegt (Muster
`93-nullstand.sh`: Volumeninhalt, `oc_findling_file_state`, Marken in `meta`,
Ausgabe von `occ findling:index`, danach `findling:index --restart -n`). Das
Runbook macht daraus einen Abbruchpfad, keine Empfehlung.
**Warnzeichen:** Der Durchsatz liegt in den ersten Minuten unplausibel hoch.

### Pitfall 5: Das Runbook beschreibt einen Weg, den niemand gegangen ist

**Was schiefgeht:** Das Runbook entsteht aus drei Berichten, liest sich
vollstaendig, und in Phase 15 stellt sich heraus, dass Schritt 4 nicht geht.
**Warum:** D-09 verlangt genau deshalb den Verzicht auf den ungetesteten
Neuaufbau-von-null. Aber auch der Snapshot-Pfad ist noch nie gegangen worden.
**Vermeidung:** Jeder Block traegt eine erwartete Ausgabe (D-10). Alles, was in
Phase 12 lokal oder gegen die AWS-API OHNE laufende Box trockengeprueft werden
kann, wird trockengeprueft (`aws ec2 describe-snapshots` ist lesend und
kostenlos). Was nicht pruefbar ist, wird im Runbook AUSDRUECKLICH als
"in Phase 15 erstmals vollzogen" markiert, statt Gewissheit vorzutaeuschen.
**Warnzeichen:** Ein Block ohne Pruefpunkt.

### Pitfall 6: Der stable35-Entscheid wird am 16.09. entworfen

**Was schiefgeht:** Am 16.09. steht der Releasestand fest, aber der Text, der
Kommentar und die Notiz sind noch nicht geschrieben, und der Tag geht vorbei.
**Warum:** Die Frist liegt zwei Tage nach Phasenbeginn.
**Vermeidung:** Beide Zweige (D-01/D-02 und D-03) werden VORHER vollstaendig
ausformuliert. Am 16.09. wird nur noch gelesen, welcher greift, der Beweislauf
gestartet und der fertige Text eingesetzt.
**Warnzeichen:** Im Plan steht "Entscheid treffen" als eine einzige Aufgabe.

### Pitfall 7: Der Abbau nimmt die Historie mit

**Was schiefgeht:** `destroy` loescht `box.env` und damit die einzige
Kosten- und Schadenshistorie.
**Warum:** Das ist das dokumentierte Verhalten, und `FINDLING_STATE_BACKUP` ist
genau dagegen eingebaut worden.
**Vermeidung:** Die Abbau-Checkliste (D-11) fuehrt die Reihenfolge: Endmessungen
und Gegenproben VOR dem Abbau, Historie nach origin, Sicherung anlegen, erst
dann `destroy`, danach Tag-Sweep und Kostenueberblick.
**Warnzeichen:** Im Runbook steht `destroy` vor einem Schritt, der noch Zahlen
erhebt.

### Pitfall 8: Der neunte Unterbefehl macht den Gate-Test rot

**Was schiefgeht:** `test_the_aws_tool_names_its_eight_subcommands_in_the_usage`
prueft die Usage-Zeile woertlich.
**Vermeidung:** Test in derselben Aenderung umbenennen und anpassen.
**Warnzeichen:** Der Plan beruehrt `aws_box.sh`, aber nicht
`backend/tests/test_ops_scripts.py`.

---

## Code Examples

### Beispiel A: In-Container-Sonde, Grundgeruest

Quelle des Aufrufmusters: `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/94-grundlast.sh:102-113`.
Quelle der API: `backend/src/findling/index/search.py`, `api/diagnose.py`,
eigene Probe gegen tantivy 0.26.0 am 14.09.2026.

```python
#!/usr/bin/env python3
"""Der Bestand des Index zu einem Begriff, im Prozess gemessen.

Keine Route, kein Draht, keine Zahl ueber eine Prozessgrenze: die Zaehlung
bleibt im Container, und damit entsteht das Zaehl-Orakel aus T-02-93 gar
nicht erst.
"""

from findling.api import resources
from findling.index.search import SemanticSide, ranked_sides
from findling.config import settings
from findling.query.rewrite import build_query

BEGRIFFE = ("Genehmigung", "Frist", "Mueller", "Vertrag", '"drei Monate"',
            "bescheid", "type:pdf bescheid", "Belehrung", "Auszug", "Erinnerung")


def messe(text):
    side = resources.read_side()
    rewritten = build_query(side.index, text, title_only=False)
    if rewritten.query is None:
        return None
    searcher = side.index.searcher()
    # Die ungedeckelte Zahl. count ist im Typstub nicht deklariert, zur
    # Laufzeit aber vorhanden; gemessen am 14.09.2026 gegen tantivy 0.26.0.
    bestand = searcher.search(rewritten.query, 1, count=True).count
    semantic = None
    if side.vectors is not None and settings().embed_enabled:
        semantic = SemanticSide(vectors=side.vectors,
                                model=resources.query_model(), text=text)
    sides = ranked_sides(side.index, rewritten.query, semantic=semantic)
    return (bestand, len(sides.lexical), len(sides.semantic))


for begriff in BEGRIFFE:
    ergebnis = messe(begriff)
    if ergebnis is None:
        print("bestand %-22s keine-suchbare-zeile" % begriff)
        continue
    print("bestand %-22s index=%-6d fenster_lex=%-4d fenster_sem=%-4d"
          % (begriff, ergebnis[0], ergebnis[1], ergebnis[2]))
```

Hinweis: `resources.read_side()` ist der Zugang, den `api/diagnose.py:169`
benutzt. Der Plan sollte vor dem Bau pruefen, ob die Sonde im Container den
Lesezugriff bekommt, ohne den Poller zu stoeren; `read_side` ist im
Diagnosepfad ausdruecklich fuer lesende Fragen vorgesehen.

### Beispiel B: Der Fahrer auf der Box

```sh
SONDE="$SKRIPTE/73-bestand-sonde.py"
sudo docker cp "$SONDE" "$CONTAINER:/tmp/73-bestand-sonde.py"
sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/73-bestand-sonde.py \
    >"$WORK/bestand.txt" || {
    echo "die Bestandssonde konnte nicht gefahren werden" >&2
    exit 19
}
```

Der Exit-Code 19 ist der bestehende Code fuer "die Vorpruefung des
Fremdbestands konnte nicht gefahren werden" aus `98b-sprachfaelle.sh` und bleibt
damit unveraendert lesbar.

### Beispiel C: `occ` ueber zwei Schichten, mit Passwort aus der Umgebung

Quelle: `docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh:183-190`.

```sh
occ() {
    if [ -n "${OC_PASS:-}" ]; then
        sudo --preserve-env=OC_PASS docker exec -e OC_PASS \
            --user www-data "$NEXTCLOUD" php occ "$@"
    else
        sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
    fi
}
```

### Beispiel D: Volume aus Snapshot, mit den drei Pflichtpruefungen

Quelle des Kommandos: `07-snapshot-und-abbau.txt`, Abschnitt 10.
Quelle des Musters (Aufnahme statt zweiter Erzeugung, Waiter, Nachlese):
`aws_box.sh::cmd_volume` und `cmd_snapshot`.

```sh
# 1. Snapshot lesend bestaetigen, bevor irgendetwas entsteht
ec2 describe-snapshots --snapshot-ids "$snapshot_id"    # State completed?

# 2. Volume in der Zone der Box, Groesse mindestens die des Snapshots
ec2 create-volume --snapshot-id "$snapshot_id" \
    --availability-zone "$ZONE" --volume-type "$VOLUME_TYPE" \
    --size "$VOLUME_SIZE_GB"

# 3. Umtaggen, sonst findet der Sweep von destroy es nie
ec2 create-tags --resources "$volume_id" \
    --tags "Key=$TAG_KEY,Value=$TAG_VALUE" "Key=Name,Value=$VOLUME_NAME"
ec2 describe-tags --filters "Name=resource-id,Values=$volume_id"   # Nachlese

# 4. Warten mit dem Waiter, nicht mit einer Schleife
"$AWS_BIN" --region "$REGION" ec2 wait volume-available --volume-ids "$volume_id"
```

---

## State of the Art

| Alt | Neu | Wann | Auswirkung |
|---|---|---|---|
| Fremdbestand = Treffer der OCS-Route | Bestand = Dokumente im Index (`SearchResult.count`) plus Fensterbelegung aus `ranked_sides` | diese Phase | Deckel 26 faellt weg, Schwelle 64 wird pruefbar |
| `aws_box.sh` mit acht Unterbefehlen | neunter Unterbefehl fuer Volume aus Snapshot | diese Phase | Der Wiederaufbau ist erstmals werkzeuggestuetzt |
| Ablaufplaene je Lauf (`00-ablauf.md`) | ein dauerhaftes `docs/runbook-messbox.md` plus je Lauf ein schlanker Ablaufplan | diese Phase | Die wiederkehrenden Handgriffe stehen einmal statt dreimal |
| Cron-Intervall als Nebenbefund im Bericht | protokollpflichtige, fail-closed durchgesetzte Messbedingung | diese Phase | Ein Lauf ohne Protokoll gilt als unvollstaendig |
| stable35 als tolerierter CI-Ast | muss-gruener Ast (bei NC 35 final) bzw. dokumentiert verlaengerter RE-CHECK | 16.09.2026 | Die Store-Zusage max NC 35 bekommt einen Beweis |

**Veraltet / nicht mehr zutreffend:**
- "Die Box ist angehalten." Sie ist seit 11.09.2026 abgebaut.
- "Das Versionsfenster muss auf 35 gehoben werden." Es steht bereits auf 35.
- "`aws_box.sh start` faehrt die Box an." Ohne `box.env` laeuft der Unterbefehl
  nicht, und ohne Instanz gaebe es nichts zu starten.

---

## Package Legitimacy Audit

**Nicht anwendbar.** Diese Phase installiert keine externen Pakete. Die neuen
Werkzeuge benutzen ausschliesslich: POSIX-Shell, `jq` (bereits Vorbedingung von
`98b`, Exit 18), `curl`, die AWS CLI, `gh`, und im Container die bereits
installierten Projektabhaengigkeiten (`tantivy` 0.26.0 und die eigenen Module).
Es gibt nichts zu pruefen und nichts freizugeben.

---

## Environment Availability

Geprueft am 2026-09-14 auf der Entwicklungsmaschine (Windows 11, Git Bash):

| Abhaengigkeit | Gebraucht fuer | Verfuegbar | Version | Rueckfall |
|---|---|---|---|---|
| AWS CLI v2 | `aws_box.sh`, Snapshot-Nachlese | ja | aws-cli/2.36.39 (auch unter `C:/Program Files/Amazon/AWSCLIV2/aws.exe`, `aws_box.sh` findet beide) | keiner |
| `gh` | NC-35-Releasestand, CI-Laufnummern, `deploy-harp`-Lauf | ja | 2.92.0 | GitHub-Web |
| `jq` | Messskripte auf der Box (nicht hier) | ja (lokal) | jq-1.8.1 | Auf der BOX pruefen, `98b` endet dort mit 18 |
| `uv` | Backend-Tests lokal gruen vor Commit | ja | 0.11.7 | keiner |
| `python3` | `aws_box.sh::json`, lokale Proben | ja | 3.13.1 | keiner |
| AWS-Anmeldung | jeder AWS-Aufruf | Datei vorhanden: `C:/Users/Student/.findling-aws.env` (126 Byte, IAM-User `findling-loadtest`) | n/a | keiner |
| `snap-03f1d1d9ad9262704` | Wiederaufbau | **in dieser Sitzung NICHT gegen die API geprueft** | n/a | keiner |
| `box.env` | jeder zustandsbehaftete `aws_box.sh`-Aufruf | **NEIN, existiert nicht** | n/a | Neu schreiben; Abschrift des alten Inhalts in `07-snapshot-und-abbau.txt` |
| Messbox (Instanz) | alles Messen | **NEIN, abgebaut 11.09.2026** | n/a | Phase 15 baut neu |
| `home-ubuntu-work.tar.gz` (Passwoerter, Beobachter) | Wiederaufbau | ja, `C:/Users/Student/.findling-loadtest/systemplatte-2026-09/` | n/a | keiner |

**Fehlende Abhaengigkeiten ohne Rueckfall, die Phase 12 aber NICHT blockieren:**
Box und `box.env`. Phase 12 ist ausdruecklich ohne Box geplant; sie sind
Vorbedingungen von Phase 15 und Gegenstand des Runbooks.

**Empfohlene lesende Probe in Phase 12 (kostenlos, kein Ressourcenverbrauch):**

```sh
aws ec2 describe-snapshots --region eu-central-1 \
    --snapshot-ids snap-03f1d1d9ad9262704
```

Das bestaetigt Existenz, `State=completed`, Groesse und Tag des Snapshots,
bevor das Runbook einen Wiederaufbau darauf aufbaut. Ohne diese Probe steht die
gesamte Phase-15-Planung auf einer Annahme.

---

## Project Constraints (from CLAUDE.md)

| Vorgabe | Auswirkung auf diese Phase |
|---|---|
| Code weiterhin Englisch; Projektkommunikation Deutsch | Skript-Kommentare folgen dem bestehenden Stil der Nachbardateien (englische und deutsche Abschnitte gemischt, wie in `98b`); `docs/runbook-messbox.md` ist deutsche Prosa |
| **Keine Em-Dashes** | Durchgesetzt als Gate: `DASHES = (chr(0x2014), chr(0x2013))` in `test_measurement_scripts.py` und `test_ops_scripts.py`. Gilt fuer Skripte; fuer `docs/runbook-messbox.md` gibt es kein Gate, die Regel gilt trotzdem |
| Echte Umlaute nur in deutscher Prosa, nie in Code | Skripte benutzen ASCII-Bezeichner (`ue`, `ae`), wie `98b` es durchgaengig tut. `docs/runbook-messbox.md` benutzt echte Umlaute |
| Qualitaetsgates: ruff-Vollregelsatz, pyright basic, vulture, lokal gruen vor Commit | Greift fuer `scripts/**` (ruff) und `backend/**` (alle drei). Fuer `docs/measurements/**` greift keines davon, siehe Befund 6.3 |
| Nach jeder Phase Security-, Bug- und Performance-Audit (15.08.2026) | Auch fuer diese Phase, obwohl sie kein Produkt aendert. Der Security-Anteil ist der Umgang mit AWS-Anmeldung und Box-Passwoertern |
| Launch-Haertung vor der Store-Abgabe | Nicht diese Phase (Phase 16) |
| Kurze Produkttexte | Nicht diese Phase (kein Store-Text) |
| GSD-Workflow: keine direkten Repo-Aenderungen ausserhalb eines GSD-Kommandos | gilt |

**Hinweis zum "Vokabular-Gate archiv":** Die Aufgabenbeschreibung nennt ein
Verbot des Wortes "archiv" in oeffentlichen Artefakten. In diesem Repositorium
existiert kein solches Gate, und `.planning/ROADMAP.md` benutzt das Wort
mehrfach ("Archiv: .planning/milestones/..."). Die Regel stammt sehr
wahrscheinlich aus einem anderen Projekt des Owners. [ASSUMED] Der Planer sollte
sie nicht als Repo-Regel behandeln, ohne sie beim Owner zu bestaetigen; sie
ohne Not anzuwenden waere harmlos, sie als Gate zu bauen waere falsch.

---

## Security Domain

Diese Phase aendert kein Produkt und keine Angriffsflaeche der App. Die
relevanten ASVS-Kategorien sind die, die den Umgang der Werkzeuge mit
Geheimnissen betreffen.

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Trifft zu | Bestehende Kontrolle |
|---|---|---|
| V2 Authentication | nein (kein Auth-Code beruehrt) | n/a |
| V3 Session Management | nein | n/a |
| V4 Access Control | teilweise | Die Sonde umgeht bewusst keinen Rechtefilter, sondern misst absichtlich ohne Vorfilter, admin-seitig im Container. `ranked_sides` ist ausdruecklich dafuer gebaut (D-14) |
| V5 Input Validation | nein | n/a |
| V6 Cryptography | nein | n/a |
| V7 Error Handling and Logging | ja | Messskripte schreiben Rohdaten ins Repositorium. Sie duerfen keine Passwoerter, keine Anmeldedaten und keine oeffentlichen Adressen mit Geheimnischarakter tragen |
| V14 Configuration | ja | AWS-Anmeldung nur aus der Umgebung; `aws_box.sh` nennt die beiden Variablennamen genau einmal und druckt nie einen Wert (T-05-17) |

### Bekannte Bedrohungsmuster fuer diese Werkzeugklasse

| Muster | STRIDE | Gegenmassnahme im Bestand |
|---|---|---|
| Passwort als Argument landet in der Prozessliste und in jedem Protokoll | Information Disclosure | `test_the_script_of_this_run_puts_no_password_on_a_command_line` plus das `OC_PASS`-Wrapper-Muster (T-10-03, T-10-27) |
| Zustandsdatei mit Kosten- und Instanzdaten wandert versehentlich ins oeffentliche Repositorium | Information Disclosure | `box.env` liegt ausserhalb des Arbeitsbaums, `test_the_aws_tool_keeps_the_state_out_of_the_repo` |
| Systemplatten-Protokolle einer Testinstanz werden unbesehen committet | Information Disclosure | Entscheid aus Plan 11-12: Sicherung ausserhalb des Arbeitsbaums, Repo-Aufnahme erst nach Geheimnis-Durchsicht. Bleibt so |
| Ein Zaehl-Orakel entsteht ueber die Prozessgrenze | Information Disclosure | T-02-93; siehe Befund 1.2 und Pitfall 1 |
| Ein zerstoerender Abbau nimmt die Historie mit | Denial of Service (gegen die eigene Nachvollziehbarkeit) | `FINDLING_STATE_BACKUP` als Pflichtpfad vor dem ersten zerstoerenden Aufruf |
| Security Group mit zu weitem SSH | Elevation of Privilege | SSH nur von einer /32-Adresse; `cmd_start` zieht die Regel mit `revoke` vor `authorize` nach |

**Eine neue Betrachtung, die diese Phase mitbringt:** Das Runbook wird
`docs/runbook-messbox.md` und liegt damit im OEFFENTLICHEN Repositorium. Es darf
Dateipfade und Variablennamen nennen, aber keine Werte: keine IP-Adressen des
Owners, keine Instanz- oder Volume-Kennungen, die noch leben, keine
Passwortdateiinhalte. Die Snapshot-Kennung ist unbedenklich (sie steht bereits
in mehreren committeten Dateien und ist ohne Konto nutzlos). Das gehoert als
ausdrueckliche Regel in den Kopf des Runbooks.

---

## Assumptions Log

| # | Behauptung | Abschnitt | Risiko, wenn falsch |
|---|---|---|---|
| A1 | Die 194/812- und die 62/325-Zahl stammen aus zwei verschiedenen Beobachterreihen (Statusbeobachter 120 s gegen Waechter 300 s) | Befund 4.2 | Gering. Das Runbook benennt dann die falsche Quelle; die Groessenordnung stimmt in beiden Faellen |
| A2 | Das "Vokabular-Gate archiv" ist keine Regel dieses Repositoriums | Project Constraints | Gering. Ein zu vorsichtiger Umgang kostet nichts; ein gebautes Gate waere falscher Aufwand |
| A3 | `snap-03f1d1d9ad9262704` existiert weiterhin, ist `completed` und traegt `purpose=findling-corpus-keep` | Befund 2, 3, Environment | HOCH. Faellt der Snapshot weg, ist der gesamte D-09-Hauptpfad hinfaellig und der Neuaufbau von null wird Pflicht. In Phase 12 lesend pruefen |
| A4 | Die AWS-Anmeldung in `C:/Users/Student/.findling-aws.env` ist noch gueltig | Environment | Mittel. Faellt sie aus, blockiert Phase 15, nicht Phase 12 |
| A5 | `resources.read_side()` liefert der Sonde im Container einen brauchbaren Lesezugriff, ohne den Poller zu stoeren | Code Example A | Mittel. Sonst muss die Sonde den Index selbst read-only oeffnen; das ist mehr Code, aber machbar |
| A6 | Der Wirkungszweig des Cron-Checks laesst sich aus den bestehenden Beobachtern (`96b`, `96d`) ableiten, ohne neues Werkzeug | Befund 4.1 | Mittel. Sonst braucht es eine eigene kleine Messschleife |
| A7 | NC 35 wird am 16.09.2026 final; der Zeitplan nennt das Datum selbst als "not final" | Befund 5.3 | Gering fuer den Plan, weil BEIDE Zweige (D-01/D-02 und D-03) vorher ausformuliert werden. Hoch, wenn der Plan nur einen Zweig vorbereitet |
| A8 | Der Aufbau der Maschine ist in Phase 15 in rund 2 bis 3 Stunden zu schaffen | Befund 7.2 | Mittel bis hoch. Es ist der einzige Posten des Rechenblatts ohne Messwert. Das Rechenblatt sollte ihn als Schaetzung KENNZEICHNEN |

---

## Open Questions

1. **Wird `98b-sprachfaelle.sh` ersetzt oder erweitert?**
   - Bekannt: Die Hausregel verlangt eine neue Datei in einem neuen
     Laufverzeichnis fuer eine GEFAHRENE Fassung. `98b` ist am 10.09. gefahren
     worden und traegt Rohdaten unter `2026-09-werkzeugfixe/rohdaten/`.
   - Unklar: Der Waechter mit sha256 haengt heute nur an `98-sprachfaelle.sh`,
     nicht an `98b`. Ob `98b` damit formal ebenfalls unantastbar ist, sagt der
     Test nicht.
   - Empfehlung: Wie unantastbar behandeln. Neue Datei, neues Laufverzeichnis;
     das ist die Lesart, die der Bericht vom 10.09. selbst formuliert.

2. **Wo liegt die Sonde: Laufverzeichnis oder `scripts/ops/`?**
   - Bekannt: Laufverzeichnis entspricht dem Muster und der Belegregel; es ist
     aber nicht ruff-/pyright-geprueft und nicht von `python.yml` getriggert.
     `scripts/ops/` waere geprueft, ist aber fuer wiederverwendbares Werkzeug
     gedacht und traegt keine Laufbindung.
   - Empfehlung: Laufverzeichnis, plus `docs/measurements/**` in die Pfadliste
     von `python.yml`, plus `NARROW_SCOPE_DIRS` ergaenzen. Das holt beide
     Vorteile.

3. **Welche Schwellen-Semantik wird verbindlich?**
   - Drei Kandidaten: `bestand` gegen eine noch zu waehlende Zahl,
     Fensterbelegung gegen 64, Rang der eigenen Datei gegen 64.
   - Empfehlung: Rang gegen `MAX_RECHECKS_ABSOLUTE`, mit `bestand` und
     Fensterbelegung als begleitenden Zahlen in derselben Zeile. Nur der Rang
     beantwortet die Frage, die DI-10-02 stellt.
   - Offen bleibt: Der Rang ist erst nach Upload und Indexierung messbar. Der
     Abschnitt wandert damit in `98c` hinter die Indexierung, und die
     Reihenfolge der Abschnitte aendert sich gegenueber `98b`.

4. **Wie weit kann das Runbook in Phase 12 trockengeprueft werden?**
   - Ohne Box gar nicht laufend. Lesend pruefbar: Snapshot-Existenz, Preise
     (`aws_box.sh prices`), Tag-Landschaft (`describe-tags`).
   - Empfehlung: Diese drei lesenden Proben in Phase 12 fahren und ihre Ausgabe
     als erwartete Ausgabe ins Runbook uebernehmen. Alles andere wird als
     "in Phase 15 erstmals vollzogen" markiert.

5. **Bekommt der neue Unterbefehl auch das Mounten?**
   - `cmd_volume` endet beim Anhaengen und sagt ausdruecklich: "nitro exposes it
     as a nvme device and ignores $VOLUME_DEVICE, so find it by size on the box
     and mount it by uuid, never by name". Das Mounten ist ein Handgriff auf der
     Box und kein AWS-Aufruf.
   - Empfehlung: Unterbefehl endet wie `cmd_volume` beim Anhaengen; das Mounten
     ist ein nummerierter Runbook-Block mit erwarteter Ausgabe.

---

## Sources

### Primaer (HIGH confidence)

**Eigener Quellcode, Stand 2026-09-14:**
- `backend/src/findling/index/search.py` (`_sides`, `ranked_sides`, `candidates`,
  Fenster- und Orakel-Regeln)
- `backend/src/findling/api/diagnose.py` (Route, `origin`, D-14)
- `backend/src/findling/config.py` (`SEARCH_RRF_WINDOW=100`,
  `SEARCH_SCAN_MAX=10_000`, `VECTOR_SCAN_MAX=300`)
- `php/lib/Search/Provider.php` (`MAX_RECHECKS_ABSOLUTE=64`, `MAX_ROUNDS=3`,
  `OVERFETCH=4`, `BUDGET_SECONDS=2.5`)
- `php/lib/Service/AdminViewService.php:694-726` (`/diagnose` ohne `query`)
- `php/appinfo/info.xml:219`, `backend/appinfo/info.xml:225` (Fenster 33-35)
- `backend/appinfo/info.xml:238-328` (fuenf Routen, `/diagnose` mit ADMIN)
- `scripts/ops/aws_box.sh` (acht Unterbefehle, Saetze, Tags, Zustandsdatei)
- `backend/tests/test_ops_scripts.py:264-280` (Usage-Gate)
- `backend/tests/test_measurement_scripts.py` (weiter und enger Bereich,
  Waechter, `DRIVEN_FASSUNG_RULE`)
- `backend/tests/test_lockstep_versions.py:387` (Matrix deckt das Fenster ab)
- `.github/workflows/deploy-harp.yml:170-275` (stable35-Ast, RE-CHECK)
- `.github/workflows/python.yml:5-30, 76-114` (Pfadfilter, Lintumfang)

**Eigene Messberichte:**
- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`, Abschnitte 7, 15,
  16, 19.2 (Laufzeit, Bestand, Kosten, Deckel)
- `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md`
  (Anfahrt, 13 Schritte, Ablesestellen, Wartefristen, Abbruchpfade)
- `docs/measurements/2026-09-werkzeugfixe/README.md` (Fremdbestand 26,
  Nachfolge-Messgroesse woertlich)
- `docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh`
  (dreiwertiges Urteil, Exit-Codes, `occ`-Wrapper)
- `docs/measurements/2026-09-werkzeugfixe/skripte/72-fremdbestand.py`
  (Gegenprobe zum Antwortdeckel)
- `docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`
  (Abbau, Snapshot-Inhalt, `box.env`-Abschrift, Wiederaufbau-Hinweise)
- `docs/performance.md:158` (DI-10-04, Cron-Wirkung)
- `.planning/milestones/v1.1-phases/11-.../11-12-SUMMARY.md` (Abbau vollzogen)
- `.planning/milestones/v1.1-phases/11-.../deferred-items.md` (DI-10-04,
  DI-11-01, DI-11-05, DI-11-06)

**Eigene Proben in dieser Sitzung (2026-09-14):**
- tantivy 0.26.0 aus `backend/.venv`: `SearchResult.count` existiert zur
  Laufzeit, liefert 300 bei 300 passenden Dokumenten und `limit=10`
- Dateisystem: `C:/Users/Student/.findling-loadtest/` ohne `box.env`
- Werkzeugverfuegbarkeit: aws-cli 2.36.39, gh 2.92.0, jq 1.8.1, uv 0.11.7,
  python3 3.13.1

**GitHub API (2026-09-14):**
- `repos/nextcloud/server/releases`: v35.0.0rc4 (prerelease), v34.0.4 (release)
- `repos/nextcloud/server/branches/stable35` und
  `repos/nextcloud/app_api/branches/stable35`: beide vorhanden

### Sekundaer (MEDIUM confidence)

- `github.com/nextcloud/server/wiki/Maintenance-and-Release-Schedule`:
  NC 35 final am 2026-09-16, ausdruecklich "date not final"
- `.planning/research/PITFALLS.md`, Pitfalls 15 bis 18 (Deckel,
  Vergleichbarkeit, Aufwaermphase, Werkzeug); Zahlen dort teils ohne
  Rohdaten-Belegstelle, siehe A1
- `.planning/research/SUMMARY.md`, Disagreement 4 (Box-Budget-Konflikt)
- `.planning/research/ARCHITECTURE.md`, Teil C (Wiederverwendung aus
  `scripts/ops` und `docs/measurements`)

### Tertiaer (LOW confidence)

- Die Vermutung, dass ein rc5 am 17.09.2026 der Kadenz entspraeche, ist eine
  Extrapolation aus vier Datumsangaben und keine Quelle
- Der Zeitaufwand des Maschinen-Handaufbaus in Phase 15 ist nirgends gemessen

---

## Metadata

**Konfidenz je Bereich:**

| Bereich | Stufe | Begruendung |
|---|---|---|
| Messgroesse und Skript-Design | HIGH | Alle Aussagen am Quellcode mit Datei:Zeile belegt; `SearchResult.count` empirisch gegen die installierte Fassung gemessen |
| `aws_box.sh` und Snapshot-Weg | HIGH fuer den Ist-Zustand und die Tag-Falle, MEDIUM fuer den Snapshot selbst | Ist-Zustand am Skript gelesen; der Snapshot ist in dieser Sitzung nicht gegen die AWS-API geprueft worden (A3) |
| Runbook-Umfang | HIGH | Der Abbau ist doppelt belegt (Plansummary und Dateisystem-Probe); der Snapshot-Inhalt steht in der Rohdatei des Abbaus |
| Cron-Befund | HIGH fuer den Befund, MEDIUM fuer die Zahlenreihe | `docs/performance.md` ist die Primaerquelle, die beiden Reihen A1 sind ungeklaert |
| stable35 | HIGH | Releasestand und Zweige ueber die GitHub-API geprueft, Zeitplan zitiert, Fensterstand am Baum gelesen |
| Deckel-Rechenblatt | MEDIUM | Alle Posten sind belegt, aber sie stammen aus genau einem Lauf, und die neuen Posten der Phase 15 sind Schaetzungen (A8) |
| Gate-Landschaft | HIGH | Alle drei betroffenen Tests gelesen; die Pfadfilter-Luecke ist aus der Workflow-Datei direkt ablesbar |

**Research date:** 2026-09-14
**Valid until:** 2026-09-21 fuer den NC-35-Anteil (der Releasestand aendert sich
in diesem Fenster), 2026-10-14 fuer alles Uebrige (eigener Baum, stabil)
