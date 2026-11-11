# Phase 43: Owner-Abnahme 1.6.3

GO: ja
(Die Zeile darüber gilt seit Runde 2, siehe unten. Runde 1 endete am 09.11.2026 mit dem Entscheid "kein GO"; ihr Protokoll folgt unverändert.)
Zitat: "Wie ja" (Bestätigung des Vorschlags: GO erst nach der Rückmeldung von mbozem, spätestens am 12.11.2026; ohne Rückmeldung bis dahin gilt "weitergehen ja, W grenze, GO ja")
Datum: 2026-11-09 07:05
Kanal: Claude Code Terminal
Frage: Owner-Abnahme Findling 1.6.3 nach 43-OWNER-VORLAGE.md, "wie empfohlen" oder Abweichungen je Punkt; W und GO mit eigenem Wort.

Das GO deckt Tag v1.6.3 und die Einreichung beider Apps; beides führt der Owner aus. Es deckt keinen Push.

## Entscheide je Punkt

- B Store-Text: wie empfohlen (a), Zitat "Ok" (2026-11-09 07:00).
- C Release-Notiz: wie empfohlen (a), Zitat "Ok"; die Known-limitation-Zeile kommt nur bei W = grenze dazu.
- V Sätze V1 und V2: wie empfohlen (a), Zitat "Ok".
- D2 CHANGELOG-Satz zu F-43A-01: wie empfohlen (a), Zitat "Ok"; umgesetzt unter [1.6.3] Fixed.
- I Außentexte I1 und I2: wie empfohlen (a), Zitat "Ok"; I2 erst nach dem Store-Release mit eigener Freigabe.
- P Push der Abnahme-Commits: ja, Zitat "Wie empfohlen" und "Wie ja" (43-FREIGABEN.md).
- W Wurzel-Frage: offen. Owner fragte "Was empfehlst du"; Empfehlung Claude: auf mbozem warten, ohne Antwort bis 12.11.2026 grenze. Bestätigt mit "Wie ja". Die Maschinenzeile `Freigabe Wurzel 43-12` folgt mit dem Entscheid.
- F GO: nein bis zur Rückmeldung von mbozem oder bis 12.11.2026 (siehe Zitat oben). Diese Zeile wird dann neu gesetzt.

Hinweis zur Prüfung: Der Kommentar an mbozem ist vom 09.11.2026 05:23 UTC; die Runde lief eine knappe Stunde danach.

## Nachtrag 2026-11-09 09:20: Wurzel-Frage ja

mbozem hat geantwortet (https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6735344512): dieselbe Freigabe mit verschiedenen Wurzeln kommt auf seiner Instanz vor (//Daten mit Wurzel / 25-mal und mit sechs Unterwurzeln 17-mal), dazu dieselbe Freigabe in zwei Schreibweisen (//Daten und //daten). Nach D-43-15 und der G2-Sperre bleibt GO: nein; die Frist 12.11.2026 entfällt. Weiter geht es mit einem Zusatzplan vor dem Store, danach Audit-Nachtrag und neue Owner-Runde für das GO.

## Runde 2

Zitat Runde 2: "Wie empfohlen"
Datum Runde 2: 2026-11-11 22:53
Kanal Runde 2: Claude Code Terminal
Frage Runde 2: Owner-Abnahme Findling 1.6.3, Runde 2: Vorlage .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-OWNER-VORLAGE.md, Abschnitt # Runde 2. "wie empfohlen" oder Abweichungen je Punkt.

Verlauf: Auf die Vorlage fragte der Owner "Was empfehlst du". Claude empfahl: alles wie in der Vorlage, I2 mit der von mbozem gemessenen Dauer (7,5 Stunden unter rc.1) statt der gerechneten 8 bis 9 Stunden, GO, Push ja, keine weitere Playwright-Runde, weil sich Oberfläche und App-Texte seit Runde 1 nicht geändert haben. Antwort des Owners: "Wie empfohlen".

Das GO deckt Tag v1.6.3 und die Einreichung beider Apps; beides führt der Owner aus. Es deckt keinen Push.

### Entscheide je Punkt, Runde 2

- B Store-Text: (a) so einreichen, unverändert seit Runde 1.
- C Release-Notiz: (a) fünf Punkte plus die Grenzzeile zu %U und %S, ohne sechsten Punkt.
- T1 bis T3 CHANGELOG (Wurzeln und Schreibweisen, zwei bekannte Grenzen): (a) so.
- T4 Satz zu F-43B-02: (a) aufnehmen.
- T5 Satz zu F-43B-05: (a) aufnehmen.
- T6 Datum der Überschrift [1.6.3]: (a) in allen drei Dateien auf das Tag-Datum setzen.
- D Audit-Nachtrag 43-27, R Testbuild (kein rc.2), E End-to-End-Beleg, K Neuaufbau, Mischbetrieb, rc-Branch: zur Kenntnis.
- I1 Forum-Post: (a) so.
- I2 Antwort in #25: (b) mit einer Änderung nach der Empfehlung von Claude: statt "I'd reckon 8 to 9 for your ~491k rows" die gemessene Dauer des rc.1-Backfills auf seiner Instanz (7,5 Stunden). Gepostet wird erst nach dem Store-Release mit eigener Freigabe (43-14).
- F GO: (a) ja.
- P Push der Abnahme-Commits: (a) ja (43-FREIGABEN.md).

Restrisiken, die das GO mitträgt (dem Owner so vorgelegt): die Zahl nach der Behebung ist auf keiner echten Instanz gemessen; der Neuaufbau zeigt bei sehr großen Instanzen stundenlang "wird gezählt"; der Wiederholungsweg von F-43B-05 ist nur durch PHPUnit belegt.
