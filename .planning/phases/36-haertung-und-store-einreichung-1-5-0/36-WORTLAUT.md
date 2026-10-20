# Phase 36: Wortlaut-Vorabplan (de, en, fr)

Stand: 20.10.2026, Entwurf aus Plan 36-01 auf Basis von Commit 47914ac9.
Status: **Entwurf, Owner-Abnahme offen** (Abschnitt E).

Grundlage: 36-CONTEXT.md, D-36-03 (eine Sammelklasse, Arbeitsname `blocked_malicious`, Detailgrund in der
Diagnose-Zeile), D-36-04 (Wortlaut vor Code und Katalogen), D-36-07 (Halbsatz `docs/embeddings.md`),
D-36-08 ("half of the box" präzisieren), D-36-14 (abgeschalteter Schalter ohne Karenz), D-36-16 (Faktenzeile
Ähnliche Dokumente plus CHANGELOG), D-36-17 (nur klare Angriffssignatur sperrt, exakte Schwellen hier);
36-RESEARCH.md Pattern 1 bis 3, Abschnitt "Bösartiger Korpus", Open Question 5; 36-PATTERNS.md "Zwei Befunde
dieser Analyse".

Regeln für alle Zeilen:

- Französisch nach `docs/l10n-french.md`: ASCII-Apostroph, einfaches Leerzeichen vor `:`, `;`, `?`, `!`,
  kein geschütztes Leerzeichen.
- Deutsch in der Sie-Form wie der Katalogbestand, wo der Satz den Leser anspricht. Abhilfe-Sätze der
  Admin-Karte stehen im Bestand im Infinitiv ("Die Datei außerhalb von Nextcloud prüfen und neu hochladen."),
  und mit "Keine." / "None." / "Aucune." am Anfang, wenn der Admin nichts tun muss; die neuen Abhilfen folgen
  diesem Bestand.
- Platzhalter wie im Bestand: `%s` bei einem Wert, `%1$s`/`%2$s` bei mehreren. Der Platzhalter der Detailzeile
  trägt ausschließlich einen Code aus der geschlossenen Liste in A3 (ASCII, `[a-z_]`), nie einen Dateinamen,
  Mitgliedsnamen oder Meldungstext (T-36-03, T-02-56).
- Vokabelregel E-H2: der Wortstamm "Archiv" ist in deutscher Prosa der Produkttexte, der Kataloge und in
  `docs/store-listing.md` gesperrt; die Wortlaute sagen "ZIP-Datei".
- Englische Quellschlüssel stehen so in der Tabelle, wie sie in `$l->t()` bzw. `t('findling', ...)` stehen
  werden.

## (A1) Klassenname und Zustand

- Wire-Code: `blocked_malicious` (ASCII, passt auf `[a-z_]` und auf `ERROR_CLASS_PATTERN`).
- Zustand: `skipped`, nicht `failed`. Eine gesperrte Datei ist eine Entscheidung des Backends, keine Panne;
  `failed` zählt die Statusseite als Fehler ("wir wollten und konnten nicht"), Research Anti-Pattern. Gleiche
  Einordnung wie `archive_limit` (31-02).
- Generation: 3, ohne neue Generation. Generation 3 ist mit 1.5.0 noch unveröffentlicht (Store: 1.4.3), die
  Klasse gehört dorthin wie `archive_limit`.
- Fallback für 1.4.x-Companions (Generation 2 und ohne Generation) in `nc/queue.py`: `skipped/blocked_malicious`
  geht als `skipped/too_large` über den Draht, ein theoretisches `failed/blocked_malicious` als `failed/corrupt`.
- Detailgrund: reist im bestehenden Feld `error_class` (state.db `file_errors`, `/diagnose` `errorClass`,
  Admin-Karte), ausschließlich als einer der acht Codes aus A3.

## (A2) Schlüsseltabelle

Neue Schlüssel: drei (Label, Abhilfe, Detail-Label), sofern O3 wie empfohlen beantwortet wird; ein vierter nur,
wenn O13 die `archive_limit`-Abhilfe ändert. Katalog-Schlüsselzahl damit 348 auf 351 (bzw. 352).

