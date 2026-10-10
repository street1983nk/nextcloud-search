---
phase: 30-owner-tor-schema-und-tschechisch
audited: 2026-10-10
diff: cfe0c33a..7310f9b3
files_reviewed: 54
findings:
  critical: 0
  high: 0
  medium: 0
  low: 3
  total: 3
status: issues_found
---

# Phase 30: Security-, Bug- und Performance-Audit

**Umfang:** `git diff cfe0c33a..7310f9b3` (Basis = Elternteil von 094885e3, dem
ersten Commit mit "(30-01)"; 29 Commits), 54 Dateien, 4811 Zeilen dazu, 631 weg.
Produktiver Code: `config.py`, `api/resources.py`, `store/repo.py`,
`index/analyzer.py`, `index/open.py`, `index/schema.py`, `index/rebuild.py`
(nur Kommentar), `index/stopwords_cs.py` (neu, generiert), `query/rewrite.py`,
dazu `backend/Dockerfile`, zwei Workflows (`deploy-harp.yml`, `docker.yml`),
`REUSE.toml`, `.gitattributes`, `THIRD-PARTY.md`, beide `info.xml`. Der Rest
sind Tests, Doku, Planung und das Dev-Skript `scripts/dev/czech_stopwords.py`.

Die Grenzproben stehen als Regressionstests in
`backend/tests/test_phase30_audit.py`; jede Probe mit einer Positivkontrolle,
die zeigt, dass sie auf das Geprüfte reagiert und nicht auf etwas anderes.

## Security

### S1 OCR-Argumentgrenze T-03-502 mit ces

- `config.py:430` `OCR_LANGUAGE_ALLOWLIST` hat zehn Einträge, `ces` gepaart mit
  `backend/Dockerfile:350` (`tesseract-ocr-ces=1:4.1.0-2`) und der Bauprüfung
  `Dockerfile:362` (`tesseract --list-langs 2>&1 | grep -qx ces`).
- `_ocr_languages` (`config.py:1492` bis `1530`) zerlegt an `+`, senkt jeden Teil
  per `.strip().lower()` (Zeile 1516) und lässt nur Allowlist-Einträge durch
  (Zeile 1519). Grenzproben gefahren
  (`test_a_manipulated_ocr_value_never_reaches_tesseract`, 12 Fälle):
  `ces+../x` -> `("ces",)`, `ces;id`, `ces deu`, `../ces`, `cze`, `ces|sh`,
  `ces$(id)`, `+` -> Standard `("deu","eng","fra")`, `ces+--psm+0` und `-l+ces`
  -> `("ces",)`, `ces++deu` -> `("ces","deu")`, `ces+ces` -> `("ces",)`. In jedem
  Fall ist jedes Element Teil der Allowlist und keines beginnt mit `-`.
- `CES` wird angenommen (`CES+Deu` -> `("ces","deu")`): Die Senkung ist im Code
  gewollt; sie kann nur auf einen Allowlist-Eintrag abbilden, und an Tesseract
  geht dieser Eintrag, nie die Schreibweise des Admins. Kein Befund.
- Positivkontrolle: Mit `ces;id` per monkeypatch IN der Allowlist kommt `ces;id`
  durch. Die Ablehnungen kommen also aus der Allowlist und aus nichts anderem.
- Aufruf als Liste: `extract/ocr.py:203`
  `[_ENGINE, "-", "-", "-l", languages, *_ENGINE_OPTIONS]`. Gefahren mit
  gefälschtem `subprocess.run`: Liste, `-l` gefolgt von `deu+ces`, kein `shell`.
  AST-Scan über alle 74 Dateien unter `backend/src/findling`: kein Aufruf mit
  `shell=` ungleich `False` (Positivkontrolle: der Scanner findet
  `subprocess.run('x', shell=True)`). Zusätzlich
  `git diff cfe0c33a..HEAD | grep '^+.*shell=True'`: leer.
- Mutation M3 (Allowlist-Prüfung in Zeile 1519 auf `if False:`): 9 Fälle rot.

### S2 Markenlogik

- `store/repo.py:161` `LEGACY_SCHEMA_STEPS = {("1","2"), ("2","3"), ("1","3")}`,
  Abfrage `repo.py:1588` als Paarmenge, kein Zahlenvergleich.
  `test_the_ratchet_carries_exactly_the_three_forward_pairs` hält die Menge exakt;
  `("3","2")`, `("2","1")`, `("3","1")`, `("4","3")`, `("3","4")`, `("2","2")` sind
  weder enthalten noch von `_schema_is_legacy` entschuldigt; `None` und
  `UNKNOWN_VERSION` ebenfalls nicht.
