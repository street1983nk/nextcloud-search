# 39-DEDUP-ERGEBNIS: Abschluss DEDUP-02

**Stand:** 28.10.2026
**Grundlage:** .planning/milestones/v1.5-phases/35-stretch-aehnliche-dokumente-und-spikes/35-DEDUP-NOTIZ.md, .planning/phases/37-owner-tor-und-store-sichtbarkeit/37-OWNER-ENTSCHEIDE.md (D-37-01 bis D-37-04), 39-OWNER-VORLAGE.md
**Anforderung:** DEDUP-02 (Plaene 39-01 und 39-04)

| Teil | Status | Beleg |
|------|--------|-------|
| Weg C | geliefert in 1.6.0 | 39-01, Commits 1fce632f, 4fc2fc18, 8d6306aa |
| Messung A6 | gelaufen, A6 bestaetigt | CI-Lauf 40716240639, Commit 59f93e49 |
| A7 | beantwortet: Zaehlung je fileid | backend/tests/test_phase39_a7_counter.py, Commit d8d287a2 |
| Weg A | nicht gebaut (D-39-01 = b) | Owner-Antwort unten |
| Weg B | vertagt auf v1.7 (D-39-02) | Owner-Antwort unten |

## Owner-Antwort (woertlich)

> "Wie empfohlen (Recommended)"

- Datum und Uhrzeit: 28.10.2026, ca. 16:5x Uhr (Europe/Berlin)
- Kanal: Remote Control (Claude-App, AskUserQuestion), Auswahl auf die Frage "Dedup-Entscheide D-39-01 (Weg A) und D-39-02 (Weg B) nach der A6-Messung: wie entscheidest du?"
- Abweichungen: keine genannt; damit gelten beide Empfehlungen aus 39-OWNER-VORLAGE.md.
- D-39-03 (Abweichung von D-37-04) entfaellt, weil die Messung gelaufen ist.

## Weg C

Geliefert in Plan 39-01 (D-37-03 = a, erster Schritt der Phase).

- Commits: 077d63ba/1fce632f (Schluesselgruppen, Container-Zaehler `indexedLeftOut`/`embeddedLeftOut` ueber `GET /status?leaveOut=`), f92cc03f/4fc2fc18 (AdminViewService rechnet je Schluessel, korrigierter Mehrfachzaehlungs-Satz in 16 Katalogen), 96b7d6d2/8d6306aa (Erklaersatz bei 0 und Hinweis nach Regelaenderung).
- Schluesselformel: Storage-ID ohne Anmeldenamen, `<backend>::<host>//<rest>`; Host ist der Text nach dem letzten `@` vor dem ersten `//`; Root steht nach Platzhalter-Ersetzung schon in der ID (F4), ein Root mit `$user` ist also je Nutzer ein eigener Schluessel.
- Belegte Backends: `smb::` und `sftp::` (getId() in stable34 gelesen); WebDAV/ownCloud werden nie gruppiert.
- Rueckfaelle: unbekanntes ID-Format oder Container ohne Antwort auf `leaveOut` heisst keine Gruppierung, also die alte Zaehlung je Storage.

## Messung A6

- Lauf: GitHub Actions, Workflow smb-acl-measure.yml (nur workflow_dispatch), Lauf 40716240639, Commit 59f93e49, 28.10.2026 15:28 bis 15:32 UTC, Ergebnis success, Artefakt smb-acl-result.
- Vorlauf: Lauf 40714077919 (Commit d8d287a2) bestand die Positivkontrolle und hing danach ohne Ausgabe; abgebrochen. Ursache laut Lauf 2: der WebDAV-GET von Nutzer B auf die gesperrte Datei antwortet nicht, und curl hatte noch kein Timeout. Fix 59f93e49 (Timeouts und Schrittmarken).
- Aufbau: Samba 4.19.5-Ubuntu aus dem Ubuntu-Archiv auf dem Runner, Freigabe mit `vfs objects = acl_xattr` und `acl_xattr:ignore system acls = yes`; usera legt frei.txt und verboten.txt an und setzt per smbcacls `ACL:MESSUNG\userb:DENIED/0x0/READ` (zurueckgelesen im Log). Nextcloud stable34 ueber setup-test-nc, kein Image; Backend smb ueber das smbclient-Binary (icewind/smb ohne libsmbclient-php).
- Anmeldung: `password::logincredentials` ("Log-in credentials, save in database"), Zugangsdaten beim ersten WebDAV-Login beider Nutzer gespeichert; der eingebaute Rueckfall (Einspielen ueber ICredentialsManager) wurde nicht gebraucht.
- Positivkontrolle am Samba-Server: usera liest verboten.txt, userb bekommt NT_STATUS_ACCESS_DENIED, userb liest frei.txt. Lauf gueltig.
- `check_acl` ist eine Backend-Option und wurde mit `occ files_external:config <id> check_acl true` gesetzt (der Plan nannte `files_external:option`), danach `files:scan` je Nutzer.

