---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 10
subsystem: audit
tags: [audit, asvs, di-07-02, di-07-03, t-09-29, di-10-04, di-10-05, di-10-02, di-11-01, di-11-02, di-11-03, di-11-04, rel-01]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: der Diff der Plaene 11-02 bis 11-09 und 11-13, der Produktionscode enthaelt
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-VORENTSCHEIDE.md, Entscheid v1-a vom 10.09.2026, und 11-13-SUMMARY.md als Belegstelle des gebauten Fixes
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: DI-10-02, DI-10-04, DI-10-05, die Zahlen der Vergleichsmessung und das Formvorbild des Auditberichts
  - phase: 07-gemeinsame-embedding-engine
    provides: DI-07-02 und DI-07-03 mit ihren Zahlen
  - phase: 09-ergebnisseite
    provides: T-09-29 und die drei Entscheidungszeilen des Leerzustands
provides:
  - "docs/audits/2026-09-phase-11/README.md, der Auditbericht der Phase nach dem Schema der Phase 10"
  - "das Verdikt zu fuenf geerbten und vier in dieser Phase entstandenen Befunden"
  - "die Entscheidung ueber die vier regressiven Laststufen, die die ROADMAP dieser Phase zugewiesen hat"
  - "DI-10-05 vollzogen: die drei Saetze zu Baumhash, Digest und dev im Kopf von measure.yml"
  - "DI-11-04 behoben: der Runner steht im Artefaktnamen von deploy-harp.yml"
  - ".planning/phases/11-.../deferred-items.md in der Form der Phase 10, mit Verdikt je Eintrag"
