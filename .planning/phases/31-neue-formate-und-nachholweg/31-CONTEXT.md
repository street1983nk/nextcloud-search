# Phase 31: Neue Formate und Nachholweg, Context

**Gathered:** 2026-10-10 (Owner-Rückfrage nach 31-RESEARCH.md, alle vier Empfehlungen angenommen)
**Status:** Ready for planning

## Geerbte Entscheide (Phase 30)

- **D-30-03:** EIN Treffer je ZIP-Archiv, Text aller inneren Dateien zusammen, das Snippet nennt die innere Datei. Kein neues Schemafeld.
- **D-30-04:** Alle neu lesbaren Typen werden nach dem Upgrade nachgeholt, in Bändern, ohne bestehende Treffer anzufassen. Präzisiert durch D-31-01.
- **D-30-08:** Kein weiterer Schemaschritt in v1.5 (SCHEMA_VERSION bleibt 3).
- **L-30-03:** Formprüfung der Werte, die deploy-harp in GITHUB_ENV schreibt (plus die zwei weiteren Stellen aus 31-RESEARCH.md).

## Entscheide Phase 31

- **D-31-01 Nachholweg (FMT-06):** Umsetzung wie in 31-RESEARCH.md empfohlen: einmaliger Lauf nach Generation 3 der Companion. Teil A: Durchlauf über state.db (legacy_format-Zeilen und nicht indexierte Zeilen mit neuem Mimetyp), in Bändern, Marke `recheck_1_5_0`. Teil B: sofort fälliger Abgleich-Zyklus nur über Metadaten für nie gesehene Dateien. Kein Vollcrawl, keine Neu-Einbettung bestehender Treffer.
- **D-31-02 Aufgegebene Dateien (Owner):** Zeilen mit `repeatedly_stuck` werden einmal mit in den Nachholweg genommen (zusammen mit dem POL-02-Fix).
- **D-31-03 Skip-Codes (Owner):** Neuer Code `archive_limit` für ZIP-Grenzüberschreitungen (alle Übersetzungskataloge und Doku). Nicht lesbare .doc/.xls-Varianten laufen unter `unsupported_variant`, das Label wird allgemeiner gefasst.
- **D-31-04 Mail-Anhänge (Owner):** .eml indexiert Betreff, Absender, Empfänger, Textteil (HTML als Text) und die Dateinamen der Anhänge, NICHT den Inhalt der Anhänge. Anhangsinhalt ist v1.6-Kandidat.
- **D-31-05 ZIP im Typfilter (Owner):** ZIP-Treffer gehören zu keiner der sechs Typgruppen (erscheinen nur bei "alle Typen"); als Grenze dokumentieren.
- **D-31-06 HEIC-Bibliothek:** pillow-heif (pi-heif ist eingestellt), Lizenzlage (GPLv2-or-later durch x265, AGPL-verträglich) in THIRD-PARTY.md/REUSE.toml belegen; Speicherbedarf beim Dekodieren großer HEIC-Fotos im Plan messen und die RAM-Schätzung anpassen.
- **D-31-07 ZIP-Grenzwerte:** Startwerte aus der Research (10.000 Einträge, 256 MiB entpackt, Rate 100:1 ab 1 MiB, Tiefe 2, kein OCR im Archiv); Eintragszahl vor dem Öffnen prüfen. Werte im Plan messen und begründet festlegen.
- **D-31-08 Generation:** Generationsprüfung in nc/queue.py auf 3 heben und 2 weiter akzeptieren.

## Quellen

- 31-RESEARCH.md (dieser Ordner)
- .planning/phases/30-owner-tor-schema-und-tschechisch/30-CONTEXT.md, 30-AUDIT.md
