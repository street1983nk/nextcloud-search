# Changelog

Alle wesentlichen Änderungen an Findling (der Begleit-App `findling` und der
External App `findling_backend`) stehen hier. Beide Apps tragen dieselbe
Version. Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).
Deutsche Fassung ab 1.6.3; ältere Einträge stehen in [CHANGELOG.md](CHANGELOG.md).

## [Unreleased]

## [1.6.3] - 2026-11-12

### Hinzugefügt

- Ein Hinweis neben der Abdeckungszahl für sieben Tage nach der ersten Zählung
  von 1.6.3, ein Satz, solange die Zählung läuft, und die Zahl der Dateien,
  die gelistet sind, aber nicht gelesen werden konnten oder hängen geblieben
  sind; sie zählen jetzt als nicht durchsuchbar (#25).

### Behoben

- Der Speicher-Durchlauf läuft einmal je Abgleich-Takt, auch während der
  Crawl oder eine lange Warteschlange den vollständigen Vergleich zurückhält,
  sodass Dokumente gelöschter oder ausgehängter Speicher den Index verlassen
  (#25).
- Die Abdeckungszahl zählt jedes Dokument einmal, auch wenn eine Freigabe für
  jeden Nutzer getrennt eingehängt ist, und Dokumente, die nur auf nicht mehr
  eingehängten Speichern liegen, zählen nicht mehr (#25).
- Die Abdeckungszahl zählt ein Dokument auch dann einmal, wenn eine Freigabe
  mit verschiedenen Wurzeln konfiguriert ist oder Server- oder Freigabename
  in anderer Groß- und Kleinschreibung stehen (#25). Eine
  Samba-[homes]-Freigabe wird nie über Nutzer hinweg gruppiert, SFTP-Speicher
  nur je Anmeldename.
- Der Nenner wird je Freigabegruppe ermittelt und fällt nie unter die in
  dieser Gruppe beurteilten Dokumente plus die Dateien, die Nextcloud nicht
  lesen konnte, sodass der Anteil nie über 100 Prozent liegt und die echte
  Abdeckung zeigt, sobald die Warteschlange leer ist (#25). Abgelehnte
  Dateitypen auf nicht mehr eingehängten Speichern verkleinern ihn nicht mehr.
- Gelöschte Dateien zählen in den Statuszahlen nicht mehr als indexiert.
- Auf SMB-Speicher ohne die Erweiterung php-smbclient blockiert eine Datei,
  die sich nicht öffnen lässt (Zugriff verweigert, Sharing Violation,
  offline), keinen PHP-Worker mehr, und solche Dateien zählen als nicht
  lesbar. Eine lesbare leere Datei wird mit 200 beantwortet, nicht mit 400.
- Dateien, die 1.6.2 als Gateway-Fehler vermerkt hat, werden nach dem Update
  noch einmal geprüft, auch wenn ihre Wiederholungen aufgebraucht waren,
  sodass eine gesperrte oder abgewiesene Datei als nicht lesbar mit ihrer
  Abhilfe erscheint.
- Die synchrone Abdeckungszählung ist auf 25.000 Zeilen begrenzt, damit die
  Antwort auf langsamer Hardware innerhalb des Admin-Timeouts der Begleit-App
  bleibt; größere Instanzen sehen die Zahl nach dem Update einmal im
  Hintergrund gezählt.
- Der einmalige Nachhol-Durchlauf nach einem Update startet keine Runde mehr,
  wenn der Abgleich genau in diesem Augenblick ausgeschaltet wird.
- Eine vorübergehende Datenbanksperre während des ersten Index beendet den
  Durchlauf eines Speichers nicht mehr; der Abschnitt wird wenige Sekunden
  später erneut versucht, bis zu fünfmal hintereinander.

### Bekannte Einschränkungen

- SMB-Speicher unter serverseitiger Verschlüsselung wird wie bisher gelesen,
  ohne die Frist.
- Ein Netzwerkfehler zwischen der Prüfung und dem Öffnen einer Datei zählt als
  nicht lesbar; einige Wiederholungen folgen.
- Eine kurze Antwort für eine Datei, deren Größe Nextcloud nicht kennt, gilt
  als vollständig.
- Auf SMB ohne die Erweiterung php-smbclient endet eine Datei über etwa
  469 MiB vorzeitig und wird als hängend aufgegeben (nur mit
  FINDLING_MAX_FILE_BYTES über dem Standard von 50 MB).
- Auf SMB ohne die Erweiterung php-smbclient kann eine Leitung unter etwa
  420 KB/s einen 8-MiB-Leseblock nicht innerhalb des 20-s-Timeouts von
  smbclient liefern, sodass Dateien größer als ein Block als nicht lesbar
  zählen; die Erweiterung installieren oder die Timeout-Option des Speichers
  erhöhen (occ files_external:config).
- Eine Samba-Freigabe, deren Ordner serverseitig vom Nutzer abhängt (ein Pfad
  mit %U oder %S), zählt weiterhin als ein Baum für alle Nutzer.
- Speicher mit einer Id länger als 64 Zeichen, die sich nicht aus ihrer
  Konfiguration neu bilden lässt (globale oder vom Nutzer hinterlegte
  Zugangsdaten, ein Anmeldename ungleich der Nutzer-Id), werden je Speicher
  gezählt.
