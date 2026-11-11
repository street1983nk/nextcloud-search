# Testbuild 1.6.3-rc.2: nicht gebaut, Plan 43-29 gestrichen

Stand 11.11.2026.

## Was gilt

Ein Testbuild rc.2 ist nie gebaut worden und wird nicht gebaut. Der Plan 43-28 (Bau von rc.2) ist seit dem 09.11.2026 gestrichen, der Plan 43-29 (Kommentar zu rc.2 an mbozem, Rückmeldung abwarten) seit dem 11.11.2026. In #25 ist deshalb kein Kommentar zu rc.2 gepostet worden, und es wird auf keine Rückmeldung gewartet.

## Warum

- mbozem hat rc.1 installiert und am 09.11.2026 in #25 den Landebericht geschickt (Backfill vollständig, Zahl gesetzt, 16 Prozent).
- Der Owner hat ihm am 09.11.2026 in #25 geantwortet, dass er kein rc.2 installieren muss und 1.6.3 in den Store geht, sobald die Zusammenführung der Wurzeln und Schreibweisen drin und geprüft ist.
- Der Versionsnachweis rc.1 auf 1.6.3 liegt in den Beinen upgrade-rc1 und upgrade-rc1-cf des Abnahmetests (43-26, 43-27). Beide sind im Lauf 43094681914 grün.
- Wurzeln und Schreibweisen sind behoben und auditiert: 43-AUDIT.md führt `d_43_15: behoben` und `status_43_27: passed`.

## Owner-Entscheid

Vorlage im Chat am 11.11.2026: 43-29 als gestrichen führen (kein Kommentar, kein Warten auf Rückmeldung), 43-11 formal als "abweichend, abgelöst" schließen, danach 43-12 Runde 2. Antwort des Owners: "Ok".

## Ergebnis

Die Zeile unten ist die Maschinenzeile, die 43-12 als erste Handlung liest. "keine Antwort" heißt hier: es wurde keine Frage zu rc.2 gestellt, weil es rc.2 nicht gibt.

Ergebnis: keine Antwort (Owner-Entscheid "Ok")

## Für 43-14 (Antwort in #25 nach dem Store-Release)

- mbozem geht von rc.1 direkt auf das Store-Release. Erwartung aus dem Verlauf: seine Zahl landet nach dem Update bei etwa 18 Prozent, ohne weiteren Schritt.
- Erwähnen: bei sehr großen Instanzen steht nach dem Update stundenlang "wird gezählt" (gerechnet etwa 8 bis 9 Stunden bei 491.000 Zeilen), die Suche läuft dabei normal.
- Wie viele seiner langen Speicher-IDs nicht zuzuordnen sind (hashedUngrouped), kann nur er nach dem Update sagen; die Zahl gehört in seine Rückmeldung zu 1.6.3.
