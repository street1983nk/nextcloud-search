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

## Was sonst noch gilt

- Jeder Treffer wird von Nextcloud rechtegeprüft, in PHP auf dem Server, nicht
  im Container. Es gibt kein zweites, eigenes Rechtemodell, das driften könnte.
- Läuft die Begleit-App in einer anderen Major- oder Minor-Version als das
  Backend, antwortet die Suche mit nichts statt mit womöglich falschen
  Treffern, und die Verwaltungsseite nennt beide Versionsnummern.
- Messwerte, Methoden und Rohdaten zu allen Zahlen dieses Projekts:
  [performance.md](performance.md) und [embeddings.md](embeddings.md).