| Schlüssel (en) | de | fr | Platzhalter | Ort |
|---|---|---|---|---|
| File blocked as malicious | Datei als bösartig gesperrt | Fichier bloqué comme malveillant | keine | `AdminViewService::REASON_TEXT['blocked_malicious'][0]`, Label der Admin-Karte (Zeile neben `archive_limit`, um Zeile 527) |
| None. The file carries the signature of an attack (see the detail) and is not read any further, so the container keeps running. Remove or replace the file if it is not meant to be there. | Keine. Die Datei trägt die Signatur eines Angriffs (siehe Detail) und wird nicht weiter gelesen, damit der Container weiterläuft. Die Datei entfernen oder ersetzen, wenn sie dort nicht hingehört. | Aucune. Le fichier porte la signature d'une attaque (voir le détail) et n'est pas lu davantage, afin que le conteneur continue de fonctionner. Supprimer ou remplacer le fichier s'il n'a pas sa place ici. | keine | `REASON_TEXT['blocked_malicious'][1]`, Abhilfe der Admin-Karte |
| Detail: %s | Detail: %s | Détail : %s | `%s` = Detailcode aus A3 (`zip_ratio` usw.) | `php/js/admin.js:802`, Diagnose-Zeile `findling-diagnosis-errorclass`; nur für Zeilen im Zustand `skipped` (O3 (a)); `failed`-Zeilen behalten "Error class: %s" / "Fehlerklasse: %s" / "Classe d'erreur : %s" (Bestand) |
| None. ZIP files that are nested too deep, too large or hold too many files are skipped so the container keeps running. | Keine. ZIP-Dateien, die zu tief verschachtelt oder zu groß sind oder zu viele Dateien enthalten, werden übersprungen, damit der Container weiterläuft. | Aucune. Les fichiers ZIP trop imbriqués, trop volumineux ou contenant trop de fichiers sont ignorés afin que le conteneur continue de fonctionner. | keine | `REASON_TEXT['archive_limit'][1]`, NUR wenn O13 (b) gewählt wird; Empfehlung O13 (a): Bestandssatz mit "too densely packed" / "zu dicht gepackt" / "trop fortement compressés" bleibt, weil der Bereich über 100:1 bis zur Owner-Zahl aus O12 weiter `archive_limit` ist |

Hinweise zur Tabelle:

- Die Abhilfe sagt "nicht weiter gelesen" statt "nie gelesen": um die Signatur zu erkennen, liest das Backend
  die Struktur (Zentralverzeichnis, Kopf, Kette); den Inhalt liest es nicht. Ein "nie" wäre nicht wahr.
- "(siehe Detail)" verweist auf die Diagnose-Zeile direkt darunter; der Satz selbst nennt keinen Code und
  keinen Namen.
- Die Abhilfe nennt keine Rechte, keinen Nutzer und keinen Pfad; der Pfad steht wie im Bestand in der eigenen
  Pfadzeile der Karte.
- Das Wort "bösartig" / "malicious" / "malveillant" steht im Label, weil D-36-17 die Klasse nur bei einer
  Signatur vergibt, die kein normales Werkzeug erzeugt (A3).

## (A3) Zuordnungstabelle mit exakten Schwellen (D-36-17)

Konstanten heute (`backend/src/findling/config.py:402-433`, `extract/image.py:77`): `ARCHIVE_MAX_ENTRIES`
10 000, `ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES` 8 MiB, `ARCHIVE_MAX_RATIO` 100, `ARCHIVE_RATIO_MIN_BYTES` 1 MiB,
`ARCHIVE_MAX_DEPTH` 2, Summe der deklarierten Größen 256 MiB, `MAX_IMAGE_PIXELS` 50 MP (Pillow wirft
`DecompressionBombError` ab dem Doppelten, also über 100 MP). Neu: `ARCHIVE_MALICIOUS_RATIO` (Zahl aus O12,
Empfehlung 1000).

### Sperrt (blocked_malicious)

