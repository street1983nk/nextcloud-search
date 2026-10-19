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
