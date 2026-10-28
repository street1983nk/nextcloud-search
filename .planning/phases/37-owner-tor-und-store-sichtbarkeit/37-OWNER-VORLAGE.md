# Phase 37: Owner-Vorlage (eine Runde, neun Punkte)

Stand: 28.10.2026

Antwort "wie empfohlen" übernimmt jede Empfehlung; Abweichungen als "D2 b, S4 b" nennen. Nicht genannte Punkte gelten als wie empfohlen. Bei S3 b bitte die neue URL nennen, bei eigenem S4-Wortlaut en/de/fr.

## Block 1: Dedup (#25), vier Fragen

Kurzfassung der drei Wege (aus 35-DEDUP-NOTIZ.md, Abschnitt 5):
- Weg A (fileid-Mapping): hohes ACL-Risiko, spart am meisten (Download, OCR, Einbettung, Indexplatz).
- Weg B (Inhalts-Hash-Wiederverwendung): kein neues ACL-Risiko, spart OCR und Einbettung, rund 81 Prozent beim Melder (Hochrechnung, Annahme A5).
- Weg C (nur die Zählung entdoppeln): spart keine Arbeit, kein Risiko, richtige Prozentzahl auf der Admin-Seite.

**D1: Weg-Wahl für die Arbeitsentdopplung**
- (a) Weg B als Standard.
- (b) Weg A als Standard.
- (c) keine Arbeitsentdopplung, nur Weg C.
- Empfehlung: (a); einziger Weg, der spart, ohne das ACL-Modell anzufassen.

**D2: Weg A als Admin-Opt-in je Mount-Config**
- (a) ja, mit Warnsatz (Abschnitt 6), nur für SMB mit gesetztem `check_acl`.
- (b) nein, Weg A wird nicht gebaut.
- (c) erst nach Messung A6 (D4) entscheiden.
- Empfehlung: (c); ohne Messung ist das Leck nur aus dem Quelltext abgeleitet, und selbst mit `check_acl` bleiben Gruppen-ACEs offen. Fällt A6 wie erwartet aus, dann (b) oder (a) nur mit dem Warnsatz.

**D3: Weg C vorziehen**
- (a) ja, als erster v1.6-Schritt (oder Patch-Release), unabhängig von D1.
- (b) zusammen mit dem Bau aus D1.
- (c) nein, der Satz aus 1429eebc reicht.
- Empfehlung: (a); kleinster Eingriff, sichtbar für jede Instanz mit nutzerspezifischer Anmeldung, kein Index-Risiko.

**D4: Prüfpunkt A6 vor dem Bau messen**
- (a) ja, auf einer SMB-Testfreigabe (Samba-Container, zwei Nutzer mit Log-in credentials, eine Datei mit Leseverbot für Nutzer B, einmal mit und einmal ohne `check_acl`; gemessen: Listing, `isReadable()`, Download).
- (b) nein, Weg A wird ohnehin nicht gebaut (D2 = b).
- (c) nur, wenn D2 auf (a) oder (c) steht.
- Empfehlung: (a), solange D2 nicht (b) ist; ein halber Tag Messung gegen eine dauerhafte Rechte-Frage. Im selben Lauf A7 klären: wie der Zähler beim Melder zur eindeutigen Menge passt, obwohl Findling keine Inhalts-Entdopplung hat (Abschnitt 1, Randnotiz).
- Hinweis: Docker auf der Entwicklerbox hängt; die Samba-Messung A6/A7 liefe deshalb in CI oder auf der Testbox. Bei D4 = a wird sie Teil der Phase 39.

Release-Grenze (aus DEDUP-02): Weg B wird nur gebaut, wenn der Bau in den Rahmen der Einreichung 1.6.0 (Ziel 29.10.2026) passt; sonst dokumentiert vertagt.

## Block 2: Store-Sichtbarkeit, vier Punkte

**S1: Anzeigename der App findling je Sprache**
- (a) wie seit 1.5.1: en "Findling Search", de "Findling Suche", fr "Findling Recherche".
- (b) "Findling Search" in allen drei Sprachen.
- Empfehlung: (a); Owner-Entscheid und Abnahme vom 22.10.2026, steht schon im Store, kein zweiter Namenswechsel.

**S2: Anzeigename der App findling_backend**
- (a) bleibt "Findling Backend" in allen drei Sprachen.
- (b) "Findling Search Backend" in allen drei Sprachen.
- Empfehlung: (a); Owner 22.10.2026 "Findling Backend bleibt", Beschreibungen und READMEs nennen ihn so.
- Hinweis: die App-IDs findling und findling_backend ändern sich in keinem Fall.

