# Phase 35: Entscheidungsvorlage #25-Dedup je Mount-Config

- **Stand:** 19.10.2026, Repo-Basis `5a66ba1e`; Nextcloud-Quelltext `nextcloud/server` Branch `stable34` (Kopf `db45ce29`), abgerufen am 19.10.2026
- **Status:** Entscheidungsvorlage, Owner-Entscheid v1.6 offen
- **Anforderung:** STR-03 (D-35-09)
- **Hinweis:** intern, kein Issue-Kommentar (D-35-09), keine Namen aus dem Issue. Aus Issue #25 stehen hier nur aggregierte Zahlen; Nutzer-, Host- und Share-Namen sowie `smb::`-Kennungen des Melders sind bewusst weggelassen.
- **Baut nichts.** Kein Code, kein Schema, kein Index in v1.5.

## 1. Sachstand

Gelesen am 19.10.2026 per `gh issue view 25 --comments` (Issue-Text, ein Melder-Kommentar, zwei Owner-Kommentare).

| Fakt | Wert | Quelle |
|------|------|--------|
| Versionen beim Melder | Nextcloud 34.0.4, Findling 1.4.1 (App und Backend), 16 GB | Issue-Text |
| Mount-Bild | 4 SMB-Shares, je Nutzer einmal eingebunden | Issue-Text |
| SMB-Storages in `oc_storages` | 116 | Issue-Text |
| Storages mit Mount (`COUNT(DISTINCT storage_id)` aus `oc_mounts`) | 67 | Melder-Kommentar |
| Zeilen in `oc_findling_scan_stats` | 77, davon 10 ohne Mount (eingefroren aus einer älteren Mount-Konfiguration) | Melder-Kommentar |
| `files_seen` gesamt (alter Nenner) | 1.640.911 | Melder-Kommentar |
| davon eingefroren | 324.530 (rund 20 Prozent) | Melder-Kommentar |
| davon live | 1.316.381 | Melder-Kommentar |
| eine Share, je Nutzer gezählt (Beispiel, vier Mounts) | 88.969 / 88.812 / 87.079 / 86.998 | Melder-Kommentar |
| Urteilszeilen in `oc_findling_file_state` | 205.522 (205.165 übersprungen, 357 fehlgeschlagen) über 24 Storages | Melder-Kommentar |
| eindeutige (Share, Pfad) dahinter | 39.209 | Melder-Kommentar |
| Kopienverteilung (Beispiele) | 9.075 Pfade mit je 6 Zeilen, 5.351 Pfade mit je 9 Zeilen | Melder-Kommentar |
| indexiert (angezeigter Zähler) | 123.744 | Melder-Kommentar |
| Warteschlangen | leer seit 09.10.2026, Lauf vollständig; Anzeige damals 7 Prozent | Melder-Kommentar |

**Was 1429eebc schon löst** (laut `docs/admin-page.md:130-145`):

- Der Nenner summiert nur noch über Storages, die aktuell einen gecrawlten Mount haben. Die 10 eingefrorenen Zeilen (324.530) fallen damit beim Melder heraus.
- Sind Warteschlangen leer, alle Mounts durchgezählt, der Container erreichbar und bleibt trotzdem eine Lücke, die die fehlgeschlagenen Dateien nicht erklären, sagt die Seite, dass dieselbe Datei mehrfach in der Zahl stehen kann (einmal je Einbindung).
- `docs/admin-page.md:143-145` nennt die echte Deduplizierung je Mount-Konfiguration als offen, "braucht zuerst die ACL-Antwort". Diese Notiz liefert die Vorlage dafür.

**Was offen bleibt:** Die Arbeit selbst ist nicht entdoppelt. Jede Kopie hat eine eigene fileid, einen eigenen Queue-Eintrag, eine eigene Urteilszeile und (bei Erfolg) eigene Index-Dokumente. Die Anzeige ist ehrlich, die Last nicht.

