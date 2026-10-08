Deutsch | [English](README.en.md) | [Français](README.fr.md)

# Findling

[![Python gates](https://github.com/street1983nk/nextcloud-search/actions/workflows/python.yml/badge.svg)](https://github.com/street1983nk/nextcloud-search/actions/workflows/python.yml)
[![PHP and store metadata gates](https://github.com/street1983nk/nextcloud-search/actions/workflows/php.yml/badge.svg)](https://github.com/street1983nk/nextcloud-search/actions/workflows/php.yml)
[![Security scans](https://github.com/street1983nk/nextcloud-search/actions/workflows/security.yml/badge.svg)](https://github.com/street1983nk/nextcloud-search/actions/workflows/security.yml)
[![Nextcloud App Store](https://img.shields.io/badge/App_Store-findling-0082c9)](https://apps.nextcloud.com/apps/findling)
[![Lizenz](https://img.shields.io/badge/Lizenz-AGPL--3.0--or--later-blue)](LICENSE)

Volltextsuche, Texterkennung und semantische Suche für Nextcloud, ohne
Konfiguration. Treffer erscheinen in der normalen Suchleiste.

**Findling + Nextcloud MCP Connector = die Retrieval-Schicht für Ihr eigenes RAG.**
Der [MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) reicht Findlings Treffer an jeden MCP-Client weiter, mit
genau den Rechten des fragenden Nutzers; gemessen im
[Fidelity-Test](https://github.com/street1983nk/nextcloud-mcp-connector/blob/main/tests/integration/test_content_hit_fidelity.py).
Das Modell bringen Sie mit, kein Inhalt verlässt Ihren Server.

![Die semantische Suche in der Nextcloud-Suchleiste: kein Wort der Frage steht im gefundenen Dokument, der Treffer kommt über die Bedeutung](store/media/screenshot-search-v2.png)

## Was Findling kann

- Volltextsuche mit deutscher Wortbehandlung: Komposita, Flexion, Umlaute,
  Phrasen, Ausschlüsse, Dateityp-Filter
- Texterkennung für gescannte PDFs und Bilder: neun Sprachen verfügbar
  (Deutsch, Englisch, Französisch, Spanisch, Italienisch, Niederländisch,
  Portugiesisch, Dänisch, Estnisch), voreingestellt sind Deutsch, Englisch und
  Französisch
- Semantische Suche: findet Dokumente auch über Umschreibungen
- Jeder Treffer wird von Nextcloud rechtegeprüft
- Keine Konfiguration: der erste Indexlauf startet von selbst
- Leistungsprofile: Sparsam voreingestellt, Standard und Leistung nach einer
  Vorab-Prüfung der Hardware
- Suchmodell: int8 eingebaut, das genauere fp32 unter Standard und Leistung
  einmalig ladbar

## Unterstützte Dateitypen

PDF (auch gescannt), DOCX, PPTX, XLSX, ODT, ODS, ODP, HTML, RTF, TXT,
Markdown, CSV sowie Bilder (JPEG, PNG, TIFF, WebP) per Texterkennung.

## Anforderungen

- Nextcloud 33 bis 35 mit der App AppAPI (HaRP als Deploy-Ziel)
- RAM: 4 GB genügen. Auf einer 4-GB-ARM64-Box mit 52.111 indexierten
  Dokumenten und aktiver semantischer Suche lag die Spitze des Containers bei
  1.764 MB residentem anonymem Speicher, unter einer harten 2-GB-Grenze, die der
  Kernel durchsetzt.
- Nach einem Indexlauf steht der Container mit entladenem Modell bei 730,2 MB
  residentem Speicher (gemessen am 26.09.2026 auf einer m7g.large mit arm64
  gegen das v1.3-Abbild, Methode und Rohdaten in
  [docs/performance.md](docs/performance.md)).
- CPU: 2 Kerne genügen, amd64 und arm64, keine GPU
- Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware
  hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder
  alles bis auf einen Kern (Profil Leistung).
- Die beiden zusätzlichen Profile schalten mehrere OCR-Slots und eine parallele
  Einbettungsspur frei und verkürzen so die Indexierung. Umgestellt wird mit
  einem Klick in den Verwaltungseinstellungen unter Findling; ein Vorschlag
  passend zur Box steht daneben.

## Installation

Beide Store-Einträge installieren, immer in derselben Version:
[Findling](https://apps.nextcloud.com/apps/findling) (Apps) und
[Findling Backend](https://apps.nextcloud.com/apps/findling_backend)
(External Apps). Danach startet der erste Indexlauf von selbst;
`occ findling:index --status` zeigt den Fortschritt.

## Architektur

Findling besteht aus zwei Apps unter einer Version:

- **findling** (Store-Bereich Apps): die PHP-Begleit-App registriert den
  Suchanbieter in der Suchleiste und prüft jeden Treffer gegen die
  Nextcloud-Rechte, bevor er angezeigt wird.
- **findling_backend** (Store-Bereich External Apps): der Container macht die
  Arbeit, Textauszug, Texterkennung (Tesseract), Volltextindex (Tantivy) und
  semantischer Index (SQLite mit sqlite-vec). Er ist nur über AppAPI/HaRP
  erreichbar, und die Routen, die Inhalte liefern, sind aus dem Browser nicht
  erreichbar.

Der Index liegt im App-Volume auf Ihrem Server; es gibt keinen Dienst
dazwischen und nichts verlässt die Instanz.

## Datenschutz

Alles läuft lokal im Container, keine Telemetrie, Dateien werden nie
verändert. Gespeichert wird der extrahierte Text im Datenbereich der
Backend-App: Eine Sicherung dieses Bereichs enthält ihn, und der Index ist
nicht verschlüsselt gespeichert.

## Messwerte

Alle Zahlen (Speicher, Laufzeiten, Suchlast, Ausfalltests, Modellqualität)
stehen mit Methode und Rohdaten in [docs/performance.md](docs/performance.md)
und [docs/embeddings.md](docs/embeddings.md).

## Enterprise

Findling ist und bleibt AGPL. Geplant, aber noch nicht verfügbar, sind
kostenpflichtige Zusatzmodule und Support mit zugesagten Reaktionszeiten für
Häuser, die das brauchen.

Angebot anfordern: admin@infranode.dev

## Lizenz

AGPL-3.0-or-later. Siehe [LICENSE](LICENSE).
