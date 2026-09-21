---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 02
subsystem: testing
tags: [gate, secrets, vocabulary, docs, pytest, m-02, l-10, e-h2, auflage-a2]

# Dependency graph
requires:
  - phase: 15-messphase-eine-box-anfahrt
    provides: den Auditbefund M-02 mit den acht Familien der Gegenprobe, den Geschwisterbefund L-10 und die 58 Altfunde
  - phase: 05-store-vorbereitung
    provides: die Hausform der Textgates (test_store_metadata.py) mit Konstanten, scan-Funktionen, Anti-Leerlauf-Klausel und Selbsttests
provides:
  - backend/tests/test_public_artifacts.py als Gate ueber ALLE Dateien unter docs/, rekursiv
  - neun Geheimnisfamilien plus die Vokabularregel, je mit sauberem und mutiertem Selbsttest
  - AUSNAHMEN als Abbildung von (Pfad, Familie) auf einen eigenen Grund, ohne einen einzigen Wert
  - eine Untergrenze der Dateizahl (DOCS_FILES_FLOOR) gegen das stille Leerlaufen
affects: [16-05-bereinigung-der-altfunde, 16-12-phasenaudit, 16-13-launch-haertung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate ueber ein Verzeichnis statt ueber eine Namensliste: wer eine Datei nicht nennt, prueft sie nicht"
    - "Anti-Leerlauf in zwei Haelften: eine Untergrenze der Dateizahl gegen das verschobene Verzeichnis, Selbsttests je Familie gegen den geloeschten Rumpf"
    - "Ausnahmeliste mit Gruenden: je Eintrag ein eigener Satz, Mindestlaenge als Fall geprueft, Doppelnutzung eines Satzes als Fall verboten"
    - "Ratsche in die Gegenrichtung: ein Ausnahmeeintrag, dessen Fund verschwunden ist, macht das Gate rot und zwingt 16-05, die Liste mitzuschrumpfen"
    - "Eine Verengung eines Musters ist eine benannte Regel mit Begruendung, keine dreissig Eintraege auf der Ausnahmeliste"

key-files:
  created:
    - backend/tests/test_public_artifacts.py
  modified: []

key-decisions:
  - "Die zwei Fehlalarm-Mechanismen, die der Auditbericht selbst benannt hat, sind als benannte Regeln verengt statt als Ausnahmeeintraege gelistet: ein reiner Hexlauf ist eine Pruefsumme (36 von 37 Treffern des Audits), und ein Lauf, den Schraegstriche in lauter Stuecke unter 40 Zeichen zerlegt, ist ein Pfad (der 37. Treffer). Ohne diese zwei Regeln traegt die Ausnahmeliste 30 Dateien fuer die base64-Familie allein, und eine Liste in dieser Groesse ist keine Liste mehr, sondern Rauschen"
  - "Dieselbe Entscheidung fuer die IPv4-Haelfte des Musters der Umsetzung: Oktette ueber 255 oder mit fuehrender Null sind mit Punkten gruppierte Zahlen und keine Adresse, und die unspezifizierte Adresse, die Rueckschleife, die drei privaten Bereiche, der Link-Local-Bereich und alles ab 224 nennen keine Maschine dieses Kontos. Beides steht woertlich in der Erklaerung der neun Treffer des Audits; ohne die Verengung fiele das Gate auf 58 Dateien statt auf 19"
  - "Ein Wert, der mit einem Dollarzeichen beginnt, ist beim Schluesselwort-mit-Wert kein Fund: er nennt die Herkunft und traegt sie nie. Das nimmt eine der elf Dateien von der Liste und erklaert die anderen zehn besser"
  - "Die Gruende der Ausnahmeliste sind englisch, obwohl die Familiennamen deutsch sind: eine Zeichenkette in einem Python-Modul ist Code, und echte Umlaute gehoeren nach der Projektregel in deutsche Prosa und nie in Code. Deutsch ohne Umlaute waere die dritte Variante und die schlechteste"
  - "Das Gate laeuft in einem eigenen Fall ueber sich selbst. Die acceptance_criteria haben einen Probelaufhinweis im Kommentar verlangt; ein Fall ist dasselbe Versprechen, nur gehalten. Er hat waehrend des Baus zweimal zugeschlagen und beide Male eine Musterprobe erwischt, die das Modul sonst getragen haette"
  - "Die Vokabularregel liest die englische Endung und nicht den Stamm: getroffen ist jede Form, der kein e folgt. Das ist Entscheid E-H2 mechanisch gemacht und nimmt in Kauf, dass der deutsche Plural mit der englischen Form zusammenfaellt; der dritte Selbsttest sagt genau das aus"

patterns-established:
  - "Zehn Familien, eine Ausnahmeliste, ein Report-Satz: ein Fund heisst Pfad plus Familie und nie ein Wert"
  - "Eine Zahl mit Zaehldatum im Kommentar ist die Form, in der eine Untergrenze in diesem Repositorium steht"

requirements-completed: []
requirements-partial:
  - "A2: die Geheimnisregel laeuft ab jetzt als Gate ueber docs/, und der Bestand steht benannt statt verschwiegen. Die zweite Haelfte der Auflage, die Bereinigung der redigierbaren Dateien, ist Plan 16-05"

# Metrics
duration: 70 min
completed: 2026-09-21
---

# Phase 16 Plan 02: Geheimnis- und Vokabular-Gate ueber docs/ Summary

Die Geheimnisregel dieses Projekts hat zum ersten Mal ein Gate: `backend/tests/test_public_artifacts.py` liest jede Datei unter `docs/` rekursiv, prüft sie gegen neun Musterfamilien und die Vokabularregel, und trägt jeden heutigen Fund als benannte Ausnahme mit eigenem Grund, so dass es an dem Tag grün entsteht, an dem es gebaut wird.

## Was gebaut wurde

**Ein Gate über ein Verzeichnis, nicht über eine Namensliste.** Befund M-02 in einem Satz: die Regel war nirgends als Gate gefahren, sondern je Plan als Suche über die Dateien, die der Plan selbst nannte. Wer eine Datei nicht nennt, prüft sie nicht. Das neue Modul geht `docs/` rekursiv ab, heute 389 Dateien, und die Datei, die morgen dazukommt, wird an dem Tag geprüft, an dem sie entsteht.

**Neun Familien plus die Vokabularregel**, je als eigene benannte Konstante mit einem Kommentar, der sagt, was sie sucht und woran sie es erkennt: `pem-privatschluessel`, `ssh-schluesselmaterial`, `aws-zugangskennung`, `aws-ressourcenkennung`, `rechnername-der-box`, `schluesselwort-mit-wert`, `ipv6-adresse`, `base64-block-ab-40`, das Muster der Umsetzung aus den Plänen 15-09 bis 15-14, und als zehnte Regel `vokabular`.

**Zwei Anti-Leerlauf-Klauseln.** `DOCS_FILES_FLOOR = 380` mit dem Zähldatum daneben fängt das verschobene oder geleerte Verzeichnis; ein sauberes und ein mutiertes Muster je Familie fangen den gelöschten Rumpf. Das saubere Muster wird gegen **alle** Familien gehalten, nicht nur gegen die eigene, weil ein Muster, das auf die saubere Probe des Nachbarn feuert, auf 389 Dateien gewöhnlicher Prosa feuern wird.

**Eine Ausnahmeliste mit Gründen.** 49 Einträge, Schlüssel ist `(Pfad, Familie)`, jeder Eintrag trägt seinen eigenen Satz. Drei Fälle halten sie ehrlich: kein Grund unter 20 Zeichen, kein Satz zweimal benutzt, und die ganze Liste besteht ihrerseits das Geheimnis-Gate, zitiert also keinen einzigen Wert. Ein vierter Fall verbietet den veralteten Eintrag: verschwindet ein Fund, wird das Gate rot, bis die Zeile mitgeht. Das ist die Ratsche, an der Plan 16-05 die Liste schrumpfen muss statt sie stehen zu lassen.

**Das Gate läuft über sich selbst.** Alle Präfixe, Schlüsselwörter, der gesperrte Stamm und jede Musterprobe sind aus Teilstücken zusammengesetzt, damit das Modul nicht trägt, was es fernhält. Zwei Fälle prüfen das: einer über die ganze Datei, einer eigens für den gesperrten Stamm.

## Der Bestand, den das Gate heute sieht

| Familie | Dateien mit Fund |
|---|---:|
| `pem-privatschluessel` | 2 |
| `ssh-schluesselmaterial` | 0 |
| `aws-zugangskennung` | 0 |
| `aws-ressourcenkennung` | 10 |
| `rechnername-der-box` | 0 |
| `schluesselwort-mit-wert` | 10 |
| `ipv6-adresse` | 0 |
| `base64-block-ab-40` | 2 |
| `muster-der-umsetzung` | 19 |
| `vokabular` | 6 |

Das ist der Bestand aus den Phasen 5 bis 12, den Befund M-02 mit "58 Werte in 18 Dateien" beschreibt; die Dateizahl fällt hier höher aus, weil das Gate je Familie zählt und eine Datei in mehreren Familien stehen kann. Die Vokabularzahl bestätigt L-10 von der anderen Seite: 116 Vorkommen des Stamms in 17 Dateien, davon 45 in deutschen Formen in 6 Dateien, und die Differenz ist genau die englische Endung.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - fehlende kritische Funktionalitaet] Zwei Musterverengungen statt einer unbrauchbar langen Ausnahmeliste**

