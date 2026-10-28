# Phase 36: Wortlaut-Vorabplan (de, en, fr)

Stand: 20.10.2026, Entwurf aus Plan 36-01 auf Basis von Commit 47914ac9.
Status: **abgenommen am 20.10.2026** (Option A, alle Empfehlungen (a); Abschnitt E).

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

# (B) Entwurf v1.5.0 (Gesamttext)

Grundlage: Store-Text 1.4.3 (`docs/store-listing.md` Zeilen 120-370, heute im Store), die Teile der Phasen 30
bis 34 (`docs/store-listing.md` ab Zeile 2020), der Stand beider `info.xml` (Teil Phase 30 und Teil Phase 31
stehen dort schon), D-36-08 und D-36-16. Owner-Regel Kurztext: Faktenliste, höchstens eine Messzahl (730,2),
Details nur als Verweis auf `docs/`.

## (B1) Die sechs Beschreibungen

So, wie sie in die `info.xml` gehen (CDATA-Inhalt), ohne Doppelzeilen. Platz der neuen Zeilen in der
Funktionsliste von `findling`: Filter hinter der Volltextzeile, Ähnliche Dokumente hinter der semantischen
Suche, Ausschlüsse hinter "Keine Konfiguration" (Vorschlag Teil Phase 33). In `findling_backend` stehen
dieselben drei Zeilen hinter der Zeile "Leistungsprofil und Suchmodell", weil diese Liste keine Volltext-,
Semantik- oder Konfigurationszeile hat. Die Umstiegszeile (Teil Phase 34) steht als eigene Zeile direkt
hinter der Funktionsliste, vor "Known limitations:".

### `findling`, en (ohne `lang`)

```
What Findling does:
- Full text search in the normal Nextcloud search bar
- Filter by file type or folder directly in the Nextcloud search
- OCR for scanned PDFs and images: ten languages available, German, English and French are the default
- Semantic search: finds documents through paraphrases
- Similar documents: a link at every hit on the results page lists files with related content
- Every result is permission-checked by Nextcloud
- No configuration: the first index run starts on its own
- Exclude folders or patterns such as *.photoslibrary from the index
- Performance profiles: Economy by default, Standard and Performance after a pre-check of the hardware
- Search model: int8 built in, the more accurate fp32 can be downloaded once under Standard and Performance
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch, Portuguese and Czech available

Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.en.md)

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text
- Czech: no stemming, inflected forms count as separate words

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOC, DOCX, PPTX, XLS, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV, mails (EML)
- ZIP files: the files inside, without OCR
- Images through OCR: JPEG, PNG, TIFF, WebP, HEIC

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the machine the backend runs on (Standard profile) or everything but one core (Performance profile).

Enterprise support and paid add-ons: request a quote at admin@infranode.dev
```

### `findling`, de

```
Was Findling kann:
- Volltextsuche über die normale Nextcloud-Suchleiste
- Filter nach Dateityp oder Ordner direkt in der Nextcloud-Suche
- Texterkennung für gescannte PDFs und Bilder: zehn Sprachen verfügbar, voreingestellt sind Deutsch, Englisch und Französisch
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Ähnliche Dokumente: ein Link an jedem Treffer der Ergebnisseite listet Dateien mit verwandtem Inhalt
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst
- Ordner oder Muster wie *.photoslibrary vom Index ausschließen
- Leistungsprofile: Sparsam voreingestellt, Standard und Leistung nach einer Vorab-Prüfung der Hardware
- Suchmodell: int8 eingebaut, das genauere fp32 unter Standard und Leistung einmalig ladbar
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch, Portugiesisch und Tschechisch verfügbar

Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.md)

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext
- Tschechisch: keine Stammformreduktion, gebeugte Formen gelten als eigene Wörter

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOC, DOCX, PPTX, XLS, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV, Mails (EML)
- ZIP-Dateien: die enthaltenen Dateien, ohne Texterkennung
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP, HEIC

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil frei: höchstens die Hälfte der Maschine, auf der das Backend läuft (Profil Standard), oder alles bis auf einen Kern (Profil Leistung).

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev
```

