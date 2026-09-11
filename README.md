Deutsch | [English](README.en.md) | [Français](README.fr.md)

# Findling

Volltextsuche, Texterkennung und semantische Suche für Nextcloud, ohne
Konfiguration. Treffer erscheinen in der normalen Suchleiste.

**Findling + Nextcloud MCP Connector = die Retrieval-Schicht für Ihr eigenes RAG.**
Der [MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) reicht Findlings Treffer an jeden MCP-Client weiter, mit
genau den Rechten des fragenden Nutzers; gemessen im
[Fidelity-Test](https://github.com/street1983nk/nextcloud-mcp-connector/blob/main/tests/integration/test_content_hit_fidelity.py).
Das Modell bringen Sie mit, kein Inhalt verlässt Ihren Server.

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
- RAM: 4 GB genügen. Auf einer 4-GB-ARM64-Box mit 52.111 indexierten
  Dokumenten und aktiver semantischer Suche lag die Spitze des Containers bei
  1.764 MB residentem anonymem Speicher, unter einer harten 2-GB-Grenze, die der
  Kernel durchsetzt.
- Die Grundlast im Leerlauf ist von 691,8 MB in v1.0 auf 103,2 MB in v1.1
  gefallen, minus 85,1 Prozent (gemessen am 10.09.2026, Methode und Rohdaten in
  [docs/performance.md](docs/performance.md)).
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

## Enterprise

Findling ist und bleibt AGPL. Geplant, aber noch nicht verfügbar, sind
kostenpflichtige Zusatzmodule und Support mit zugesagten Reaktionszeiten für
Häuser, die das brauchen.

Angebot anfordern: admin@infranode.dev

## Lizenz

AGPL-3.0-or-later. Siehe [LICENSE](LICENSE).