- Lesetor `api/resources.py:403` `QUERYABLE_SCHEMA_GENERATIONS = {"2","3"}`,
  Prüfung Zeile 420. `_of_the_marks` liefert `None` für `"1"`, `"4"`, `""`,
  fehlend, `UNKNOWN_VERSION`, `" 3"`, `"3.0"`; für `"2"` und `"3"` behält es alle
  sechs Sprachen `de,en,es,it,nl,pt` (Pflicht-Fix, kein stiller Sprachfeldverlust).
- Kein Umbau für 1.2.x/1.4.2 ohne cs: belegt durch
  `test_czech_switch.py::test_a_schema_2_stock_under_schema_3_code_is_not_rebuilt`,
  `..._with_spanish_keeps_spanish_without_a_rebuild`,
  `test_a_1_2_stock_of_schema_1_is_not_rebuilt_and_keeps_the_legacy_plan` (30-05)
  und auf echter Nextcloud durch Store upgrade 5 (Lauf 38036946762:
  `unchanged .marks.schemaVersion = 2`, `rebuildState = idle`).
- Mutationen: M1 (Rückwärtspaar `("3","2")` zugefügt) 2 Fälle rot; M2 (Lesetor
  wieder literal `!= "3"`) 3 Fälle rot.

### S3 Generator und Fremdliste

- Herkunft gegen Upstream statt gegen den Pin geprüft:
  `curl .../releases/lucene/10.5.2/.../cz/stopwords.txt` ergibt SHA-256
  `61f06aa1...ad915`, `cmp` gegen die Fixture: bytegleich.
  `git ls-files --eol`: `i/lf w/lf attr/-text`.
- `scripts/dev/czech_stopwords.py:148` prüft den SHA-256 in `build()`, bevor
  `main()` (Zeile 215 bis 220) irgendetwas schreibt. Gefahren mit drei anderen
  Manipulationen als der bestehende Test (der kippt Byte 0): Byte angehängt,
  letztes Byte gekippt, LF zu CRLF. Jeweils Rückgabe 1, und weder die
  Ausgabedatei noch ihr Verzeichnis existieren danach. Positivkontrolle: gleicher
  Aufruf auf dem Original schreibt die Datei. Mutation M5 (Ausgabe vor der
  Prüfung schreiben): 3 Fälle rot.
- Nicht im Paketbaum, nie importiert: Pfad liegt außerhalb `backend/src`; AST
  über alle Paketdateien: kein Import von `czech_stopwords` oder `scripts`, kein
  `spec_from_file_location` im Paket (Positivkontrolle: der Scanner sieht
  `import czech_stopwords`). Das Image kopiert aus `scripts/` nur
  `dev/quantize_model.py` (Test auf die COPY-Zeilen des Dockerfiles). Im Image
  nachgesehen (`ghcr.io/street1983nk/findling_backend:dev`, erzeugt
  2026-10-10T07:13Z): `find / -name stopwords_cs.py` nur unter
  `site-packages/findling/index/`, kein Generator.
- Keine Netzabfrage zur Laufzeit: AST-Importe von `stopwords_cs.py` und
  `analyzer.py` enthalten weder `urllib` noch `httpx`, `requests`, `socket`,
  `http.client`.
- Lizenz: `REUSE.toml` annotiert Fixture (Apache-2.0) und Modul
  (AGPL-3.0-or-later AND Apache-2.0); `LICENSES/Apache-2.0.txt` liegt bei.
  `reuse lint` ist lokal nicht installiert (keine Paketinstallation); CI
  Security scans 38040459964 auf 7310f9b3: "Congratulations! Your project is
  compliant with version 3.3 of the REUSE Specification". THIRD-PARTY.md trägt
  Quelle, SHA, NOTICE und Änderungsvermerk 4(b). Lücke im ausgelieferten
  Artefakt: siehe **L-30-01**.

### S4 deploy-harp und docker.yml

- `git diff cfe0c33a..HEAD -- .github/workflows/ | grep '^+.*uses:'`: leer, also
  keine neue Action.
- `${{ }}` in hinzugefügten Zeilen: nur `MATRIX_SERVER_VERSION`,
  `MATRIX_RUNNER` (deploy-harp, `env:` von Store upgrade 7) und `DIGEST`
  (docker.yml, `env:` des CZ-01-Schritts). Kein Ausdruck im Run-Text.
- Geheimnisse: Die App-Passwort-Funktion `take_app_password` in
  `rebuild-probe.sh` maskiert per `::add-mask::`, löscht die Zwischendatei und
  gibt nur die Länge aus. Wegwerfinstanz, `permissions: contents: read`, kein
  `secrets.` im Job.
