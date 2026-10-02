---
phase: quick-261002-cvf
plan: 01
type: tdd
wave: 1
depends_on: []
files_modified:
  - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
  - backend/tests/test_v14_zelle.py
autonomous: true
requirements: [T-28-03, D-28-06]
must_haves:
  truths:
    - "Das Zaehltor besteht mit den Lauf-5-Zahlen (vorrat 3535, eingebettet 1465, 41 fremde Altzustaende in oc_findling_file_state): summe 5000, nicht 5041"
    - "Frische skipped/failed-Zustaende von Teilkorpus-Dateien der laufenden Zelle zaehlen mit; Altzustaende (fremde UND eigene Teilkorpus-Zustaende einer Vorzelle) zaehlen nie"
    - "Ein echtes Defizit fuehrt weiter zu Abbruch 71, auch wenn globale Altzaehler die Luecke exakt fuellen wuerden (Lauf-2-Kalibrierfalle)"
    - "Vollkorpus-Zellen (ZELLE_KORPUS=voll) beruehren die Datenbank nicht"
  artifacts:
    - path: "docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh"
      provides: "zaehlmarke vor dem Trigger, teilkorpus- und zellscharfe Frischzaehlung am Zaehltor"
      contains: "zaehlmarke"
    - path: "backend/tests/test_v14_zelle.py"
      provides: "psql-Zweig im Docker-Stub, Lauf-5-Belegtest, Maskierungstest, angepasste Zaehltor-Tests"
      contains: "STUB_FRISCH_SKIPPED"
  key_links:
    - from: "docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh"
      to: "nextcloud-aio-database (psql)"
      via: "sudo docker exec, SQL gegen oc_findling_file_state JOIN oc_filecache"
      pattern: "updated_at"
    - from: "docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh"
      to: "01-teilkorpus.py zaehltor"
      via: "summe als Argument, Werkzeug unveraendert"
      pattern: "zaehltor"
---

<objective>
Das Zaehltor der Teilkorpus-Zellen (T-28-03, exakt 5000) zaehlt heute die GLOBALEN
Zaehler uebersprungen/fehlgeschlagen aus `occ findling:index`. Darin stecken 41
Alt-Endzustaende von Dateien AUSSERHALB des Teilkorpus (oc_findling_file_state,
PHP-Haelfte, ueberlebt --rm-data UND --restart; 93i raeumt nur oc_findling_queue).
Lauf 5: vorrat 3535 + eingebettet 1465 = EXAKT 5000 Teilkorpus-Dateien, +41 fremde
= 5041, Abbruch 71. Die Zaehlquelle wird teilkorpus- und zellscharf.

**Gewaehlter Weg: zeitscharfe Frischzaehlung (Kernproblem-Weg 2) kombiniert mit dem
Pfadfilter aus Weg a, als reine Harness-Aenderung in 10-zelle.sh (Option a,
Owner-Praezedenz: kein Produkteingriff).**

Mechanik: Unmittelbar vor dem Trigger (nur bei ZELLE_KORPUS=teil) liest 10-zelle.sh
eine Zaehlmarke aus der Datenbank: `max(updated_at)` ueber oc_findling_file_state.
Am Zaehltor zaehlt es statt der globalen occ-Zaehler nur Zeilen mit
`state IN ('skipped','failed') AND updated_at > zaehlmarke` UND Pfad
`files/teilkorpus/%` (Join auf oc_filecache). Formel: summe = vorrat +
frisch_uebersprungen + frisch_fehlgeschlagen + eingebettet. Das Tor selbst
(01-teilkorpus.py zaehltor, exakt 5000) bleibt woertlich unveraendert, ebenso jede
php/-Datei.

**Warum dieser Weg fuer ALLE drei Teil-Zellen (S-T-anker + St-T + L-T) korrekt
zaehlt:**

1. **Ankerzelle (Lauf-5-Beleg, 5041 -> 5000):** Vor Lauf 5 trug files/teilkorpus
   KEINEN Eintrag in oc_findling_file_state (04-Nachlese, count 0); die 41 fremden
   Altzustaende (updated_at 2026-09-30/10-01, also vor der Zaehlmarke) fallen durch
   den Zeitfilter UND den Pfadfilter. Ergebnis mit den Lauf-5-Zahlen:
   3535 + 0 + 0 + 1465 = 5000, Tor bestanden.
