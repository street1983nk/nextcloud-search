# Requirements: Milestone v1.5 Umsteiger-Release

**Defined:** 2026-10-10 (Owner-Freigabe 10.10.2026: "mache dich an die arbeit mit 1.5 danach 1.6")
**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Milestone-Ziel:** Wer heute fulltextsearch mit Elasticsearch betreibt, findet keinen Grund mehr zu bleiben.
**Grundlage:** .planning/research/v1.5-recherche-2026-10-10.md

## v1.5 Requirements

### Umstieg (UMST)

- [ ] **UMST-01**: Admin findet eine Doku-Seite "Von fulltextsearch/Elasticsearch umsteigen" (dreisprachig wie die READMEs: de/en/fr) mit Schritten zum Abschalten der alten Apps, Funktionsvergleich als Faktenliste und dem Wortlaut "OCR ohne Dateiaenderung und ohne Elasticsearch" (nie "einzige OCR")
- [ ] **UMST-02**: Admin sieht auf der Findling-Admin-Seite einen Hinweis, wenn fulltextsearch (bzw. files_fulltextsearch) parallel aktiviert ist, mit Folge (doppelte Treffer in der Unified Search) und Link auf die Umstiegs-Seite; ohne die alten Apps erscheint nichts
- [ ] **UMST-03**: README und Store-Texte verlinken die Umstiegs-Seite (Kurztext-Regel, Owner-Abnahme des Textentwurfs vor Release)

### Unified Search (USRCH)

- [ ] **USRCH-01**: Nutzer kann in der Nextcloud Unified Search nach Dateityp filtern (die sechs bestehenden Typgruppen) ueber einen Custom Filter des Findling-Providers
- [ ] **USRCH-02**: Nutzer kann die Suche in der Unified Search auf einen Ordner einschraenken (Pfad-Praefix, inklusive Unterordner); die Rechtegrenze bleibt der finale PHP-Recheck
- [ ] **USRCH-03**: Unbekannte oder leere Filterwerte fuehren nie zu einer leeren oder fehlerhaften Suche, sondern werden ignoriert (Regressionstest)

### Ausschluesse (EXCL, Issue #22)

- [ ] **EXCL-01**: Admin kann Ausschlussmuster mit Platzhaltern (z. B. `*.photoslibrary`, `*/node_modules/*`) auf der Admin-Seite pflegen; bestehende Praefix-Ausschluesse bleiben gueltig
- [ ] **EXCL-02**: Mac-Bundles (Ordner mit Bundle-Endungen wie .photoslibrary, .app, .bundle) koennen mit einer Regel komplett ausgeschlossen werden; bereits indexierte Treffer daraus verschwinden aus dem Index
- [ ] **EXCL-03**: Ausgeschlossene Dateien zaehlen sichtbar als "excluded" und nicht als Fehler; Musterzahl und -laenge sind begrenzt (kein ReDoS, keine Regex-Eingabe)

### Formate (FMT)

- [ ] **FMT-01**: Nutzer findet Inhalt von `.eml`-Dateien (Betreff, Absender, Empfaenger, Textteil; HTML-Teil als Text)
- [ ] **FMT-02**: Nutzer findet Inhalt von Dateien in ZIP-Archiven (Treffer zeigt Archiv + innere Datei); harte Grenzen fuer Verschachtelungstiefe, entpackte Gesamtgroesse, Dateianzahl und Kompressionsrate; Grenzueberschreitung = sichtbares Skip-Urteil, nie Absturz
- [ ] **FMT-03**: Nutzer findet Text aus Legacy-Word (`.doc`) ohne LibreOffice (olefile/stdlib); nicht lesbare Varianten enden als benanntes Skip-Urteil
- [ ] **FMT-04**: Nutzer findet Text aus Legacy-Excel (`.xls`) ohne LibreOffice (xlrd), mit derselben Zellgrenze wie XLSX
- [ ] **FMT-05**: Nutzer findet Text in HEIC/HEIF-Fotos per OCR (pi-heif oder gleichwertig, arm64-tauglich)
- [ ] **FMT-06**: Bestandsinstallationen: Dateien, die bisher als `legacy_format` bzw. nicht unterstuetzt uebersprungen wurden, werden nach dem Upgrade selbsttaetig nachgeholt (Upgrade-CI-Beweis)