### `findling`, fr

```
Ce que Findling sait faire :
- Recherche plein texte dans la barre de recherche normale de Nextcloud
- Filtre par type de fichier ou par dossier directement dans la recherche Nextcloud
- Reconnaissance optique pour les PDF numérisés et les images : dix langues disponibles, allemand, anglais et français par défaut
- Recherche sémantique : trouve les documents par des périphrases
- Documents similaires : un lien sur chaque résultat de la page de résultats liste les fichiers au contenu proche
- Chaque résultat est vérifié par Nextcloud selon vos droits
- Aucune configuration : la première indexation démarre d'elle-même
- Exclure de l'index des dossiers ou des motifs comme *.photoslibrary
- Profils de performance : Économe par défaut, Standard et Performance après une vérification préalable du matériel
- Modèle de recherche : int8 intégré, le fp32 plus précis se télécharge une fois sous Standard et Performance
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais, portugais et tchèque disponibles

Passer de fulltextsearch/Elasticsearch à Findling : [étapes dans la documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.fr.md)

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents
- Tchèque : pas de racinisation, les formes fléchies comptent comme des mots distincts

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOC, DOCX, PPTX, XLS, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV, e-mails (EML)
- Fichiers ZIP : les fichiers contenus, sans OCR
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP, HEIC

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine sur laquelle tourne le service (profil Standard) ou tout sauf un cœur (profil Performance).

Support entreprise et modules payants : demande de devis à admin@infranode.dev
```

### `findling_backend`, en (ohne `lang`)

```
What Findling Backend is:
- The External App behind the Findling search app: text extraction, OCR and the search index
- Runs entirely inside your own instance and does nothing without the Findling app
- Never modifies your files
- Performance profile and search model are chosen on the admin page of the Findling app
- Filter by file type or folder directly in the Nextcloud search
- Similar documents: a link at every hit on the results page lists files with related content
- Exclude folders or patterns such as *.photoslibrary from the index
- Privacy: everything runs locally, no telemetry, nothing leaves your server
- Search languages: German and English by default, Spanish, Italian, Dutch, Portuguese and Czech available

Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.en.md)

Known limitations:
- Spanish: año and ano are treated as the same word
- Portuguese: spellings before and after the spelling reform are not unified
- Compound words are split for German and Dutch only
- French has no full text analysis chain for document text
- Czech: no stemming, inflected forms count as separate words

Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server.

Supported file types:
- PDF (scanned too), DOC, DOCX, PPTX, XLS, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV, mails (EML)
- ZIP files: the files inside, without OCR
- Images through OCR: JPEG, PNG, TIFF, WebP, HEIC

Requirements:
- Nextcloud 33 to 35, apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB is enough, 730.2 MB resident after an index run, under a hard 2 GB limit (measured)
- CPU: 2 cores are enough, amd64 and arm64

Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the machine the backend runs on (Standard profile) or everything but one core (Performance profile).

Enterprise support and paid add-ons: request a quote at admin@infranode.dev
```

### `findling_backend`, de