- `REBUILD_VECTORS_BEFORE` geht per `GITHUB_ENV` an Store upgrade 7
  (`deploy-harp.yml:5301`), ungeprüft: siehe **L-30-03**.

## Bugs

- **KeyError über SNOWBALL_NAME:** AST-Scan des Pakets nach `SNOWBALL_NAME[...]`
  mit nicht konstantem Schlüssel: keiner (Positivkontrolle `SNOWBALL_NAME[code]`
  wird gefunden). Die sechs Zugriffe (`analyzer.py:463/472/523`,
  `open.py:185/186/195`) haben feste Schlüssel. Schleifen über Sprachcodes
  (`resources.py:437/441/564/1027/1054`, `rebuild.py:518`, `writer.py:317`,
  `main.py:847`) indizieren `BODY_FIELD`, `BODY_BOOST`, `TESSERACT_NAME`; alle drei
  tragen `cs`.
- **Sprachnormalisierung** (`test_a_language_value_with_cs_resolves_as_documented_and_never_raises`,
  10 Fälle): `cs` -> `("cs",)`, `cs,cs` -> `("cs",)`, `CS,de`, ` cs , de ` und
  `cs,de` -> `("de","cs")`, `de,en,cs` -> `("de","en","cs")`; `cz`, `cs;rm`,
  `czech`, `ces` -> `DEFAULT_LANGUAGES` mit Warnung. Für jeden aufgelösten Code
  sind `BODY_FIELD`, `BODY_BOOST` und `TESSERACT_NAME` belegt, er steht in genau
  einer der beiden Kettenarten, und der Feldplan aus diesen Marken beginnt mit den
  Körperfeldern in Schemaordnung.
- **Feldplan Schema 2 unter Schema-3-Code:** `FINDLING_LANGUAGES=de,cs`, Marken
  noch `2`/`de,en` (Umbau nicht gelaufen): Plan
  `body_de, body_en, name, title`, keine Warnung von `_probed`, Suche `Akte`
  liefert Treffer. Gegenprobe mit einer Marke, die `cs` NENNT (`2`/`de,cs`):
  `_probed` wirft `body_cs` mit genau einer Warnung aus, der Rest bleibt, die
  Suche antwortet. Sechs Sprachen auf Schema 2 behalten alle sechs Felder.
  Mutation M4 (Plan aus den Settings statt aus den Marken): 5 Fälle rot.
- **Halbgefülltes Umbauziel:** Der Fall mit Schema-2-Fingerabdruck steht in
  `test_czech_switch.py::test_a_half_filled_target_of_the_schema_2_expectation_is_discarded`.
  Neu und mit anderem fremdem Merkmal: ein Ziel DIESES Schemas, gefüllt für
  `de,en`, gewünscht `de,cs`: verworfen (Log "other version marks"), 0 Dokumente,
  neuer Fingerabdruck. Mutation M6 (`rebuild.py:1005` verwirft nie): rot.
- **Reihenfolge:** `tuple(BODY_FIELD) == SUPPORTED_LANGUAGES`, `cs` am Ende,
  `cs,de` -> `de,cs`.
- **Stoppliste nach Faltung, unabhängig nachgerechnet:** NFKD über `unicodedata`
  statt tantivy-Faltung: 172 Zeilen, 171 eindeutig, 169 gefaltet; minus
  `byt`/`jez` ist das Ergebnis in Reihenfolge gleich `CZECH_STOPWORDS_FOLDED`.
  Kein Eintrag, den die Kette nie erzeugen könnte; kein Original-Eintrag
  (klein und GROSS) erreicht über `czech_analyzer()` den Index, außer den zwei
  Ausnahmen. Die Prüftabelle im Docstring gegen die Generator-Ausgabe hält
  `test_czech_analyzer.py::test_the_review_table_covers_every_new_form_and_names_the_exceptions`.
- **Treffer nur über body_cs ohne Auszug:** gemessen, siehe **L-30-02**.
- **Schreibpfad in ein Schema-2-Verzeichnis bei abgelehntem Umbau:** Der Writer
  nimmt die Sprachen aus den Settings (`writer.py:176`), `body_cs` fällt im
  13-Felder-Verzeichnis still weg. Gleiches Verhalten wie seit 1.3 bei jeder
  Sprache im abgelehnten Umbau, nicht durch Phase 30 entstanden, Lesestelle
  fragt ohnehin nach den Marken. Kein Befund.

## Befunde

### L-30-01 (LOW): NOTICE-Zeilen von Apache Lucene fehlen im ausgelieferten Modul

