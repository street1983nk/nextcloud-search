# Phase 37: Owner-Entscheide (Phasen-Kontext)

Grundlage: 37-OWNER-VORLAGE.md (Commit aee10169), eine Remote-Runde über D1 bis D4, S1 bis S4 und Z1.

## 1. Owner-Antwort (wörtlich)

> "Wie empfohlen (Recommended)"

- Datum und Uhrzeit: 28.10.2026, ca. 13:0x Uhr (Europe/Berlin)
- Kanal: Remote Control (Claude-App, AskUserQuestion), Auswahl auf die Frage "Owner-Tor Phase 37 (Findling v1.6): Wie entscheidest du die neun Punkte D1-D4, S1-S4, Z1?"
- Abweichungen: keine genannt; damit gilt für alle neun Punkte die Empfehlung der Vorlage.
- Keine Klärungsfrage nötig (Antwort direkt auf die Vorlage-Frage, eindeutig).

## 2. Entscheide

| ID | Punkt | Option | Wortlaut der Option (aus der Vorlage) |
|----|-------|--------|----------------------------------------|
| D-37-01 | D1 Weg-Wahl für die Arbeitsentdopplung | (a) | Weg B als Standard. |
| D-37-02 | D2 Weg A als Admin-Opt-in je Mount-Config | (c) | erst nach Messung A6 (D4) entscheiden. |
| D-37-03 | D3 Weg C vorziehen | (a) | ja, als erster v1.6-Schritt (oder Patch-Release), unabhängig von D1. |
| D-37-04 | D4 Prüfpunkt A6 vor dem Bau messen | (a) | ja, auf einer SMB-Testfreigabe (Samba-Container, zwei Nutzer mit Log-in credentials, eine Datei mit Leseverbot für Nutzer B, einmal mit und einmal ohne `check_acl`; gemessen: Listing, `isReadable()`, Download). |
| D-37-05 | S1 Anzeigename der App findling je Sprache | (a) | wie seit 1.5.1: en "Findling Search", de "Findling Suche", fr "Findling Recherche". |
| D-37-06 | S2 Anzeigename der App findling_backend | (a) | bleibt "Findling Backend" in allen drei Sprachen. |
| D-37-07 | S3 discussion-Link in beiden info.xml | (a) | https://help.nextcloud.com/t/findling-1-2-0-and-mcp-connector-0-2-1-released/249775 |
| D-37-08 | S4 Cross-Promo-Satz zum Nextcloud MCP Connector | (a) | Satz bleibt unverändert. |
| D-37-09 | Z1 Neuer Wortlaut für ZERT-01 | (a) | Der Container erkennt die Neuausstellung (x509-Logmuster) und meldet sie ratenbegrenzt mit Abhilfe im Log; neue Dateien unter /certs/frp übernimmt er ohne Re-Register und ohne Container-Neustart (frpc heilt binnen ca. 20 s, Wächter mit Deckel gegen Neustart-Sturm); der Admin repariert mit einem dokumentierten Kopierbefehl statt unregister/register; dazu ein Upstream-Vorschlag an nextcloud/HaRP (Entwurf, Owner sendet) und eine kurze englische Antwort in Issue #33 (Entwurf, Owner sieht sie vor dem Senden). |

## 3. Folge für DEDUP-02 (Phase 39)