```
Was Findling Backend ist:
- Die External App hinter der Such-App Findling: Textauszug, Texterkennung und der Suchindex
- Läuft komplett in Ihrer eigenen Instanz und tut ohne die App Findling nichts
- Verändert nie Ihre Dateien
- Leistungsprofil und Suchmodell werden in der Verwaltung der App Findling gewählt
- Filter nach Dateityp oder Ordner direkt in der Nextcloud-Suche
- Ähnliche Dokumente: ein Link an jedem Treffer der Ergebnisseite listet Dateien mit verwandtem Inhalt
- Ordner oder Muster wie *.photoslibrary vom Index ausschließen
- Datenschutz: alles läuft lokal, keine Telemetrie, nichts verlässt den Server
- Suchsprachen: Deutsch und Englisch voreingestellt, Spanisch, Italienisch, Niederländisch, Portugiesisch und Tschechisch verfügbar

Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.md)

Bekannte Grenzen:
- Spanisch: año und ano gelten als dasselbe Wort
- Portugiesisch: Schreibweisen vor und nach der Rechtschreibreform werden nicht vereinheitlicht
- Zusammengesetzte Wörter werden nur für Deutsch und Niederländisch zerlegt
- Französisch hat keine eigene Analysekette für den Dokumenttext
- Tschechisch: keine Stammformreduktion, gebeugte Formen gelten als eigene Wörter

Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server.

Unterstützte Dateitypen:
- PDF (auch gescannt), DOC, DOCX, PPTX, XLS, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV, Mails (EML)
- ZIP-Dateien: die enthaltenen Dateien, ohne Texterkennung
- Bilder per Texterkennung: JPEG, PNG, TIFF, WebP, HEIC

Anforderungen:
- Nextcloud 33 bis 35, Apps: AppAPI, Findling Backend (External Apps), Findling
- RAM: 4 GB genügen, 730,2 MB resident nach einem Indexlauf, unter einer harten 2-GB-Grenze (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64

Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil frei: höchstens die Hälfte der Maschine, auf der das Backend läuft (Profil Standard), oder alles bis auf einen Kern (Profil Leistung).

Enterprise-Support und bezahlte Add-ons: Angebot anfordern unter admin@infranode.dev
```

### `findling_backend`, fr

```
Ce qu'est Findling Backend :
- L'External App derrière l'application de recherche Findling : extraction de texte, reconnaissance optique et index
- Fonctionne entièrement dans votre propre instance et ne fait rien sans l'application Findling
- Ne modifie jamais vos fichiers
- Le profil de performance et le modèle de recherche se choisissent dans la page d'administration de l'application Findling
- Filtre par type de fichier ou par dossier directement dans la recherche Nextcloud
- Documents similaires : un lien sur chaque résultat de la page de résultats liste les fichiers au contenu proche
- Exclure de l'index des dossiers ou des motifs comme *.photoslibrary
- Confidentialité : tout fonctionne localement, aucune télémétrie, rien ne quitte votre serveur
- Langues de recherche : allemand et anglais par défaut, espagnol, italien, néerlandais, portugais et tchèque disponibles

Passer de fulltextsearch/Elasticsearch à Findling : [étapes dans la documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.fr.md)

Limites connues :
- Espagnol : año et ano sont traités comme le même mot
- Portugais : les graphies d'avant et d'après la réforme orthographique ne sont pas unifiées
- Les mots composés ne sont découpés que pour l'allemand et le néerlandais
- Le français n'a pas de chaîne d'analyse plein texte pour le contenu des documents
- Tchèque : pas de racinisation, les formes fléchies comptent comme des mots distincts

Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur.

Types de fichiers pris en charge :
- PDF (numérisés aussi), DOC, DOCX, PPTX, XLS, XLSX, ODT, ODS, ODP
- HTML, RTF, TXT, Markdown, CSV, e-mails (EML)
- Fichiers ZIP : les fichiers contenus, sans OCR
- Images par reconnaissance optique : JPEG, PNG, TIFF, WebP, HEIC

Prérequis :
- Nextcloud 33 à 35, applications : AppAPI, Findling Backend (External Apps), Findling
- RAM : 4 Go suffisent, 730,2 Mo résidents après une indexation, sous une limite stricte de 2 Go (mesuré)
- CPU : 2 cœurs suffisent, amd64 et arm64

Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine sur laquelle tourne le service (profil Standard) ou tout sauf un cœur (profil Performance).

Support entreprise et modules payants : demande de devis à admin@infranode.dev
```

### Unterschiede zum Store-Text 1.4.3, je Sprache gleich gebaut

