# Phase 21: Niederlaendische Komposita - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning
**Source:** Owner-Go/No-Go-Tor 2026-09-25 (siehe 21-GO-ENTSCHEID.md) + 21-RESEARCH.md

<domain>
## Phase Boundary

Nutzer findet niederlaendische Komposita ueber ihre Glieder (Beispiel:
`gemeentebelastingen` ueber `belasting`). Die Phase liefert den zweiten
split_compound-Automaten (nl) hinter der Faltung in der nl-Kette, die
Wortlisten-Pipeline aus dem Debian-Paket wdutch, die siebte Digest-Marke
`wordlist_hash_nl` mit Umbau nur bei aktivem Niederlaendisch, den
CI-Sprachfall (rot ohne Splitter) und die Lizenzdokumentation. Kein neues
Backend, keine Schemaaenderung, kein Anstieg von ANALYZER_VERSION.

</domain>

<decisions>
## Implementation Decisions

### Owner-Tor (GO erteilt 2026-09-25, alle LOCKED)
- D-01: GO fuer die Phase; bei den Erfolgskriterien gilt die Roadmap unveraendert.
- D-02: NL-Wortliste wird nach dem Automatenbau FREIGEGEBEN (Ziel 17,6 MB
  Zusatzkosten, nicht 37,2 MB wie beim Halten).
- D-03: Zerlegungsfenster 4 bis 14 Zeichen (Rezept aus der Research; 4-12 ist
  ausdruecklich verworfen wegen Fehlzerlegungen wie `onderhandel, ing`).
- D-04: THIRD-PARTY.md nennt fuer die OpenTaal-Wortliste CC-BY-3.0 (Bezugskette
  ueber Debian wdutch); die Upstream-Wahlfreiheit BSD-3/CC-BY-3.0 darf als
  Anmerkung erwaehnt werden.

### Harte Leitplanken (aus Research, LOCKED)
- D-05: ANALYZER_VERSION steigt NICHT (sonst Vollreindex ~19 h ueberall).
- D-06: `wordlist_hash_nl` verhaelt sich exakt wie die Sprachmarke: nicht
  vorbelegen; Fehlen bei inaktivem nl = Altbestand, keine Abweichung, kein
  Rebuild-Hinweis, kein Lauf; Schreiben nur hinter dem Verzeichnistausch bzw.
  beim Anlegen eines neuen Verzeichnisses.
- D-07: Splitter-Position wie in Phase 17 gemessen: HINTER der Faltung
  (ascii_fold), Fugenlaute s, e, en; Listenaufbereitung mit tantivys eigener
  Faltung (316.740 Eintraege bei wdutch 1:2.20.19+1-3).
- D-08: Vor dem ersten Baustein klaert ein Test die offene Frage 4 der
  Research: stempelt der Rueckfallpfad ueber Vollreindex die
  Verzeichnismarken? Ergebnis bestimmt die Absicherung der Marke.
- D-09: Der End-to-End-Beweis fuer Erfolgskriterium 4 laeuft ueber den
  bestehenden CI-Schritt "Store upgrade 5" (Bestand ohne nl bleibt unberuehrt).

### Claude's Discretion
- Anzeige des niederlaendischen Digests auf der Adminseite (Research-Frage 5).
- Aufteilung in Plaene und Wellen (Research schlaegt 8 Plaene vor).
- Genaue Namen der Gates/Testdateien, solange die bestehenden Muster
  (parametrisierte Katalog- und Sprachgates, search-parity-Sprachbeweis)
  eingehalten werden.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 21
- `.planning/phases/21-niederlaendische-komposita/21-RESEARCH.md` , Rezept,
  Messungen, Markenmechanik, No-Go-Rueckbauliste, 8-Plaene-Vorschlag
- `.planning/phases/21-niederlaendische-komposita/21-GO-ENTSCHEID.md` —
  datiertes Owner-Go samt Teilentscheiden

### Praezedenzen
- Phase 17 (deutscher Splitter): Rezeptwahl, Splitter-Position, Messmethode
- Phase 18/19: Umbauweg, Sprachmarken, Re-Analyse statt Vollreindex
- Phase 20: CI-Sprachbeweis in search-parity ("The result page answers in
  every new language")

</canonical_refs>

<specifics>
## Specific Ideas

- CI-Sprachfall: `gemeentebelastingen` wird ueber `belasting` gefunden und der
  Fall wird OHNE Splitter rot (in der Research nachgewiesen: ohne Splitter kein
  Treffer in de/en/nl).
- 33 Waechterwoerter aus der Research als Anti-Fehlzerlegungs-Gate uebernehmen.

</specifics>

<deferred>
## Deferred Ideas

- Native ARM-RAM-Messung: erst in der Box-Anfahrt (Phase 22 / Messphase);
  qemu-Werte sind unbrauchbar.

</deferred>

---

*Phase: 21-niederlaendische-komposita*
*Context gathered: 2026-09-25 via Owner-Tor nach Research*