**Randnotiz zum Zähler:** Der Melder deutet den Zähler als "vom Index entdoppelt". Findling hat im Backend keine inhaltsbasierte Entdopplung (Suche nach `content_hash`/Hash-Dedup in `backend/src/findling` am 19.10.2026 ohne Treffer außerhalb von Modell-, Wortlisten- und Upload-Prüfsummen). Warum 123.744 plus rund 39.200 übersprungen so genau zur eindeutigen Menge passt, ist hier nicht geklärt; Prüfpunkt A7 in Abschnitt 7.

## 2. Nextcloud-Fakten

Alle Quelltextstellen aus `nextcloud/server`, Branch `stable34`, abgerufen am 19.10.2026 per `gh api -H "Accept: application/vnd.github.raw" "repos/nextcloud/server/contents/<pfad>?ref=stable34"`.

**F1: SMB-Storage-ID enthält den Anmeldenamen.**
`apps/files_external/lib/Lib/Storage/SMB.php:137-142` (stable34, abgerufen 19.10.2026), `getId()`:
`'smb::' . <auth-user> . '@' . <host> . '//' . <share> . '/' . <root>`.
Gleiche Share mit anderer Anmeldung ergibt eine andere Storage-ID, damit einen eigenen Filecache-Baum und andere fileids.

**F2: Die ACL-Prüfung des SMB-Backends ist eine Option, standardmäßig aus.**
`apps/files_external/lib/Lib/Storage/SMB.php:120` (stable34, abgerufen 19.10.2026): `check_acl` ist nur aktiv, wenn gesetzt.
`SMB.php:207-222`: `getACL()` sucht in den ACEs der Datei nur den Eintrag, dessen Name (ohne Domäne) gleich dem Anmeldenamen ist; Gruppen-ACEs werden nicht ausgewertet.
`SMB.php:249-256`: nur mit `check_acl` blendet `getFolderContents()` Einträge mit ausdrücklichem Lese- oder Ausführungsverbot aus ("better to have false negatives here then false positives").

**F3: `isReadable()` prüft keine SMB-ACL.**
`apps/files_external/lib/Lib/Storage/SMB.php:678-688` (stable34, abgerufen 19.10.2026): `isReadable()` liefert `true`, sobald `getFileInfo()` gelingt und die Datei nicht versteckt ist (oder versteckte gezeigt werden). Ein Leseverbot auf den Dateiinhalt fällt hier nur auf, wenn schon der Stat scheitert.

**F4: Platzhalter werden je Nutzer in jede Backend-Option eingesetzt.**
`apps/files_external/lib/Config/ConfigAdapter.php:64-66` (stable34, abgerufen 19.10.2026): `prepareStorageConfig()` ruft für jede Backend-Option `MountConfig::substitutePlaceholdersInConfig($value, $user->getUID())`.
`apps/files_external/lib/MountConfig.php:54-66` (stable34, abgerufen 19.10.2026): läuft alle Config-Handler; `apps/files_external/lib/Config/UserPlaceholderHandler.php:20-27` setzt den Platzhalter `$user` auf die UID.
Folge: eine Mount-Config mit `$user` in Share oder Root zeigt je Nutzer **andere** Inhalte, obwohl die Mount-Config-ID gleich ist.

