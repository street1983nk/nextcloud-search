# Datenschutz: was Findling speichert und wer es lesen kann

Dieses Dokument beantwortet die drei Fragen, die ein Admin vor dem Einsatz auf
vertraulichen Beständen stellen sollte: Was liegt wo? Wer kann es lesen? Und
was ist dagegen zu tun? Es ist bewusst ehrlich gehalten: die eine Zeile, die
andere Projekte gern weglassen, steht hier zuerst.

## Die eine Zeile zuerst

**Der Index ist nicht verschlüsselt gespeichert.** Er enthält den extrahierten
Text der indexierten Dokumente. Wer das App-Volume des Backends oder eine
Sicherung dieses Volumes lesen kann, kann diesen Text lesen, unabhängig von
den Nextcloud-Rechten. Die Abhilfen stehen weiter unten.

## Was gespeichert wird und wo

Alles liegt im Datenbereich der Backend-App (dem App-Volume) auf Ihrem eigenen
Server. Es gibt keinen Dienst dazwischen und nichts verlässt die Instanz, keine
Telemetrie, keine Cloud-Abfrage, kein Modelldownload zur Laufzeit (das
eingebaute Modell reist im Container-Abbild mit).

Im Einzelnen:

- **Volltextindex (Tantivy):** der extrahierte Text jeder indexierten Datei in
  durchsuchbarer Form, dazu Dateiname, Pfad und Metadaten wie Änderungszeit.
  Seit 1.5 gehören bei Mails (.eml) die Kopfzeilen Betreff, Von, An und Cc
  samt Mailadressen sowie die Namen der Anhänge zum durchsuchbaren Text (Bcc
  und Anhanginhalte nicht); ein Treffer läuft durch dieselbe Rechteprüfung wie
  jeder andere Inhalt.
- **Semantischer Index (SQLite mit sqlite-vec):** Textabschnitte und ihre
  Vektoren. Die Vektoren selbst sind kein Klartext, die Abschnitte daneben
  schon.
- **Zustandsdaten:** Warteschlange, Fehlerdiagnosen je Datei, Versionsmarken.
  Fehlerdiagnosen nennen Dateiname und Fehlerart, nie Dateiinhalt.

Die Originaldateien werden nie verändert. Gelöschte Dateien verschwinden über
die Ereignisverarbeitung auch aus dem Index.

## Wer den Index lesen kann

- **Nicht aus dem Browser:** die Routen, die Inhalte liefern, sind nur über
  AppAPI/HaRP erreichbar. Jeder Suchtreffer läuft vor der Anzeige durch die
  Rechteprüfung der PHP-Begleit-App auf dem Nextcloud-Server.
- **Wohl aber vom Host:** wer auf dem Server Root- oder Docker-Rechte hat,
  kann das App-Volume lesen, so wie er auch die Nextcloud-Datenverzeichnisse
  lesen kann. Findling erweitert diesen Personenkreis nicht, aber der Index
  bündelt Inhalte vieler Nutzer an einem Ort.
- **Und jeder Leser einer Sicherung:** eine Kopie des App-Volumes enthält den
  extrahierten Text aller indexierten Dokumente.

## Abhilfen

1. **Festplattenverschlüsselung des Hosts** (LUKS/dm-crypt unter Linux,
   BitLocker unter Windows-Hosts). Das ist die richtige Ebene: sie schützt
   den Index genauso wie die Nextcloud-Daten daneben, gegen denselben Angriff
   (entwendeter oder ausgemusterter Datenträger).
2. **Sicherungen bewusst behandeln.** Zwei saubere Wege:
   entweder das App-Volume von der Sicherung ausnehmen, der Index ist aus den
   Dateien vollständig reproduzierbar und baut sich nach einer Wiederherstellung
   neu auf; oder die Sicherung des Volumes genauso verschlüsseln und
   zugriffsbeschränken wie die Sicherung der Nutzdaten. Nicht sauber ist nur
   der dritte Weg: die Dateisicherung streng behandeln und die Volume-Sicherung
   vergessen.
3. **Ausnehmen statt indexieren.** Was gar nicht erst im Index liegen soll,
   gehört nicht in den indexierten Bestand. Ende-zu-Ende-verschlüsselte Ordner
   kann der Server prinzipbedingt nicht lesen; ihr Inhalt landet deshalb nie im
   Index.

Ein Hinweis zur serverseitigen Verschlüsselung von Nextcloud: sie schützt die
Dateien im Datenverzeichnis, nicht den Findling-Index. Das Backend liest die
Dateien über die Nextcloud-Schnittstellen und erhält dort Klartext, der
extrahierte Text liegt also auch dann unverschlüsselt im Index, wenn die
Dateien selbst verschlüsselt gespeichert sind. Auch dafür ist die
Festplattenverschlüsselung des Hosts die passende Antwort.

## Warum Findling den Index nicht selbst verschlüsselt

Die kurze Antwort: weil es Sicherheit nur vortäuschen würde.