- **Found during:** Task 1, beim ersten Lauf über `docs/`
- **Issue:** Die Familien `base64-block-ab-40` und `muster-der-umsetzung` in der Wortlautfassung des Auditberichts finden 1.561 Treffer in 98 Dateien beziehungsweise 317 Treffer in 58 Dateien. Der Plan verlangt, jeden heutigen Fund einzeln mit eigenem Grund auf die Ausnahmeliste zu setzen; bei 98 Dateien für eine einzige Familie wäre die Liste länger als das Gate und würde jede echte Aussage begraben. Eine Ausnahmeliste dieser Größe ist die Vorstufe der stillen Abschaltung, die der Plan ausdrücklich verhindern will.
- **Fix:** Die beiden Fehlalarm-Mechanismen, die der Auditbericht selbst in Prosa erklärt, sind als benannte Regeln mit Begründung in den Code gezogen: `RUN_IS_A_CHECKSUM` (reiner Hexlauf, 36 der 37 Audittreffer waren sha256-Summen) und `run_is_a_path` (Schrägstriche zerlegen den Lauf in Stücke unter 40, der 37. Treffer war ein Pfad); für die IPv4-Hälfte `address_names_a_machine` (Oktette über 255 oder mit führender Null sind mit Punkten gruppierte Zahlen, und die reservierten Bereiche nennen keine Maschine dieses Kontos). Beide Verengungen haben je einen eigenen Fall. Danach: 2 statt 98 Dateien und 19 statt 58 Dateien, und jede der 19 ist eine echte Fundstelle oder eine benannte Versionsnummer.
- **Files modified:** `backend/tests/test_public_artifacts.py`
- **Commit:** 38ebd9d

