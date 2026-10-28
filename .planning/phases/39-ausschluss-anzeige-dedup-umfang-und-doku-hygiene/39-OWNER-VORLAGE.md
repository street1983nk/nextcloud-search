# Phase 39: Owner-Vorlage (eine Runde, zwei Punkte)

Stand: 28.10.2026

Antwort "wie empfohlen" uebernimmt beide Empfehlungen; Abweichungen als "D-39-01 a" oder "D-39-02 bauen" nennen. Nicht genannte Punkte gelten als wie empfohlen.

Ein Punkt D-39-03 (Abweichung von D-37-04) entfaellt: die Messung A6 ist gelaufen.

## Messergebnis A6 (CI-Lauf 40716240639, Commit 59f93e49, 28.10.2026 15:28 bis 15:32 UTC)

Aufbau: Samba 4.19.5 auf dem Runner, Freigabe mit acl_xattr, Datei verboten.txt mit ausdruecklichem DENY READ fuer Nutzer B. Positivkontrolle am Samba-Server bestanden: Nutzer A liest die Datei, Nutzer B bekommt NT_STATUS_ACCESS_DENIED. Nextcloud stable34, Mount mit "Log-in credentials, save in database" (Zugangsdaten beim ersten Login gespeichert, nicht nachgeholfen).

| check_acl | Nutzer | Listing verboten.txt | isReadable() (Node / SMB-Storage) | Download verboten.txt |
|-----------|--------|----------------------|-----------------------------------|-----------------------|
| aus | A | gelistet | true / true | HTTP 200, Inhalt da |
| aus | B | gelistet | true / true | keine Antwort binnen 90 s, kein Inhalt |
| an | A | gelistet | true / true | HTTP 200, Inhalt da |
| an | B | gelistet | true / true | keine Antwort binnen 90 s, kein Inhalt |

In drei Saetzen: Nutzer B sieht die verbotene Datei im Listing, ohne und auch mit `check_acl`. `isReadable()` sagt fuer B in beiden Faellen true, im Node und direkt am SMB-Storage. Nur der Download liefert B keinen Inhalt (die Anfrage haengt, bis der Client abbricht).

Folge fuer Weg A: Annahme A6 ist bestaetigt, und `check_acl` grenzt den Leck-Fall in diesem Aufbau nicht einmal ein. Der PHP-Recheck `readableFile()` wuerde B einen Treffer aus der Lesung von A zeigen. Weg A waere damit auch als Opt-in nur sicher, wenn alle Nutzer einer Einbindung dieselben Leserechte haben, und das kann Findling nicht pruefen.

A7 (Test backend/tests/test_phase39_a7_counter.py, Commit d8d287a2): der indexed-Zaehler zaehlt je fileid; zwei Kopien mit gleichem Inhalt ergeben 2. Es gibt keine verborgene Entdopplung.

## D-39-01: Weg A als Admin-Opt-in (nach Messung A6, D-37-02)

- (b) Weg A wird nicht gebaut.
- (a) Weg A spaeter (v1.7) als Opt-in nur fuer SMB mit `check_acl` und Warnsatz.
- (c) vertagt auf v1.7 (nur Pflicht, wenn die Messung nicht gelaufen waere).
- Empfehlung: (b). Die Messung zeigt das Leck ohne und mit `check_acl`; damit faellt auch die Bedingung fuer (a) weg ("nur sinnvoll, wenn A6 mit check_acl kein Listing fuer B zeigt"). Die Projektregel "Berechtigungs-Durchgriff strikt" bleibt unangetastet.

## D-39-02: Weg B in 1.6.0 bauen oder auf v1.7 vertagen (D-37-01)

- vertagen: Weg B nach v1.7, Begruendung Release-Rahmen 29.10. und Audit-Pflicht.
- bauen: Weg B in 1.6.0.
- Empfehlung: vertagen. Weg B greift in die Indexierungs-Pipeline (Kopierpfad fuer Tantivy-Dokument, Chunks und Vektoren) und muesste durch das Audit der Phase 40; der Termin 29.10. fiele sehr wahrscheinlich. 1.6.0 bleibt im Termin, kein ungeprueftes Risiko im Indexpfad. Nachteil: OCR- und Einbettungslast fuer Mehrfach-Einbindungen bleibt bis v1.7. Startpunkt fuer v1.7: poller `is_unchanged` und `files.content_hash`.

## Frage an den Owner

"Phase 39 (Findling v1.6), Dedup: Messung A6 gelaufen, B sieht die verbotene Datei gelistet und isReadable() true, auch mit check_acl; nur der Download bleibt ohne Inhalt. Wie entscheidest du D-39-01 (Empfehlung b: Weg A nicht bauen) und D-39-02 (Empfehlung: Weg B auf v1.7 vertagen)?"
