# Requirements: Milestone v1.8 Findling 1.7.1

**Defined:** 2026-11-27 (Auftrag des Owners über den Koordinator, 27.11.2026)
**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Milestone-Ziel:** Findling 1.7.1 räumt die fünf offenen kleinen Befunde aus Phase 45 ab (drei auf der Admin-Seite, zwei in der CI) und geht nach Volltest DE/EN/FR, secure-phase und je eigener Owner-Freigabe in den Store.
**Grundlage:** 45-VOLLTEST.md Befundtabelle (I-45-10-04, I-45-10-06, I-45-10-08), 45-AUDIT.md Nachtrag Push 45-10 Fix (I-45-10-07, CI) und Ergebnis der Nachprüfung (I-45-12-01), 45-ABNAHME.md Rerun HaRP deploy 45885132945, 45-15-SUMMARY.md ("1.7.1: I-45-10-04, I-45-10-06, I-45-10-07, I-45-10-08, I-45-12-01"); keine Domain-Recherche.

**Klarstellung zur ID I-45-10-07:** Die ID ist in Phase 45 doppelt vergeben. In 45-AUDIT.md (Nachtrag nach dem Push 45-10 Fix) ist I-45-10-07 der Wörterbuch-Download in der CI ohne Zeitlimit und ohne Wiederholversuch (LOW). In 45-VOLLTEST.md (Befundtabelle) ist I-45-10-07 das grau gefüllte gesperrte Kästchen bei ausgeschaltetem Hauptschalter, eine Darstellung von Nextcloud selbst und kein Befund von Findling. Nur der CI-Punkt gehört in 1.7.1 (PRUEF-05). In Phase 46 heißt er immer "I-45-10-07 (45-AUDIT.md)".

## v1.8 Requirements

### Ausschlüsse (EXCL)

- [x] **EXCL-07**: Admin liest im Hilfesatz der Ordnerliste in jeder Sprache dasselbe Beispiel, das der Platzhalter des Ordnerfelds zeigt (DE "Sicherungen", FR "Sauvegardes", EN "Backups", ebenso ES, IT, NL, pt_BR, pt_PT, zh_TW), in allen 18 Katalogdateien (I-45-10-04)
- [x] **EXCL-08**: Admin fügt einen Eintrag der Ordnerliste und der Musterliste auch mit Enter im Eingabefeld hinzu, mit derselben Prüfung und denselben Meldungen wie beim Knopf; Enter während einer Eingabe mit Eingabemethode (IME, etwa für zh_TW) fügt nichts hinzu (I-45-10-06)

### Admin-Seite (ADM)

- [x] **ADM-05**: Admin sieht die Fehlerliste "Dateien, die nicht indexiert wurden" auch bei 320 px Breite ohne Wort, das mitten im Wort umbricht, und ohne waagerechtes Scrollen, in DE, EN und FR, hell und dunkel; 375 px und 1280 px bleiben wie in 1.7.0 abgenommen (I-45-10-08)

### CI-Robustheit (PRUEF)

- [x] **PRUEF-05**: Der Schritt "Install the German dictionary the analyzer reads" in .github/actions/setup-test-nc/action.yml hat ein eigenes Zeitlimit und Wiederholversuche; ein Netzhänger beim Download kostet höchstens dieses Zeitlimit und nicht das ganze Job-Limit (I-45-10-07 aus 45-AUDIT.md)
- [x] **PRUEF-06**: Die Annahme von "Store upgrade 2b" in .github/workflows/deploy-harp.yml urteilt über die Logzeilen und die Queue erst, wenn die Queue-Zeile der veralteten Datei innerhalb des Budgets verschwunden ist (die Übergabe an die Embed-Spur nach dem Indexieren gilt nicht als Fehler); bleibt die Zeile bis zum Budgetende, ist der Schritt weiter rot (I-45-12-01)

### Release (REL)

- [x] **REL-08**: Findling 1.7.1 (beide Apps) steht im Store nach Volltest DE/EN/FR (Playwright 1280, 375 und 320 px, hell und dunkel), Umlaut-Audit, README-Faktencheck aller Sprachen, CHANGELOG EN/DE/FR, Upgrade ab 1.7.0 und secure-phase vor dem Tag; Push, Signatur, Tag, Store und jeder Kommentar je mit eigener Owner-Freigabe; der Tag sitzt auf dem CI-geprüften Kopf

## Future Requirements

- body_zh (#53, PR #60 von foolfitz): Merge nach Rebase und Prüfung, danach OCR chi_tra und Messbericht
- Rückmeldungen #45, #59, #25: Schließen nach Bestätigung der Melder, nur mit Owner-Freigabe
- Dedup Weg B (D-39-02)
- Weitere apt-Installationen der CI mit Zeitlimit (falls der Owner bei E-46-04 nur den Wörterbuch-Schritt wählt)

## Out of Scope

- I-45-10-07 aus 45-VOLLTEST.md (graues Kästchen): Darstellung von Nextcloud, kein Befund von Findling
- I-45-10-01, I-45-10-02, I-45-10-03, I-45-10-05 aus 45-VOLLTEST.md: zur Kenntnis bzw. zugelassen, kein Fix
- Neue Funktionen jeder Art; 1.7.1 ist ein Patch-Release ohne Migration und ohne Schemawechsel

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXCL-07 | Phase 46 | Complete |
| EXCL-08 | Phase 46 | Complete |
| ADM-05 | Phase 46 | Complete |
| PRUEF-05 | Phase 46 | Complete |
| PRUEF-06 | Phase 46 | Complete |
| REL-08 | Phase 46 | Complete |
