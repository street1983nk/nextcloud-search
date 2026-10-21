# 36-15: Owner-Abnahme von Store-Text und Produkt 1.5.0 (Fremdinstallation auf http://localhost:8096)

## Kopf

| Punkt | Wert |
|---|---|
| Datum Aufbau | 21.10.2026, 11:44Z bis 12:06Z |
| Instanz | frische Nextcloud 34.0.3 (nextcloud:34.0.3-apache, SQLite), http://localhost:8096, compose-Projekt `findling-accept` (Scratch, abgeleitet aus `scripts/dev/compose-harp.yaml`, aber OHNE den Arbeitsbaum-Mount `../../php`) |
| HaRP | ghcr.io/nextcloud/nextcloud-appapi-harp@sha256:603fdf5c...ce39 (derselbe Pin wie compose-harp.yaml/deploy-harp.yml), Vorproxy nginx:1.27-alpine (beide Richtungen 200) |
| Companion | `gh release download v1.5.0 -p findling.tar.gz`, SHA-256 14e9b218e6ddf0d9a26fa5e02f68cd7756d5414c6ad0873b02601c88a53602df (gleich 36-14), per `docker cp` nach custom_apps/findling; `occ app:list`: `findling: 1.5.0` |
| Backend | `findling_backend.tar.gz`, SHA-256 d9c7b28f307c0e61c09f95a62cc1e3c33ff6788d33218a10615146a23c067aae; `app_api:app:register --info-xml` mit der unveränderten info.xml aus dem Tarball (ghcr.io, street1983nk/findling_backend, image-tag 1.5.0); `occ app_api:app:list`: `findling_backend (Array): 1.5.0 [enabled]` |
| Image-Digest | ghcr.io/street1983nk/findling_backend:1.5.0 = Index sha256:cf805dfa058f0be24d01c37ad63ca0975f82204675ccdedc0046ad95667549d8 (gleich 36-14), Container nc_app_findling_backend läuft darauf |
| Tunnel | Backend-Log: `harp_connect: client certificates in /certs/frp, configuring the tunnel with mutual TLS` |
| Deploy-Option | `FINDLING_LANGUAGES=de,en,cs` (Redeploy 11:56Z, Daten behalten), Admin-Seite: "Sprachen des Index: de,en,cs eingeschaltet, de,en,cs mit Text im Index"; Umbau lief über den Produktpfad (`carried 100 documents over into the new index directory`) |
| Hintergrundjobs | Modus cron, Schleife `php -f cron.php` alle 60 s im Container |
| Nutzer | admin / findling-harp-admin (Sprache de), testuser / findling-test-2026 (Sprache de, Anzeigename Testnutzer) |
| Freier RAM (Windows) | vor dem Aufbau 2,23 GB (2.341.424 KB); nach dem Image-Pull 0,17 GB, nach `drop_caches` im Docker-VM 1,51 GB; nach dem Aufbau 1,96 GB. Stack: Nextcloud 372 MiB, Backend 137 MiB, HaRP 95 MiB, Vorproxy 11 MiB |

Alte Instanz: Der Stack `findling-harp` (1.4.3-Abnahme vom 12.10.) war gestoppt und bleibt
unangetastet (Volumes `findling-harp_nextcloud`, `findling-harp_harp-certs`). Weil AppAPI
Container- und Volumenamen allein aus der App-Id bildet, wurde der alte, gestoppte Container
`nc_app_findling_backend` (Image 1.4.3) entfernt und sein Datenvolume vorher vollständig nach
`findling-harp143_backend_data` kopiert (16520 KB), dann `nc_app_findling_backend_data` entfernt.
Damit startet 1.5.0 mit einem leeren Datenvolume. Entfernen der Kopie erst nach Owner-Ja.

## Testdateien (alle als testuser per WebDAV, alle 201)

| Ordner | Dateien | Herkunft |
|---|---|---|
| Korpus | 09-bescheid.pdf, 10-kuendigung.docx, 11-uebersicht.odt, 12-aktenvermerk.txt, 13-ratsvorlage-scan.pdf, 15-schweiz-baubewilligung.pdf, 17-beleg.jpg, 18-aushang.png, 19-uebermittlung.tif | testdata/corpus |
| Neue-Formate | seed-word.doc, seed-excel.xls, seed-mail.eml, seed-archive.zip, seed-photo.heic | .github/fixtures/upgrade-seed-formats |
| Tschechisch | zprava-o-kotli.txt | Scratch, eigener tschechischer Text |
| Aehnlich | nebenkosten-2025.txt (ID 174), betriebskosten-2024.txt (ID 175) | Scratch, zwei inhaltlich nahe Texte |
| Urlaub.photoslibrary | notiz.txt (Wort `ausschlussquendel`) | Scratch, für das Ausschlussmuster |
| Sammelklasse | probe-traversal.zip (ID 177, `zip_traversal(b"../../etc/fluchtwort.txt")`), probe-bomb.png (ID 178, `png_bomb()`) | Generator `backend/tests/hostile.py`, nur im Scratch geschrieben, nicht im Repo |