### Tschechisch (CZ, Issue #26)

- [ ] **CZ-01**: Admin kann Tschechisch als OCR-Sprache waehlen (`ces` im Image und in der Allowlist, Bau-Pruefung wie dan/est)
- [ ] **CZ-02**: Admin kann Tschechisch als lexikalische Sprache einschalten: eigenes Koerperfeld ohne Stemmer (Kleinschreibung, Akzentfaltung, tschechische Stoppwoerter mit Lizenzbeleg); Wechsel per Re-Analyse-Umbau, Bestandsinstallationen ohne `cs` bauen nicht um
- [ ] **CZ-03**: Grenze dokumentiert: tschechische Suche ohne Stammformreduktion (Flexionsformen werden als eigene Woerter behandelt, Semantik gleicht teilweise aus)

### Feinschliff (POL)

- [ ] **POL-01**: Admin sieht die wirksamen Grenzwerte (Zellgrenze, Adressraum, Groessengrenze, OCR-Seitendeckel) auf der Admin-Seite, nur lesend, mit Hinweis wie sie geaendert werden (#21)
- [ ] **POL-02**: Datei mit veralteter Groesse im Dateicache endet nicht mehr als `repeatedly_stuck`, sondern wird korrekt gelesen oder mit benanntem Urteil uebersprungen (F-29-03)
- [ ] **POL-03**: Hardware-Hinweis "This box has fewer cores..." ist in allen Katalogen verstaendlich umformuliert

### Stretch (STR)

- [ ] **STR-01**: Nutzer kann auf der Ergebnisseite zu einem Treffer "Aehnliche Dokumente" abrufen (Vektor-Nachbarn aus dem bestehenden Index, Rechte-Recheck in PHP)
- [ ] **STR-02**: Messbericht granite-embedding-97m-multilingual-r2 gegen e5-small (deutscher Korpus, Trefferqualitaet, CPU-Latenz amd64+arm64, RAM, eigener int8-Build) mit Empfehlung fuer v1.6; KEIN Modellwechsel in v1.5
- [ ] **STR-03**: Design-Notiz #25-Dedup je Mount-Config (fileid-Mapping vs. per-User-Crawl, ACL-Folgen), Entscheidungsvorlage fuer v1.6

### Haertung und Release (HART/REL)

- [ ] **HART-06**: Launch-Haertung vor Abgabe: Audit Security/Bugs/Performance (0 CRIT/0 HIGH), boesartige Archive/Mails/OLE-Dateien als Testkorpus, Upgrade-Strecke 1.4.2 -> 1.5.0 in CI, Fremdinstallation
- [ ] **REL-05**: Store-Einreichung 1.5.0 beider Apps (Owner-Abnahme Text + Playwright-Runde vorher), Beleg in docs/store-listing.md

## Future (v1.6, vorlaeufig)

- Embedding-Wechsel auf granite r2, nur wenn STR-02 messbar gewinnt
- #25-Dedup-Bau nach STR-03-Entscheid
- Kleiner Reranker fuer Top-10 (optional)
- CLIP-Bildsuche (SigLIP2, Lizenz je Modell pruefen)
- whisper.cpp-Transkription als Opt-in
- `.msg` (extract-msg, GPL-3 pruefen), Franzoesisches Koerperfeld, Suchlatenz bei >= 12 parallelen Anfragen

## Out of Scope

| Feature | Grund |
|---------|-------|
| sqlite-vector | Elastic License 2.0 |
| jina-embeddings v3/v5 | CC BY-NC |
| EmbeddingGemma | Gemma Terms, ~3x groesser |
| Mail-Server/IMAP, Deck, Talk als Quelle | weiter "fremde Quellen" (PROJECT.md); .eml-Dateien in Nextcloud sind Files |
| Spracherkennung | Anti-Feature (v1.3-Entscheid) |
| Grenzwerte in der UI editierbar | Werte sind Deploy-Optionen; erst Anzeige (POL-01) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| (wird vom Roadmapper gefuellt) | | |

---
*Requirements defined: 2026-10-10*