- Teil Phase 30: OCR-Zeile (nur `findling`) "nine"/"neun"/"neuf" wird "ten"/"zehn"/"dix"; Suchsprachen-Zeile
  um Tschechisch ergänzt; Grenzliste um den fünften Eintrag Tschechisch ergänzt.
- Teil Phase 31: Dateitypen-Liste mit DOC, XLS, Mails (EML), ZIP-Zeile und HEIC (zeichengleich aus Teil 1 der
  Phase 31).
- Teil Phase 32 (neu in der Funktionsliste): Filterzeile.
- Teil Phase 33 (neu in der Funktionsliste): Ausschlusszeile.
- D-36-16 (neu in der Funktionsliste): Zeile "Ähnliche Dokumente".
- Teil Phase 34 (neu, eigene Zeile hinter der Funktionsliste): Umstiegszeile mit Tag-Link `blob/v1.5.0`.
- D-36-08: Profilsatz sagt statt "half of the box" / "die Hälfte der Box" / "la moitié de la machine" jetzt
  "half of the machine the backend runs on" / "die Hälfte der Maschine, auf der das Backend läuft" / "la moitié
  de la machine sur laquelle tourne le service".
- Unverändert: Name, Summary, MCP-Satz, Anforderungen samt Messzahl 730,2, Enterprise-Zeile, Grenzliste
  Einträge eins bis vier.

Hinweise zu B1:

- Französisch sagt "le service" statt "le backend", weil `docs/l10n-french.md` (Wortwahl, Zeile "the backend")
  das so festlegt; der Eigenname "Findling Backend" bleibt, wo die App gemeint ist.
- Die Ähnlich-Zeile nennt keine Zahl (höchstens zehn Nachbarn stehen in `docs/`) und keine Rechte: der Satz
  "Every result is permission-checked by Nextcloud" gilt für die Ähnlich-Liste mit. Wer die Rechte in der Zeile
  will, bekommt den Zusatz ", only from files you can read" / ", nur aus Dateien, die Sie lesen dürfen" /
  ", uniquement parmi les fichiers que vous pouvez lire" (Teil von O8).
- Die Zeile spricht von der "Ergebnisseite" / "results page" / "page de résultats", weil der Link nur dort steht
  (35-WORTLAUT, O1), nicht im Aufklappfeld der Nextcloud-Suchleiste.

## (B2) README-Zeilen

Je README geändert bzw. neu, die übrigen Zeilen bleiben:

- `README.md`, Funktionsliste "Was Findling kann": neue Zeilen "Filter nach Dateityp oder Ordner direkt in der
  Nextcloud-Suche" (hinter der Volltextzeile), "Ähnliche Dokumente: ein Link an jedem Treffer der Ergebnisseite
  listet Dateien mit verwandtem Inhalt" (hinter "Semantische Suche"), "Ordner oder Muster wie *.photoslibrary
  vom Index ausschließen" (hinter "Keine Konfiguration"). Anforderungen, Zeile 61: "gibt per Profil frei:
  höchstens die Hälfte der Maschine, auf der das Backend läuft (Profil Standard), oder alles bis auf einen Kern
  (Profil Leistung)".
- `README.en.md`, "What Findling does": dieselben drei Zeilen wie Store en; Anforderungen: "free at most half of
  the machine the backend runs on (Standard profile) or everything but one core (Performance profile)".
- `README.fr.md`, "Ce que Findling sait faire": dieselben drei Zeilen wie Store fr; Prérequis, Zeile 64: "un
  profil libère au plus la moitié de la machine sur laquelle tourne le service (profil Standard) ou tout sauf un
  cœur (profil Performance)".
- Unverändert: Zeile "Phrasen, Ausschlüsse, Dateityp-Filter" (Suchsyntax, Teil Phase 33), Dateitypen-Absatz und
  Verweis auf `docs/formats.md` (Teil Phase 31), Abschnitt "Umstieg von fulltextsearch" (Teil Phase 34, relativer
  Link).