**F5: Welche Authentifizierung je Nutzer verbindet.**
Nextcloud Admin-Doku "Authentication mechanisms" (https://docs.nextcloud.com/server/latest/admin_manual/configuration_files/external_storage/auth_mechanisms.html, abgerufen 19.10.2026):

| Mechanismus | je Nutzer eigene Verbindung | Hintergrund-Scan |
|-------------|-----------------------------|------------------|
| Username and password | nein, beim Einrichten fest hinterlegt | ja (keine Einschränkung genannt) |
| Global credentials | nein, ein Satz für den Mount | ja (keine Einschränkung genannt) |
| Log-in credentials, save in database | ja, Login des Nutzers, verschlüsselt in der Datenbank | ja (keine Einschränkung genannt) |
| Log-in credentials, save in session | ja, nur in der Sitzung | **nein**: "Background file scanning does not work" |
| User entered, store in database | ja, jeder Nutzer trägt eigene Anmeldung ein | ja (keine Einschränkung genannt) |

Abschnitt "Considerations for shared storage" derselben Seite: "Every external storage, which is using user specific authentication, is connected individually."

**F6: Findling-Seite.** Findling indexiert je fileid. Die Tabelle `acl (uid, file_id)` in state.db (`backend/src/findling/store/schema.sql:82-86`) ist nur Vorfilter; die verbindliche Prüfung macht PHP je fileid in `SearchService::readableFile()` (`php/lib/Service/SearchService.php:568`) über `getUserFolder()->getFirstNodeById()`.

**Abweichung zum Research (35-RESEARCH.md):** Research nannte die ACL-Option "um Zeile 214". Frischer Stand: Option gelesen in Zeile 120, `getACL()` 207-222, Anwendung im Listing 249-256. Neu belegt: `isReadable()` 678-688 ohne ACL-Prüfung, und `getACL()` wertet nur den ACE des Anmeldenamens aus, keine Gruppen. Storage-ID (137-142) und Platzhalter (64-66) stimmen mit dem Research überein.

## 3. Wann Duplikate entstehen

Duplikate entstehen, wenn **eine Mount-Config mit nutzerspezifischer Authentifizierung** (Log-in credentials in Datenbank oder Sitzung, User entered) mehreren Nutzern zugeordnet ist. Dann gilt:

1. Jeder Nutzer verbindet mit seinem eigenen Anmeldenamen (F5).
2. Der Anmeldename steht in der Storage-ID (F1), also je Nutzer eine eigene Storage.
3. Jede Storage hat ihren eigenen Filecache-Baum, also bekommt dieselbe Datei je Nutzer eine andere fileid.
4. Findling crawlt je Storage und indexiert je fileid (F6): n Nutzer ergeben n Queue-Einträge, n Urteile, n Lesungen, bei Scans n OCR-Läufe und n Einbettungen.

Keine Duplikate entstehen bei "Username and password" und "Global credentials": eine Anmeldung für alle, eine Storage-ID, ein Baum.

**Der Schlüssel für jede Entdopplung darf nie die Mount-Config-ID allein sein.** Mit `$user` in Share oder Root (F4) zeigt dieselbe Config je Nutzer andere Inhalte; ein Schlüssel nur aus der Config-ID würde fremde Dateien verschmelzen. Tragfähig ist nur:

`(Backend-Typ, Host, Share, Root NACH der Platzhalter-Ersetzung, Pfad relativ zum Root)`

Der Anmeldename gehört bewusst **nicht** in den Schlüssel (sonst gäbe es wieder je Nutzer einen eigenen), aber er ist genau die Stelle, an der sich die Rechte unterscheiden. Das ist die ACL-Frage, an der die drei Wege in Abschnitt 4 hängen.

## 4. Die drei Wege

Gemeinsamer Rahmen heute: Findling indexiert je fileid (Tantivy-Dokumente, Chunks und Vektoren in state.db), die Tabelle `acl (uid, file_id)` ist Vorfilter, PHP rechecked jede fileid über `readableFile()` (F6). Keiner der Wege darf diese letzte Prüfung ersetzen.

### Weg A: fileid-Mapping (Kanon plus Alias)

- **Kern:** Je Schlüssel (Abschnitt 3) wird eine Kopie gelesen und indexiert (Kanon). Die fileids der anderen Nutzer werden als Alias auf den Kanon gemappt und nicht gelesen.
- **Ablauf im Index:** Crawler bildet je fileid den Schlüssel und trägt Alias-Zeilen ein; Index und Vektoren existieren nur für die Kanon-ID; die ACL-Tabelle führt jeden Nutzer mit seiner Alias-fileid; bei einem Treffer übersetzt PHP die Kanon-ID in die eigene Alias-fileid des Fragenden und rechecked **diese** mit `readableFile()`.
- **ACL-Folge, Leck-Fall:** Nextcloud listet die Datei im Baum von Nutzer B, `isReadable()` liefert `true` (F3: Stat gelingt, Datei nicht versteckt), der SMB-Server verweigert B aber das Lesen des Inhalts. Der PHP-Recheck auf B's Alias-fileid besteht, und B bekäme Auszüge, Titel-Treffer und semantische Nähe aus **A's** Lesung. Das ist eine Information-Disclosure, die der heutige Recheck nicht fängt, weil er nur Nextclouds Sicht prüft, nicht das Leserecht am SMB-Server.
- **Eingrenzung:** nur mit der SMB-Option "ACL prüfen" (`check_acl`, F2), dann blendet Nextcloud Einträge mit ausdrücklichem Leseverbot für den Anmeldenamen schon im Listing aus. Auch das ist lückenhaft: `getACL()` wertet nur den ACE des Anmeldenamens aus, keine Gruppen-ACEs (F2, `SMB.php:207-222`), und Erben ist "nicht voll berücksichtigt" (Kommentar `SMB.php:250-251`). Für andere Backends (SFTP, WebDAV) gibt es gar keine solche Option.
- **Prüfpunkt A6 (offen, MEDIUM):** Listet SMB ohne `check_acl` Dateien, deren Inhalt der Nutzer nicht lesen darf, und liefert `isReadable()` dafür `true`? Laut Quelltext (F3) sehr wahrscheinlich, aber am Server nicht gemessen. Ist A6 falsch, wird Weg A sicherer, aber nicht sicher (Gruppen-ACEs bleiben).
- **Ersparnis:** Lesen (Download), OCR, Einbettung und Indexplatz der Kopien. Beim Melder bis rund 81 Prozent der Arbeit an Kopien [Annahme, Hochrechnung, siehe Weg B].
- **Aufwand in Bauteilen:** Crawler (Schlüsselbildung mit Mount-Config-Auflösung nach Platzhalter-Ersetzung, Alias-Zuordnung), state.db (neue Alias-Spalte oder -Tabelle, Kanon-Wechsel wenn der Kanon-Nutzer die Datei verliert oder gelöscht wird), Index (keiner je Alias, aber Kanon-Wechsel heißt Neuzuordnung), PHP-Recheck (Übersetzung Kanon zu Alias je Nutzer, neue Gate-Stelle neben `readableFile()`).
- **Migration Bestand:** Bestehende Kopien sind schon je fileid indexiert. Umstellung heißt: Schlüssel für alle Bestands-fileids bilden, je Schlüssel einen Kanon wählen, übrige Index-Dokumente löschen. Kein Neulesen, aber eine riskante Schreibwelle; Fehler im Schlüssel verschmelzen fremde Inhalte dauerhaft.

### Weg B: per-User-Crawl mit Inhalts-Hash-Wiederverwendung

- **Kern:** Jede Kopie wird wie heute mit den Anmeldedaten ihres Nutzers geladen; das Laden selbst beweist das Leserecht am Server. Aus den geladenen Bytes entsteht ein Inhalts-Hash. Gibt es schon ein indexiertes Dokument mit gleichem Hash (und gleichem Schlüssel), werden Text, Chunks und Vektoren unter der neuen fileid übernommen, ohne OCR und ohne Einbettung.
- **Ablauf im Index:** Crawler unverändert je fileid; neue Stufe nach dem Download: Hash bilden, in state.db nachschlagen (Hash zu Quell-Dokument); bei Treffer Tantivy-Dokument und Vektorzeilen unter der neuen fileid kopieren, Urteil "indexiert" setzen; sonst normaler Pfad (Extraktion, OCR, Einbettung). ACL-Tabelle und PHP-Recheck bleiben exakt wie heute, je fileid.
- **ACL-Folge:** keine neue. Jede fileid im Index wurde mit den Anmeldedaten genau des Nutzers gelesen, dem sie gehört; verweigert der SMB-Server das Lesen, gibt es keinen Hash, keine Übernahme und keinen Index-Eintrag. Der Schlüssel ist für die Sicherheit nicht einmal nötig (gleicher Hash heißt gleicher Inhalt, und den hat der Nutzer selbst gelesen); er begrenzt nur die Nachschlage-Menge.
- **Ersparnis:** OCR und Einbettung, also der teure Teil. **Nicht** gespart: Download je Kopie, Urteilszeile je Kopie und Indexplatz (Dokumente und Vektoren liegen je fileid vor).
- **Hochrechnung beim Melder [Annahme, Hochrechnung]:** 39.209 eindeutige (Share, Pfad) gegen 205.522 Urteilszeilen heißt rund 81 Prozent der Zeilen sind Kopien (1 minus 39.209 / 205.522 = 0,809). Diese Zahl stammt aus den übersprungenen und fehlgeschlagenen Zeilen (indexierte Urteile werden laut Melder nach Erfolg entfernt); dass indexierte Dateien dieselbe Kopienquote haben, ist unbelegt (Annahme A5).
- **Aufwand in Bauteilen:** Crawler bzw. Indexierungs-Pipeline (Hash-Stufe nach dem Download, Übernahme-Pfad), state.db (Hash-Spalte je Dokument plus Index darauf), Index (Kopieren eines Tantivy-Dokuments und seiner Vektorzeilen unter neuer fileid), PHP-Recheck unverändert.
- **Migration Bestand:** Bestehende Dokumente haben keinen Hash. Zwei Möglichkeiten: Hash nur für neue Lesungen (Wiederverwendung wächst mit der Zeit, kein Zusatzaufwand) oder ein einmaliger Hash-Nachlauf (ein Download je Bestandsdokument, keine OCR). Bestehende Index-Einträge bleiben gültig; nichts wird gelöscht.

### Weg C: nur die Zählung entdoppeln

- **Kern:** Nenner und Zähler der Abdeckung werden je Schlüssel (Abschnitt 3) gezählt, nicht je Storage.
- **Ablauf im Index:** keiner. Nur `totals()` und die Zähler auf der Admin-Seite rechnen je Schlüssel; Crawl, Index, ACL und Recheck bleiben unverändert.
- **ACL-Folge:** keine, es ändert sich nur eine Anzeige für Admins.
- **Ersparnis:** keine Arbeit. Die Seite zeigt aber eine richtige Prozentzahl statt des Mehrfachzählungs-Satzes aus 1429eebc.
- **Aufwand in Bauteilen:** PHP (Schlüsselbildung aus Mount-Config nach Platzhalter-Ersetzung, Zählung), ggf. Zähler-Endpunkt im Container. Kein Index-, kein Schema-Eingriff.
- **Migration Bestand:** keine; gilt ab dem Update.

## 5. Vergleich

| Weg | ACL-Risiko | spart | kostet | Bestandsmigration |
|-----|-----------|-------|--------|-------------------|
| A fileid-Mapping | **hoch:** Leck-Fall (Auszüge aus fremder Lesung), nur teilweise eingrenzbar mit `check_acl`, nicht für Gruppen-ACEs, nicht für andere Backends | Download, OCR, Einbettung, Indexplatz | neue Gate-Stelle im PHP-Recheck, Alias-Verwaltung, Kanon-Wechsel | Schreibwelle, Fehler verschmelzen fremde Inhalte dauerhaft |
| B Hash-Wiederverwendung | keins neu, ACL je fileid durch Konstruktion | OCR und Einbettung (rund 81 Prozent beim Melder, Hochrechnung) | Hash-Stufe, Hash-Spalte, Kopierpfad für Dokument und Vektoren | keine Pflicht; optionaler Hash-Nachlauf |
| C Zählung entdoppeln | keins | nichts an Arbeit | Schlüsselbildung in PHP | keine |

## 6. Empfehlung

Empfehlung (Owner entscheidet): **Weg B als Standard, Weg A nur als ausdrückliches Admin-Opt-in je Mount-Config mit Warnsatz, Weg C sofort als billige Ergänzung.**

Begründung: B spart den teuren Teil (OCR und Einbettung) und lässt das Berechtigungsmodell unberührt, weil jede fileid weiter mit den Anmeldedaten ihres Nutzers gelesen wird. A spart mehr, macht aber den heutigen Recheck unzureichend: Nextclouds `isReadable()` sagt "lesbar", während der SMB-Server das Lesen verweigert, und Findling würde fremd gelesene Auszüge zeigen. Das widerspricht der Projektregel "Berechtigungs-Durchgriff strikt" und darf nie Standard sein. C kostet fast nichts, ersetzt den Mehrfachzählungs-Satz durch eine richtige Zahl und hilft unabhängig von A und B. Wenn A als Opt-in kommt, dann nur mit Warnsatz in der Art "Nur einschalten, wenn alle Nutzer dieser Einbindung auf der Freigabe dieselben Leserechte haben; sonst können Suchtreffer Auszüge aus Dateien zeigen, die ein Nutzer nicht öffnen darf."

## 7. Entscheidungen für den Owner (v1.6)

**D1: Weg-Wahl für die Arbeitsentdopplung**
- (a) Weg B als Standard.
- (b) Weg A als Standard.
- (c) keine Arbeitsentdopplung, nur Weg C.
- Empfehlung: (a); einziger Weg, der spart, ohne das ACL-Modell anzufassen.

**D2: Weg A als Admin-Opt-in je Mount-Config**
- (a) ja, mit Warnsatz (Abschnitt 6), nur für SMB mit gesetztem `check_acl`.
- (b) nein, Weg A wird nicht gebaut.
- (c) erst nach Messung A6 (D4) entscheiden.
- Empfehlung: (c); ohne Messung ist das Leck nur aus dem Quelltext abgeleitet, und selbst mit `check_acl` bleiben Gruppen-ACEs offen. Fällt A6 wie erwartet aus, dann (b) oder (a) nur mit dem Warnsatz.

**D3: Weg C vorziehen**
- (a) ja, als erster v1.6-Schritt (oder Patch-Release), unabhängig von D1.
- (b) zusammen mit dem Bau aus D1.
- (c) nein, der Satz aus 1429eebc reicht.
- Empfehlung: (a); kleinster Eingriff, sichtbar für jede Instanz mit nutzerspezifischer Anmeldung, kein Index-Risiko.

**D4: Prüfpunkt A6 vor dem Bau messen**
- (a) ja, auf einer SMB-Testfreigabe (Samba-Container, zwei Nutzer mit Log-in credentials, eine Datei mit Leseverbot für Nutzer B, einmal mit und einmal ohne `check_acl`; gemessen: Listing, `isReadable()`, Download).
- (b) nein, Weg A wird ohnehin nicht gebaut (D2 = b).
- (c) nur, wenn D2 auf (a) oder (c) steht.
- Empfehlung: (a), solange D2 nicht (b) ist; ein halber Tag Messung gegen eine dauerhafte Rechte-Frage. Im selben Lauf A7 klären: wie der Zähler beim Melder zur eindeutigen Menge passt, obwohl Findling keine Inhalts-Entdopplung hat (Abschnitt 1, Randnotiz).

Annahmen dieser Notiz:

| ID | Annahme | wenn falsch |
|----|---------|-------------|
| A5 | rund 81 Prozent Ersparnis mit Weg B beim Melder | nur Hochrechnung aus Urteilszeilen ohne indexierte Kopien; die echte Quote kann höher oder niedriger sein |
| A6 | SMB listet ohne `check_acl` Dateien, deren Inhalt der Nutzer nicht lesen darf, und `isReadable()` ist dafür `true` | Weg A wird sicherer, bleibt aber wegen Gruppen-ACEs und anderer Backends unsicher |
| A7 | der Zähler beim Melder ist eine Zählung je fileid, kein entdoppelter Wert | dann gibt es irgendwo schon Entdopplung, die vor dem Bau verstanden sein muss |

## 8. Nicht Teil dieser Notiz

- Kein Bau in v1.5: kein Code, kein Schema, kein Index, keine Migration.
- Kein Kommentar und kein Kommentar-Entwurf für Issue #25 (D-35-09); eine Antwort im Issue gibt es nur nach Owner-Wort.
- Keine Namen, Hosts, Shares oder `smb::`-Kennungen aus dem Issue; die Formel in F1 steht nur mit Platzhaltern.
- Keine Entscheidung: D1 bis D4 fällt der Owner für v1.6.