2. **Folgezellen (St-T, L-T):** Nach einer erfolgreichen Zelle tragen die
   Teilkorpus-Dateien selbst Endzustaende, die --rm-data und --restart ueberleben.
   Diese Altzeilen haben updated_at <= Zaehlmarke und zaehlen nicht, obwohl sie
   unter files/teilkorpus liegen. Jede Datei zaehlt genau einmal: solange ihre
   Zeile alt ist, steckt sie im Vorrat (oder ist eingebettet); wird die Zeile
   waehrend der Zelle in-place ueberschrieben, bekommt sie ein frisches updated_at
   und wandert in die Frischzaehlung. Das Ueberschreib-Problem des Baseline-Deltas
   (Weg 1) entfaellt: eine Datei, die in Zelle 1 skipped war und in Zelle 2 WIEDER
   skipped wird, aendert den globalen Zaehler nicht (Delta 0, Unterzaehlung), aber
   ihre Zeile bekommt ein frisches updated_at und zaehlt hier mit. Die Marke wird
   unmittelbar vor dem Trigger gelesen, Minuten nach dem letzten Alt-Schreiben
   derselben Boxuhr; das strikte `>` ist damit eindeutig.
3. **Keine Doppelzaehlung mit eingebettet:** Lauf 5 bettete 1465 OCR-lastige
   Dateien ein, der globale skipped-Zaehler blieb dabei 35: frisch eingebettete
   Dateien erzeugen keine skipped/failed-Zeile, die mitzaehlen wuerde.
4. **Fremdschutz doppelt:** Die Exclusions verhindern belegt frische
   Fremdzustaende waehrend der Zelle (skipped blieb 35); der Pfadfilter deckt
   zusaetzlich eine verlorene Exclusion auf der Zaehlseite ab. Eine Leckage in
   vorrat/eingebettet liesse das Tor weiterhin scheitern, was gewollt ist.

