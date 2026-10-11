# Testdateien für den .doc- und den .xls-Leser (Pläne 31-05 und 31-06, FMT-03 und FMT-04)

Drei Word-97-Dateien und zwei Excel-97-Dateien (BIFF8), geschrieben von
LibreOffice aus eigenem Inhalt. Die Suchwörter sind erfunden, damit Plan 31-12
die Dateien als Saat wiederverwenden kann. Lizenz wie das übrige Repository
(eigenes Werk, AGPL-3.0-or-later über die `**`-Annotation in `REUSE.toml`).

| Datei | Inhalt | Suchwort | SHA-256 |
|---|---|---|---|
| `word97-latin.doc` | Umlaute, typografische Anführungszeichen, Eurozeichen, weiches und geschütztes Trennzeichen | `wortquendel` | `a353da53140613930e68eb7db478bc1e531defa0610e98b916d54a40c9834845` |
| `word97-unicode.doc` | tschechischer und griechischer Text | `glyphquendel` | `0dc7e408d9a46d74cd674ea28629dae2164de624ae665d27677aef3c2eb6faee` |
| `word97-table-field.doc` | Tabelle mit zwei Zeilen und zwei Spalten, Seitenzahlfeld, festes Datumsfeld | `zellquendel` | `d662ad00e1997f8ef7944d5e449807a6bcfabbbda421971e6f3c6be728b3185c` |
| `biff8-values.xls` | zwei Blätter: Text, ganze Zahl 3, Zahl 2,5, Datum 15.03.2024, leere Zelle, Fehlerzelle `=1/0`; zweites Blatt heißt `geheimblatt` | `zellquendel`, `blattquendel` | `77c04f4d82efe8ca60ea9ec442f3b59ccc5bd872d1663bcb5ea0edabb65c7b48` |
| `biff8-far-cell.xls` | eine einzige Zelle in Zeile 65000, Spalte 200 | `fernquendel` | `eeb1697c38f926ba5d979a280fa48d8dc647e8d4eec50ea83ec226fea91aa4fb` |

## Herkunft

- Die .doc-Dateien erzeugt am 11.10.2026, die .xls-Dateien am selben Tag in
  Plan 31-06, beide mit LibreOffice 26.2.4.2 (Windows, x86-64, Build-ID
  `0229ac93fcf0d7cbc6376066c6f35021cef002dc`, für die .xls-Dateien aus
  `program/version.ini` gelesen).
- Werkzeug: `scripts/dev/make_legacy_fixtures.py`. Es schreibt die Quellen als
  flache ODF-Dateien (`.fodt` für Text, `.fods` für Tabellen) in ein
  temporäres Verzeichnis und ruft je Datei auf:

  ```
  soffice -env:UserInstallation=file:///<temp>/profile --headless --norestore \
      --convert-to "doc:MS Word 97" --outdir <temp>/out <quelle>.fodt
  soffice -env:UserInstallation=file:///<temp>/profile --headless --norestore \
      --convert-to "xls:MS Excel 97" --outdir <temp>/out <quelle>.fods
  ```

- Aufruf aus `backend/`: `uv run python ../scripts/dev/make_legacy_fixtures.py`
  (Optionen `--soffice PFAD`, `--output VERZEICHNIS`, `--only doc` oder
  `--only xls`). Plan 31-06 lief mit `--only xls`, die .doc-Dateien sind
  unverändert die aus Plan 31-05.

LibreOffice schreibt nie zweimal dieselben Bytes. Die Tests in
`tests/test_legacy_doc.py` und `tests/test_legacy_xls.py` pinnen deshalb den
SHA-256 der eingecheckten Dateien; wer das Werkzeug erneut laufen lässt, pinnt
die neuen Werte.

## Was die Dateien zeigen (gemessen)

- `nFib` 0x0101, Tabellenstrom `1Table`, je ein einziges Textstück in UTF-16:
  LibreOffice schreibt keine komprimierten 8-Bit-Stücke. Die komprimierten
  Stücke prüfen die Tests deshalb mit Dateien, die sie selbst nach [MS-DOC]
  bauen.
- `1Table` liegt bei allen drei Dateien unter 4096 Byte und damit im
  Ministrom, `WordDocument` bei `word97-latin.doc` und `word97-unicode.doc`
  ebenso (3631 Byte); bei `word97-table-field.doc` ist er mit 4143 Byte ein
  gewöhnlicher Strom. Die Tests zur MiniFAT verändern `word97-latin.doc`,
  statt eigene Dateien zu bauen.
- Das weiche Trennzeichen U+00AD steht als 0x1F im Text, das geschützte
  Trennzeichen U+2011 als 0x1E.
- Die Felder stehen als `PAGE` und `DATE \@"dd.MM.yy"` mit den Ergebnissen
  `1` und `11.10.26` im Text.
- Beide .xls-Dateien sind BIFF8 (xlrd: `biff_version` 80, `datemode` 0). Der
  `Workbook`-Strom ist mit 2538 und 1659 Byte kleiner als 4096 Byte und liegt
  damit im Ministrom; die Tests zur MiniFAT verändern `biff8-values.xls`, die
  Tests zur FAT legen denselben Strom mit `conftest.build_cfb` in die FAT.
- In `biff8-values.xls` steht das Datum als Zahl 45366.0 mit Datumsformat,
  die Fehlerzelle als Fehlercode 7 (`#DIV/0!`). Dieselbe Quelle, von derselben
  LibreOffice nach .xlsx gewandelt und mit `extract_xlsx` gelesen, ergibt
  genau den Text, den `test_legacy_xls.py` für die .xls-Datei erwartet.
- `biff8-far-cell.xls` hat 65000 Zeilen und 200 Spalten; mit
  `ragged_rows=True` liefert xlrd nur die letzte Zeile mit 200 Einträgen. Als
  .xlsx gewandelt endet dieselbe Quelle bei `extract_xlsx` als
  `too_many_cells`, weil openpyxl das ganze Rechteck liefert.
