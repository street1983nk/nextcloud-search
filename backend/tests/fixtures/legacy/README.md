# Testdateien für den .doc-Leser (Plan 31-05, FMT-03)

Drei Word-97-Dateien, geschrieben von LibreOffice aus eigenem Inhalt. Die
Suchwörter sind erfunden, damit Plan 31-12 die Dateien als Saat wiederverwenden
kann. Lizenz wie das übrige Repository (eigenes Werk, AGPL-3.0-or-later über die
`**`-Annotation in `REUSE.toml`).

| Datei | Inhalt | Suchwort | SHA-256 |
|---|---|---|---|
| `word97-latin.doc` | Umlaute, typografische Anführungszeichen, Eurozeichen, weiches und geschütztes Trennzeichen | `wortquendel` | `a353da53140613930e68eb7db478bc1e531defa0610e98b916d54a40c9834845` |
| `word97-unicode.doc` | tschechischer und griechischer Text | `glyphquendel` | `0dc7e408d9a46d74cd674ea28629dae2164de624ae665d27677aef3c2eb6faee` |
| `word97-table-field.doc` | Tabelle mit zwei Zeilen und zwei Spalten, Seitenzahlfeld, festes Datumsfeld | `zellquendel` | `d662ad00e1997f8ef7944d5e449807a6bcfabbbda421971e6f3c6be728b3185c` |

## Herkunft

- Erzeugt am 11.10.2026 mit LibreOffice 26.2.4.2 (Windows, x86-64,
  Build-ID `0229ac93fcf0d7cbc6376066c6f35021cef002dc`).
- Werkzeug: `scripts/dev/make_legacy_fixtures.py`. Es schreibt die Quellen als
  flache ODF-Textdateien (`.fodt`) in ein temporäres Verzeichnis und ruft je
  Datei auf:

  ```
  soffice -env:UserInstallation=file:///<temp>/profile --headless --norestore \
      --convert-to "doc:MS Word 97" --outdir <temp>/out <quelle>.fodt
  ```

- Aufruf aus `backend/`: `uv run python ../scripts/dev/make_legacy_fixtures.py`
  (Optionen `--soffice PFAD`, `--output VERZEICHNIS`).

LibreOffice schreibt nie zweimal dieselben Bytes. Die Tests in
`tests/test_legacy_doc.py` pinnen deshalb den SHA-256 der eingecheckten Dateien;
wer das Werkzeug erneut laufen lässt, pinnt die neuen Werte.

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
