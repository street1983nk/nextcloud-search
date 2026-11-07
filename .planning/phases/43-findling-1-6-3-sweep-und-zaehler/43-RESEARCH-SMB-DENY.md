# 43 RESEARCH: SMB-Datei mit DENY-ACE blockiert den Content-Gateway

Stand: 07.11.2026. Nur Recherche, kein Code geändert.

Geprüfte Quellen:
- Lokale Server-Kopie `C:/Users/Student/.cache/findling-phpunit/server`: **Nextcloud 34.0.5** (`version.php`: `$OC_VersionString = '34.0.5'`), also eine Patch-Version unter der CI (34.0.6). Gebündelt: **icewind/smb 3.8.1**, **icewind/streams v0.7.8** (`3rdparty/composer/installed.json`).
- icewind/smb 3.8.1 ist laut Packagist die neueste Version (13.11.2025). Das Projekt ist von GitHub (archiviert seit 30.05.2025) nach codeberg.org/icewind/SMB umgezogen.
- Samba-Quellen Zweig `v4-19-stable` (passt zu Samba 4.19.5 in der CI): `source3/client/client.c`, `libcli/smbreadline/smbreadline.c`.
- php-src Zweig `PHP-8.3`: `main/streams/plain_wrapper.c`, `main/streams/userspace.c`, `ext/standard/proc_open.c`.

Kennzeichnung: **[belegt]** = Code-Stelle oder Link, **[abgeleitet]** = logisch aus belegten Stellen gefolgert, aber nicht im Lauf gemessen, **[vermutet]** = plausibel, ungeprüft.

---

## Kurzfazit

- **Es ist ein Deadlock zwischen PHP und smbclient, kein Timeout-Problem.** PHP wartet blockierend auf Daten an FD 5, smbclient wartet auf eine Eingabe auf stdin. Das `exit`, das icewind direkt nach `get` schickt, liegt schon im stdio-Puffer von smbclient, aber smbclient prüft vor `fgets` mit `poll()` nur den Kernel-Puffer und sieht es deshalb nie. [belegt im Code, Ablauf abgeleitet]
- **Normale Dateien klappen nur wegen eines "Anstupsers":** icewind hängt an jedes `fread` einen Callback, der eine Leerzeile an smbclient schickt. Kommen Daten, kommt der Anstupser, smbclient liest `exit` und beendet sich. Bei `ACCESS_DENIED` kommen keine Daten, also gibt es keinen Anstupser und es geht nie weiter. Die Fehlerausgabe von smbclient wird in `Share::read()` gar nicht gelesen, anders als in `Share::get()`. [belegt]
- **Nativer Modus (php-smbclient) hängt nicht:** `smbclient_open` scheitert, errno 13 wird zu `ForbiddenException`, `SMB::fopen` gibt `false` zurück, und der Gateway antwortet mit seinem schon vorhandenen 422-Zweig. [belegt im Code, nicht im Lauf gemessen]
- **Kein öffentliches Issue zu genau diesem Fall gefunden.** Verwandt sind icewind #84 ("commands hung forever", offen) und nextcloud/server #31308 (Abbruch bei 512 MB im smbclient-Modus, geschlossen nur mit dem Hinweis "nehmt php-smbclient"). `Share::read()` ist seit 2021 funktional unverändert, auch in 3.8.1. [belegt]
- **Empfehlung für Findling:** Den Stream im Gateway nicht blockierend lesen, mit Zeitdeckel. Jedes leere nicht blockierende `fread` löst selbst den Anstupser aus. smbclient beendet sich dann, PHP sieht EOF mit 0 Bytes bei einer Datei mit Größe über 0 und kann sauber "nicht lesbar" melden. `stream_select` und `stream_set_timeout` gehen auf diesem Stream nicht. Dazu ein eigener `ICallbackResponse` mit Zeitdeckel pro Block und `Content-Length`. Den Nextcloud-Kern muss man dafür nicht patchen. [Lösung abgeleitet, Test nötig]

---

## 1. Mechanismus mit Belegen

### 1.1 Aufrufpfad