- **Ort:** `backend/src/findling/index/stopwords_cs.py:12` bis `17`.
- **Beleg:** Im Image liegt das Modul unter
  `/app/.venv/lib/python3.13/site-packages/findling/index/stopwords_cs.py`;
  `grep -i "notice\|apache"` findet nur Herkunft, "License: Apache-2.0" und den
  4(b)-Satz, der auf THIRD-PARTY.md und REUSE.toml verweist. Beide Dateien sind
  nicht im Image (`ls /usr/local/share/findling/`: sechs COPYING-Dateien, keine
  für Lucene). Lucene 10.5.2 `NOTICE.txt` (abgerufen 2026-10-10) beginnt mit
  "Apache Lucene / Copyright 2001-2025 The Apache Software Foundation / This
  product includes software developed at The Apache Software Foundation". Der
  Apache-2.0-Text selbst liegt im Image unter
  `/usr/share/common-licenses/Apache-2.0` (base-files, 11358 Byte), wird aber
  nirgends genannt.
- **Warum LOW:** Lizenz, Urheber und Änderungsvermerk stehen im Modul; es fehlt
  die NOTICE-Attribution nach Apache-2.0 4(d) im verteilten Artefakt. Projektregel
  D-09: Pflichten hängen am Image.
- **Fix:** NOTICE-Zeilen und Pfad des Lizenztextes in den Moduldocstring
  (4(d) erlaubt "within the Source form").

### L-30-02 (LOW): Ein Treffer nur über body_cs kommt ohne Auszug

- **Ort:** `backend/src/findling/index/search.py:875`
  (`SnippetGenerator.create(..., FIELD_BODY_DE)`).
- **Beleg (gefahren):** Index `de,cs`, Dokument "Nájemní smlouvě o bytu v Praze
  je třeba podpis.": `smlouve` 1 Treffer, Fragment `''`; `najemni` 1 Treffer,
  `''`; Kontrolle `smlouvě` und `Praze`: volles Fragment.
- **Einordnung:** Das ist die allgemeine, dokumentierte Grenze
  `docs/language-analyzers.md:504` ("A hit found through a new language field
  alone comes back without an excerpt"), gemessen in Phase 19 für `es`. Für
  Tschechisch trifft sie die akzentlose Eingabe, also häufiger. Der Treffer geht
  nicht verloren, die Unterzeile fällt auf den Pfad zurück.

### L-30-03 (LOW): Vektordigest geht ungeprüft in GITHUB_ENV

- **Ort:** `.github/workflows/deploy-harp.yml:5301`.
- **Beleg:** `vectors_before=$(vectors_digest)`; `vectors_digest` gibt die Ausgabe
  von `docker exec ... sha256sum | cut -d" " -f1` oder `absent` zurück, und die
  Zeile schreibt sie ohne Formprüfung nach `GITHUB_ENV`.
- **Einordnung:** Die Quelle ist der Container des geprüften Commits; die Form
  ist durch `sha256sum | cut` einzeilig hex. Der Job hat
  `permissions: contents: read` und kein Geheimnis.

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| Herkunft der Liste | curl gegen Upstream, `sha256sum`, `cmp` | bytegleich, SHA `61f06aa1...ad915` |
| Faltung der Liste | NFKD über `unicodedata` statt tantivy | 169 gefaltet, minus 2 = 167 in gleicher Reihenfolge |
| Generator-Abbruch | drei neue Manipulationen, Ausgabepfad geprüft | Rückgabe 1, keine Ausgabe; Original schreibt |
| OCR-Grenze | 12 Grenzwerte, Allowlist-Positivkontrolle, gefälschter `subprocess.run`, AST-Scan | alles in der Allowlist, Liste, kein Shell |
| Ratsche und Lesetor | exakte Paarmenge, 6 Gegenpaare, 7 Marken | nur Vorwärtspaare, nur 2 und 3 |
| Halbgefülltes Ziel | Ziel gleichen Schemas, fremde Sprachen | verworfen |
| Feldplan Schema 2 | Settings `de,cs` gegen Marken `de,en`, Gegenprobe Marke `de,cs` | kein `body_cs` gefragt, Treffer |
| Trennschärfe der Proben | sechs Mutationen M1 bis M6 an `src`/Generator, je zurückgedreht | jede Mutation rot (2, 3, 9, 5, 3, 1 Fälle) |
| Auszug für cs | Index `de,cs`, vier Fragen | L-30-02 bestätigt |
| Image | `docker run` auf `findling_backend:dev` | `ces` gelistet, Generator fehlt, Modul ohne NOTICE |
| REUSE | CI-Lauf 38040459964 (lokal kein `reuse`) | konform 3.3 |