| Familie | Signal (exakt) | heute | neu | Detailcode |
|---|---|---|---|---|
| ZIP, Verhältnis | ein Mitglied mit deklarierter Größe >= `ARCHIVE_RATIO_MIN_BYTES` (1 MiB) und deklarierter Größe > `ARCHIVE_MALICIOUS_RATIO` x max(komprimierte Größe, 1), auf jeder Ebene; Empfehlung 1000 (O12) | skipped/archive_limit | skipped/blocked_malicious | `zip_ratio` |
| ZIP, Überlappung | `zipfile` meldet "Overlapped entries" (Muster `archive._is_overlap`), auf jeder Ebene (O2) | außen archive_limit, innen indexed | skipped/blocked_malicious | `zip_overlap` |
| ZIP, Pfad-Traversal | roher Mitgliedsname (`info.orig_filename` bzw. Name vor jeder Bereinigung) enthält ein Segment `..` (Trenner `/` oder `\`), beginnt mit `/` oder `\`, beginnt mit Laufwerksbuchstabe `[A-Za-z]:` oder enthält NUL | indexed (Name bereinigt) | skipped/blocked_malicious | `zip_traversal` |
| ODF/OOXML, Paket | Zentralverzeichnis eines ODF- oder OOXML-Pakets mit mehr als `ARCHIVE_MAX_ENTRIES` (10 000) Einträgen, gezählt vor `ZipFile()` (`count_central_directory`) | out_of_memory oder timeout möglich | skipped/blocked_malicious | `package_entries` |
| ODF/OOXML, XML-Bombe | libxml2- bzw. expat-Ausnahme, deren Meldung das Wort "amplification" trägt, beim Parsen eines ODF/OOXML-Teils (Meldung wird nur verglichen, nie gespeichert oder geloggt) | failed/xml_invalid bzw. failed/corrupt | skipped/blocked_malicious | `xml_entities` |
| Bild | Pillow wirft `DecompressionBombError` (mehr als 2 x 50 MP = 100 MP) UND Pixel je Dateibyte > 1000 | skipped/too_large | skipped/blocked_malicious | `image_pixels` |
| Mail | message/rfc822-Verschachtelung tiefer als 32 Ebenen | failed/corrupt | skipped/blocked_malicious | `mail_nesting` |
| OLE/CFB | Zyklus in FAT-, MiniFAT-, DIFAT- oder Verzeichniskette | failed/corrupt bzw. benanntes Urteil | skipped/blocked_malicious | `cfb_cycle` |

### Bleibt beim bisherigen Urteil

| Fall | Signal (exakt) | Urteil (unverändert) |
|---|---|---|
| ZIP, dicht gepackt, aber nicht extrem | Mitglied >= 1 MiB mit Verhältnis über `ARCHIVE_MAX_RATIO` (100) bis einschließlich `ARCHIVE_MALICIOUS_RATIO` (Empfehlung 1000); Positivkontrolle im Korpus etwa 150:1 ab 1 MiB | skipped/archive_limit |
| ZIP, ehrlich groß oder tief | mehr als 10 000 Einträge, Zentralverzeichnis über 8 MiB, Summe der deklarierten Größen über 256 MiB, Tiefe über 2 | skipped/archive_limit |
| Bild, groß, aber plausibel | über 100 MP mit höchstens 1000 Pixeln je Dateibyte (z. B. echte 102-MP-Mittelformataufnahme) | skipped/too_large |
| OLE/CFB, sonst kaputt | sonstige Strukturfehler ohne Zyklus | failed/corrupt |
| Übergroßer Einzeleintrag | ZIP-Mitglied über `max_file_bytes` bzw. Paketteil über 64 MiB | Name im Text, Datei indexiert bzw. skipped/too_large |
| Polyglotte | PDF+ZIP, GIFAR, JPEG+ZIP | Leser je Mimetype, kein eigenes Urteil; der Test verlangt nur ein benanntes Urteil |

### Begründung je Schwelle

- `zip_ratio` 1000:1 (Empfehlung O12): Deflate endet bei reinen Nullen am Format selbst (gemessen am
  20.10.2026 mit `zlib` im uv-Python des Backends, Rohdeflate wie im ZIP: 1 MiB Nullen 1015,1:1, 2 MiB
  1023,5:1, 50 MiB 1028,6:1 bei Stufe 4 bis 9; Stufe 1 bis 3 nur 228,9:1). Ehrliche Dateien liegen weit
  darunter (`config.py`: zehn echte Dateien von 1 bis 56 MB zwischen 1,1:1 und 17,9:1; ein synthetisches Log
  am 20.10.2026 8,0:1). Über 1000:1 kommt unter Deflate praktisch nur eine Füllung aus einem einzigen Byte
  vor, also eine Bombe. bzip2 und LZMA kommen bei 2 MiB Nullen auf 43 690,7:1 bzw. 5 447,1:1.
- Bereich 100 bis 1000:1 bleibt `archive_limit`: 100:1 ab 1 MiB trifft auch Sparse-Exporte, Dumps mit langen
  Leerfeldern und Logs mit Wiederholungen; das ist eine Grenze, keine Signatur (D-36-17 verlangt EXTREME
  Verhältnisse).
- `zip_overlap`: überlappende Einträge erzeugt kein normales Packprogramm; sie sind die Bauform der
  Überlappungsbombe.
- `zip_traversal`: `..`-Segmente, absolute Pfade, Laufwerksbuchstaben und NUL in Mitgliedsnamen erzeugt kein
  normales Packprogramm; sie zielen auf Entpacker, die unter dem Namen schreiben. Findling schreibt nie unter
  Mitgliedsnamen, die Sperre ist ein Urteil, keine Abwehr eines echten Schreibzugriffs.
- `package_entries` 10 000: ein Office-Paket hat typisch 10 bis 300 Teile; die Zahl ist dieselbe wie
  `ARCHIVE_MAX_ENTRIES`, damit es nur eine Grenze für Einträge gibt.
- `xml_entities`: libxml2 und expat melden "amplification" nur, wenn Entity-Expansion ein Vielfaches der
  Eingabe erzeugt; OPC/ECMA-376 und ODF brauchen keine eigenen Entities.
- `image_pixels` 1000 Pixel je Byte und über 100 MP: ein weißer 1-bit-Scan in CCITT G4 erreicht mehrere tausend
  Pixel je Byte, bleibt aber unter 100 MP (A4 bei 600 dpi: etwa 35 MP); erst beide Bedingungen zusammen
  ergeben eine Bombe. Annahme A1 der Research, keine Messung (O6).
- `mail_nesting` 32 Ebenen: Weiterleitungsketten echter Postfächer erreichen wenige Ebenen; 32 lässt Raum
  für automatisch weitergeleitete Ketten, der Korpusfall mit 1000 Ebenen bleibt weit darüber. Annahme A1 (O6).
- `cfb_cycle`: ein Zyklus in einer Sektorkette ist in einer gültigen OLE-Datei unmöglich; jeder Zyklus ist
  konstruiert.

## (A4) Fragen an den Owner

**O1: Klassenname und Zustand**
- (a) Wire-Code `blocked_malicious`, Zustand `skipped`, Generation 3, Fallback `too_large` bzw. `corrupt` für
  1.4.x-Companions (A1).
- (b) anderer Code (z. B. `hostile_file`) oder Zustand `failed`.
- Empfehlung: (a); `skipped` ist eine Entscheidung, keine Panne, und zählt nicht als Fehler auf der
  Statusseite.

**O2: Überlappung in einer INNEREN ZIP-Datei**
- (a) sperrt die ganze Datei (`zip_overlap` auf jeder Ebene); Folge: Korpusfall `inner-zip-with-overlap` in
  `backend/tests/test_phase31_audit.py` (Zeilen 292-297) wechselt von `INDEXED` auf
  `skipped/blocked_malicious`.
- (b) nur die äußere Ebene sperrt; die innere ZIP-Datei wird wie heute übergangen, die äußeren Mitglieder
  bleiben indexiert.
- Empfehlung: (a); die Signatur ist auf jeder Ebene dieselbe und gleich klar.

**O3: Label der Detailzeile**
- (a) "Detail: %s" / "Detail: %s" / "Détail : %s" für Zeilen im Zustand `skipped`; `failed`-Zeilen behalten
  "Error class: %s".
- (b) einheitlich "Error class: %s" auch für den Signaturcode (kein neuer Schlüssel).
- Empfehlung: (a); ein Signaturcode ist keine Fehlerklasse, und `skipped` ist kein Fehler.

**O4: Saat `seed-bomb.zip` (Pattern-Mapper-Befund 1)**
- Lage: `scripts/ci/make_upgrade_seed_formats.py` (Zeilen 26-30, 94-99, 247-254) baut die Saat mit Tiefe 3 und
  einem Nullen-Mitglied `nullen.bin`; die Datei liegt als `.github/fixtures/upgrade-seed-formats/seed-bomb.zip`
  im Repo. Die Verhältnisprüfung läuft in `archive._read_zip` vor der Tiefe. Gemessen am 20.10.2026: das
  Mitglied hat 1 048 771 Byte bei 6 608 Byte komprimiert, also 158,7:1.
- (a) Saat auf reine Tiefe 3 ohne Nullen-Mitglied umbauen; die Erwartung `skipped/archive_limit` in
  `.github/workflows/deploy-harp.yml` bleibt; keine bombenartige Füllung mehr als Binärdatei im Repo (D-36-01).
- (b) Erwartungen in `deploy-harp.yml` (Zeilen 5615-5644, 5700, 6134-6138, 6224) auf
  `skipped/blocked_malicious` ziehen. Nur richtig, wenn die O12-Zahl unter 158,7 liegt; bei der Empfehlung
  1000 bliebe die Saat `archive_limit`, und (b) machte die Upgrade-Strecke rot.
- Empfehlung: (a). Bei O12 (a) ist die Saat ohnehin `archive_limit`; der Umbau macht die Ursache eindeutig
  (Tiefe statt Verhältnis) und hält die Upgrade-Strecke als Beleg der Klasse `archive_limit`.

**O5: Korpusfall `name-nul-and-both-separators`**
- Heute `(State.INDEXED, None)` mit bereinigtem Namen (`test_phase31_audit.py` Zeilen 272-279; Namen
  `..\..\boese/../x<NUL>.txt.bin` und `/abs/../../y.txt`).
- (a) wird `skipped/blocked_malicious` mit Detail `zip_traversal`.
- (b) bleibt indexiert mit bereinigtem Namen.
- Empfehlung: (a), Bestätigung von D-36-17 ("Traversal-Pfade").

**O6: Schwellen Mailtiefe 32 und 1000 Pixel je Byte**
- Beide sind Abwägungen (Annahme A1 der Research), keine Messungen.
- (a) bestätigen.
- (b) andere Zahl je Schwelle nennen.
- Empfehlung: (a); die Bildregel greift ohnehin erst über 100 MP, die Mailtiefe liegt um ein Vielfaches über
  echten Weiterleitungsketten.

**O7: Reihenfolge in `archive._read_zip`**
- Heute: Einträge zählen, Summe der deklarierten Größen (über 256 MiB: `archive_limit`), dann Verhältnis je
  Mitglied. Der Korpusfall `lying-huge` (deklariert 0xFFFFFFF0 Byte bei 5 Byte Inhalt) bleibt nur
  `archive_limit`, wenn die Summe vor dem Verhältnis geprüft wird.
- (a) Reihenfolge bleibt; `lying-huge` bleibt `archive_limit`.
- (b) Verhältnis vor Summe; `lying-huge` wird `zip_ratio`.
- Empfehlung: (a); eine einzelne lügende Größenangabe ist eine Grenzverletzung, und die Upgrade-Strecke bleibt
  unberührt.

**O12: Schwelle für `blocked_malicious/zip_ratio` (D-36-17 "extreme Kompressionsverhältnisse")**
- Der Owner nennt eine ZAHL für `ARCHIVE_MALICIOUS_RATIO`.
- Fakten: heute sperrt `ARCHIVE_MAX_RATIO` = 100 ab 1 MiB als `archive_limit`. Ehrliche Textlogs, CSV-Exporte,
  Sparse-Dateien und Dumps erreichen unter Deflate 10:1 bis einige 100:1. Deflate erreicht bei reinen Nullen
  höchstens etwa 1032:1 (theoretische Grenze 258 Byte je Match); gemessen am 20.10.2026: 2-MiB-Nullen-Mitglied
  unter Deflate 1023,5:1 (Stufe 4 bis 9), 1 MiB 1015,1:1, 50 MiB 1028,6:1; mit Stufe 1 bis 3 nur 228,9:1.
  bzip2: 43 690,7:1, LZMA: 5 447,1:1 (je 2 MiB Nullen).
- (a) Bereich über 100 bis einschließlich 1000:1 bleibt `archive_limit`, erst über 1000:1
  `blocked_malicious/zip_ratio`.
- (b) eine andere Zahl im Bereich 100 bis etwa 1000:1, vom Owner genannt.
- (c) eine Zahl über 1032:1; dann sperren nur bzip2-/LZMA-Mitglieder und kein einziges Deflate-Mitglied, und
  verschachtelte Bomben erst dann, wenn eine Ebene selbst über der Zahl liegt.
- Empfehlung: (a), Zahl 1000. Über 1000:1 liegt unter Deflate praktisch nur eine Füllung aus einem Byte, also
  eine klare Bombe; eine mit Stufe 1 bis 3 gepackte Nullenbombe (228,9:1) bleibt `archive_limit` und wird
  trotzdem nicht gelesen.
- Folge für den Korpus (36-07) und die Tests (36-08): Positivkontrolle mit etwa 150:1 ab 1 MiB bleibt
  `archive_limit`; ein Fall knapp über der Owner-Zahl wird `zip_ratio`, ein Fall knapp darunter bleibt
  `archive_limit`.
- Folge für O4: liegt das Nullen-Mitglied von `seed-bomb.zip` (158,7:1) unter der Owner-Zahl, ist Weg (b)
  falsch und der Status quo wirkungsgleich mit Weg (a) im Urteil.

**O13: Abhilfe von `archive_limit` (Zusatzfrage dieses Entwurfs)**
- Der Plan sah vor, "too densely packed" aus der `archive_limit`-Abhilfe zu streichen. Das gilt nur, wenn
  `archive_limit` keine dicht gepackten Dateien mehr trägt; nach O12 (a) oder (b) bleibt der Bereich über
  100:1 bis zur Owner-Zahl aber `archive_limit`.
- (a) Bestandssatz bleibt unverändert (kein neuer Schlüssel): "None. ZIP files that are nested too deep, too
  large, too densely packed or hold too many files are skipped so the container keeps running."
- (b) Satz ohne "too densely packed" aus Tabelle A2, nur sinnvoll bei O12 mit der Zahl 100.
- Empfehlung: (a); der Satz bleibt wahr, und 16 Kataloge bleiben an dieser Stelle unberührt.

**Feststellungen ohne Frage:** D-36-13 (Upgrade-Strecke ab v1.4.3, `UPGRADE_FROM_TAG` erst nach dem Bump) und
D-36-14 (abgeschalteter Findling-Schalter: keine Karenz, Entfernen im nächsten vollständigen Abgleich über die
bestehende Ausschluss-Mechanik; Karenz von 30 Tagen nur für Speicher, die aus `oc_storages`/Mounts echt weg
sind) sind entschieden.

## (A5) Vorab-Prüfung Teil A

Die Entwurfstexte aus A2 (alle de-, en- und fr-Zellen der vier Zeilen, zwölf Zeilen) lagen am 20.10.2026 als
Scratch-Datei vor und wurden per `grep` geprüft, jede Prüfung mit einer Positivkontrolle:

- Gesperrter Wortstamm aus `backend/tests/test_public_artifacts.py` (`BLOCKED_TERM`, ohne Rücksicht auf Groß-
  und Kleinschreibung) in allen zwölf Zeilen: kein Fund (0); in den vier deutschen Zeilen: kein Fund (0);
  Positivkontrolle auf "Die Archivdatei" schlägt an (1).
- Halbgeviert- und Geviertstriche (U+2013, U+2014) in der Scratch-Datei: 0; in dieser ganzen Datei: 0;
  Positivkontrolle 1.
- Platzhalter `%s` je Sprache: de 1, en 1, fr 1 (gleich; nur in "Detail: %s").
- Französische Typografie: U+2019, U+00A0, U+202F: 0 (Positivkontrolle 1); Doppelpunkt ohne Leerzeichen
  davor: 0.
- Ziffern in den zwölf Zeilen: 0 (keine Zahl in den Sätzen).