- **Weg C: ja, als erster Schritt der Phase 39** (D-37-03 = a), unabhängig von D1. Abdeckung zählt je Schlüssel (Backend-Typ, Host, Share, Root nach Platzhalter-Ersetzung, Pfad relativ zum Root) statt je Storage.
- **Weg B: ja, wenn er in den Rahmen der Einreichung 1.6.0 passt** (D-37-01 = a, Release-Grenze aus DEDUP-02, Ziel 29.10.2026); sonst mit Begründung dokumentiert vertagt. Der PHP-Recheck und die ACL-Tabelle je fileid bleiben unverändert.
- **Weg A: in v1.6 nicht gebaut** (D-37-02 = c). Der Entscheid über Weg A als Opt-in fällt erst mit dem Ergebnis der Messung A6; ohne Messergebnis in v1.6 gilt er als vertagt auf v1.7. Kommt er später als Opt-in, dann nur für SMB mit `check_acl` und mit dem Warnsatz aus Abschnitt 6 der Notiz; Weg A als Standard ist ausgeschlossen (Konflikt mit der Projektregel "Berechtigungs-Durchgriff strikt").
- **Messung A6/A7: ja** (D-37-04 = a), auf einer SMB-Testfreigabe in CI oder auf der Testbox, weil Docker auf der Entwicklerbox hängt. Sie ist Teil der Phase 39; das Ergebnis steht im Phasen-Artefakt.
- Eingetragen in ROADMAP.md, Phase 39, Erfolgskriterium 3, mit Verweisen D-37-01, D-37-02, D-37-03, D-37-04. Kein Widerspruch zum Wortlaut von DEDUP-02 ("mindestens Weg C"); keine Abweichung nötig.

## 4. Folge für ZERT (Phase 38)

- D-37-09 = (a). REQUIREMENTS.md: ZERT-01 trägt den neuen Wortlaut aus Option (a) mit Zusatz "(Owner-Entscheid D-37-09, ersetzt den Wortlaut vom 28.10.2026)"; ZERT-02 verlangt jetzt CI-Probe mit echter CA-Neuausstellung und Positivkontrolle (ohne neue Dateien bleibt der Tunnel tot), Deckel gegen Neustart-Sturm, Doku von Ursache, Erkennen, Kopierbefehl und Rückfallweg, Entwürfe für HaRP-Upstream-Vorschlag und Issue-#33-Antwort an den Owner.
- ROADMAP.md: Kurzzeile, Ziel und Erfolgskriterien 1 bis 4 der Phase 38 neu gefasst, jeweils mit Verweis auf D-37-09. Kriterium 1: Neuausstellung wird erkannt und mit Abhilfe gemeldet; nach Austausch der drei Dateien unter /certs/frp verbindet sich das Backend ohne Re-Register und ohne Container-Neustart wieder, die Unified Search liefert wieder Findling-Treffer.
- Selbstabruf über die HaRP-Steuer-API bleibt verworfen (Missbrauch HP_SHARED_KEY).

## 5. Freigegebene Store-Wortlaute (Eingang für Plan 37-02)

Abgenommen am 28.10.2026 (D-37-05 bis D-37-08).

Namen (name-Element, en ohne lang-Attribut):

| App | Sprache | Wert |
|-----|---------|------|
| findling | en | Findling Search |
| findling | de | Findling Suche |
| findling | fr | Findling Recherche |
| findling_backend | en | Findling Backend |
| findling_backend | de | Findling Backend |
| findling_backend | fr | Findling Backend |

App-IDs findling und findling_backend unverändert. Bei beiden Apps entsprechen die Namen dem Ist-Stand seit 1.5.1; die name-Elemente bleiben Byte für Byte.

discussion-URL (beide info.xml, D-37-07): https://help.nextcloud.com/t/findling-1-2-0-and-mcp-connector-0-2-1-released/249775 (gemessen 28.10.2026 12:51: HTTP 200, keine Weiterleitung)

Cross-Promo-Satz (D-37-08 = a, unverändert in allen sechs Beschreibungen):

- en: "Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server."
- de: "Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server."
- fr: "Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur."

Hinweis: Die Regel "keine RAG-Wortwahl" in docs/store-listing.md bleibt unverändert; die Spannung zwischen Regel und Satz hat der Owner mit D-37-08 bewusst so belassen.

## 6. Mitgeführte Präzisierung

- ROADMAP.md Phase 37 Erfolgskriterium 2 und REQUIREMENTS.md STORE-01 verlangten "Findling Search" in allen Sprachvarianten beider info.xml. Nach D-37-05 und D-37-06 tragen sie jetzt die freigegebenen Sprachvarianten (de "Findling Suche", fr "Findling Recherche", Backend "Findling Backend") mit Verweis, damit Plan 37-02 und der Verifier nicht gegen den alten Wortlaut prüfen.