**S3: discussion-Link in beiden info.xml**
- (a) https://help.nextcloud.com/t/findling-1-2-0-and-mcp-connector-0-2-1-released/249775
- (b) andere URL (Owner nennt sie).
- Empfehlung: (a); Vorgabe aus STORE-02.
- Gemessen am 28.10.2026 12:51: HTTP 200, keine Weiterleitung (End-URL gleich).

**S4: Cross-Promo-Satz zum Nextcloud MCP Connector** (genau ein Satz je Beschreibung, alle sechs Beschreibungen)
- (a) Satz bleibt unverändert:
  - en: "Together with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forms the retrieval layer for your own RAG: AI assistants search your document contents with exactly the rights of the asking user, and no content leaves your server."
  - de: "Zusammen mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) ergibt Findling die Retrieval-Schicht für Ihr eigenes RAG: KI-Assistenten durchsuchen Ihre Dokumentinhalte mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server."
  - fr: "Avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector), Findling forme la couche de récupération de votre propre RAG : les assistants IA cherchent dans le contenu de vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur."
- (b) Regelbereinigung: neuer Satz in schlichter Sprache ohne RAG-Wortwahl:
  - en: "Works with the [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector): AI assistants search your documents with exactly the rights of the asking user, and no content leaves your server."
  - de: "Arbeitet mit dem [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) zusammen: KI-Assistenten durchsuchen Ihre Dokumente mit genau den Rechten des fragenden Nutzers, und kein Inhalt verlässt Ihren Server."
  - fr: "Fonctionne avec le [Nextcloud MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) : les assistants IA cherchent dans vos documents avec exactement les droits de l'utilisateur qui demande, et aucun contenu ne quitte votre serveur."
- Empfehlung: (a); der Satz erfüllt STORE-02 seit 1.0.3, der Gesamttext ist am 20.10.2026 abgenommen, kein Textwechsel nötig.
- Zu (b): die Regel in docs/store-listing.md (Abschnitt "Was in den sechs Texten oben bewusst nicht steht") sagt "keine RAG-Wortwahl". (b) bringt Satz und Regel in Einklang, kostet aber das Stichwort RAG im Store-Text und einen Textwechsel in sechs Beschreibungen. Alternative zu (b) wäre, die Regel an den Satz anzupassen; bei (a) bleibt beides, wie es ist.

## Block 3: Zertifikatsrotation (Issue #33), eine Frage

Befund (38-RESEARCH.md):
- /certs/frp im Backend-Container ist kein Mount, sondern eine Einmal-Kopie durch HaRP bei register/update (HaRP-README: "ExApps embed the certificates at install time").
- frpc 0.61.1 lädt Zertifikat, Schlüssel und CA bei jedem Verbindungsversuch neu und beendet sich nie (Backoff bis 20 s); ein Neustart bei unveränderten Dateien ist wirkungslos.
- ZERT-01 ist im heutigen Wortlaut nicht erfüllbar.

**Z1: Neuer Wortlaut für ZERT-01**
- (a) Der Container erkennt die Neuausstellung (x509-Logmuster) und meldet sie ratenbegrenzt mit Abhilfe im Log; neue Dateien unter /certs/frp übernimmt er ohne Re-Register und ohne Container-Neustart (frpc heilt binnen ca. 20 s, Wächter mit Deckel gegen Neustart-Sturm); der Admin repariert mit einem dokumentierten Kopierbefehl statt unregister/register; dazu ein Upstream-Vorschlag an nextcloud/HaRP (Entwurf, Owner sendet) und eine kurze englische Antwort in Issue #33 (Entwurf, Owner sieht sie vor dem Senden).
- (b) ZERT-01 unverändert lassen; Phase 38 wird am heutigen Wortlaut scheitern.
- Empfehlung: (a); einziger Weg, der im Container machbar ist. Selbstabruf über die HaRP-Steuer-API ist in der Research verworfen (Missbrauch HP_SHARED_KEY).

## Nicht in dieser Runde

- Store-Einreichung (Phase 40)
- Bau Dedup (Phase 39)
- Bau ZERT (Phase 38)
- Cross-Promo zu Gameworld (noch nicht im Store)
- Rückverweis in der Connector-App (anderes Repository)