Die längere: Der Volltextindex liegt als Tantivy-Index auf der Platte und wird
über mmap gelesen; eine transparente Verschlüsselungsschicht gibt es dort
nicht. Eine selbst gebaute Schicht davor wäre eigenes Krypto in einer
Suchanwendung, genau die Sorte Konstruktion, vor der jedes Audit warnt. Und
der entscheidende Punkt: der Schlüssel müsste auf derselben Maschine liegen,
damit die Suche ohne Zutun funktioniert (Zero-Config ist das Kernversprechen
dieser App). Ein Angreifer mit Lesezugriff auf das Volume hätte in fast allen
realen Szenarien auch Zugriff auf den Schlüssel daneben. Gewonnen wäre nichts,
verloren wären Geschwindigkeit, Einfachheit und Prüfbarkeit.

Die Festplattenverschlüsselung des Hosts löst dasselbe Problem eine Ebene
tiefer, mit geprüftem Krypto, für den Index und die Nextcloud-Daten zugleich.

## Wasserzeichen von Nextcloud Office (ab 1.7.0)

- **Wer liest:** Findling öffnet eine Datei ohne angemeldete Person. Nur wenn
  die Secure View von Nextcloud Office (Wasserzeichen) dieses Öffnen ablehnt,
  liest Findling die Datei einmal erneut im Namen einer Person, die sie lesen
  darf: zuerst als Besitzer, ohne erkennbaren Besitzer als einer der übrigen
  Nutzer, höchstens 20. Die Prüfspur (admin_audit) nennt für diesen
  Lesevorgang diese Person: neben der eigenen Zeile von admin_audit, die die
  angemeldete Person der Anfrage nennt (hier keine, `--`), schreibt Findling
  eine Zeile `Findling read the file with id "<id>" at "<Pfad>" as the user
  "<uid>" after the secure view of Nextcloud Office refused it without a user`,
  mit Datei-ID, Pfad und Nutzer, nie mit Inhalt. Ohne admin_audit entsteht diese
  Zeile nicht. Die info-Zeile `Findling: read a file as a reader of it after
  secure view refused the first open` in `nextcloud.log` nennt dieselbe Person
  unter `reader`. Für jede andere Datei bleibt es wie in 1.6.5 bei einem Lesen
  ohne Person.
- **Team Folder:** groupfolders meldet für einen Team Folder die lesende Person
  selbst als Besitzer. Unter `watermark_shareAll` darf ein Mitglied eine Datei
  im Team Folder deshalb selbst herunterladen, und Findling liest sie nach der
  Ablehnung des ersten Öffnens als dieses Mitglied; es liest damit nur, was die
  Person selbst herunterladen darf.
- **Keine Umgehung:** gilt das Wasserzeichen auch für diese Personen oder lehnt
  eine andere Regel das Öffnen ab, liest Findling die Datei nicht, sondern
  urteilt `policy_blocked` ("Durch eine Regel blockiert").
- **Keine Textausschnitte:** Suchtreffer einer Datei, die die suchende Person
  nur unter dem Wasserzeichen sehen darf, zeigen Name und Pfad, aber keinen
  Textausschnitt. In den Modi für fremde Dateien (`watermark_shareAll`,
  `watermark_shareRead`, `watermark_shareDisabledDownload`) zeigt bei aktivem Wasserzeichen
  keine fremde Datei einen Ausschnitt, auch eine Freigabe mit Download nicht:
  ob eine Freigabe ohne Download hinter einem Treffer steht, lässt sich mit den
  öffentlichen Schnittstellen von Nextcloud nicht sicher erkennen, deshalb
  unterdrückt Findling lieber einen Ausschnitt zu viel. Das gilt auch für
  Treffer aus einem Inhalt, der vor dem Einschalten des Wasserzeichens indexiert
  wurde.

## Was sonst noch gilt

- Jeder Treffer wird von Nextcloud rechtegeprüft, in PHP auf dem Server, nicht
  im Container. Es gibt kein zweites, eigenes Rechtemodell, das driften könnte.
- Läuft die Begleit-App in einer anderen Major- oder Minor-Version als das
  Backend, antwortet die Suche mit nichts statt mit womöglich falschen
  Treffern, und die Verwaltungsseite nennt beide Versionsnummern.
- Findling schreibt weder Suchbegriffe noch Pfade oder Ordnernamen in seine
  Logzeilen. Nextcloud selbst hängt aber an jede Zeile in `nextcloud.log` die
  Adresse der laufenden Anfrage an, und die Adresse einer Suche enthält den
  Suchbegriff und, mit dem Ordnerfilter der Unified Search, den gewählten
  Ordner. Entsteht während einer Suche eine Zeile, steht beides also daneben:
  bei einer Störung des Backends (nicht erreichbar, Fehlerantwort, verschiedene
  Versionen; Warnungen von AppAPI und Findling), auf dem Loglevel info bei einem
  Backend-Aufruf über einer Sekunde und auf dem Loglevel debug. Im
  Normalbetrieb auf der Voreinstellung (Warnung) schreibt eine Suche keine
  Zeile.
- Messwerte, Methoden und Rohdaten zu allen Zahlen dieses Projekts:
  [performance.md](performance.md) und [embeddings.md](embeddings.md).