## Sichtprobe per curl (OCS Unified Search, testuser, 12:00Z, nach dem cs-Umbau)

| Prüfung | Begriff | Treffer |
|---|---|---|
| P1 PDF Textlayer | Genehmigung | 09-bescheid.pdf |
| P1 DOCX | Frist | 10-kuendigung.docx |
| P1 ODT | Verträge | 11-uebersicht.odt |
| P1 TXT cp1252 | Müller | 12-aktenvermerk.txt |
| P1 Scan-PDF (OCR) | Bebauungsplan | 13-ratsvorlage-scan.pdf |
| P1 Scan-PDF (OCR, CH) | Baubewilligung | 15-schweiz-baubewilligung.pdf |
| P1 JPEG / PNG / TIFF (OCR) | Zahlungsavis / Sperrmüllabfuhr / Übermittlungsprotokoll | 17-beleg.jpg / 18-aushang.png / 19-uebermittlung.tif |
| P2 DOC / XLS / EML / ZIP / HEIC | wortquendel / zellquendel / mailquendel / archivquendel / fotoquendel | je die Seed-Datei |
| P3 Tschechisch | kotelně und kotelne, žluťoučký und zlutoucky | je zprava-o-kotli.txt |
| P4 Filter Ordner | Heizkosten mit folder=/Aehnlich: 2; mit folder=/Korpus: 0 | Filter wirkt |
| P5 vor dem Muster | ausschlussquendel | notiz.txt (Muster noch NICHT gesetzt) |
| P6 Quelle | Nebenkostenabrechnung | nebenkosten-2025.txt |
| P7 Sammelklasse | aussenwort, fluchtwort | 0 Treffer, wie verlangt |

Ähnliche Dokumente: `?similar=174&query=Heizkosten` zeigt "Ähnlich zu: nebenkosten-2025.txt",
Rückweg "Zurück zu den Treffern", Nachbar betriebskosten-2024.txt.

Diagnose (`occ findling:diagnose testuser:Sammelklasse/...`):

| Datei | state | reason code | error class (Detail) | label |
|---|---|---|---|---|
| probe-traversal.zip (177) | skipped | blocked_malicious | zip_traversal | File blocked as malicious |
| probe-bomb.png (178) | skipped | blocked_malicious | image_pixels | File blocked as malicious |

Admin-Karte (de): Gruppe "Datei als bösartig gesperrt", 2 Dateien, Beispielpfade
Sammelklasse/probe-bomb.png (ID 178) und Sammelklasse/probe-traversal.zip (ID 177).

Banner fulltextsearch: App fulltextsearch 34.0.2 installiert und deaktiviert. Gegenprobe:
aktiviert zeigt die Admin-Seite den Banner (`findling-banner-parallel` ohne `hidden`, nach
APCu-Verzögerung), deaktiviert ist er nach etwa 5 s wieder verborgen.

## Store-Text

Automatischer Vergleich der sechs Beschreibungen der installierten info.xml (aus den
Release-Tarballs) mit den Codeblöcken von 36-WORTLAUT.md (B1): alle sechs zeichengleich.

| Text | Fundstelle in der Installation | Ergebnis Vergleich | Ergebnis Owner |
|---|---|---|---|
| findling en | Apps-Verwaltung, Findling (Kontosprache en) | gleich, 2517 Zeichen, sha256 b8f20ac4025c | abgenommen, live identisch |
| findling de | Apps-Verwaltung, Findling (Kontosprache de) | gleich, 2662 Zeichen, sha256 658f0a332d98 | abgenommen, live identisch |
| findling fr | Apps-Verwaltung, Findling (Kontosprache fr) | gleich, 2884 Zeichen, sha256 c7505bbd8442 | abgenommen, live identisch |
| findling_backend en | release-Tarball appinfo/info.xml bzw. blob/v1.5.0/backend/appinfo/info.xml | gleich, 2284 Zeichen, sha256 a0f048293e83 | abgenommen über die Tag-Datei (Katalog zeigt bis zur Einreichung 1.4.3) |
| findling_backend de | wie oben | gleich, 2403 Zeichen, sha256 32b0384feab8 | abgenommen über die Tag-Datei (Katalog zeigt bis zur Einreichung 1.4.3) |
| findling_backend fr | wie oben | gleich, 2631 Zeichen, sha256 19fc7a42dfd8 | abgenommen über die Tag-Datei (Katalog zeigt bis zur Einreichung 1.4.3) |