| Schritt | Stelle | Was passiert |
|---|---|---|
| 1 | `nextcloud-search/php/lib/Controller/GatewayController.php:102` | `$stream = $file->fopen('r');` |
| 2 | `server/lib/private/Files/View.php:1036-1074` | `basicOperation('fopen', ...)`, kein zusätzlicher Wrapper beim Lesen |
| 3 | `server/apps/files_external/lib/Lib/Storage/SMB.php:441-447` | Bei `r`/`rb`: erst `file_exists()`, also `stat` über die dauerhafte Share-Verbindung, dann `return $this->share->read($fullPath);`. Die catch-Zweige (`ForbiddenException` usw., Zeilen 492-504) greifen nur, wenn `read()` eine Exception wirft. Das tut es im Wrapped-Modus nie (siehe 1.2). |
| 4 | `3rdparty/icewind/smb/src/Wrapped/Share.php:342-359` | `read()` |
| 5 | `GatewayController.php:112` | `new StreamResponse($stream)` |
| 6 | `server/lib/public/AppFramework/Http/StreamResponse.php:44-53` | `callback()`: `$output->setReadfile($this->filePath)` |
| 7 | `server/lib/private/AppFramework/Http/Output.php:35-38` | `stream_copy_to_stream($path, fopen('php://output','w'))`: liest blockierend, bis EOF kommt |

### 1.2 `Wrapped\Share::read()` (icewind/smb 3.8.1) [belegt]

```php
// src/Wrapped/Share.php:342-359
$connection = $this->getConnection();                         // 346: neuer smbclient-Prozess
stream_set_blocking($connection->getOutputStream(), false);   // 347: nur STDOUT nicht blockierend
$connection->write('get ' . $source . ' ' . $this->system->getFD(5));  // 349
$connection->write('exit');                                    // 350
$fh = $connection->getFileOutputStream();                      // 351: Pipe FD 5, blockierend
$fh = CallbackWrapper::wrap($fh, function () use ($connection) {
    $connection->write('');                                    // 352-354: READ-Callback, kein Close-Callback
});
```

- `Connection::write()` hängt `PHP_EOL` an (`Wrapped/Connection.php:39-41`). `get` und `exit` gehen also als zwei Zeilen direkt hintereinander raus, ohne dass auf eine Antwort gewartet wird.
- Das zweite Argument von `CallbackWrapper::wrap($source, $read, $write, $close, ...)` ist der **Read**-Callback (`icewind/streams/src/CallbackWrapper.php:62`). `stream_read()` ruft ihn **nach** dem `fread` auf der Quelle auf (`CallbackWrapper.php:93-99`). Jedes erfolgreiche `fread` schickt also eine Leerzeile an smbclient. Das ist der Anstupser.
- **Die übersprungene Fehlerprüfung:** `Share::get()` (`Share.php:326-331`) liest nach `get` die Ausgabe bis zum Prompt und gibt sie an `parseOutput()` und `Parser::checkForError()` weiter (`Parser.php:80-95`, `NT_STATUS_ACCESS_DENIED` steht in `ErrorCodes.php:23`). `read()` liest stdout nie und stderr nie. Die Zeile `NT_STATUS_ACCESS_DENIED opening remote file ...` bleibt ungelesen in der stdout-Pipe liegen.

### 1.3 RawConnection (Prozess und Pipes) [belegt]

- `Share::getConnection()` baut `exec [stdbuf -o0] smbclient -t <timeout> --authentication-file=/proc/self/fd/3 ... //host/share` (`Share.php:94-105`). Durch `exec` gibt es pro Verbindung genau einen smbclient-Prozess. `stdbuf -o0` (falls vorhanden, Ubuntu hat es in coreutils) schaltet nur die **Ausgabe**-Pufferung ab, nicht die Eingabe.
- `RawConnection::connect()`: `proc_open` mit FD 0 (stdin), 1 (stdout), 2 (stderr), 3 (Auth), 4 (Upload) und 5 (Download, Kind schreibt) (`RawConnection.php:62-80`). Umgebung: `CLI_FORCE_INTERACTIVE=y`, `CLI_NO_READLINE=1` (Zeilen 73-74).
- PHP setzt die Eltern-Enden der Pipes auf `FD_CLOEXEC` (`php-src ext/standard/proc_open.c`, `make_descriptor_cloexec`). Spätere Kindprozesse erben das Schreibende von FD 5 also nicht. Ein "fremder Halter" der Pipe scheidet als Ursache aus. [belegt]

### 1.4 smbclient-Seite (Samba 4.19) [belegt]