**Warum nicht die anderen Wege:** Weg 1 (Baseline-Delta) unterzaehlt bei
Ueberschreibung (siehe Punkt 2). Weg 3 (Tor nur in der Ankerzelle) widerspricht
28-RESEARCH.md Zeile 313 ("Zaehltor: nach dem Crawl muss der Vorrat genau 5.000
Dateien kennen, sonst Abbruch der Zelle", also je Teilkorpus-Zelle) und schwaechte
die T-28-03-Mitigation je Zelle. Wege b/c (occ raeumt oc_findling_file_state bzw.
Handraeumung) sind Produkt- bzw. Zustandseingriffe, die Option a ausschliesst.
Der DB-Lesezugriff ist live validiert: die Lauf-5-Forensik lieferte die
41er-Diagnose mit genau diesem Join (07:05Z, Dateiidentitaet gegen oc_filecache).

Purpose: Die drei Teilkorpus-Zellen auf m7g.large (und spaeter die Matrix-Boxen)
koennen das Zaehltor passieren, ohne dass Altzustaende es verfaelschen; Blocker
28-07 Lauf 5 ist geschlossen.
Output: 10-zelle.sh mit zaehlmarke + Frischzaehlung, test_v14_zelle.py mit
psql-Stub und Belegtests, boxlos gruen.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
@backend/tests/test_v14_zelle.py
@docs/measurements/2026-10-abnahme-anfahrt/rohdaten/04-teilkorpus-arm.txt

<interfaces>
Schema (php/lib/Migration/Version001000Date20260816000000.php):
- Tabelle oc_findling_file_state: PK file_id (BIGINT), state (indexed|skipped|failed), updated_at (DATETIME, notnull), Index auf state.
- oc_filecache: fileid, path (relativ zur Storage-Wurzel, Teilkorpus = 'files/teilkorpus/...').

occ findling:index status() (php/lib/Command/IndexCommand.php): "Work stock" mit
scheduled/handed (vorrat_von summiert beide), danach "End states" mit indexed
(strukturell 0), skipped, failed aus FileStateService::counts() -- GLOBAL,
ungefiltert (GROUP BY state ueber die ganze Tabelle). Deshalb ist occ als
Zaehlquelle fuer skipped/failed unbrauchbar und die DB-Query noetig.

DB-Zugriff auf der Box (AIO, Postgres, lokale trust-Auth im Container):

```sh
sql='select ...'
sudo docker exec "$DB_CONTAINER" sh -c \
    'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "$1"' psql "$sql"
```

mit DB_CONTAINER="${DB_CONTAINER:-nextcloud-aio-database}". POSTGRES_USER und
POSTGRES_DB stehen in der Umgebung des DB-Containers, kein Passwort auf einer
Kommandozeile (T-28-10-Geist).

Die zwei Queries (SQL-Schluesselwoerter klein, damit der Test-Stub woertlich
matchen kann; Tabellenpraefix literal oc_, Override DB_PREFIX):

```sql
-- zaehlmarke, unmittelbar vor dem Trigger:
select coalesce(max(updated_at), timestamp '1970-01-01 00:00:00')
  from oc_findling_file_state;

-- frischzaehlung am zaehltor (marke eingesetzt, Format vorher geprueft):
select s.state, count(*)
  from oc_findling_file_state s
  join oc_filecache f on f.fileid = s.file_id
 where s.state in ('skipped','failed')
   and s.updated_at > timestamp '<marke>'
   and f.path like 'files/teilkorpus/%'
 group by s.state;
```

-At-Ausgabe der Frischzaehlung: Zeilen der Form `skipped|35` bzw. `failed|6`;
fehlende Staaten fehlen als Zeile (group by), der Parser muss auf 0 vorbelegen.

Harness-Stub (backend/tests/test_v14_zelle.py, STUB_DOCKER, exec-Zweig): docker
wird durch ein sh-Skript auf dem PATH ersetzt, das occ-Aufrufe beantwortet und
jeden Aufruf in STUB_LOG protokolliert. STUB_SCHEDULED/STUB_HANDED speisen den
Vorrat nach dem Trigger, STUB_SKIPPED/STUB_FAILED die GLOBALEN occ-Endzaehler,
STUB_EMBEDDED/STUB_INDEXED die uebersicht (STUB_PYTHON). Bestehende
Zaehltor-Tests: Zeilen 812-897 (test_cell_teilkorpus_*, ABORT_71_COUNTERS).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: RED - psql-Stub und Zaehltor-Tests auf die Frischzaehlung umschreiben</name>
  <files>backend/tests/test_v14_zelle.py</files>
  <behavior>
    Neue Stub-Umgebungsvariablen: STUB_ZAEHLMARKE (Vorgabe '2026-10-01 00:00:00'),
    STUB_FRISCH_SKIPPED, STUB_FRISCH_FAILED. Der STUB_DOCKER-exec-Zweig bekommt
    einen Fall fuer den DB-Container (Match auf nextcloud-aio-database im "$*"):
    enthaelt der Aufruf 'max(updated_at)', antwortet er mit "$STUB_ZAEHLMARKE";
    enthaelt er 'group by s.state', gibt er je gesetzter, von 0 verschiedener
    Variable eine Zeile `skipped|$STUB_FRISCH_SKIPPED` bzw.
    `failed|$STUB_FRISCH_FAILED` aus (ungesetzt oder 0 = keine Zeile, wie
    group by). Beide Aufrufe landen wie alle docker-Aufrufe in STUB_LOG.

    - Test 1 (NEU, Belegtest Lauf 5, 5041 -> 5000): ZELLE_KORPUS=teil,
      STUB_SCHEDULED=3525, STUB_HANDED=10 (vorrat 3535), STUB_EMBEDDED=1465,
      STUB_INDEXED=1465, STUB_SKIPPED=35, STUB_FAILED=6 (globale Altzaehler,
      duerfen NICHT mehr einfliessen), keine FRISCH-Variablen. Erwartung:
      returncode 0, "zaehltor bestanden 5000" in den Zellzeilen, die
      "zaehlung "-Zeile traegt "summe 5000" (nicht 5041), und eine mit
      "zaehlmarke " beginnende Zeile steht im Protokoll. Docstring nennt
      Lauf 5 (04-teilkorpus-arm.txt) als Quelle.
    - Test 2 (NEU, Lauf-2-Kalibrierfalle): wie Test 1, aber STUB_EMBEDDED=1424
      und STUB_INDEXED=1424 (echtes Defizit 41): returncode 71,
      "zaehltor verfehlt 4959 statt 5000"; die globalen Altzaehler 35+6 fuellen
      die Luecke nicht mehr.
    - Test 3 (Umbau test_cell_teilkorpus_demands_the_count_gate): die
      Endzustaende kommen jetzt aus STUB_FRISCH_SKIPPED=6 und
      STUB_FRISCH_FAILED=4; STUB_SKIPPED=35/STUB_FAILED=6 bleiben als
      Stoergroesse gesetzt und beweisen, dass sie nicht zaehlen;
      STUB_EMBEDDED=4990, STUB_INDEXED=4990: returncode 0,
      "zaehltor bestanden 5000".
    - Test 4 (Umbau ABORT_71_COUNTERS + test_cell_teilkorpus_counts_embedded_not_indexed):
      die 41 Endzustaende werden frisch (STUB_FRISCH_SKIPPED=35,
      STUB_FRISCH_FAILED=6 statt der globalen Variablen), vorrat 3528
      (3518+10), embedded 1431: 3528+41+1431=5000 bestanden; Kommentarblock
      aktualisieren (die Lauf-2-Kalibrierung summierte Altzustaende, Beleg
      Lauf 5 Punkt 4 der Nachlese).
    - Test 5 (test_cell_teilkorpus_still_fails_on_a_real_shortfall und
      test_cell_teilkorpus_ends_the_cell_on_a_missed_count sinngemaess auf die
      FRISCH-Zaehler umstellen): echtes Defizit bleibt Abbruch 71 mit der
      korrekten verfehlt-Zahl; der Wackel-Test (zaehlung-instabil) bleibt mit
      umgestellten Zaehlern bestehen.
    - Test 6 (Assert in bestehendem Voll-Test, z. B.
      test_cell_trigger_carries_the_n): ein Lauf mit ZELLE_KORPUS=voll
      (Vorgabe) erzeugt KEINEN psql-Aufruf: kein 'psql' in bench.calls().
  </behavior>
  <action>
    Stub erweitern und Tests schreiben/umbauen wie unter behavior. Reihenfolge
    TDD: erst dieser Task; der Lauf der Zaehltor-Tests MUSS danach rot sein,
    weil 10-zelle.sh noch die globalen occ-Zaehler summiert und keine
    zaehlmarke schreibt. Alt-Tests ausserhalb des Zaehltors (vorrat-tor,
    nachschub, probe, ende, kette) duerfen nicht brechen. ASCII im
    Stub-Shellcode, keine Umlaute in Code, keine Em-Dashes, kein CR. Commit
    (street1983nk, k.cherif@outlook.de, kein Claude-Trailer, NICHT pushen):
    "test(quick-261002-cvf): zaehltor erwartet teilkorpus-scharfe frischzaehlung".
  </action>
  <verify>
    <automated>PYTHONUTF8=1 uv run pytest backend/tests/test_v14_zelle.py -k "teilkorpus or zaehl" (erwartet ROT an den neuen/umgebauten Zaehltor-Tests); PYTHONUTF8=1 uv run pytest backend/tests/test_v14_zelle.py -k "not teilkorpus and not zaehl" (gruen); uv run ruff check backend/tests/test_v14_zelle.py</automated>
  </verify>
  <done>Stub beantwortet beide psql-Queries; die Verhaltenstests 1-6 stehen; Suite rot genau an den Zaehltor-Tests, sonst gruen; ruff sauber; Commit liegt lokal.</done>
</task>

<task type="auto">
  <name>Task 2: GREEN - 10-zelle.sh zaehlt teilkorpus- und zellscharf</name>
  <files>docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh</files>
  <action>
    Nur bei ZELLE_KORPUS=teil, Produkt und 01-teilkorpus.py unangetastet:

    1. Variablen-Block: DB_CONTAINER="${DB_CONTAINER:-nextcloud-aio-database}"
       und DB_PREFIX="${DB_PREFIX:-oc_}" ergaenzen.
    2. Hilfsfunktion db_lesen(): fuehrt eine uebergebene SQL-Zeile per
       sudo docker exec nach dem Muster aus dem interfaces-Block aus (psql
       -At, Benutzer und Datenbank aus der Container-Umgebung, kein Passwort
       auf einer Kommandozeile); stdout liefert das Ergebnis, ein Fehler
       liefert 'unlesbar'.
    3. Schritt trigger: VOR dem occ-Trigger (nur teil) die Zaehlmarke lesen:
       select coalesce(max(updated_at), timestamp '1970-01-01 00:00:00') from
       der file_state-Tabelle (DB_PREFIX). Format-Tor gegen die Einsetzung in
       SQL: case-Pattern, das nur Ziffern, Bindestrich, Doppelpunkt, Punkt und
       Leerzeichen zulaesst; sonst abbruch 71 mit Grund "zaehlmarke unlesbar"
       (ohne Marke ist das Tor nicht pruefbar, die Zelle darf nicht messen).
       Zeile "zaehlmarke $marke" ins Zellprotokoll.
    4. Zaehltor-Block: in der Stabilisierungsschleife direkt nach bestand_lesen
       die Frischzaehlung lesen (Query aus dem interfaces-Block mit
       eingesetzter Marke, Join auf oc_filecache, Pfad files/teilkorpus/%,
       group by s.state), Ausgabe `state|zahl` mit awk -F'|' parsen, fehlende
       Staaten auf 0 vorbelegen. Die Variablen uebersprungen und
       fehlgeschlagen speisen sich aus dieser Zaehlung statt aus
       $WORK/bestand.txt; die beiden awk-Zeilen auf bestand.txt entfallen.
       ist_zahl-Pruefung wie gehabt: nicht-numerisch ergibt summe unlesbar,
       das Zaehltor scheitert, abbruch 71 (bestehender Pfad). zaehlung-Zeile
       umbenennen in "zaehlung vorrat $vorrat uebersprungen-frisch ...
       fehlgeschlagen-frisch ... eingebettet ... indexiert ... summe ..."
       (kein anderes Skript parst die Zeile; die Umbenennung macht die neue
       Semantik in den Rohdaten sichtbar).
    5. Kopfkommentar aktualisieren: Schritt trigger erwaehnt die zaehlmarke;
       der Zaehltor-Kommentar (um Zeile 550) erklaert die Frischzaehlung in
       zwei bis drei Saetzen mit Lauf-5-Beleg (5041 = 5000 Teilkorpus + 41
       fremde Altzustaende; oc_findling_file_state ueberlebt --rm-data und
       --restart, deshalb zeit- und pfadscharf statt global). Der Hinweis
       "DIESE FASSUNG IST NICHT GEFAHREN" bleibt stehen.

    Zwaenge: POSIX sh, set -eu bleibt tragfaehig (keine ungepruefte Expansion),
    ASCII, kein CR, keine Em-Dashes. Der Vollkorpus-Pfad (ZELLE_KORPUS=voll)
    ruft db_lesen nie. Commit: "feat(quick-261002-cvf): zaehltor liest frische
    teilkorpus-zustaende statt globaler zaehler".
  </action>
  <verify>
    <automated>PYTHONUTF8=1 uv run pytest backend/tests/test_v14_zelle.py backend/tests/test_measurement_scripts.py && uv run ruff check backend/tests/test_v14_zelle.py && sh -n docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh</automated>
  </verify>
  <done>Beide Testdateien gruen (inklusive Belegtest 5041 -> 5000 und Kalibrierfallen-Test), sh -n sauber, keine CR-Zeilenenden in 10-zelle.sh, zwei lokale Commits, nichts gepusht.</done>
</task>

</tasks>

<verification>
- PYTHONUTF8=1 uv run pytest backend/tests/test_v14_zelle.py backend/tests/test_measurement_scripts.py: gruen.
- uv run ruff check backend/tests/test_v14_zelle.py: sauber.
- grep -n "zaehlmarke" docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh: Treffer im trigger-Block und im Kopfkommentar.
- git log --format='%an %ae' -2: street1983nk k.cherif@outlook.de, keine Claude-Trailer; git status zeigt nichts gepusht.
- php/ und docs/measurements/2026-10-abnahme-anfahrt/skripte/01-teilkorpus.py unveraendert (git diff leer fuer beide Pfade).
</verification>

<success_criteria>
- Der Belegtest reproduziert Lauf 5: mit vorrat 3535, eingebettet 1465 und 41 globalen Altzustaenden besteht das Tor mit summe 5000 (vorher: verfehlt 5041).
- Frische Teilkorpus-Endzustaende zaehlen (6+4+4990=5000 bestanden); Altzustaende maskieren kein Defizit mehr (4959 -> Abbruch 71).
- Vollkorpus-Zellen erzeugen keinen psql-Aufruf.
- Kein Produkteingriff; 01-teilkorpus.py zaehltor unveraendert bei exakt 5000.
</success_criteria>

<output>
Create `.planning/quick/261002-cvf-zaehltor-teilkorpus-scharfe-zaehlquelle/261002-cvf-SUMMARY.md` when done.
</output>