Befund zur Fundstelle des Backends: Die Seite "External Apps" (AppAPI) zeigt für
findling_backend den Text aus dem App-Store-Katalog, also den der Store-Version 1.4.3
(de: 1781 statt 2403 Zeichen), nicht den der lokal registrierten 1.5.0. Die Companion-Seite
zeigt dagegen die lokale info.xml 1.5.0 (gegen die Release-Fassung geprüft). Die drei
Backend-Texte werden deshalb an der info.xml des Tags gelesen, nicht auf der Seite External Apps.

## Produkt

1. P1 Suche Volltext und OCR: Suchleiste und Ergebnisseite, Bebauungsplan (Scan-PDF), Zahlungsavis (JPEG), Genehmigung (PDF Text). Ergebnis: GRÜN, Bebauungsplan -> 13-ratsvorlage-scan.pdf, Zahlungsavis -> 17-beleg.jpg
2. P2 neue Formate: wortquendel (DOC), zellquendel (XLS), mailquendel (EML, nur HTML-Teil), archivquendel (ZIP-Inhalt), fotoquendel (HEIC). Ergebnis: GRÜN, je ein Treffer; beim ZIP steht innen/notiz.txt im Auszug
3. P3 Tschechisch mit und ohne Akzente: kotelně / kotelne, žluťoučký / zlutoucky. Ergebnis: GRÜN, kotelně, kotelne und zlutoucky finden zprava-o-kotli.txt
4. P4 Filter in der Unified Search: Heizkosten mit Ordnerfilter und Dateitypfilter. Ergebnis: GRÜN, OCS folder=/Aehnlich 2, folder=/Korpus 0, types=text 2, types=pdf 0, unbekannter Typ wird ignoriert
5. P5 Ausschlussmuster: `*.photoslibrary` auf der Admin-Seite hinzufügen, danach findet ausschlussquendel nichts mehr. Ergebnis: GRÜN, Muster gespeichert mit der Rückfrage "Ausschließen und entfernen", danach ausschlussquendel 0 Treffer; Beobachtung L-36-06 (Zähler) für 1.5.1
6. P6 Ähnliche Dokumente: Link am Treffer nebenkosten-2025.txt, Nachbar betriebskosten-2024.txt, Rückweg. Ergebnis: GRÜN, "Ähnlich zu: betriebskosten-2024.txt" listet nebenkosten-2025.txt, "Zurück zu den Treffern"
7. P7 Admin-Karte mit Sammelklasse und Detail-Label: "Datei als bösartig gesperrt", 2 Dateien, Einzelprüfung ID 177 (zip_traversal) und 178 (image_pixels). Ergebnis: GRÜN, Gruppe "Datei als bösartig gesperrt" 2 (IDs 177, 178), Einzelprüfung 177 mit Detail zip_traversal
8. P8 Grenzliste mit Tschechisch-Eintrag: "Bekannte Grenzen" in der Beschreibung (Apps-Verwaltung), Zeile "Tschechisch: keine Stammformreduktion, gebeugte Formen gelten als eigene Wörter". Ergebnis: GRÜN, mit der Companion-Beschreibung abgenommen

Zusatz (vom Koordinator erbeten): Grenzen je Datei auf der Admin-Seite (50,0 MB,
512,0 MB, 200.000 Zellen, 30 Seiten), Banner fulltextsearch (an/aus). Upgrade-Nachlese:
entfällt, frische Installation; der Upgrade-Weg ab 1.4.3 ist in 36-13/36-14 belegt.

Ergebnis Zusatz: Grenzwerte 50,0 MB / 512,0 MB / 200.000 / 30 mit Variablennamen gesehen;
Sprachen de,en,cs; Banner fulltextsearch an und aus korrekt, fulltextsearch danach wieder
deaktiviert. Das Muster `*.photoslibrary` bleibt auf 8096 gesetzt.

Beobachtungen, vom Owner akzeptiert, kein Blocker für 1.5.0 (LOW-Nachtrag in 36-AUDIT.md,
Ziel 1.5.1 in deferred-items.md):

- L-36-05: Bei 0 ausgelassenen Dateien zeigt die Admin-Seite "Bewusst ausgelassen: 0" samt
  Erklärsatz "Diese Dateien sind zu groß ...".
- L-36-06: Nach dem Speichern des Ausschlussmusters war die Datei sofort aus der Suche, die
  Zähler Indexiert / Durch Regel ausgeschlossen / Bewusst ausgelassen standen etwa 2 min
  später (zwei cron.php-Läufe) noch auf 100 / 0 / 0.

## Owner-Abnahme

Gemeinsame Runde am 21.10.2026 im Playwright-Browser auf http://localhost:8096 (Koordinator
steuert, Owner sieht mit), alle Punkte P1 bis P8, sechs Beschreibungen und Zusatzpunkte wie oben.
Frage: "abgenommen oder Einwände je Punkt". Antwort wörtlich "okok", als Abnahme gewertet.

Owner-Abnahme: 21.10.2026, okok