- `do_get()` (`source3/client/client.c:1036 ff.`) öffnet **zuerst die entfernte Datei**: `cli_open(...)` in Zeile 1076. Scheitert das, wird nur `"%s opening remote file %s\n"` auf stdout ausgegeben (Zeile 1078), und die Funktion kehrt mit `return 1` zurück. Die lokale Datei `/proc/self/fd/5` wird **nie geöffnet** (`open(lname, ...)` erst in Zeile 1097). Es wird also nichts nach FD 5 geschrieben. Das geerbte FD 5 bleibt offen, solange der Prozess lebt.
- Hauptschleife `process_stdin()` (ca. Zeile 6110-6160): `smb_readline(prompt, readline_callback, ...)`, danach der Befehl. `exit` und `quit` führen zu `cmd_quit()` und damit zu `exit(0)` (Zeilen 1470-1476, Tabelle Zeile 5578).
- `smb_readline()` (`libcli/smbreadline/smbreadline.c:114-132`): Wegen `CLI_FORCE_INTERACTIVE` gilt die Sitzung als interaktiv, wegen `CLI_NO_READLINE` läuft `smb_readline_replacement()`.
- **Kern des Deadlocks**, `smb_readline_replacement()` (`smbreadline.c:70-108`):
  ```c
  while (!smb_rl_done) {
      pfd.fd = fileno(stdin); pfd.events = POLLIN|POLLHUP;
      if (sys_poll_intr(&pfd, 1, 5000) == 1) {   // 95: fragt den KERNEL-Puffer von FD 0 ab
          ret = fgets(line, BUFSIZ, stdin);      // 96: liest aus dem stdio-Puffer
          return ret;
      }
      if (callback) callback();                  // alle 5 s
  }
  ```
  `fgets` auf dem gepufferten `stdin` holt mit einem einzigen `read()` alles, was in der Pipe liegt, also `get "...."\nexit\n`, und gibt nur die erste Zeile zurück. `exit\n` bleibt im **stdio-Puffer** von smbclient. Beim nächsten Prompt fragt `poll()` den Kernel, der nichts mehr hat. Ergebnis: `poll` läuft alle 5 s ins Leere, `fgets` wird nie wieder aufgerufen, und `exit` wird nie ausgeführt.
- `readline_callback()` (`client.c:6068-6103`) schickt alle 5 s ein `SMBecho` an den Server. Damit greift auch kein Idle-Timeout des Servers (deadtime): **der Prozess lebt unbegrenzt.** `-t 20` gilt nur für SMB-Anfragen, nicht für das Warten auf stdin.

### 1.5 Warum normale Dateien klappen [abgeleitet]

1. smbclient liest `get` und `exit` in einem Rutsch, `exit` liegt im stdio-Puffer.
2. `get` schreibt die Daten nach `/proc/self/fd/5`. PHP bekommt einen Block, und der Read-Callback schickt `\n`.
3. Der Kernel-Puffer von stdin hat jetzt Daten, `poll` liefert 1, und `fgets` gibt `exit` aus dem stdio-Puffer zurück. smbclient ruft `exit(0)` auf, alle FDs gehen zu, PHP sieht EOF.

Bei `ACCESS_DENIED` fehlt Schritt 2: Es kommt kein Block, also gibt es keinen Callback und keinen Anstupser. PHP bleibt in `fread` (Pipe FD 5 ist blockierend, nur stdout wurde in Zeile 347 auf nicht blockierend gestellt), und smbclient bleibt in `poll`. **Gegenseitiges Warten, dauerhaft.**

Ob `exit` schon im stdio-Puffer liegt, ist eigentlich ein Wettlauf. Die beiden `fwrite`+`fflush` liegen aber nur Mikrosekunden auseinander, smbclient wacht später auf. In der Praxis liegen also fast immer beide Zeilen zusammen in der Pipe. Das passt zur CI, wo es jedes Mal hängt. [abgeleitet]

### 1.6 Die zwei smbclient-Prozesse pro Hänger [abgeleitet]

1. **Dauerhafte Share-Verbindung** (`Share::$connection`, `Share.php:123-129`): Sie wurde für `file_exists`/`stat` in `SMB::fopen` aufgebaut und lebt bis zum Ende des Requests (`Share::__destruct`, Zeile 550). Weil der Request nie endet, lebt sie mit.
2. **Lese-Verbindung** aus `read()` (`Share.php:346`), die eigentlich hängende.

Beide haben dieselbe Kommandozeile, das passt zum `ps`-Befund.

### 1.7 Warum PHP selbst nicht abbricht [belegt/vermutet]

