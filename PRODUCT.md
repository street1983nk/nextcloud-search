# Product

<!-- impeccable:product-schema 1 -->

> Abgeleitet aus README.md, CLAUDE.md und .planning/PROJECT.md (Stand 04.11.2026). Aussagen mit Quellenangabe stehen so im Repo. Die abgeleiteten Aussagen ohne Quellenangabe sind vom Owner bestätigt am 04.11.2026.

## Platform

web

## Users

- **Nextcloud-Nutzer, die Dateien wiederfinden wollen:** suchen in der normalen Nextcloud-Suchleiste und auf der eigenen Ergebnisseite nach Dokumentinhalten, auch in gescannten PDFs und Bildern (Quelle: README).
- **Admins von Selfhost-Instanzen und kleinen Organisationen** auf typischer Hardware (4 bis 8 GB RAM, oft ARM), für die das fulltextsearch-Framework mit Elasticsearch keine Option ist (Quelle: PROJECT.md). Sie installieren beide Store-Apps und schauen danach höchstens auf die Verwaltungsseite (Abdeckung, Fehler, Profil, Ausschlüsse).
- Der Admin besucht die Verwaltungsseite selten und mit einer konkreten Frage (Läuft der Index? Warum fehlt Datei X?), nicht als tägliches Dashboard.
- Behörden und öffentliche Einrichtungen (Enterprise-Flag im Store, ZenDiS-Kontakt über den Schwester-Connector) sind eine wachsende Zweitzielgruppe.

## Product Purpose

Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten, inklusive gescannter PDFs, ohne dass der Admin etwas konfigurieren muss (Core Value, Quelle: PROJECT.md). Ein Container erledigt Textauszug, Texterkennung, Volltext- und semantischen Index; die PHP-App bringt die Treffer rechtegeprüft in die Unified Search und auf eine eigene Ergebnisseite (Quelle: README).

Erfolg heißt, dass ein Nutzer ein Dokument über ein Wort aus dem Inhalt oder eine Umschreibung findet, ohne zu wissen, dass Findling installiert ist.

## Positioning

- Kein Elasticsearch, OCR eingebaut, semantische Suche lokal auf der CPU, kleines RAM-Budget, deutsche Komposita, eigene Ergebnisseite (Differenzierer laut PROJECT.md).
- Kein Inhalt verlässt den Server, keine Telemetrie, Dateien werden nie verändert (Quelle: README, Datenschutz).
- Zusammen mit dem Nextcloud MCP Connector die Retrieval-Schicht für ein eigenes RAG, mit den Rechten des fragenden Nutzers (Quelle: README).

## Operating Context

- Zwei Store-Einträge in derselben Version: `findling` (Apps, PHP) und `findling_backend` (External Apps, Container über AppAPI/HaRP). Nextcloud 33 bis 35 (Quelle: README).
- Nutzeroberflächen: Treffer in der Unified Search inklusive Typ- und Ordnerfilter, die Ergebnisseite mit Dateityp-, Zeitraumfilter, Sortierung, Paginierung und "Ähnliche Dokumente", die Verwaltungsseite unter den Admin-Einstellungen (Quelle: README, PROJECT.md).
- Die Ergebnisseite funktioniert vollständig ohne JavaScript (Quelle: `php/templates/search.php`).
- Oberfläche in acht Sprachen: EN, DE, FR, ES, IT, NL, pt_PT, pt_BR (Quelle: PROJECT.md).

## Capabilities and Constraints

- Volltext mit deutscher Wortbehandlung, OCR in zehn Sprachen, semantische Suche, ähnliche Dokumente, Ausschlussmuster, Leistungsprofile Sparsam/Standard/Leistung (Quelle: README).
- Jeder Treffer wird von Nextcloud rechtegeprüft; Unified Search bleibt die einzige Berechtigungsgrenze, kein eigenes MCP-Tool gegen den Index (Quelle: PROJECT.md, Out of Scope).
- Out of Scope: Elasticsearch/OpenSearch, RAG- oder Chat-Antworten, externe Cloud-Embeddings, Indexierung fremder Quellen (Quelle: PROJECT.md).
- UI-Stack: PHP-Templates, Vanilla-JS, zwei CSS-Dateien, keine Vue-Komponenten (Quelle: Repo-Struktur, nextcloud-ui-Skill).
- Texte nur über die Übersetzungskataloge; Kataloge EN/DE/FR im Gleichstand (Quelle: PROJECT.md).
- Offen laut PROJECT.md (v1.6): Anzeigetext "Bewusst ausgelassen: 0", Dedup-Bau, Anzeigename "Findling Search".

## Brand Commitments

- Name "Findling"; im Store künftig Anzeigename "Findling Search" (GO vom 22.10., Quelle: PROJECT.md).
- Keine eigene visuelle Marke in der App: die Oberfläche folgt Nextcloud-Design und Theming (Quelle: nextcloud-ui-Skill, Owner-Regel in CLAUDE.md global).
- Produkttexte sind kurze Faktenlisten, höchstens eine Zahl, Entwurf vor Release dem Owner zeigen (Quelle: CLAUDE.md, Owner-Regeln).
- Deutsch mit echten Umlauten in Prosa, keine Gedankenstriche, keine Emojis (Quelle: CLAUDE.md).

## Evidence on Hand

- Store-Screenshots unter `store/media/` (u. a. `screenshot-search-v2.png`).
- Messwerte mit Methode und Rohdaten: `docs/performance.md`, `docs/embeddings.md`, `docs/measurements/`.
- Eine freigegebene Speicherzahl für Produkttexte: 730,2 MB (Quelle: PROJECT.md, Store-Regeln).
- Nicht vorhanden und nicht zu erfinden: Kundenstimmen, Nutzerzahlen, Preise oder Zusagen für die geplanten Enterprise-Zusatzmodule (laut README "geplant, aber noch nicht verfügbar").

## Product Principles

Abgeleitet aus Core Value und Owner-Regeln:

1. Null Konfiguration ist das Produkt: jede Einstellung braucht einen Grund, der Werkzustand muss ohne sie funktionieren.
2. Rechte vor Treffern: lieber kein Ergebnis als ein falsches oder fremdes.
3. Nichts verlässt den Server.
4. Ehrliche Zustände: übersprungene, fehlgeschlagene und ausgeschlossene Dateien werden sichtbar benannt, nie verschwiegen.
5. Sieht aus wie Nextcloud: keine eigene Marke in der Oberfläche.

## Accessibility & Inclusion

Zielstandard WCAG 2.1 AA (BITV-relevant für öffentliche Einrichtungen). Im Code belegt: Fokusring wird nie entfernt, Farbe nie alleiniger Träger, Icon-Knöpfe mit `aria-label`, Klickflächen mindestens `--default-clickable-area` und 44 px bei grobem Zeiger, hoher-Kontrast-Theme über Server-Variablen (Quelle: `php/css/*.css`).
