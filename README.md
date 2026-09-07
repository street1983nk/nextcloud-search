Deutsch | [English](README.en.md) | [Français](README.fr.md)

# Findling

Volltextsuche, Texterkennung und semantische Suche für Nextcloud, ohne
Konfiguration. Treffer erscheinen in der normalen Suchleiste.

## Was Findling kann

- Volltextsuche mit deutscher Wortbehandlung: Komposita, Flexion, Umlaute,
  Phrasen, Ausschlüsse, Dateityp-Filter
- Texterkennung für gescannte PDFs und Bilder: Deutsch, Englisch, Französisch
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst

## Unterstützte Dateitypen

PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP, HTML, RTF, TXT,
Markdown, CSV sowie Bilder (JPEG, PNG, TIFF, WebP) per Texterkennung.

## Anforderungen

- Nextcloud 33 bis 35 mit der App AppAPI (HaRP als Deploy-Ziel)
- RAM: 4 GB genügen, der Container läuft unter einer harten 2-GB-Grenze
  (gemessen)
- CPU: 2 Kerne genügen, amd64 und arm64, keine GPU

## Installation

Beide Store-Einträge installieren, immer in derselben Version:
[Findling](https://apps.nextcloud.com/apps/findling) (Apps) und
[Findling Backend](https://apps.nextcloud.com/apps/findling_backend)
(External Apps). Danach startet der erste Indexlauf von selbst;
`occ findling:index --status` zeigt den Fortschritt.

## Datenschutz

Alles läuft lokal im Container, keine Telemetrie, Dateien werden nie
verändert. Gespeichert wird der extrahierte Text im Datenbereich der
Backend-App: Eine Sicherung dieses Bereichs enthält ihn, und der Index ist
nicht verschlüsselt gespeichert.

## Messwerte

Alle Zahlen (Speicher, Laufzeiten, Suchlast, Ausfalltests, Modellqualität)
stehen mit Methode und Rohdaten in [docs/performance.md](docs/performance.md)
und [docs/embeddings.md](docs/embeddings.md).

## Lizenz

AGPL-3.0-or-later. Siehe [LICENSE](LICENSE).
