---
phase: 22-messanfahrt-bl-f03
audited: 2026-09-26
tree: a2757ebd67792d4ea4c63bca6a29d56d2c7a2c62
commit: 79b523024ebe559da6246af506ceab82bf8dd690
scope: "git diff fee701f..HEAD, 236 Dateien: Messwerkzeuge unter docs/measurements/2026-09-v13-messung/skripte, 187 Rohdateien, scripts/ops (drei neue Abtaster), .github/workflows/measure.yml und probe-92d.yml, Tests, docs/performance.md, docs/runbook-messbox.md, docs/language-analyzers.md"
findings:
  critical: 0
  high: 0
  medium: 0
  low: 8
  total: 8
status: no_medium_or_above
fixed: [L-22-01, L-22-02]
still_open: [L-22-03, L-22-04, L-22-05, L-22-06, L-22-07, L-22-08]
preexisting: [V-22-01]
---

# Phase 22: Security-, Bug- und Performance-Audit

**Umfang:** die Pläne 22-01 bis 22-11 der Messanfahrt BL-F03, gelesen gegen den
Baum von Commit `79b5230`. Der Bericht liegt nach der Owner-Regel vom
15.08.2026 vor der Abnahme der Phase und folgt der Form von
`docs/audits/2026-09-phase-18/README.md`. Die Überschriften stehen ohne
Umlaute, weil Prüfungen und Verweise auf sie zeigen.

**Bilanz vorweg: kein CRITICAL, kein HIGH, kein MEDIUM, acht LOW.** Zwei LOW
sind mit Tests behoben (Commit `79b5230`), sechs stehen dokumentiert und
entschieden offen. Dazu kommt ein vorbestehender Produktbefund (V-22-01), der
nicht aus dieser Phase stammt, den die Anfahrt aber auf der Zielhardware
bestätigt hat; über ihn entscheidet der Owner mit der Wahl des Weges für die
Kaltstart-Nachmessung.

Der Kern in einem Satz: **Die Phase hat den Produktcode nicht angefasst.**
`git diff --stat fee701f..HEAD -- backend/src php .github/workflows/deploy-harp.yml`
ist leer. MESS-09 ist nach der Regel E10 verworfen (README der Messung, 6.10),
`backend/src/findling/query/rewrite.py` ist unverändert, und damit entfallen
die Prüfungen, die nur bei einer dismax-Umsetzung gegolten hätten
(`allow_regexes=False`, Filterwirkung, Ratsche, lexikalische Latenz gegen die
E10-Grenze). Geprüft wurde also, was die Phase gebaut und committet hat:
Messwerkzeuge, Rohdaten, zwei Workflows, Tests und Dokumente.