**2. [Rule 2 - fehlende kritische Funktionalitaet] Der Fall gegen den veralteten Ausnahmeeintrag**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt eine Liste, die in 16-05 schrumpft. Nichts hätte das erzwungen: eine bereinigte Datei hätte ihren Eintrag behalten, und die Liste wäre über die Phasen gewachsen, ohne je zu schrumpfen.
- **Fix:** `test_every_exception_of_a_family_is_still_earning_its_place` hält die Gegenrichtung: ein Eintrag ohne Fund macht das Gate rot. Dazu `test_every_exception_names_a_file_that_exists` gegen den Eintrag auf eine gelöschte Datei.
- **Files modified:** `backend/tests/test_public_artifacts.py`
- **Commit:** 38ebd9d

**3. [Rule 2 - fehlende kritische Funktionalitaet] Der Probelauf ueber das Modul selbst als Fall statt als Kommentar**

- **Found during:** Task 1
- **Issue:** Die acceptance_criteria verlangen, dass das Modul sein eigenes Gate besteht, "wenn man es versuchsweise auch über sich selbst laufen lässt", und dass der Probelauf im Kommentar erwähnt wird. Ein Probelauf, den niemand wiederholt, ist eine Behauptung über einen vergangenen Stand der Datei.
- **Fix:** `test_this_gate_passes_its_own_rule` und `test_the_blocked_term_stands_in_this_module_only_as_an_assembled_stem`. Beide haben während des Baus zugeschlagen: die erste auf eine Adressprobe, die zweite wäre auf die englische Vokabularprobe angesprungen, wenn sie nicht an derselben Stelle geteilt worden wäre wie die deutsche.
- **Files modified:** `backend/tests/test_public_artifacts.py`
- **Commit:** 38ebd9d, 1f25a74