- `max_execution_time` misst auf Linux nur CPU-Zeit des Skripts. Zeit in blockierenden Systemaufrufen (Stream-Lesen) zählt nicht (PHP-Doku zu `set_time_limit`). [belegt durch Doku, nicht hier zitiert]
- `php -S` hat keinen Wanduhr-Timeout. Unter PHP-FPM würde `request_terminate_timeout` den Worker töten. Dann schließen die Eltern-Enden der Pipes, `poll` auf stdin meldet `POLLHUP`, `fgets` liefert `exit` aus dem Puffer, und smbclient beendet sich. [vermutet]
- Ein Client-Abbruch (curl-Timeout) wird nicht bemerkt, weil PHP nichts ausgibt. [abgeleitet]

### 1.8 Was das für Nextcloud selbst heißt [abgeleitet]

Jeder Leser über `fopen('r')` auf einer SMB-Mount ohne php-smbclient ist betroffen, nicht nur Findling: WebDAV-Download, Vorschau-Erzeugung, files_fulltextsearch, context_chat und recognize gehen alle über denselben `Storage::fopen` und lesen blockierend bis EOF. Konkrete Meldungen dazu wurden nicht gefunden (siehe Abschnitt 3).

### 1.9 Folgerung: auch leere Dateien müssten hängen [abgeleitet, Test nötig]

Bei einer **0-Byte-Datei**, die lesbar ist, läuft `get` erfolgreich, schreibt aber nichts nach FD 5. Damit gibt es keinen Block und keinen Anstupser, also derselbe Deadlock. Das ist der beste Gegentest für den hier beschriebenen Mechanismus (siehe offene Punkte).

---

## 2. Nativer Modus (php-smbclient) [belegt im Code]

- `NativeShare::read()` (`src/Native/NativeShare.php:269-273`): `$this->getState()->open($url, 'r')`, danach `NativeReadStream::wrap(...)`.
- `NativeState::open()` (`src/Native/NativeState.php:275-284`): `@smbclient_open(...)`, danach `testResult()`. Bei `false` folgt `handleError()` mit `smbclient_state_errno()` und dann `Exception::fromMap(EXCEPTION_MAP, ...)` (Zeilen 66-93).
- `EXCEPTION_MAP` (`NativeState.php:47-64`): `13 => ForbiddenException` (EACCES), `16 => FileInUseException` (EBUSY, z. B. Sharing Violation), `2 => NotFoundException`, `110 => TimedOutException`.
- Das Öffnen geschieht **synchron in `read()`**, also vor jedem Stream. Die Exception fliegt sofort.
- `SMB::fopen` fängt `ForbiddenException`, schreibt die Warnung "forbidden" ins Log und gibt `false` zurück (`SMB.php:495-497`). Der Gateway landet im Zweig `if (!$stream)` und antwortet 422 mit Log (`GatewayController.php:103-110`).
- `FileInUseException` wird in `SMB::fopen` **nicht** gefangen. Sie liefe bis zum `catch (\Throwable)` des Gateways und würde 500 (`gateway_error`). [abgeleitet, Ausschnitt `SMB.php:492-504` zeigt nur NotFound, Forbidden, OutOfSpace, Connect]
- Grenze: libsmbclient blockiert bei hängendem Netz ebenfalls, hat aber eigene SMB-Timeouts. Ein Deadlock wie im Wrapped-Modus ist dort nicht möglich, weil keine stdin-Steuerung im Spiel ist. [vermutet]

---

## 3. Bekannte Issues, PRs, Doku