**Gates am Baum `a2757eb`:** `ruff check .` grün, `ruff format --check .` grün
(147 Dateien), pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest` 0 Fehler,
`vulture src tests --min-confidence 80` grün, volle Suite 3323 bestanden und
15 übersprungen, `ruff check` und `ruff format --check` über `../scripts`
grün (14 Dateien).

---

## 1. Was geprueft wurde

| Nr. | Pfad | Womit geprüft | Beleg | Urteil |
|---|---|---|---|---|
| 1 | Produktcode unverändert | `git diff --stat fee701f..HEAD -- backend/src php .github/workflows/deploy-harp.yml` | leere Ausgabe | **Suchpfad unverändert**, kein Befund |
| 2 | Geheimnisse in allen 34.404 neuen Zeilen | Muster über jede hinzugefügte Zeile: `AKIA`/`ASIA`-Schlüssel, `aws_secret`, PEM-Kopf, Passwort- und Tokenzuweisungen mit Wert | keine Treffer außer drei PEM-Kopfzeilen im Runbook, die das Format eines Schlüssels beschreiben (`runbook-messbox.md:467-473`, vorbestehend) | **kein Geheimnis im Repo**, kein Befund |
| 3 | AWS-Kennungen in den neuen Zeilen | `i-`, `vol-`, `sg-`, `snap-`, `ami-`, `eni-`, `subnet-`, `vpc-` mit Hexteil, ARNs, EC2-Hostnamen, zwölfstellige Kontonummern | kein Treffer in den hinzugefügten Zeilen; die Snapshot-Kennung in `runbook-messbox.md` und `performance.md` ist vor dieser Phase eingeführt und in `test_public_artifacts.py` freigegeben | **keine neue Kennung**, kein Befund |
| 4 | Adressen, Domänen, lokale Pfade | IPv4-Muster, Domänen, E-Mail-Adressen, `C:/Users/...`, `/home/...` über die neuen Zeilen | nur Docker-interne 172.18.0.x, Loopback, eine Adresse aus dem Dokumentationsnetz nach RFC 5737 in einem Test, `loadtest.infranode.dev` (seit Phase 5 im Repo), `/home/ubuntu` (Standardnutzer der Box) | **keine öffentliche Adresse und kein Pfad der Entwicklungsmaschine**, kein Befund |
| 5 | Öffentliche Artefakte | `uv run pytest tests/test_public_artifacts.py` | 55 bestanden | **grün**, kein Befund |
| 6 | `--network none` der Wegwerf-Container | jede `docker run`-Zeile in `skripte/*.sh`, `scripts/ops/*`, `measure.yml` | `00-wegwerf.sh` 6 von 6, `00-lauf.sh` 1 von 1, `92d-wechsel.sh` 1 von 1, `measure.yml` 13 von 13, `ocr_slot_probe.py:44` | **lückenlos**; `probe-92d.yml` startet keinen Wegwerf-, sondern einen Nextcloud-Stapel mit `--net host` (Abschnitt 2.3) |
| 7 | Abbruchwerte 40 bis 59 | Katalog `skripte/00-ablauf.md` Abschnitt 4 gegen die Nicht-Kommentarzeilen aller Werkzeuge | jeder Wert genau einmal katalogisiert und genau in dem Werkzeug, das der Katalog nennt; bisher nur für `00-lauf.sh` bewacht | **eindeutig**, Wächter ergänzt (L-22-01) |
| 8 | Rohdateien je Block zuordenbar | jede der 187 Dateien unter `rohdaten/` gegen README, Skripte, Runbook, `performance.md` und die `beiseite`-Zeilen von `00-lauf.txt` | alle zugeordnet; die sieben `fahrt2-*` über `00-lauf.txt:67-70`, `bench-threads-*` und `w3-single.txt` über `measure.yml:565-580`, `ab-pii-92d/92d-konsole.txt` über README 6.5 | **vollständig**, kein Befund |
| 9 | Prüfungen, die ein Kommentar erfüllen könnte | alle positiven `in text`-Prüfungen der v13-Tests auf Sicherheitszusagen | drei Stellen lasen den ganzen Text statt der Codezeilen | **drei Stellen**, behoben (L-22-02) |
| 10 | Workflow `probe-92d.yml` | Quelltextlesung: Auslöser, Rechte, Pins, Schlüssel, Artefakt | `workflow_dispatch`, `contents: read`, Actions per SHA, HaRP-Schlüssel per `openssl rand` und `::add-mask::`, Artefakt ohne Zertifikate | **sauber**, ein LOW (L-22-03) |
| 11 | Workflow `measure.yml` | Quelltextlesung, `test_workflow_pins.py` | `IMAGE_REF` über `env` und Musterprüfung (`measure.yml:134-136`, `453-455`), Actions per SHA | **sauber**, kein Befund |
| 12 | Zeitpunkt der dismax-Regel | Commit-Zeitstempel gegen den ersten Boxstart | Regel in `9ee4e70` um 04:52:03Z, LaunchTime der Box 04:59:25Z, 98d gefahren 12:53:17Z | **Regel vor der Messung**, kein Befund |
| 13 | Abbau und Verbleib | `rohdaten/07-abbau.txt`, `93-kosten-und-verbleib.txt` | Instanz, Volume, Security Group, Schlüsselpaar gelöscht zurückgelesen, 17 Regionen leer, nur der Korpus-Snapshot bleibt | **nichts vergessen**, kein Befund |

---

## 2. Security

### 2.1 Die Bedrohungen T-22-01 bis T-22-48 mit Beleg

Jede Nummer aus den Plänen 22-01 bis 22-12 steht hier mit der Stelle, die sie
einlöst. "Prozess" heißt, die Mitigation ist ein Vorgehen und kein Code; der
Beleg ist dann ein Protokoll oder ein Commit.

| Nummer | Mitigation | Beleg | Urteil |
|---|---|---|---|
| T-22-01 | Anon-Abtaster liest nur Name, `RssAnon`, `VmHWM` | `test_ops_scripts.py:238-244` verbietet die Argumentliste und `/environ` im ganzen Text | eingelöst (L-22-04 zur positiven Hälfte) |
| T-22-02 | Slot-Probe druckt keinen Extraktionstext | `test_ops_scripts.py:1555-1584` pflanzt einen Text und prüft jede Ausgabezeile | eingelöst |
| T-22-03 | `image_ref` über env und Muster, Actions per SHA | `measure.yml:134-136`, `453-455`; `test_workflow_pins.py` über alle Workflows | eingelöst |
| T-22-04 | `--network none` im W4-Job | `measure.yml` 13 von 13 `docker run` | eingelöst |
| T-22-05 | 92d ohne `--rm-data`, Instanzzählung vor unregister | `test_v13_wechsel.py:83-91`, `:94` | eingelöst |
| T-22-06 | 92e: Umgebungsdatei 600, nur Namen | `test_v13_wechsel.py:262-279` (statisch) und der Verhaltenstest mit gepflanztem Geheimnis | eingelöst |
| T-22-07 | 90e nur Endung und Kennung | `90e-einzelliste.json`: 50 Einträge ohne Pfad; `test_public_artifacts.py` | eingelöst |
| T-22-08 | 90e `mode=ro`, kein schreibendes SQL | `test_v13_wechsel.py:598-606` (Literal plus AST über alle Zeichenketten) | eingelöst |
| T-22-09 | 91m nur Route, `innerMs`, `ceilingMs`, Zeit | `test_v13_wechsel.py:845` (`prints_no_user_data`) | eingelöst |
| T-22-10 | 98d nur Nummern, Klassen, Kennungen, Kennzahlen | `test_dismax_probe.py:230` | eingelöst |
| T-22-11 | 94c/95c Passwort nur aus Datei, `curl -K` | `test_v13_zyklen.py:159-165`, `test_v13_ablauf.py:1041-1046`, Gate `passwords_on_a_command_line` | eingelöst |
| T-22-12 | kein Neubau zwischen C1 und C2 | `test_v13_zyklen.py:41` (`REBUILDS`) | eingelöst |
| T-22-13 | Typwechsel: Zugangsdaten nur aus der Umgebung, nie gedruckt | `test_v13_wegwerf.py:377-397` | eingelöst |
| T-22-14 | Rückfallkette endet auf m7g.large, Timer neu | `test_v13_wegwerf.py:448-470`; README 6.7 (Timer 14:45:42Z vor Deckelende 14:46:56Z) | eingelöst |
| T-22-15 | Vorprüfung `stop`, sonst 52 | `test_v13_wegwerf.py:399-416`; `rohdaten/00-typwechsel.txt` `shutdown-verhalten stop` | eingelöst |
| T-22-16 | `--network none` und synthetischer Scan | `test_v13_wegwerf.py:93-104` (jetzt nur Codezeilen, L-22-02) | eingelöst |
| T-22-17 | Timer beim Start, Rücklesen, 55 | `test_v13_ablauf.py:217`, `:288`; `rohdaten/00-timer.txt` | eingelöst |
| T-22-18 | Laufwerte und Passwortdatei außerhalb des Repos, 600 | `test_v13_ablauf.py:100-194`, `chmod 700 "$WORK"`; Scan Nr. 4 ohne Pfad der Entwicklungsmaschine | eingelöst |
| T-22-19 | Altverzeichnisse sauber, sonst 54 | `test_v13_ablauf.py:304` | eingelöst |
| T-22-20 | `test_public_artifacts.py` vor Rohdaten-Commits | 55 bestanden am Baum `a2757eb` | eingelöst |
| T-22-21 | UTC-Stempel je Block | `rohdaten/00-lauf.txt` (Tabelle README 6.6), `test_v13_ablauf.py` Prüfung `"$1-ende $(utc)"` | eingelöst |
| T-22-22 | Owner-Checkpoint vor dem Push | Prozess: Pushes der Phase 22 vom Owner freigegeben (Checkpoints 22-06 bis 22-11) | eingelöst |
| T-22-23 | W4-Rohdaten öffentlich prüfen | `test_public_artifacts.py` | eingelöst |
| T-22-24 | Digest gegen Laufnummer der Abbildstrecke | README Abschnitt 2 (imagetools), `ab-pii-92d/92d-konsole.txt` `abbild-digest-gefordert` | eingelöst |
| T-22-25 | Generalprobe außerhalb des Repos | Scan Nr. 4: kein lokaler Pfad, keine lokale Adresse | eingelöst |
| T-22-26 | ohne `DECKEL_MINUTEN` keine Fahrt | `test_v13_ablauf.py:122-172` (leer, 0, Wort) | eingelöst |
| T-22-27 | Regel vor der Messung committet | Nr. 12 oben: `9ee4e70` 04:52:03Z vor LaunchTime 04:59:25Z | eingelöst |
| T-22-28 | Preisabfrage ohne Zugangsdaten im README | Scan Nr. 2 | eingelöst |
| T-22-29 | AWS-Zugangsdaten nie auf der Box, nie in Argumenten | Scan Nr. 2; `test_v13_wegwerf.py:345` (Typwechsel läuft nie auf der Box) | eingelöst |
| T-22-30 | SSH nur eigene Adresse /32 | `runbook-messbox.md:393`, `:428`, `:448` | eingelöst (Prozess) |
| T-22-31 | Timer aus LaunchTime, Selbstabschaltung | README 6.6: kein harter Stopp, Selbstabschaltung 13:13:39Z | eingelöst |
| T-22-32 | Instanzzählung vor jedem `--rm-data` | `test_measurement_scripts.py:1413-1452` | eingelöst |
| T-22-33 | Rohdaten öffentlich prüfen, Platzhalter vermerkt | `test_public_artifacts.py` | eingelöst |
| T-22-34 | Commits nur mit ausdrücklichen Pfaden, Box-Klon fest | Prozess; `rohdaten/40b-baumhash.txt` belegt den gefahrenen Baum | eingelöst |
| T-22-35 | destroy mit Tag-Sweep, null Ressourcen | `rohdaten/07-abbau.txt` | eingelöst |
| T-22-36 | Restdeckel vor dem Typwechsel | README 6.7: `DECKEL_REST_MINUTEN` 84 | eingelöst |
| T-22-37 | Korpus-Snapshot unverändert (accept) | README 6.8: kein Ende-Snapshot, der Snapshot bleibt | angenommen, wie geplant |
| T-22-38 | Zustandssicherung außerhalb des Repos | `runbook-messbox.md:1915-1918` | eingelöst |
| T-22-39 | `allow_regexes=False` im per-Wort-Zweig | entfällt: dismax verworfen, `rewrite.py` unverändert (Nr. 1) | nicht anwendbar |
| T-22-40 | Filter bleibt `Occur.Must` | entfällt, wie T-22-39 | nicht anwendbar |
| T-22-41 | Baumhash im selben Commit wie `rewrite.py` | entfällt, kein Produktcommit; Ratsche unverändert grün | nicht anwendbar |
| T-22-42 | Regel E10 vor der Messung | wie T-22-27; Urteil in README 6.10 in drei Wörtern | eingelöst |
| T-22-43 | Einzelliste ohne Pfade | `performance.md` Abschnitt v1.3-Anfahrt, `test_public_artifacts.py` | eingelöst |
| T-22-44 | Prüfsummen je gefahrener Fassung mit Mutationsprobe | `test_v13_gefahren.py` (46 Fälle), `DRIVEN_SUCCESSOR_FASSUNGEN` | eingelöst |
| T-22-45 | E1 bis E14 unverändert | `test_v13_ablauf.py:786-795`; README 6.12 ergänzt nur Urteile | eingelöst |
| T-22-46 | Owner-Checkpoint vor dem Push | Plan 22-12 Task 2, blockierend | offen bis zur Abnahme, gewollt |
| T-22-47 | Abhaken nur nach Owner-Angabe | Plan 22-12 Task 3 | offen bis zur Abnahme, gewollt |
| T-22-48 | Geheimnisregel über alle Phase-22-Dateien vor dem Push | dieser Abschnitt, Nr. 2 bis 5 | eingelöst |

### 2.2 Die Geheimnisregel über die Rohdaten

Geprüft wurden nicht die Dateien einzeln, sondern jede der 34.404 Zeilen, die
die Phase hinzugefügt hat (`git diff fee701f..HEAD -U0`, nur `+`-Zeilen). Das
fängt auch eine Datei, die `test_public_artifacts.py` nicht kennt. Ergebnis:
kein Schlüssel, kein Passwort mit Wert, keine AWS-Kennung, keine öffentliche
Adresse der Box. Die 48 Vorkommen von `172.18.0.9` stammen aus den
Protokollen von 92c, 92d, `90-bestand.txt` und `00-lauf-protokoll.txt`; das ist das Docker-Netz
`nextcloud-aio` auf der Box, ein privater Bereich ohne Bezug nach außen. Die
Datei `rohdaten/.claude-active` liegt im Arbeitsbaum, ist aber über
`.gitignore:36` ausgeschlossen und nicht committet.

### 2.3 probe-92d.yml

Der Workflow startet eine Nextcloud, HaRP und einen nginx mit `--net host` auf
einem flüchtigen arm64-Runner. Das ist kein Wegwerf-Container im Sinne von
T-22-16, sondern der Aufbau, gegen den 92d laufen muss, und `--net host` hat
denselben Grund wie in `deploy-harp.yml` (Kommentar über dem Schritt). Der
HaRP-Schlüssel entsteht je Lauf mit `openssl rand -hex 16` und ist maskiert,
das Artefakt sammelt Protokolle und Rohdateien, aber nicht
`${RUNNER_TEMP}/certs`. Der eine Rest steht als L-22-03.

### 2.4 Rechtegrenze

Unverändert, weil kein Produktcode geändert ist: keine Route, kein Feld, keine
Filterstelle. Die Endfilterung der Suche bleibt in PHP.

---

## 3. Bugs

### 3.1 Abbruchwerte

Der Katalog in `skripte/00-ablauf.md` Abschnitt 4 führt 40 bis 59 je genau
einmal; `test_v13_ablauf.py` prüfte das für den Katalog selbst und für
`00-lauf.sh` (54 bis 59). Ob 40 bis 53 wirklich in dem Werkzeug stehen, das
der Katalog nennt, und in keinem anderen, prüfte kein Test. Von Hand
nachgezählt stimmt es:

| Werkzeug | eigene Werte | geerbt aus v1.2 (15 bis 39) |
|---|---|---|
| `92d-wechsel.sh` | 40, 41 | 36 bis 39 wie 92c |
| `92e-umgebung.sh` | 42, 43 | |
| `90e-einzelliste.py` | 44, 45 | |
| `94c-bodensatz-zyklen.sh` | 46, 47 | 29, 31, 32, 33 wie 94b |
| `95c-kaltstart.sh` | 48 | |
| `98d-dismax-probe.py` | 49 (`TREFFERMENGE_UNGLEICH`) | |
| `00-wegwerf.sh` | 50, 51 | |
| `00-typwechsel.sh` | 52, 53 | |
| `00-lauf.sh` | 54 bis 59 | |

Die geerbten Werte in 94c tragen dieselbe Bedeutung wie in 94b; auch die
doppelte 33 (kein Indexlauf, Container neu gebaut) ist dort schon so. Der
fehlende Wächter ist L-22-01 und mit Commit `79b5230` behoben.

### 3.2 Rohdateien und Blöcke

Jede der 187 Rohdateien ist einem Block oder einem Werkzeug zuzuordnen (Nr. 8).
Die Umbenennungen der zweiten Fahrt schreibt `00-lauf.sh` selbst als
`beiseite ... nach fahrt2-...` in `00-lauf.txt`, die erste Fahrt liegt
geschlossen in `rohdaten/lauf1-tor41/`. Keine Rohdatei ist nach der Fahrt
bearbeitet: `git diff 44bba82 -- docs/measurements` ist leer (Summary 22-11).

### 3.3 Prüfungen auf Kommentartext

Die v13-Tests lesen Sicherheitszusagen fast überall über `code_of`, also ohne
Kommentarzeilen. Drei positive Prüfungen lasen den ganzen Text und wären von
einem Kommentar erfüllt worden (L-22-02). Negative Prüfungen auf den ganzen
Text (etwa `PROC_ARGUMENT_FILE not in text`) sind strenger als nötig und
bleiben so.

### 3.4 Was die Anfahrt über das Produkt gezeigt hat

Die drei verfehlten Erwartungen E4, E5 und E8 sind Messergebnisse, keine
Werkzeugfehler (README 6.12). Zwei davon haben dieselbe Wurzel im Produkt, und
sie steht als V-22-01.

---

## 4. Performance

**Suchpfad unverändert.** MESS-09 ist verworfen, der Produktcode ist nicht
geändert, die lexikalische Latenz ist also die ausgelieferte. Zur Einordnung
aus der Messung selbst (README 6.10): der Median der Summe lag bei 4,77 ms, der
Altplan bei 3,90 ms.

Die Messwerkzeuge laufen nicht im Produkt. Ihre Last auf der Box ist in den
Kosten enthalten: 2,32 h und 0,4716 USD laufend gegen den Deckel 24 h und
3,76 USD (README 6.8).

---

## 5. Die LOW im Einzelnen

### L-22-01: Der Katalog 40 bis 59 war nur für 00-lauf.sh bewacht

**BEHOBEN am 26.09.2026, Commit 79b5230.**

**Datei:** `backend/tests/test_v13_ablauf.py`

Neuer Wächter
`test_every_value_of_the_catalogue_lives_in_the_tool_it_names_and_in_no_other`:
liest aus den Nicht-Kommentarzeilen aller `skripte/*.sh` und `skripte/*.py`
jeden Endwert 40 bis 59 (`exit`, `return` oder Modulkonstante) und verlangt,
dass er genau in dem Werkzeug steht, das der Katalog nennt. Mit einer
eingesetzten `exit 42` in einem fremden Werkzeug schlägt er an (Probe von Hand,
nicht committet, weil die Werkzeuge prüfsummengeschützt sind).

### L-22-02: Drei Sicherheitsprüfungen waren durch einen Kommentar erfüllbar

**BEHOBEN am 26.09.2026, Commit 79b5230.**

**Datei:** `backend/tests/test_v13_wechsel.py` (92d `mode=ro`),
`backend/tests/test_v13_ablauf.py` (95c Suchkonto und Passwortdatei),
`backend/tests/test_v13_wegwerf.py` (Zählung `--network none` gegen
`docker run`)

Alle drei lesen jetzt nur Codezeilen; die 92d-Prüfung verlangt zusätzlich das
vollständige `sqlite3.connect(... "?mode=ro", uri=True)` statt der Endung
allein. Die Werkzeuge selbst waren richtig, nur ihr Wächter war zu weich.

### L-22-03: probe-92d.yml führt ein festes Admin-Passwort und reicht es per -e weiter

**Offen, entschieden.** `probe-92d.yml:74` setzt `ADMIN_PASS` als Literal, und
`:127` reicht es per `-e` an `docker run`, `:344` per `curl -u`. Die Nextcloud
lebt nur im Lauf auf einem flüchtigen GitHub-Runner und ist von außen nicht
erreichbar; dasselbe Muster ist in L-18-10 für `deploy-harp.yml` als LOW
entschieden. Wird MEDIUM, sobald der Workflow auf einem selbst gehosteten
Runner läuft.

### L-22-04: Die positive Hälfte von T-22-01 liest den ganzen Text

**Offen, entschieden.** `test_ops_scripts.py:240-242` prüft `RssAnon`, `VmHWM`
und `/status` im ganzen Text. Die Sicherheitszusage ist die negative Hälfte,
und die ist streng. Ein Umbau lohnt nicht, weil der Abtaster gefahren ist und
seine Rohdaten (`b1-rss-*.csv`) die drei Felder tragen.

### L-22-05: 92c endet bei einem Abbruch im Phase-B-Block mit 0

**Offen, entschieden** (deferred-items, Abschnitt 22-02). 92c ist gefahren und
prüfsummengeschützt, in 92d und 92e fängt ein fail-closed Tor dieselbe Klasse
ab. Ein Fix gehört in eine 92c-Nachfolge.

### L-22-06: Der Bodensatz schreibt MB für 2^20 Byte

**Offen, entschieden.** 94c schreibt wie 94b "MB" und meint MiB. README 6.13
und `performance.md` sagen das ausdrücklich, die Werte bleiben wie gemessen,
damit sie mit v1.2 vergleichbar sind.

### L-22-07: v1.2-Rohdatei 94b mit geklebtem Wert

**Offen, entschieden** (deferred-items, Abschnitt 22-06).
`abtastreihe-spitze-mb=11142026092103` meint 1.114 MB. Die Rohdatei bleibt
unverändert, der v1.2-Bericht zitiert den Wert nicht.

### L-22-08: Drei Testnamen und Docstrings sagen noch "never ran"

**Offen, entschieden.** `test_v13_wechsel.py:74` sowie `test_v13_zyklen.py:58`
und `:172` beschreiben den Kopfsatz der Werkzeuge vor der Fahrt. Die
Asserts prüfen nur den Kopfsatz, der byteweise bleiben muss (Prüfsumme), und
sind richtig. Das Fahrdatum steht im Bericht (Summary 22-11).

---

## 6. Vorbestehender Befund

### V-22-01: Die erste Mehrwortsuche nach einem Containerstart zeigt keine Findling-Treffer

**Nicht aus dieser Phase, auf der Zielhardware bestätigt, Owner-Entscheid.**

**Datei:** `backend/src/findling/config.py:673`
(`EMBED_IDLE_RELEASE_SECONDS = 0`), `findling.embed.engine.query_may_load`,
`php/lib/Service/ExAppService.php` (`REQUEST_TIMEOUT_SECONDS`, 1,5 s)

Mit dem ausgelieferten Standard 0 lädt die erste hybride Suche nach einem
Start die Modellgewichte selbst. Das dauert auf m7g.large länger als der
PHP-Deckel: `innerMs` 1.505 bis 1.596 gegen `ceilingMs` 1.500 in beiden
95c-Läufen (README 6.11). Nextcloud antwortet mit HTTP 200 und einer Gruppe
ohne Findling-Treffer. Das ist der Vorfall vom 10.09.2026, der allgemeine Fall
steht als Backlog-Punkt. Er erklärt E5 vollständig und die Stufe 1 von E4
(die Stufe lief 5 s nach einem Containerstart).

Nicht in dieser Phase behoben, weil die Phase keinen Produktcode ändert und
jeder Fix das Verhalten jeder Installation beim Start ändert. Der Befund ist
zugleich Weg c der offenen Nachmessung (README 6.11) und gehört, wenn der Owner
ihn wählt, vor die Nachmessung und in die Härtung von Phase 23.