affects: [11-11, 11-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Audit, dessen Phase Produktionscode aendert, darf den tragenden Satz des Vorgaengerberichts nicht uebernehmen, sondern muss ihn ausdruecklich widerrufen"
    - "Eine Kategorie, die nicht zutrifft, bekommt trotzdem eine Ueberschrift: eine weggelassene Kategorie ist von einer geprueften nicht zu unterscheiden"
    - "Ein fixed im Frontmatter braucht eine Belegstelle; ohne sie ist es eine Behauptung"
    - "fix_commits nennt nur die Commits des eigenen Fix-Laufs; ein fremder Lauf wird nicht als eigener ausgegeben"
    - "Zwei Kennungen fuer dieselbe Frage werden zusammengelegt statt getrennt weitergereicht (DI-10-02 und DI-11-01)"
    - "Ein Fix, der gebaut wurde und nicht gewirkt hat, wird als offen gefuehrt und nicht als Erfolg verbucht"
    - "still_open heisst benannt, entschieden und adressiert, nicht uebersehen; der Bericht sagt das an seiner Stelle"

key-files:
  created:
    - docs/audits/2026-09-phase-11/README.md
  modified:
    - .planning/phases/11-haertung-und-store-einreichung-v1-1/deferred-items.md
    - .github/workflows/measure.yml
    - .github/workflows/deploy-harp.yml

key-decisions:
  - "DI-07-02 ist LOW und wird hingenommen. Die einzige gemessene Option (die Decke heben) trifft jeden Aufruf jedes Nutzers, und die Unified Search wartet auf jeden Provider; die beiden billigen Optionen (Vorwaermen, eigener Weg fuer den ersten Aufruf) sind ungemessen. Der belegte Abbruch trat genau einmal je Containerstart bei kaltem Wirtscache auf. Wiedervorlage als Bedingung und nicht als Datum: sobald ein Lauf mehr als einen Abbruch je Containerstart belegt"
  - "DI-07-03 ist MEDIUM und in dieser Phase gebaut. Optionskennung v1-a, Datum 10.09.2026, Belegstelle 11-13-SUMMARY.md mit sieben Commits. Die Berechtigungskette ist am Diff unveraendert: MAX_ROUNDS bleibt 3, isReadable bleibt die einzige Berechtigungsfrage, reduceIds ist nicht angefasst, und Provider.php traegt im ganzen Diff keine ausfuehrbare Zeile"
  - "T-09-29 bleibt accept, aus Phase 10 uebernommen und nicht neu verhandelt, mit den Zahlen und der Wiedervorlage bei deutlich mehr als 146.171 Chunks"
  - "DI-10-05: der Baumhash ist der Beweis, der aufgeloeste Digest ist die Notiz, ein Messlauf darf gegen den wandernden Tag dev pruefen. Vollzogen im Kopf von measure.yml, weil ein beschlossener und nicht vollzogener Entscheid beim naechsten Lauf wieder als Befund erscheint"
  - "DI-10-04 wird dokumentiert weitergereicht: die Frage entscheidet nur ein neuer Volllauf (26 Stunden, rund 3 USD), der Deckel dieser Phase war 4 Stunden und 0,50 USD, und der Befund beruehrt kein Erfolgskriterium. Ziel v1.2-Messplanung mit dem Box-Wiederaufbau-Runbook"
  - "Die vier regressiven Laststufen werden fuer v1.1.0 hingenommen: die Zusage steht auf Stufe 8 und haelt mit 2.125,5 gegen 2.500 ms; die Stufen 12 und 16 rissen schon in 06-11; eine Untersuchung ohne neue Reihe waere eine Deutung und keine Ursache. Die schrumpfende Reserve (585,0 auf 374,5 ms) wird benannt und nicht kleiner gemacht"
  - "DI-10-02 wird ehrlich als offen gefuehrt. Plan 11-03 hat die Nachfolgefassung gebaut, Plan 11-06 hat sie gefahren, und die Vorpruefung misst einen Antwortdeckel (konstant 26 Treffer bei jeder Tiefe) statt des Bestands, kann die Schwelle 64 also nie erreichen. DI-11-01 ist dieselbe Frage und wird mit ihm zusammengelegt"
  - "DI-11-04 wird in diesem Lauf behoben statt weitergereicht: eine Zeile, nur ein CI-Artefaktname, kein Test liest ihn, und Plan 11-11 faehrt deploy-harp.yml auf dem Release-Tag ohnehin erneut. Der Upgrade-Block laeuft auf genau einem Ast, also trug nur eines der beiden gleichnamigen Artefakte die Beweisdateien"
  - "DI-11-03 wird NICHT gefixt, und der Grund ist technisch: das Werkzeug kann abgebrochen und leer aus seiner eigenen Sicht nicht trennen, weil die OCS-Route in beiden Faellen HTTP 200 und eine Gruppe ohne Containerteil liefert. Ein zweiter Fehlschlagname waere ein Name ohne Unterscheidungsmerkmal"
  - "L-01 ist ein neuer Befund dieses Audits: der Satz aus 11-13 ist ein binaeres Existenz-Orakel ueber den Fremdbestand. LOW und hingenommen, weil er weder Zahl noch Name noch Pfad nennt, nur auf der eigenen Ergebnisseite steht, je Anfrage einen vollen Suchlauf kostet und der Owner den Wortlaut in Kenntnis der Wirkung abgenommen hat"

patterns-established:
  - "Der Auditbericht beginnt mit derselben Frage wie sein Vorbild und beantwortet sie mit dem Diff, auch wenn die Antwort die unbequemere ist"
  - "Eine Aussage ueber Unveraendertheit wird mit einem maschinellen Schnitt belegt (grep ueber den Diff ohne Kommentarzeilen), nicht mit einem Blick"
  - "Eine Feststellung ueber Dateien im Arbeitsbaum wird mit git ls-files, git log --all und git check-ignore gefuehrt und nicht mit ls"

requirements-completed: []

# Metrics
duration: 1h05min
completed: 2026-09-11
---

# Phase 11 Plan 10: Das Audit-Gate vor der Abgabe Summary

**Das letzte Audit vor der Store-Einreichung ist gefahren, und es ist das erste dieses Milestones, das nicht sagen kann "diese Phase baut nicht": ein MEDIUM-Befund ist in der Phase gebaut, zehn LOW-Befunde sind entschieden, zwei davon in diesem Lauf behoben, vier mit Zieladresse weitergereicht, und kein Befund bleibt ohne Verdikt.**

## Die eine Frage, und warum sie diesmal anders ausgeht

Das Phase-10-Audit begann mit einer Frage und einer Antwort aus einem Wort:
ändert diese Phase Produktionscode? Dort lautete sie nein, und der ganze Bericht
ruhte darauf. Hier lautet sie **ja**:

```
git diff 721bde6..HEAD --name-only | grep -E '^(php/|backend/src/)'
```

**15 Dateien.** Acht davon gehen im Companion-Paket an jeden Nutzer: die zwei
neuen französischen Kataloge, die vier deutschen mit ihrem 174. Schlüssel, das
Template und die drei geänderten Klassen unter `php/lib/`. `backend/src/` ist
mit **null** Dateien vertreten.

Umfang: **55 Dateien, 46 Commits**, Basis-SHA `721bde6`
(`docs(state): begin phase 11 execution`, der Commit vor dem ersten Plan der
Phase, analog zu `af18542` in Phase 10).

## Was jede ASVS-Kategorie ergeben hat

| Kategorie | Urteil | Der Beleg, in einem Satz |
|---|---|---|
| **V2** Authentifizierung | nicht berührt | keine Datei nimmt eine Anmeldung entgegen; im Controller-Diff steht genau eine Methode, `nextUrl`, ohne Annotation und ohne Sitzungsabfrage |
| **V3** Sitzungsverwaltung | nicht berührt | keine Sitzung, kein Cookie, kein Token, keine Lebensdauer im Diff |
| **V4** Zugriffskontrolle | in Ordnung | `MAX_ROUNDS` unverändert 3, `isReadable()` die einzige Berechtigungsfrage, `reduceIds` nicht angefasst; `Provider.php` trägt im ganzen Diff **keine ausführbare Zeile** |
| **V5** Eingabe und Ausgabe | in Ordnung | 348 FR-Werte und -Schlüssel maschinell: **0** spitze Klammern, **0** Ampersand, **0** Platzhalterabweichungen |
| **V6** Kryptografie | in Ordnung | kein `pull_request`-Trigger, Fingerabdruck über den **DER**, `tr -d '\r'` an beiden Schlüsseln, Rückverifikation gegen das Zertifikat |
| **V14** Konfiguration und Bau | in Ordnung, ein Befund | arm64-Ast, Release-Asset-Modus ohne Fallback, alle Fremd-Actions auf Commit-SHA, HaRP als Manifestindex; L-06 am Artefaktnamen |

**Der maschinelle Schnitt, der V4 trägt**, und er ist der schärfste Satz des
Berichts:

```
git diff 721bde6..HEAD -- php/lib/Search/Provider.php \
  | grep -E '^[+-]' | grep -vE '^[+-]{3}' | grep -vE '^[+-]\s*//'
```

**Ergebnis: keine Zeile.** Aus "the four reasons" wurde "the five reasons", und
sonst hat sich kein Zeichen bewegt.

**Die V5-Zahlen im Einzelnen:** `fr.json` und `fr.js` tragen je 174 Werte, sind
Schlüssel-für-Wert gleich, und ihre Schlüsselmenge ist die von `de.json`. Fünf
Werte tragen ein Anführungszeichen, und alle fünf stehen an denselben Stellen in
`de.json`, kommen also aus dem englischen Quellstring; 50 tragen einen
französischen Apostroph. Das Escaping-Gate prüft das **Template** und nicht den
Katalog, das Dash-Gate liest die **Kataloge** seit 11-08 mit; beides steht im
Bericht, weil es die häufigste Fehlannahme dieses Repositoriums ist.

## Die Bilanz

| Schwere | Zahl | Stand |
|---|---:|---|
| CRITICAL | 0 | |
| HIGH | 0 | |
| MEDIUM | 1 | M-01 (DI-07-03), von Plan 11-13 gebaut, Belegstelle `11-13-SUMMARY.md` |
| LOW | 10 | L-01 bis L-10; zwei in diesem Lauf behoben, vier hingenommen, vier weitergereicht |

`fixed: [M-01, L-05, L-06]`, `still_open: [L-07, L-08, L-09, L-10]`,
`fix_run: 2026-09-11`, `fix_commits: ab39d37, 2e8502b`.

**Warum `still_open` nicht leer ist und das Gate trotzdem gefahren ist:** alle
vier sind **LOW**, jeder trägt Verdikt, Begründung und Zieladresse. Die
Owner-Regel vom 15.08.2026 verlangt, dass jeder Befund **ab MEDIUM** vor dem
Phasenabschluss fällt; der einzige dieser Phase ist M-01, und er ist gebaut.

## Die neun Befunde mit ihrem Verdikt

| ID | Befund | Verdikt |
|---|---|---|
| **M-01** | DI-07-03, leere Liste ohne Meldung | **gefixt** von Plan 11-13, v1-a vom 10.09.2026, sieben Commits |
| **L-01** | der neue Satz ist ein Existenz-Orakel | hingenommen, benannt, vier Feststellungen |
| **L-02** | DI-07-02, die Aufrufdecke von 1,5 s | hingenommen, Wiedervorlage als Bedingung |
| **L-03** | T-09-29, Vektorscan je Anzeigeseite | accept, aus Phase 10 übernommen |
| **L-04** | die vier regressiven Laststufen | hingenommen für v1.1.0, untersucht in v1.2 |
| **L-05** | DI-10-05, der Digest von `:dev` | **behoben**, `ab39d37`, `measure.yml` |
| **L-06** | DI-11-04, zwei Artefakte gleichen Namens | **behoben**, `2e8502b`, `deploy-harp.yml` |
| **L-07** | DI-10-04, Ursache der Mehrlaufzeit | weitergereicht, Ziel v1.2-Messplanung |
| **L-08** | DI-10-02 und DI-11-01, die Vorprüfung | weitergereicht, **DI-10-02 bleibt offen** |
| **L-09** | DI-11-02, leere Antwort ohne Spur | weitergereicht, ohne Zusatzmessung beantwortbar |
| **L-10** | DI-11-03, leer gegen abgebrochen | weitergereicht, Fix technisch nicht möglich |

### M-01, und warum `fixed` hier keine Behauptung ist

Der Entscheid steht wörtlich in `11-VORENTSCHEIDE.md`, Abschnitt V-1, Zeile 116:
**v1-a, 10.09.2026**, MEDIUM mit der von der Berechtigungskette getrennten
Abhilfe. Die Belegstelle ist `11-13-SUMMARY.md`; der Plan ist gefahren und nicht
übersprungen, seine sieben Commits stehen im Bericht namentlich, und seine
Prüfung ist in den V4- und V5-Teil aufgenommen: die Kette ist am Diff
unverändert, und der 174. Schlüssel ist in der maschinellen Durchsicht der 348
Werte enthalten.

### L-01, der Befund, den dieses Audit selbst gefunden hat

Der neue Satz sagt dem Nutzer, dass **andere** Dateien sein Wort enthalten. Das
ist ein Kanal über die Vertrauensgrenze: ein angemeldetes Konto kann Begriff für
Begriff erfahren, ob irgendein Dokument der Instanz ihn trägt. LOW, und
hingenommen, weil der Satz weder Zahl noch Name noch Pfad nennt (T-11-50), der
Kanal binär und je Anfrage einen vollen Suchlauf teuer ist, er nur auf der
eigenen Ergebnisseite steht und nicht im Suchdialog, und der Owner den Wortlaut
in Kenntnis der Wirkung abgenommen hat. Die Abhilfe wäre, den Entscheid
umzudrehen.

### L-02, DI-07-02, die Entscheidung statt der Messung

Die drei Optionen stehen im Bericht nebeneinander, mit Beleglage je Zeile: die
Decke heben (trifft jeden Aufruf jedes Nutzers, und die Unified Search wartet
auf jeden Provider; kein Platz, denn der p95 der Stufe 8 steht bei 2.125,5 ms
gegen ein Gruppenbudget von 2.500 ms), Vorwärmen (**ungemessen**), ein eigener
Weg für den ersten Aufruf (**ungemessen**). Dazu die Methodik-Korrektur aus
Abschnitt 9.2, wörtlich übernommen: gemessen ist die ganze OCS-Anfrage,
gedeckelt nur der innere Containeraufruf, und der eine belegte Abbruch
(14:05:17Z, `cURL error 28`) trat genau einmal je Containerstart bei kaltem
Wirtscache auf.

**Entscheidung: LOW.** Die Schwere folgt der Wirkung und nicht der Marge.

### L-08, der Befund, den dieses Audit ehrlich offen führt

Plan 11-03 hat die Nachfolgefassung gebaut, Plan 11-06 hat sie gefahren, und
**der Fix hat nicht getan, wofür er gebaut wurde.** Die Vorprüfung misst die Zahl
der Treffer, die die OCS-Route herausgibt, und die liegt auf der Box für jeden
Begriff bei exakt **26**, bei Tiefe 64, 200 und 2000 gleichermaßen. Die Schwelle
ist **64**, also kann die Messgröße sie nie überschreiten. Bilanz `6 von 10,
davon 0 nicht messbar`, zahlengleich mit der des 10.09. **DI-10-02 bleibt
offen**, DI-11-01 ist dieselbe Frage und wird damit zusammengelegt. Zieladresse:
ein eigener Plan ohne Box in der v1.2-Härtung. Was die Aussage trägt, ist
weiterhin `integration.yml`, Job `index-search-e2e`, Lauf 34530208024.

## Die zwei Fixe dieses Laufs

**`ab39d37`, DI-10-05 vollzogen.** Der Kopf von `.github/workflows/measure.yml`
trägt jetzt die drei Sätze: der Baumhash ist der Beweis (`baumhash:`-Zeilen und
`baumhash-gleich ja`), der aufgelöste Digest ist die Notiz, und ein Messlauf darf
gegen den wandernden Tag `dev` prüfen, weil der Digest vom Auflöse-Schritt
**mitgeschrieben** statt vorher aufgeschrieben wird. Dazu der Satz, warum das die
Auslieferung nicht lockert: `docker.yml:96` bis `:110` bricht einen Tag-Lauf ab,
wenn Git-Tag, beide `<version>` und der `<image-tag>` nicht übereinstimmen. Kein
Schritt geändert, nur Kommentar, YAML weiterhin gültig.

**`2e8502b`, DI-11-04 behoben.** `harp-logs-${{ matrix.server-version }}` wurde
zu `harp-logs-${{ matrix.server-version }}-${{ matrix.runner }}`. Seit 11-04
fahren zwei Äste `stable34`, also entstanden zwei Artefakte gleichen Namens
(13.833 und 7.825 Byte im Lauf 34546421219), und nur eines trägt die sieben
Beweisdateien des Upgrade-Blocks, weil dieser auf genau einem Ast läuft. Der
Kommentar am Schritt lässt den alten Namen für die Läufe gültig, die ihn
geschrieben haben.

## Erfolgskriterium 5, mit einer Feststellung statt einer Vermutung

Vier Dateien im Wurzelverzeichnis sehen aus wie Release-Artefakte. Geprüft, nicht
übernommen:

| Datei | `git ls-files` | Commits über den Namen (`--all`) | `.gitignore` |
|---|---|---:|---|
| `findling.tar.gz` | nicht verfolgt | 0 | Zeile 31, `*.tar.gz` |
| `findling_backend.tar.gz` | nicht verfolgt | 0 | Zeile 31, `*.tar.gz` |
| `findling.crt` | nicht verfolgt | 0 | Zeile 5, `*.crt` |
| `findling_backend.crt` | nicht verfolgt | 0 | Zeile 5, `*.crt` |

Es sind Überbleibsel einer Handprobe. Die Artefakte, die das Kriterium meint,
sind die vier Assets am GitHub-Release, und `store-submit.yml` reicht genau deren
URLs ein (Zeilen 145 bis 150: `releases/download/${TAG}`, das Signatur-Asset als
Pflicht, `POST /api/v1/apps/releases`).

## Die Lieferkette, mit der Gegenprobe gegen v1.0.3

Im Phasendiff steht **keine** Abhängigkeitsdatei. Die Gegenprobe gegen den
ausgelieferten Stand nennt `backend/pyproject.toml` und `backend/uv.lock`, und
dieser Bericht sagt, wohin das gehört: Commit `0c77b7b`
("chore(deps): bump the python-minor-and-patch group"), und
`git merge-base --is-ancestor 0c77b7b 721bde6` bestätigt, dass er **vor** dem
Basis-SHA liegt. Vier Patch-Bumps vorhandener Pakete, kein neuer Name.
**T-11-SC ist bedient.**

## Tests und Gates

**Python, lokal, am 11.09.2026 in `backend/`:**

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | **2020 passed, 15 skipped**, also genau die Grundlinie |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 121 files already formatted |
| `uv run pyright` | ohne Befund |
| `uv run vulture src tests --min-confidence 80` | ohne Befund |

**Dazu die Prüfungen des Plans:**

- `python -c "import yaml; yaml.safe_load(open('.github/workflows/measure.yml'))"`
  nach der Änderung: gültig.
- Dasselbe über `.github/workflows/deploy-harp.yml`: gültig.
- Die Frontmatter-Prüfung über die sieben Pflichtfelder: vollständig.
- `grep -c "DI-07-02\|DI-07-03\|T-09-29\|DI-10-05\|DI-10-04"` über den Bericht:
  **22**.
- Das Vokabular-Gate lokal gefahren (`test_store_metadata.py`,
  `test_admin_ui_contract.py`, 91 passed), und der Bericht ist auf den gesperrten
  Begriff, auf Gedankenstriche und auf Emojis durchgesehen: je null.

**Kein PHP-Gate nötig:** dieser Plan hat keine PHP-Datei angefasst.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktionalität] DI-11-04 in diesem Lauf behoben statt weitergereicht**