### Bewusste Abweichungen ohne Regelbezug

**Die Ausnahmeliste umfasst 49 Eintraege, nicht 58.** Der Plan spricht von den "58 Altfunden aus 18 Dateien". 58 ist die Zahl der **Werte**, die das Audit gefunden hat, nicht die Zahl der Eintraege: die Liste dieses Gates ist nach `(Pfad, Familie)` geschluesselt, und eine Datei mit sechs Kennungen derselben Familie bekommt einen Eintrag und nicht sechs. Ein Eintrag je Wert haette bedeutet, die Werte zu zaehlen oder zu zitieren, und beides verbietet der Plan an derselben Stelle.

**Task 1 und Task 2 liegen in derselben Datei, aber in zwei Commits.** Task 2 traegt nur die Vokabularregel: den Stamm, die Reichweite E-H2 als Kommentarblock, den Zweig im Scanner, die drei Proben, die zwei Faelle und die sechs Ausnahmeeintraege.

## Auth Gates

Keine.

## Gate-Protokoll

| Gate | Ergebnis |
|---|---|
| `pytest tests/test_public_artifacts.py -q` | 50 bestanden |
| `pytest tests/test_public_artifacts.py -q -k "vokabular or blocked"` | 5 bestanden, 45 abgewaehlt |
| `ruff check` | All checks passed |
| `ruff format --check` | 1 file already formatted |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` | 0 errors, 0 warnings, 0 informations |
| `vulture src tests --min-confidence 80` | keine Ausgabe |
| volle Suite `pytest -q` | **2.444 bestanden / 15 uebersprungen** in 207,8 s |

**Die Skipzahl ist unveraendert.** Der Stand vor diesem Plan war 2.394 bestanden / 15 uebersprungen (Ist-Stand nach 16-01, festgehalten in STATE.md); dazu kommen die 50 Faelle dieses Moduls, also 2.444 / 15. Keine neue Auslassung.

## Was dieser Plan nicht liefert

- **Die Bereinigung.** Entscheid E2 sagt "Bereinigen + Restliste"; dieser Plan liefert die Restliste und das Gate, das sie traegt. Die redigierbaren Dokumente (`install-check.md`, `dev-setup.md`, `admin-page.md`, `performance.md`, `runbook-messbox.md`, die Berichte der Messungen) verlassen die Liste in Plan 16-05, und der Fall gegen den veralteten Eintrag zwingt dazu, ihre Zeilen mitzunehmen.
- **Eine Aussage ueber andere Verzeichnisse.** Die Reichweite ist `docs/`, weil M-02 ueber `docs/` gefahren wurde. `.planning/`, `scripts/` und `testdata/` haben dieses Gate nicht.
- **Eine Aussage ueber die Historie.** Alte Commit-Kennungen bleiben gueltig, die Werte stehen weiter in der Historie. Das ist Entscheid E2 und die Owner-Regel vom 25.08.2026.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche. Das Modul benutzt `re` und `pathlib` aus der Standardbibliothek, liest ausschliesslich, und keine neue Abhaengigkeit kommt hinzu (T-16-SC).

## Self-Check: PASSED

- `backend/tests/test_public_artifacts.py` vorhanden
- `.planning/phases/16-haertung-und-store-einreichung-v1-2-0/16-02-SUMMARY.md` vorhanden
- Commit `38ebd9d` in der Historie
- Commit `1f25a74` in der Historie
- kein gesperrtes Wort, kein Em- oder En-Dash in dieser Datei