| check_acl | Nutzer | Listing verboten.txt | isReadable() Node / SMB-Storage | Download verboten.txt |
|-----------|--------|----------------------|---------------------------------|-----------------------|
| aus | usera | gelistet | true / true | HTTP 200, Inhalt angekommen |
| aus | userb | gelistet | true / true | keine Antwort binnen 90 s (curl-Timeout), kein Inhalt |
| an | usera | gelistet | true / true | HTTP 200, Inhalt angekommen |
| an | userb | gelistet | true / true | keine Antwort binnen 90 s (curl-Timeout), kein Inhalt |

Deutung gegen Annahme A6: bestaetigt. Nextcloud listet die Datei fuer B, und `isReadable()` ist true, im Node wie direkt am SMB-Storage (F3). Nur das Lesen des Inhalts scheitert. Ein Weg A wuerde B damit Treffer aus der Lesung von A zeigen, und der PHP-Recheck `readableFile()` fiele darauf herein.

Nebenbefund `check_acl` (offen fuer v1.7): auch mit `check_acl` blieb die Datei fuer B gelistet. Die Ursache ist nicht eingegrenzt. Moeglich ist, dass B die ACL selbst nicht lesen darf (DENY READ enthaelt READ_CONTROL, `getACL()` faengt den Fehler und behandelt die Datei als erlaubt), oder dass der Filecache trotz `files:scan` die alte Liste hielt. Fuer D-39-01 ist das ohne Belang. Wer Weg A in v1.7 je wieder aufgreift, misst zuerst mit einem DENY nur auf FILE_READ_DATA und mit Log-Auszug ("Hiding non readable entry" oder "Error while getting file acls").

Nebenbefund Download: der GET von B auf die gesperrte Datei haengt in Nextcloud (smbclient-Binary-Pfad), statt mit einem Fehler zu antworten. Das betrifft Nextcloud, nicht Findling; der Crawl von Findling laeuft mit eigenen Zeitgrenzen.

## A7

- Test: backend/tests/test_phase39_a7_counter.py (Commit d8d287a2). Zwei files-Zeilen mit gleichem Pfad und gleichem content_hash auf zwei storage_id, beide indexed: `store.counts()["indexed"] == 2` und `GET /status` liefert `indexed == 2`.
- Ergebnis: Zaehlung je fileid, keine Inhalts-Entdopplung im Code.
- Folge: dass beim Melder 123.744 indexiert plus rund 39.200 uebersprungen so nah an der eindeutigen Menge liegen, ist mit den vorhandenen Daten nicht erklaert. Eine verborgene Entdopplung gibt es nicht; die Naehe ist Zufall oder liegt in den Daten des Melders.

## Weg A

Entscheid D-39-01 = (b): Weg A wird nicht gebaut. Owner-Antwort "Wie empfohlen (Recommended)" vom 28.10.2026 (siehe oben).

Begruendung: die Messung A6 zeigt den Leck-Fall ohne und mit `check_acl`. Damit faellt auch die Bedingung fuer ein Opt-in (a) weg ("nur sinnvoll, wenn A6 mit check_acl kein Listing fuer B zeigt"). Die Projektregel "Berechtigungs-Durchgriff strikt" bleibt unangetastet.

## Weg B

Entscheid D-39-02: vertagt auf v1.7. Owner-Antwort "Wie empfohlen (Recommended)" vom 28.10.2026 (siehe oben).

Begruendung: Weg B greift in die Indexierungs-Pipeline (Kopierpfad fuer Tantivy-Dokument, Chunks und Vektoren) und muesste durch das Audit der Phase 40; mit dem Einreichziel 29.10.2026 passt das nicht in den Rahmen von 1.6.0 (Release-Grenze aus DEDUP-02 und D-37-01). Die OCR- und Einbettungslast fuer Mehrfach-Einbindungen bleibt bis v1.7.

Startpunkt fuer den naechsten Planer:
- backend/src/findling/worker/poller.py, Aufruf `is_unchanged(job.file_id, read.content_hash)`: dahinter eine Nachschlage-Methode fuer eine lebende Zeile mit gleichem content_hash, state indexed, gleicher index_version und anderer file_id.
- store/schema.sql `files.content_hash` existiert schon; ein Index darauf ueber den bestehenden Migrationsweg der state.db.
- Inhalt (Text, Chunks, Vektoren, text_chars, truncated, ocr_used) aus der Quelle, Metadaten und ACL immer aus dem eigenen Job; PHP-Recheck und ACL-Tabelle unveraendert; Uebernahme nur nach eigenem erfolgreichem Download (T-39-11).