- **Found during:** Task 2, beim Entscheiden der in dieser Phase entstandenen
  Befunde.
- **Issue:** `deploy-harp.yml` steht nicht in `files_modified` des Plans. Der
  Plan sieht für DI-11-04 eine Entscheidung vor ("ob der Runner in den
  Artefaktnamen soll oder ob der Upgrade-Block ein eigenes Artefakt bekommt"),
  nicht notwendig einen Fix. Beim Prüfen stellte sich heraus, dass der
  Upgrade-Block auf **genau einem** Ast läuft (`deploy-harp.yml:2351`), also nur
  eines der beiden gleichnamigen Artefakte die Beweisdateien trägt, auf denen
  Erfolgskriterium 2 dieser Phase ruht.
- **Fix:** Eine Zeile, `harp-logs-${{ matrix.server-version }}-${{ matrix.runner }}`,
  mit einem Kommentar, der Herkunft, Zahlen und die Gültigkeit des alten Namens
  festhält.
- **Warum risikofrei:** der Name eines CI-Artefakts, kein Test liest ihn
  (`grep -rn "harp-logs"` findet außerhalb des Workflows nur Prosa), und Plan
  11-11 fährt `deploy-harp.yml` auf dem Release-Tag ohnehin erneut, sodass der
  Lauf der Abgabe eindeutige Artefakte erzeugt.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Commit:** `2e8502b`

**2. [Rule 2 - Fehlende kritische Funktionalität] Das Vokabular-Gate auf den eigenen Bericht angewandt**

- **Found during:** Task 2, vor dem Commit.
- **Issue:** Der Bericht sprach an vier Stellen vom Companion-Paket mit dem
  Begriff, den die Owner-Regel E-H2 in deutscher Prosa sperrt. Der Gate-Bereich
  ist zwar auf beide `info.xml` und `docs/store-listing.md` begrenzt, also war
  der Baum grün, aber die Regel ist eine Owner-Regel und kein Gate-Umfang.
- **Fix:** "Companion-Paket" statt des gesperrten Kompositums, und zwei weitere
  Stellen umformuliert. Ergebnis: null Vorkommen im Bericht und in der
  `deferred-items.md`.
- **Files modified:** `docs/audits/2026-09-phase-11/README.md`
- **Commit:** `74b91ea`

**3. [Rule 1 - Bug] `files_reviewed: 55` war ohne Zeitbezug nicht nachzählbar**

- **Found during:** Task 3, beim Nachziehen des Frontmatters.
- **Issue:** Die Zahl ist `git diff 721bde6..HEAD --name-only | wc -l` **vor**
  dem ersten Commit dieses Plans. Nach den Commits des Audits stimmt sie nicht
  mehr, und das Phase-10-Vorbild hat dieselbe Lücke, ohne sie zu benennen.
- **Fix:** Ein Absatz im Umfangsteil, der sagt, was die Zahl genau meint und
  welche Dateien ausdrücklich nicht darin sind.
- **Files modified:** `docs/audits/2026-09-phase-11/README.md`
- **Commit:** `2359bbe`

Keine weitere Abweichung. Kein Paket installiert (T-11-SC), keine
Architekturänderung, kein Checkpoint nötig, keine Owner-Frage entstanden: der
einzige Befund ab MEDIUM war bei Beginn des Plans bereits gebaut.

## Threat Flags

Keine. Dieser Plan führt keine Netzwerkschnittstelle, keinen Auth-Pfad, keinen
Dateizugriff und keine Schemaänderung ein; er schreibt zwei Markdown-Dateien und
zwei Workflow-Kommentare. Die sieben Dispositionen des Registers sind bedient:
T-11-40 (348 Werte maschinell durchgesehen, Zahl im Bericht), T-11-41 (V4 mit
drei Belegzeilen und dem maschinellen Schnitt), T-11-42 (V6 mit vier
Zusicherungen), T-11-43 (alle Fremd-Actions auf SHA in neun Workflows), T-11-44
(jeder Befund trägt Kennung, Schwere und Disposition; `still_open` ist ein Feld
und keine Auslassung), T-11-45 (DI-07-02 mit Zahlen und Wiedervorlagebedingung
entschieden), T-11-SC (keine Abhängigkeitsdatei im Diff, Gegenprobe gegen
v1.0.3 zeigt einen Commit vor dem Basis-SHA).

## Übergaben

- **11-11** kann sich auf zwei Feststellungen dieses Berichts stützen: die
  Signaturkette ist geprüft, bevor sie zum fünften Mal benutzt wird (V6), und
  der Versionsbump betrifft **drei** Stellen (`php/appinfo/info.xml:113`,
  `backend/appinfo/info.xml:136`, `<image-tag>` in `:230`), die `docker.yml` auf
  einem Tag-Lauf zusammenhält. Erfolgskriterium 5 hat jetzt eine Feststellung
  statt einer Vermutung. Der Release-Lauf erzeugt dank `2e8502b` eindeutig
  benannte HaRP-Artefakte.
- **11-12** erbt die Zieladresse "v1.2-Messplanung mit Box-Wiederaufbau-Runbook"
  für L-04, L-07, L-09 und L-10. Alle vier brauchen eine Box, und die Box ist
  Gegenstand von 11-12.
- **REL-01 ist NICHT abgehakt.** Dieser Plan liefert Erfolgskriterium 3, nicht
  das Requirement; das erfüllt erst die Einreichung in 11-11.

## Self-Check: PASSED