| Quelle | Thema | Status | Bezug |
|---|---|---|---|
| [codeberg icewind/SMB #84](https://codeberg.org/icewind/SMB/issues/84) | "commands hung forever" (Wrapped-Modus, u. a. Alpine/smbclient ohne readline) | offen seit 2019 | verwandt: Hänger durch die stdin-Steuerung, aber bei `dir`, nicht bei `read` |
| [codeberg icewind/SMB #120](https://codeberg.org/icewind/SMB/issues/120) | `readTillPrompt()` gibt eine unvollständige Zeile zurück | offen seit 2022 | Parser-Robustheit im Wrapped-Modus |
| [GitHub icewind1991/SMB PR #78](https://github.com/icewind1991/SMB/pull/78) | Patch für Hänger mit smbclient >= 4.7 (in #84 verlinkt) | nicht geprüft (Ratelimit geschont) | verwandt |
| [Commit a8dc9ca](https://codeberg.org/icewind/SMB/commit/a8dc9ca75b4cb5aba5b8f23131fab1fd5362126d) | "fix support for smbclient compiled without readline support" (2021) | in 3.5.x | letzte inhaltliche Änderung an `Wrapped/Share.php`, danach nur Stil, psalm, `final` (Commit-Liste der Datei) |
| [nextcloud/server #31308](https://github.com/nextcloud/server/issues/31308) | Download > 512 MB aus SMB bricht ab (NC 23) | geschlossen; "Lösung" ist nur Doku [documentation #9428](https://github.com/nextcloud/documentation/pull/9428): php-smbclient stärker empfehlen | zeigt: Wrapped-Modus gilt offiziell als eingeschränkt |
| [nextcloud/server #14362](https://github.com/nextcloud/server/issues/14362) | smbclient-Timeout beim Download nach ca. 30 s | geschlossen, Fix über #17258 (Timeout einstellbar) | anderes Problem (`-t`), nicht stdin |
| [Admin-Doku SMB](https://docs.nextcloud.com/server/stable/admin_manual/configuration_files/external_storage/smb.html) | "The PHP smbclient module is **strongly preferred** ... smbclient binary, which has known limitations" | aktuell (NC 35) | offizielle Empfehlung: nativer Modus |
| GitHub-Issues icewind1991/SMB, Suche "hang" | nur #95, #17 | archiviert seit 30.05.2025 | nichts zu read/denied |
| help.nextcloud.com, Reddit | viele "Download bleibt hängen bzw. bricht ab"-Threads (z. B. [134355](https://help.nextcloud.com/t/smb-external-storage-problems/134355), [192161](https://help.nextcloud.com/t/smb-external-storage-issue/192161): "smbclient-Paket entfernt, php-smbclient erzwungen, jetzt geht es") | ungelöst bzw. per Umstieg auf native gelöst | Symptome passen grob, ACL-Ursache wird nirgends genannt |

- **Neueste icewind/smb:** 3.8.1 (13.11.2025), Packagist-Quelle `codeberg.org/icewind/SMB`. Das ist genau die Version in der lokalen Server-Kopie. `read()` ist in 3.8.0/3.8.1 nicht geändert. Neuere icewind/streams: v0.7.8 (05.12.2024), auch gebündelt. **Ein Update behebt also nichts.** [belegt]
- **Andere Apps** (files_fulltextsearch, context_chat, recognize, Vorschauen): Es wurde keine Schutzlogik gegen hängende Streams gefunden und kein Issue zu diesem Fall. Alle nutzen `File::fopen`/`getContent` und damit denselben Pfad. [Code der Apps nicht im Detail geprüft, vermutet: gleich betroffen]
- **Nicht gefunden:** ein Samba-Bugzilla-Eintrag zu `poll()` plus `fgets()` in `smb_readline_replacement`. Für Samba ist das bei echter interaktiver Nutzung kein Fehler. Es trifft nur Programme, die mehrere Befehle auf einmal in die Pipe schreiben.

---

## 4. Lösungsoptionen auf Findling-Seite

Vorab geprüfte Eigenschaften des Streams [belegt]:
- Der von `read()` gelieferte Handle ist ein **User-Space-Stream** (`CallbackWrapper` erbt von `Wrapper`, `WrapperHandler::wrapSource` öffnet `callbackwrapper://` mit Kontext). Er ist keine echte Pipe.
- `stream_select` braucht bei User-Streams `stream_cast` (`php-src main/streams/userspace.c`, `USERSTREAM_CAST`). icewind/streams 0.7.8 implementiert **kein** `stream_cast` (grep über `src/*.php`: 0 Treffer). Ergebnis: Warnung und `false`. **stream_select auf dem Handle geht nicht.**
- `stream_set_timeout` wird von `Wrapper::stream_set_option` an die Quelle durchgereicht (`Wrapper.php:61-71`). Die Quelle ist aber eine Plain-FD-Pipe, und `php_stdiop_set_option` kennt kein `PHP_STREAM_OPTION_READ_TIMEOUT` (`plain_wrapper.c`, nur BLOCKING, WRITE_BUFFER, LOCKING, MMAP, SYNC, TRUNCATE, META_DATA). **stream_set_timeout bleibt wirkungslos.**
- `stream_set_blocking($fh, false)` **funktioniert**: Es wird an die Quelle durchgereicht (`Wrapper.php:63-64`), und `plain_wrapper.c` unterstützt `PHP_STREAM_OPTION_BLOCKING`.
- Die echte Pipe ist über die öffentliche PHP-API erreichbar: `stream_context_get_options($fh)['callbackwrapper']['source']` (`WrapperHandler.php:29-35`). `stream_get_meta_data($fh)['wrapper_data']` liefert das Wrapper-Objekt. Das wäre aber Kopplung an icewind-Interna.
- Die SMB-Storage hält `$share` nur `protected` (`SMB.php:54`), es gibt keinen öffentlichen Getter. `getACL()` und `getFileInfo()` sind `private`/`protected`. An `IFileInfo::getAcls()` kommt die App ohne Reflection nicht heran.

| # | Option | Wirkung | Vorteile | Nachteile | Bewertung |
|---|---|---|---|---|---|
| A | **Nicht blockierend lesen mit Zeitdeckel** (`stream_set_blocking($fh,false)`, Schleife `fread` + `usleep(20-50 ms)` bis Daten, EOF oder Frist) | Jedes leere `fread` löst den Read-Callback aus (`CallbackWrapper.php:94-97`, der Callback läuft auch bei `strlen 0`), also den Anstupser `\n`. Dann liest smbclient `exit` aus dem Puffer und beendet sich, PHP sieht EOF. | Nur öffentliche PHP-API, kein Patch. Löst den Deadlock selbst, statt nur abzubrechen. Wirkt auch auf andere Storages (Frist). Mit `getSize() > 0` und 0 Bytes bei EOF lässt sich "nicht lesbar" erkennen. | Beruht auf dem Callback-Verhalten von icewind (stabil seit 2021, aber nicht zugesichert). Leere Dateien (Größe 0) sind von "verweigert" nur über die Größe unterscheidbar. Etwas Polling-Overhead. | **Empfohlen**, zusammen mit B |
| B | **Eigener `ICallbackResponse`** (OCP) statt `StreamResponse`: erst den vorgelesenen Block ausgeben, dann blockweise nicht blockierend weiterlesen mit Leerlauf-Frist pro Block; `Content-Length` = `$file->getSize()` setzen | Schützt auch vor einem Hänger mitten im Stream. Ein abgeschnittener Inhalt (Fehler in `cli_pull`, `client.c:1120-1128`) wird für den Container über die zu kurze Länge sichtbar. | OCP-API, kein Kerncode. Die Gateway-Antwort bleibt ein Stream (kein RAM-Puffer). | Etwas mehr Code. Nach den Headern lässt sich der Status nicht mehr ändern, nur noch abbrechen. | **Empfohlen** |
| C | Erstes Byte mit `stream_select` auf der Roh-Pipe aus `stream_context_get_options` | Wartet mit Frist | echter select | Löst allein **nichts**: Ohne Anstupser kommen nie Daten, also immer Frist. Koppelt an icewind-Interna (Protokollname, Kontextschlüssel). | nein |
| D | `stream_set_timeout` | keine | einfach | wirkungslos auf Pipe/User-Stream (siehe oben) | nein |
| E | Vorab-Prüfung über ACL (`getAcls()` per smbcacls) oder Option `check_acl` der Mount | `check_acl` blendet im Listing Einträge aus, deren ACL für **den eingestellten Benutzer** READ/EXECUTE verweigert (`SMB.php:249-256`) | Ursache wird schon beim Scan vermieden | Kein App-Zugriff auf `$share` (protected). `getACL()` vergleicht nur den Benutzernamen (`SMB.php:212-217`): Gruppen-, "Jeder"- und vererbte DENY-ACEs fallen durch. Ein smbcacls-Prozess pro Datei. Admin-Einstellung, nicht App-Sache. | höchstens als Admin-Tipp |
| F | Erkennung über `$storage->instanceOfStorage(\OCA\Files_External\Lib\Storage\SMB::class)` und nur dort A/B anwenden | Eingrenzung | weniger Risiko für andere Storages | `OCA\Files_External` ist keine OCP-API (Klassenname kann sich ändern). Andere hängende Backends bleiben ungeschützt. | optional, besser: A/B immer, wenn der Stream `user-space` ist oder generell |
| G | Prozess abräumen per Reflection (`RawConnection::$process`) | erzwingt das Ende | sofort | private Interna, zerbrechlich | nein |
| H | Admin-Empfehlung: php-smbclient installieren | nativer Modus, `ForbiddenException`, 422 | offizielle Nextcloud-Empfehlung | liegt nicht in der Hand der App. CI und viele Distros haben es nicht. | **zusätzlich** in die Doku/README |

### Was nach Abbruch mit smbclient passiert

- **Mit Option A** endet smbclient normalerweise **von selbst** (`exit(0)` nach dem Anstupser). PHP liest danach EOF, `fclose($fh)` folgt. [abgeleitet]
- `fclose` auf dem Wrapper: `CallbackWrapper::stream_close()` ruft `Wrapper::stream_close()` und damit `fclose($this->source)` auf (`CallbackWrapper.php:109-122`, `Wrapper.php:93-97`). `read()` setzt **keinen** Close-Callback, also wird `write('')` beim Schließen **nicht** aufgerufen (Annahme in der Frage widerlegt). [belegt]
- Die Connection hängt an der Closure, die im Wrapper-Objekt und im Stream-Kontext liegt. Wird der Stream freigegeben, wird `Connection` zerstört: `RawConnection::__destruct()` ruft `Connection::close()` auf, das schickt `close\n` und dann `close_process(true)`, also `proc_terminate()` (SIGTERM) und `proc_close()` (wartet mit waitpid) (`RawConnection.php:225-251`, `Connection.php:108-114`). **Kein Zombie**, sofern smbclient auf SIGTERM endet. [belegt im Code, Freigabezeitpunkt vermutet]
- Risiko: `proc_close` wartet blockierend. Würde smbclient SIGTERM ignorieren, hinge der Worker dort. Bei Option A ist der Prozess zu diesem Zeitpunkt meist schon beendet. [vermutet, Test nötig]
- Die dauerhafte Share-Verbindung lebt bis zum Request-Ende und wird dann vom `__destruct` gleich abgeräumt. [abgeleitet]

### Empfehlung

A + B im `GatewayController::getFileContents`:
1. `fopen('r')` wie bisher. Bei `false` bleibt es beim 422-Zweig (deckt den nativen Modus ab).
2. `stream_set_blocking($stream, false)`. Gibt es `false` zurück, auf das bisherige Verhalten zurückfallen.
3. Vorlesen bis zum ersten nicht leeren Block, EOF oder Frist (z. B. 15 bis 20 s, über `-t 20` von smbclient). Jedes `fread` stupst an.
4. EOF mit 0 Bytes und `getSize() > 0`: als "nicht lesbar" melden (Status mit dem Container abstimmen, z. B. 403 oder der vorhandene 422 mit eigenem Grund) und loggen (statischer Text plus fileId, wie bei Befund E).
5. Frist überschritten: `fclose`, 504 bzw. `gateway_error`, loggen.
6. Sonst ein eigener `ICallbackResponse`: vorgelesenen Block ausgeben, dann weiter nicht blockierend mit Leerlauf-Frist pro Block. `Content-Length` nur setzen, wenn die Größe verlässlich ist.

Optional für upstream (nicht posten, nur notiert): In `Share::read()` stdout nach `get` auf eine Fehlerzeile prüfen (stdout ist schon nicht blockierend), `exit` erst nach dem Prompt schicken oder `stdbuf -i0` setzen. Mit ungepuffertem stdin liest `fgets` byteweise, `exit` bliebe im Kernel-Puffer, und `poll` sähe es. [vermutet]

---

## 5. Andere Fehler beim Öffnen (Sharing Violation, gesperrte und Offline-Dateien)

- **Belegt am Samba-Code:** **Jeder** Fehler von `cli_open()` nimmt denselben Pfad (`client.c:1076-1080`: Meldung auf stdout, `return 1`, FD 5 nie geöffnet). Dazu gehören `NT_STATUS_SHARING_VIOLATION`, `NT_STATUS_ACCESS_DENIED`, `NT_STATUS_DELETE_PENDING`, `NT_STATUS_FILE_IS_OFFLINE` und `NT_STATUS_OBJECT_NAME_NOT_FOUND` (Datei zwischen `stat` und `read` gelöscht). Das Gleiche gilt für Fehler von `cli_resolve_path` (Zeilen 1066-1072, DFS). **Im Wrapped-Modus hängen sie also alle gleich.** [belegt im Code, abgeleitet für den Ablauf]
- **Fehler mitten in der Übertragung** (`cli_pull` scheitert, z. B. `NT_STATUS_FILE_LOCK_CONFLICT` bei Byte-Range-Locks oder Verbindungsabbruch, `client.c:1120-1128`): Es gab schon Blöcke, also auch Anstupser, und smbclient beendet sich danach. PHP sieht EOF, und **der Inhalt ist still abgeschnitten**, mit HTTP 200. Das ist eher schlimmer als ein Hänger (Index mit Teilinhalt). Option B mit `Content-Length` bzw. Größenvergleich deckt das ab. [abgeleitet]
- **Geöffnete Office-Dateien:** `cli_open(..., O_RDONLY, DENY_NONE)` fordert nur Lesezugriff und erlaubt alles zu teilen. Word und Excel öffnen meist mit "andere dürfen lesen", das Lesen klappt dann. Programme, die exklusiv öffnen (z. B. Outlook-PST, Access `.mdb`/`.accdb` im Exklusivmodus, manche Fachverfahren, Datenbank-Dateien), liefern `SHARING_VIOLATION`, und der Worker hängt. [vermutet, Test nötig]
- **Offline-Dateien / HSM** (Windows-Server mit Archivierung): Ein Recall kann länger als `-t 20` dauern oder mit `FILE_IS_OFFLINE` scheitern. Im zweiten Fall hängt der Worker. [vermutet]
- **Nativer Modus:** `SHARING_VIOLATION` wird zu errno EBUSY (16), daraus `FileInUseException`, das in `SMB::fopen` nicht gefangen wird. Im Gateway führt das zu 500/`gateway_error`, also zu einer Exception statt eines Hängers. [abgeleitet]
- Für Behörden-Admins heißt das: Ohne php-smbclient kann **eine einzige** exklusiv geöffnete oder gesperrte Datei pro Abruf einen PHP-Worker **dauerhaft** blockieren (bis zum FPM-Timeout bzw. Neustart). Bei einem Massen-Scan erschöpft das den Pool.

---

## 6. Offene Punkte, die nur ein Test klären kann

1. **Gegentest des Mechanismus:** Eine lesbare **0-Byte-Datei** auf der SMB-Mount über den Gateway abrufen. Hängt auch sie, ist das Modell "kein Block, kein Anstupser" bestätigt.
2. **Gegentest mit Positivkontrolle:** In der CI einmal nach dem Hänger von außen eine Leerzeile an stdin des hängenden smbclient schicken, z. B. `echo > /proc/<pid>/fd/0` (geht nur bei gleichem Benutzer und als Pipe). Erwartet: smbclient beendet sich sofort, curl bekommt eine leere Antwort mit 200. Alternativ `strace -p <pid>`: erwartet zyklisches `poll([{fd=0...}], 1, 5000)`, und `ls -l /proc/<pid>/fd/5` zeigt die Pipe.
3. **Option A messen:** Gateway-Prototyp mit `stream_set_blocking(false)` und Polling. Die DENY-Datei sollte in unter 1 s mit EOF und 0 Bytes enden, die smbclient-Prozesse sollten verschwinden (`ps` danach), und normale Dateien müssen weiter byte-identisch kommen (Prüfsumme). Auch große Dateien (> 512 MB, #31308) prüfen.
4. **SIGTERM und `proc_close`:** Beendet sich smbclient 4.19 auf SIGTERM? Bleibt nach `fclose` + `unset` ein Prozess oder Zombie (`ps -eo stat,args`)?
5. **Nativer Modus in der CI:** `pecl install smbclient` (oder `php8.3-smbclient` aus einem PPA), dann derselbe Test. Erwartet: 422 und der Log-Eintrag "Failed to open ... forbidden".
6. **Sharing Violation:** In der CI eine Datei per `smbclient` mit exklusivem Share-Mode offen halten (oder auf dem Samba-Server mit `share modes`/`kernel share modes` und einem zweiten Client, der hält) und dann den Gateway abrufen. Erwartet im Wrapped-Modus: Hänger, im nativen Modus: 500.
7. **check_acl:** Mit `check_acl` an der Mount prüfen, ob die bob-spezifische DENY-ACE die Datei aus dem Scan nimmt und die "Jeder"-DENY-ACE nicht (nach `getACL()`-Logik erwartet).
8. **Version 34.0.6:** In der CI bestätigen, dass dort ebenfalls icewind/smb 3.8.1 gebündelt ist (`grep -A2 '"name": "icewind/smb"' 3rdparty/composer/installed.json`). Lokal geprüft wurde nur 34.0.5.
