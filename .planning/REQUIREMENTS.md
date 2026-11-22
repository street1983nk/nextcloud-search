# Requirements: Milestone v1.7 Findling 1.7.0

**Defined:** 2026-11-21 (Owner-Entscheide 21.11.2026)
**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Milestone-Ziel:** Findling 1.7.0 bringt Ausschluss je externem Speicher (Issue #45), Traditional Chinese für die Oberfläche (Fork-PRs #56, #57) und kurze Store-Texte; vorher werden die offenen PHP-Sicherheits-Gates aus Phase 42 (Kriterium 3) nachgerüstet.
**Grundlage:** Issue #45 (chocology, Owner-Zusage "planned for 1.7"), PRs #56/#57 (foolfitz, Review: mergebar), ROADMAP v1.6 Phase 42 Kriterium 3, Owner-Regel "Store-Texte kurz, Link auf GitHub-Doku" (20.11.2026); keine Domain-Recherche.

## v1.7 Requirements

### PHP-Sicherheits-Gates (PRUEF, Zusage aus Phase 42)

- [ ] **PRUEF-02**: Psalm mit Taint-Analyse läuft in CI gegen OCP 33, 34 und 35; die Befunde werden aus der SARIF-Ausgabe selbst gezählt (Psalm endet sonst mit 0), der Job ist bei mindestens einem offenen Befund rot; zum Abschluss 0 offene Befunde oder je Befund eine dokumentierte Owner-Entscheidung
- [ ] **PRUEF-03**: php-cs-fixer mit nextcloud/coding-standard läuft als dry-run in CI und ist grün
- [ ] **PRUEF-04**: zizmor und actionlint prüfen alle Workflows unter .github/workflows in CI; Befunde ab Medium sind behoben oder mit Begründung akzeptiert

### Oberflächen-Sprachen (KAT, PRs von foolfitz)

- [x] **KAT-03**: Admin und Nutzer sehen Findling auf Traditional Chinese (zh_TW-Katalog aus PR #56); PRODUCT.md und CHANGELOG nennen die Sprache
- [x] **KAT-04**: Die Admin-Seite funktioniert unter einer dreiteiligen Locale wie zh_Hant_TW (PR #57), auch im Rückfall auf root.lang (Unterstrich wird zu Bindestrich)

### Ausschlüsse (EXCL, Issue #45)

- [x] **EXCL-04**: Admin kann einzelne externe Speicher vom Index ausschließen, neben dem Schalter für externe Speicher; bereits indexierte Inhalte eines ausgeschlossenen Speichers werden entfernt, ein wieder zugelassener Speicher wird nachindexiert
- [x] **EXCL-05**: Admin sieht auf der Admin-Seite, wie viele Ausschluss-Plätze für Ordner und für Muster noch frei sind
- [x] **EXCL-06**: Gibt der Admin im Ordnerfeld ein Platzhalterzeichen ein, sagt die Fehlermeldung, was er stattdessen eingeben kann (Musterfeld), in allen 16 Katalogen

### Store-Texte (STORE, Owner-Regel 20.11.2026)

- [ ] **STORE-03**: Die Store-Beschreibungen beider Apps (findling, findling_backend) sind in DE, EN und FR kurz: Kern bleibt (Datenschutz-Satz, Connector-Satz, Umstiegs-Link, Link auf die Doku auf GitHub); der Entwurf ist vor dem Einbau vom Owner freigegeben
- [x] **STORE-04**: Die aus dem Store-Text verlagerten Pflichtinhalte (Messzahl, bekannte Grenzen, Formatliste, Share-Satz, "Similar documents") stehen in README bzw. Doku in allen drei Sprachen; die bisherigen Gates prüfen sie dort

### Release (REL)

- [ ] **REL-07**: Findling 1.7.0 (beide Apps) steht im Store nach Volltest DE/EN/FR und Launch-Härtung (Fehler- und Randpfade, Rechte-Grenzen, Upgrade ab 1.6.5, frische Installation); Tag, Signatur und Store-Abgabe je mit Owner-Freigabe; Antworten in #45, #56 und #57 erst nach dem Store-Release

## Future Requirements

- Chinesische Volltextsuche body_zh (#53): wartet auf den eigenen PR von foolfitz (Owner-Zusage 13.11.2026), danach Review mit Schema-Schritt nach Czech-Muster
- Dedup Weg B (vertagt aus v1.6, D-39-02); v1.7-Merkliste aus deferred-items.md der Phase 40

## Out of Scope

- Externer Embedding-Dienst (#43): keine Inhalte verlassen den Server (Owner-Regel 02.11.2026)
- Eigener Bau von body_zh: würde den angekündigten Beitrag von foolfitz überholen

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRUEF-02 | Phase 44 | Pending |
| PRUEF-03 | Phase 44 | Pending |
| PRUEF-04 | Phase 44 | Pending |
| KAT-03 | Phase 45 | Complete |
| KAT-04 | Phase 45 | Complete |
| EXCL-04 | Phase 45 | Complete |
| EXCL-05 | Phase 45 | Complete |
| EXCL-06 | Phase 45 | Complete |
| STORE-03 | Phase 45 | Pending |
| STORE-04 | Phase 45 | Complete |
| REL-07 | Phase 45 | Pending |

**Coverage:** 11/11 v1.7-Requirements zugeordnet, keine ohne Phase, keine doppelt.

---
*Requirements definiert: 2026-11-21. Traceability gefüllt mit der v1.7-Roadmap: 2026-11-21.*