- Tag-Links: die READMEs tragen heute keinen Link `blob/v1.5.0` (geprüft per `grep -n "blob/v1\." README*.md`:
  kein Fund); Tag-Links `blob/v1.5.0` stehen nur in den sechs Beschreibungen (Umstiegszeile) und lösen erst
  nach dem Tag auf (Prüfung in 36-14).

## (B3) CHANGELOG `[1.5.0]` (englisch, Faktenliste)

Der Abschnitt `[Unreleased]` wird zu `[1.5.0]` mit dem Datum des Tags; sein Inhalt bleibt vollständig, neu sind
die mit (neu) markierten Punkte (die Markierung steht nur hier, nicht im CHANGELOG).

```
## [1.5.0] - <date of the tag>

### Added

- Mails (.eml): subject, sender, recipients, text and the names of
  attachments; attachment content is not read.
- ZIP files: the text of the files inside, without OCR, within fixed limits
  (docs/formats.md); a ZIP file stands in no type filter group.
- Word 97 to 2003 (.doc) and Excel 97 to 2003 (.xls), read without
  LibreOffice; .xls under the cell limit of XLSX.
- HEIC and HEIF photos through OCR.
- The excerpt of a hit inside a ZIP file names the inner file.
- A one time catch up after the upgrade, without a full reindex: files of
  the new types, old Word and Excel files under OOXML names, and files given
  up as repeatedly stuck are read once more.
- (neu) Czech as a search language, without stemming, and Czech OCR; OCR
  offers ten languages (docs/language-analyzers.md).
- Unified search: filter Findling hits by type group (six entries) or by
  folder, sub folders included; unknown values are ignored
  (docs/search-filters.md).
- Exclusion patterns with `*` and `?` on the admin page, for example Mac
  bundles (`*.photoslibrary`) or build folders (`*/node_modules/*`); existing
  folder exclusions keep working. At most 32 patterns of 60 characters
  (docs/admin-page.md) (#22).
- The admin page shows the limits per file read only, with how to change
  them (#21).
- A migration page from fulltextsearch/Elasticsearch in German, English and
  French (docs/migrate-from-fulltextsearch.md).
- A banner on the admin page while fulltextsearch or files_fulltextsearch is
  enabled, with a link to that page.
- (neu) Similar documents: a link at every hit on the results page lists up
  to ten files with related content, only files the user can read.
- (neu) Hostile files end as skipped with the new code blocked_malicious and
  a detail code on the admin page (zip_ratio, zip_overlap, zip_traversal,
  package_entries, xml_entities, image_pixels, mail_nesting, cfb_cycle);
  files that are only large keep their old verdict (docs/formats.md).
- (neu) Index hygiene: documents of deleted users and deleted storages leave
  the index at the next reconcile; a storage that still exists in Nextcloud
  but is no longer mounted leaves after 30 days.
- (neu) Releases carry the source of the tag and the four corresponding
  source packages of the native libraries in the image.

### Changed

- Files under a rule leave the index at the next reconcile even when they
  did not change, and their old entries leave the error list (#22).
- The hint about too little hardware for a profile is reworded in all
  languages.
- (neu) The httpx and httpcore loggers run at WARNING in the image, so file
  ids and user ids no longer appear in the standard log; DEBUG still shows
  them.
- (neu) Store texts: the Standard profile frees at most half of the machine
  the backend runs on (was: half of the box).

### Fixed

- A file whose size in Nextcloud's file cache is larger than the file is now
  read when two downloads agree, instead of ending as repeatedly stuck
  (POL-02, F-29-03).
```

Hinweise zu B3: "hostile files" statt "malicious files" im Fließtext, weil der Code selbst `blocked_malicious`
heißt und ein zweites "malicious" im selben Satz nichts hinzufügt; Wahl beim Owner (O11). Die Zahl der
Detailcodes folgt den Antworten zu O1 bis O7 und O12.

## (B4) Release-Notiz v1.5.0 (englisch, Faktenliste, zehn Zeilen)

```
Findling 1.5.0. Both apps need to be on 1.5.0.
- New formats: mails (EML), ZIP files, DOC, XLS and HEIC, read once after the upgrade without a full reindex.
- Czech as a search language and for OCR.
- Unified search: filter by type group or folder.
- Exclusion patterns such as *.photoslibrary on the admin page (#22); limits per file shown (#21).
- Similar documents from every hit on the results page.
- Migration guide from fulltextsearch/Elasticsearch.
- Hardening: hostile files end as blocked_malicious with a detail code; deleted users and storages leave the index.
- Source of the tag and the corresponding source packages attached to this release.
**Full Changelog**: https://github.com/street1983nk/nextcloud-search/compare/v1.4.3...v1.5.0
```

## (B5) D-36-07: Satz für `docs/embeddings.md:496-497`

Heute: "Findling existiert, weil `fulltextsearch` jahrelang verwaist war und niemand das dort stehen hatte."

Neu (Präteritum bleibt, Halbsatz ergänzt): "Findling existiert, weil `fulltextsearch` jahrelang verwaist war und
niemand das dort stehen hatte; seit 2026 wird es wieder gepflegt, bleibt aber an Elasticsearch gekoppelt."

Der Rest des Absatzes bleibt unverändert.

## (B6) Offene Textfragen

**O8: Zeile zur Sammelklasse und Zusatz der Ähnlich-Zeile im Store-Text**
- (a) keine neue Zeile zur Sammelklasse im Store-Text (Härtung steht im CHANGELOG und in `docs/formats.md`);
  Ähnlich-Zeile ohne Zusatz zu Rechten.
- (b) Zeile zur Härtung, z. B. "- Hostile files (ZIP bombs, path traversal and similar) are blocked, not
  read", und/oder Ähnlich-Zeile mit Zusatz ", only from files you can read".
- Empfehlung: (a); Kurztext-Regel, und die Rechtezeile "Every result is permission-checked by Nextcloud" deckt
  die Ähnlich-Liste mit.

**O9: Teil Phase 30 (`docs/store-listing.md` Zeilen 2020-2077, Abnahme offen)**
- Teil 1, fünfter Grenz-Eintrag Tschechisch (D-30-06): en "- Czech: no stemming, inflected forms count as
  separate words", de "- Tschechisch: keine Stammformreduktion, gebeugte Formen gelten als eigene Wörter", fr
  "- Tchèque : pas de racinisation, les formes fléchies comptent comme des mots distincts".
- Teil 2 Suchsprachen-Zeile, Teil 3 OCR-Zeile ("zehn Sprachen"), Teil 4 Variablentexte `FINDLING_LANGUAGES`
  und `FINDLING_OCR_LANGUAGES` (Fundstelle Zeilen 2067-2077; stehen schon in `backend/appinfo/info.xml` Zeile
  415 und 450).
- (a) abnehmen wie dort und in B1.
- (b) Änderung je Teil; dann ändern sich Abschnitt Phase 30, `docs/language-analyzers.md` (Kurzliste) und die
  sechs Beschreibungen gemeinsam (Gate `LIMITATION_COUNT = 5`).
- Empfehlung: (a).

**O10: Grenzlisten-Frage aus Teil Phase 31 (Zeilen 2171-2189)**
- Am 12.10.2026 entschieden: ZIP kommt nicht als sechster Eintrag in die Grenzliste.
- (a) Entscheid bleibt, Grenzliste bei fünf Einträgen.
- (b) sechster Eintrag "ZIP: Inhalt ohne Texterkennung, unter keinem Typfilter".
- Empfehlung: (a), Bestätigung für den Gesamttext.

**O11: weitere offene Punkte aus den Entwürfen (per `grep -n "offen\|Frage"` ab Zeile 2020 ermittelt)**
- Teil Phase 32 (Zeilen 2195, 2217): Filterzeile in allen sechs Beschreibungen und den drei READMEs.
- Teil Phase 33 (Zeilen 2223, 2278): Ausschlusszeile in allen sechs Beschreibungen und den drei READMEs, Platz
  hinter "Keine Konfiguration".
- Teil Phase 33, Teil 3 (Zeile 2263): Grenzblock "Grenzen je Datei" und Hardware-Hinweis ohne eigene Zeile im
  Store-Text und in den READMEs (Empfehlung dort: nein).
- Teil Phase 34: Wortlaut abgenommen am 19.10.2026; offen nur der Platz in den Beschreibungen (B1: direkt hinter
  der Funktionsliste).
- Platz der drei neuen Zeilen in `findling_backend` (B1: hinter "Leistungsprofil und Suchmodell").
- Wortwahl CHANGELOG "hostile files" (B3).
- Fundzeile 2087 ("REL-05 selbst bleibt offen") und 2189 ("REL-05 bleibt für den Gesamttext offen") sind keine
  eigenen Fragen; sie schließen mit dieser Abnahme.
- (a) alles wie in B1 bis B5.
- (b) Änderung je Punkt.
- Empfehlung: (a).

## (B7) Vorab-Prüfung Teil B

Geprüft am 20.10.2026 per Skript (uv-Python, `-I`) über die sechs Blöcke aus B1, gegen die Texte 1.4.3 in
`docs/store-listing.md` (Abschnitte "App 1" und "App 2") und gegen Teil 1 des Abschnitts Phase 31, jede Prüfung
mit Positivkontrolle:

- Gesperrter Wortstamm (`BLOCKED_TERM` aus `backend/tests/test_public_artifacts.py`, ohne Rücksicht auf Groß-
  und Kleinschreibung): 0 in den zwei deutschen Texten, 0 in allen sechs; Positivkontrolle "Archivdatei" 1.
- Halbgeviert- und Geviertstriche (U+2013, U+2014): 0 in allen sechs Texten und in dieser ganzen Datei;
  Positivkontrolle 1.
- Zahlen je Beschreibung (ohne URLs): genau eine Messzahl (730.2 bzw. 730,2) je Text. Die übrigen Ziffern sind
  Anforderungen und Bezeichner wie im Store-Text 1.4.3: Nextcloud 33 bis 35, 4 GB, 2 Kerne, 2-GB-Grenze, int8,
  fp32, amd64, arm64. Die neuen Zeilen bringen keine Ziffer mit; die Umstiegszeile trägt `v1.5.0` nur in der URL.
- Zeichenzahl je Beschreibung (1.4.3 auf neu): `findling` en 1 949 auf 2 517 (+568), de 2 040 auf 2 662 (+622),
  fr 2 230 auf 2 884 (+654); `findling_backend` en 1 715 auf 2 284 (+569), de 1 781 auf 2 403 (+622), fr 1 976
  auf 2 631 (+655). Der Zuwachs sind die vier neuen Zeilen (Filter, Ähnlich, Ausschluss, Umstieg mit URL), die
  Tschechisch-Zeilen, die längere Dateitypen-Liste und der präzisierte Profilsatz.
- Dateitypen-Liste gegen Teil 1 der Phase 31 (zeichengleicher Vergleich des ganzen Blocks): identisch in allen
  sechs Texten; Positivkontrolle (HEIC gegen HEIF getauscht) meldet Abweichung.

# (E) Owner-Abnahme

Owner-Abnahme: 20.10.2026, "Abgenommen" (Option A). Alle Empfehlungen (a) übernommen für O1 bis O13, ausdrücklich: O4 = (a) Saat auf reine Tiefe 3 umbauen, O12 = 1000 (ARCHIVE_MALICIOUS_RATIO).

Datum ISO: 2026-10-20. Der Entwurf aus Teil A (A1 bis A5) und Teil B (B1 bis B7) gilt damit ohne Änderung als
abgenommene Fassung; spätere Pläne übernehmen die Sätze zeichengleich. REL-05 (Textabnahme Gesamttext) und die
offenen Abnahmen der Teile Phase 30 bis 34 in `docs/store-listing.md` schließen mit dieser Abnahme.

## Folgen für 36-06 bis 36-11

- O1 (a): Wire-Code `blocked_malicious`, Zustand `skipped`, Generation 3 ohne neue Generation; Fallback für
  1.4.x-Companions `skipped/too_large` bzw. `failed/corrupt` in `nc/queue.py` (36-06).
- O2 (a): `zip_overlap` sperrt auf jeder Ebene; Korpusfall `inner-zip-with-overlap` in
  `backend/tests/test_phase31_audit.py` wechselt von `INDEXED` auf `skipped/blocked_malicious` (36-07, 36-08).
- O3 (a): neuer Schlüssel "Detail: %s" / "Detail: %s" / "Détail : %s" nur für `skipped`-Zeilen in
  `php/js/admin.js`; `failed`-Zeilen behalten "Error class: %s" (36-06).
- O4 (a): `scripts/ci/make_upgrade_seed_formats.py` baut `seed-bomb.zip` auf reine Tiefe 3 ohne Nullen-Mitglied
  um, die Saat-Datei unter `.github/fixtures/upgrade-seed-formats/` wird neu erzeugt; die Erwartung
  `skipped/archive_limit` in `.github/workflows/deploy-harp.yml` bleibt unverändert (36-07).
- O5 (a): Korpusfall `name-nul-and-both-separators` wird `skipped/blocked_malicious` mit Detail `zip_traversal`
  (36-07, 36-08).
- O6 (a): Schwellen bestätigt: `mail_nesting` tiefer als 32 Ebenen, `image_pixels` über 100 MP UND mehr als
  1000 Pixel je Dateibyte (36-09).
- O7 (a): Reihenfolge in `archive._read_zip` bleibt (Einträge, Summe, dann Verhältnis); `lying-huge` bleibt
  `archive_limit` (36-08).
- O8 (a): keine Zeile zur Sammelklasse im Store-Text, Ähnlich-Zeile ohne Rechtezusatz (36-11).
- O9 (a): Teil Phase 30 (Tschechisch-Grenzeintrag D-30-06, Suchsprachen-, OCR- und Variablentexte) abgenommen
  wie in `docs/store-listing.md` und B1 (36-11).
- O10 (a): Grenzliste bleibt bei fünf Einträgen, ZIP kommt nicht als sechster Eintrag (36-11).
- O11 (a): Filter-, Ausschluss-, Ähnlich- und Umstiegszeilen an den Plätzen aus B1, kein eigener Grenzblock im
  Store-Text, Wortwahl CHANGELOG "hostile files" wie B3 (36-11).
- O12 (a): `ARCHIVE_MALICIOUS_RATIO = 1000` in `backend/src/findling/config.py`; Bereich über 100 bis
  einschließlich 1000:1 bleibt `skipped/archive_limit`, erst über 1000:1 `skipped/blocked_malicious/zip_ratio`;
  Korpus mit Positivkontrolle etwa 150:1 (bleibt `archive_limit`), Fall knapp über 1000:1 (`zip_ratio`), Fall
  knapp darunter (`archive_limit`) (36-07, 36-08).
- O13 (a): Abhilfe von `archive_limit` bleibt unverändert mit "too densely packed"; kein vierter Schlüssel,
  Katalog-Schlüsselzahl 348 auf 351 (36-06).
- Teil B: B1 geht zeichengleich in beide `info.xml` (sechs Beschreibungen, D-36-08 und D-36-16), B2 in die drei
  READMEs, B3 als `[1.5.0]` ins CHANGELOG, B4 als Release-Notiz, B5 in `docs/embeddings.md:496-497` (36-11).
