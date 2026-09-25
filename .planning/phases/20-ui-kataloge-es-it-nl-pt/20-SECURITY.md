---
phase: 20
slug: ui-kataloge-es-it-nl-pt
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-25
register_authored_at_plan_time: true
---

# Phase 20: Security

> Sicherheitsvertrag der Phase: Threat Register, akzeptierte Risiken und Audit Trail.
> Register vollständig aus den `<threat_model>`-Blöcken von 20-01-PLAN.md bis 20-09-PLAN.md übernommen (T-20-01 bis T-20-44 plus T-20-SC).
> Jede Evidence ist am Baum vom 25.09.2026 (HEAD `c1db8e5`) nachgeprüft, nicht aus den SUMMARY-Dateien übernommen.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Katalogdatei zu PHP-Renderer | Katalogwert läuft durch `L10NString::__toString` in `vsprintf` und in die Pipe-Verkettung der Pluralformen | Übersetzungstext, wird zu Formatierer-Eingabe |
| Katalogdatei zu Browser | `.js` wird über `OC.L10N.register` geladen, Werte landen über `textContent` in der Seite | Übersetzungstext, keine Nutzerdaten |
| Repo zu signiertem Store-Paket | `store-archive.sh` kopiert `php/l10n` als ganzes Verzeichnis | jede Datei in `php/l10n`, auch liegengebliebene Probedateien |
| Nextcloud-Kerndatei zu Gate-Konstante | Pluralregel aus `core/l10n/<code>.json` wird zu `PLURAL_FORM_OF` | Regelzeichenkette |
| Pfadfilter zu Gate | `python.yml` entscheidet, ob die Katalog-Gates überhaupt laufen | CI-Auslösung |
| CI-Schritt zu Testinstanz | Sprachbeweis setzt die Nutzersprache (geteilter Zustand) und liest die Erwartung aus dem Katalog | Wegwerf-Zugangsdaten, Sitzungscookie der Wegwerf-Instanz |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (Evidence) | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-20-01 | Tampering | Umbenennung der fünf Pluralschlüssel in sechs Dateien | mitigate | G1 `test_every_catalogue_carries_the_same_keys` über `L10N_CATALOGUES` (test_admin_ui_contract.py:2338-2380, Rotprobe 2379-2380); `git diff --numstat 51e0ea4^..HEAD` zeigt je 5/5 Zeilen für de/de_DE/fr `.js`/`.json`, ausschließlich die fünf Pluralschlüssel | closed |
| T-20-02 | Tampering | Wert verliert Form oder `%n` beim Umschreiben | mitigate | `expected_directives_per_form` mit `_::_`-Teilung (:875-899), `scan_placeholder_parity` (:902-919), Gate :2546-2595 mit Rotproben `lost`/`dirty`; Formenzahl je Schlüssel über `FORM_COUNT_OF` in :2699-2703 | closed |
| T-20-03 | Denial of Service | Falsch geschriebener Kompositschlüssel, Fallback auf englischen Plural | mitigate | Checkpoint mit gemessener Sondenausgabe an laufender Instanz in 20-01-SUMMARY.md:89-116 (`de n=2 2 Tage`, `fr n=2 2 jours`), Owner-Go in `5b93c8c`; zusätzlich dauerhaft: CI-Sprachbeweis integration.yml:3245-3312 | closed |
| T-20-04 | Repudiation | Schlüsselnamen bewegen sich ohne Spur | mitigate | Absatz im Docstring von `test_the_german_catalogue_covers_both_german_language_codes` (:2281-2297); datierter Nachtrag docs/l10n-french.md:457-463 ("Nachtrag 25.09.2026 (Phase 20, Plan 20-01)") | closed |
| T-20-05 | Tampering | Pluralregel nachgetippt statt gelesen | mitigate | `PLURAL_FORM_OF` (:516-525) mit Herkunftskommentar (:498-502); Zeichengleichheit Doku/Konstante als Gate `test_the_rule_table_of_the_documentation_and_the_constant_are_one_string` (:2717-2742, Anti-Vakuitätsklausel :2739); docs/l10n-catalogues.md Abschnitt 3 | closed |
| T-20-06 | Spoofing | Probedatei `php/l10n/pt.json` bleibt liegen | mitigate | `git status --short` am 25.09.2026 leer; `ls php/l10n` zeigt genau 16 Dateien, kein `pt.json`/`pt.js`; Sonde räumt auf (docs/l10n-catalogues.md:91-92 `rm -f php/l10n/pt.json`) | closed |
| T-20-07 | Denial of Service | Gate dauerhaft rot für `nl` wegen deutschgleicher Regel | mitigate | `scan_plural_rule` sprachbewusst (:1031 `expected != GERMAN_PLURAL_FORM`); Gegenprobe `scan_plural_rule("sample.json", "nl", GERMAN_PLURAL_FORM) == []` (:2714) | closed |
| T-20-08 | Repudiation | Katalogcommit läuft ohne Gate durch | mitigate | YAML-geparst: `php/l10n/**` in `on.push.paths` und `on.pull_request.paths` von python.yml (beide True); seit WR-03 (`69c7186`) zusätzlich `docs/l10n-*.md` in beiden Listen | closed |
| T-20-09 | Denial of Service | Nacktes Prozentzeichen (`50 % de los archivos`) | mitigate | `_carries_a_bare_percent` Zählvergleich gegen `PRINTF_DIRECTIVE` (:935-948), `scan_percent_discipline` über Schlüssel und jede Form (:951-981); Gate :2598-2649 mit roter (`bare`), grüner (`doubled`) und Pluralform-Rotprobe | closed |
| T-20-10 | Tampering | Pipe im Wortlaut ersetzt Satz durch englische Fehlermeldung | mitigate | `scan_pipe_character` über Schlüssel und Formen (:984-1008), im Gate :2622-2629 über `L10N_CATALOGUES`, Rotprobe `piped` (:2641-2642) | closed |
| T-20-11 | Tampering | Verlorenes `%2$s` | mitigate | Gate :2570-2574 iteriert `L10N_CATALOGUES` (16 Dateien, :273-290), Anti-Vakuitätsklausel :2578-2581 | closed |
| T-20-12 | Repudiation | Sprache ohne begründete Ausnahmeliste | mitigate | `unargued`-Assertion :2494-2497 (fehlender Code in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` ist benannter Fehlschlag); Stale-Prüfung :2512-2518; alle acht Codes mit Einträgen (:578-667) | closed |
| T-20-13 | Elevation of Privilege | Markup in Katalogwert als HTML gerendert | accept | siehe Accepted Risks Log AR-20-01; Begründung am 25.09.2026 nachgeprüft | closed |
| T-20-14 | Denial of Service | Spanisches Prozentzeichen | mitigate | `L10N_ES_JSON`/`L10N_ES_JS` in `L10N_CATALOGUES` (:280-281), damit im Gate :2598 | closed |
| T-20-15 | Tampering | Maschinenwert verliert `%2$s` (es) | mitigate | es-Paar in `L10N_CATALOGUES`, `scan_placeholder_parity` mit Kompositteilung (:2546) | closed |
| T-20-16 | Tampering | `es.js` driftet von `es.json` | mitigate | Seit WR-01 (`cde0aab`) dauerhaftes Gate `test_the_two_halves_of_every_language_carry_the_same_values` (:2421-2468) mit `scan_value_equality` (:805-822), Paarbildung aus `L10N_CATALOGUES`, Rotprobe in drei Formen (:2458-2467) | closed |
| T-20-17 | Information Disclosure | Wortlaut erfindet Dateinamen/Pfad | accept | siehe AR-20-02 | closed |
| T-20-18 | Repudiation | Katalog ohne Vorbehalt in den Store (es) | mitigate | docs/l10n-spanish.md Abschnitt "Abnahme": "Erzeugt am 25.09.2026, Plan 20-04" und :389 "Dieser Katalog ist von keinem Muttersprachler gelesen worden." | closed |
| T-20-19 | Denial of Service | Italienisches Prozentzeichen | mitigate | `L10N_IT_JSON`/`L10N_IT_JS` in `L10N_CATALOGUES` (:282-283) | closed |
| T-20-20 | Tampering | U+2019 als Apostroph (it) | mitigate | Unabhängige Nachmessung 25.09.2026: 0 Vorkommen von U+2014, U+2013, U+2019, U+00A0, U+202F in it.json, it.js und docs/l10n-italian.md; Prüfzeile docs/l10n-italian.md:419 | closed |
| T-20-21 | Tampering | Platzhalter verloren/umnummeriert (it) | mitigate | it-Paar im Paritäts-Gate (:2546) | closed |
| T-20-22 | Tampering | `it.js` driftet von `it.json` | mitigate | Werte-Gleichstands-Gate :2421 (WR-01) | closed |
| T-20-23 | Repudiation | Katalog ohne Vorbehalt (it) | mitigate | docs/l10n-italian.md "Erzeugt am 25.09.2026, Plan 20-05" und :450 "von keinem Muttersprachler gelesen" | closed |
| T-20-24 | Denial of Service | Drei Formen bei `nplurals=2` (nl) | mitigate | `FORM_COUNT_OF["nl"] = 2` (:539), Formenzahl-Prüfung :2699-2703; Nachmessung: alle nl-Pluralwerte haben genau 2 Formen | closed |
| T-20-25 | Denial of Service | Niederländisches Prozentzeichen | mitigate | `L10N_NL_JSON`/`L10N_NL_JS` in `L10N_CATALOGUES` (:284-285) | closed |
| T-20-26 | Tampering | U+2019 als Apostroph (nl, `foto's`) | mitigate | Nachmessung: 0 Vorkommen der fünf Zeichen in nl.json, nl.js, docs/l10n-dutch.md; Prüfzeile docs/l10n-dutch.md:467 | closed |
| T-20-27 | Tampering | Regel aus de.json kopiert statt aus Kerndatei gelesen | accept | siehe AR-20-03 | closed |
| T-20-28 | Repudiation | Katalog ohne Vorbehalt (nl) | mitigate | docs/l10n-dutch.md "Erzeugt am 25.09.2026, Plan 20-06" und :500 "von keinem Muttersprachler gelesen" | closed |
| T-20-29 | Spoofing | `pt.json` täuscht Katalog vor | mitigate | `pt.json`/`pt.js` existieren nicht; Grund in docs/l10n-catalogues.md Abschnitt 1 (:23 ff., Ladepfad ohne Kürzung) und :378; Kommentarabsatz im Gate test_admin_ui_contract.py:208-211 | closed |
| T-20-30 | Denial of Service | Portugiesisches Prozentzeichen (pt_PT) | mitigate | `L10N_PT_PT_JSON`/`L10N_PT_PT_JS` in `L10N_CATALOGUES` (:286-287) | closed |
| T-20-31 | Tampering | pt_PT trägt brasilianische Alltagswörter | mitigate | Nachmessung pt_PT.json: `ficheiro` 60, `utilizador` 1, `arquivo`/`usuário`/`tela` je 0; dauerhaft ergänzt durch T-20-34 | closed |
| T-20-32 | Tampering | Platzhalter verloren (pt_PT) | mitigate | pt_PT-Paar im Paritäts-Gate (:2546) | closed |
| T-20-33 | Repudiation | Grenzen des portugiesischen Ausbaus unerwähnt | mitigate | docs/l10n-portuguese.md:494 "## Was diese Kataloge nicht leisten" mit Rechtschreibreform (:499) und fehlenden getrennten Suchwortlauten (:507) | closed |
| T-20-34 | Tampering | pt_BR als Kopie von pt_PT | mitigate | `PORTUGUESE_WORDINGS_THAT_MUST_DIFFER` (11 Einträge, :745-767), `scan_named_difference` (:770-791), Gate `test_the_two_portuguese_catalogues_are_two` (:2383-2418) mit Kopie-Rotprobe und Fehlschlüssel-Rotprobe | closed |
| T-20-35 | Denial of Service | Brasilianisches Prozentzeichen | mitigate | `L10N_PT_BR_JSON`/`L10N_PT_BR_JS` in `L10N_CATALOGUES` (:288-289) | closed |
| T-20-36 | Tampering | Millionenform auf Index 1, falscher Satz bei n=2 | mitigate | Nachmessung: Form 1 == Form 2 in 5/5 Pluralwerten von pt_BR.json (und pt_PT.json); Begründung docs/l10n-catalogues.md Abschnitt 4 (:210) | closed |
| T-20-37 | Tampering | Platzhalter verloren (16 Dateien) | mitigate | Paritäts-Gate über alle 16 Einträge von `L10N_CATALOGUES` | closed |
| T-20-38 | Repudiation | Katalogzahl 6 auf 16 ohne Spur | mitigate | Docstring-Absatz :2299-2310 ("from six catalogues over three language codes to sixteen over eight") | closed |
| T-20-39 | Repudiation | PT_BR erbt Vorbehalt von PT_PT stillschweigend | mitigate | docs/l10n-portuguese.md:655 "### Zweiter Vorbehalt: die Spalte PT_BR", "Erzeugt am 25.09.2026, Plan 20-08"; Diff `7ae78d6..HEAD` zeigt im ersten Vorbehalt keine Änderung, nur Anfügung ab Zeile 654 | closed |
| T-20-40 | Repudiation | Sprachbeweis prüft einen nicht mehr existierenden Satz | mitigate | integration.yml:3276-3285: Erwartung zur Laufzeit per `php -r` aus `apps/findling/l10n/${code}.json`, `exit(3)` bei leer oder gleich Schlüssel, `::error::` und `failed=1`; Abwesenheitsprüfung der englischen Quelle :3302-3305; kein `${{ }}` im run-Block | closed |
| T-20-41 | Tampering | Nutzersprache bleibt auf pt_BR stehen | mitigate | Ausgangswert vor der Schleife gelesen (:3247-3251), `trap restore_language EXIT` (:3262) vor der ersten Sprachänderung (:3287), `--delete` falls kein Ausgangswert; Sichtprobe mit `finally` und belegtem Ausgangswert `de` (20-09-SUMMARY.md:39, :143). Restpunkt IN-02 siehe unten | closed |
| T-20-42 | Denial of Service | Übersetzte Seite zerbricht an ungeprüfter Stelle | mitigate | Owner-abgenommene Sichtprobe ("approved", 25.09.2026) über Adminseite und Ergebnisseiten mit/ohne Treffer in fünf Sprachen, 20-09-SUMMARY.md:53, :87 ff.; CI-Run 36126493024 grün (:75) | closed |
| T-20-43 | Spoofing | Probedatei der Sichtprobe reist ins Store-Paket | mitigate | `git status --short` am 25.09.2026 leer, `php/l10n` genau 16 Dateien (20-09-SUMMARY.md:109, hier unabhängig wiederholt) | closed |
| T-20-44 | Information Disclosure | CI-Antwortdatei mit Sitzungsdaten als Artefakt | accept | siehe AR-20-04 | closed |
| T-20-SC | Tampering | npm/pip/cargo installs | accept | siehe AR-20-05 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

Gegenprobe der Gates: `uv run --offline pytest tests/test_admin_ui_contract.py tests/test_public_artifacts.py` am 25.09.2026: 109 passed.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-20-01 | T-20-13 | Ausgabe läuft über `p()` und `textContent`. Nachgeprüft: `grep -rnE "print_unescaped\|innerHTML\|insertAdjacentHTML\|outerHTML\|document\.write" php/templates php/js` liefert 0 Treffer; letzte Änderung an `php/templates`/`php/js` ist `3fc7aa1` (24.09.2026 18:02), also vor der Research der Phase (`739338a`, 24.09.2026 21:47). Die Phase hat keine Ausgabestelle angefasst. Regressionsschutz besteht zusätzlich durch `scan_template`/`scan_script` mit Rotproben (test_admin_ui_contract.py:1769-1815) | Plan 20-03 (register_authored_at_plan_time), bestätigt im Audit | 2026-09-25 |
| AR-20-02 | T-20-17 | Katalogwerte tragen keine Daten, nur Platzhalter; die Platzhaltermenge hält das Paritäts-Gate über alle 16 Dateien, Inhalte kommen zur Laufzeit aus der Anwendung. Begründung trifft weiter zu | Plan 20-04 | 2026-09-25 |
| AR-20-03 | T-20-27 | `nl` und `de` tragen zeichengleich `nplurals=2; plural=(n != 1);`; die Herkunft aus `core/l10n/nl.json` ist dokumentiert (test_admin_ui_contract.py:160-179, docs/l10n-dutch.md:160). Zwei gleiche Zeichenketten sind maschinell nicht nach Herkunft trennbar, das Ergebnis ist funktional identisch. Begründung trifft weiter zu | Plan 20-06 | 2026-09-25 |
| AR-20-04 | T-20-44 | Die Antwortdatei `language-probe-${code}.html` bleibt im Workspace des Runners; integration.yml enthält überhaupt keinen `upload-artifact`-Schritt, die Datei stirbt mit dem Runner. Zugangsdaten sind als Wegwerf-Werte deklariert (integration.yml:2716-2717). Das Risiko ist damit kleiner als im Plan angenommen | Plan 20-09 | 2026-09-25 |
| AR-20-05 | T-20-SC | Keine Paketinstallation in der Phase. Nachgeprüft: `git diff --name-only 739338a^..HEAD` über `*pyproject.toml`, `*composer.json`, `*composer.lock`, `*uv.lock`, `*package.json`, `*package-lock.json`, `*requirements*.txt` liefert 0 Dateien | Plan 20-01 bis 20-09 | 2026-09-25 |

*Accepted risks do not resurface in future audit runs.*

---

## Hinweise ohne Blocker

- **Punktuelle statt dauerhafte Kontrollen:** T-20-20, T-20-26, T-20-31 und T-20-36 sind laut Plan als Abnahmekriterien deklariert, nicht als dauerhafte Gates. Sie sind am heutigen Baum nachgemessen erfüllt; eine spätere Katalogänderung mit U+2019, einem brasilianischen Wort in pt_PT oder Form 1 != Form 2 würde kein Gate rot machen (T-20-31 ist für pt_BR/pt_PT teilweise durch T-20-34 dauerhaft gedeckt). Kein offener Threat, da die deklarierte Mitigation genau das Abnahmekriterium war.
- **IN-02 (20-REVIEW.md) zu T-20-41:** Ein Fehlschlag von `occ user:setting ... core lang "${original}"` im EXIT-Trap wird nicht ausdrücklich als `::error::` gemeldet, der `--delete`-Zweig schluckt Fehler per `|| true`. Die deklarierte Mitigation (unbedingte Rücksetzung per Trap, auch nach Fehlschlag) ist vorhanden; die fehlende Erfolgsprüfung ist eine Härtungsmöglichkeit, kein Fehlen der Mitigation.
- **IN-01 (20-REVIEW.md) zu T-20-40:** Die Fehlermeldung nennt nur einen der beiden Abbruchgründe; der Abbruch selbst ist korrekt gebaut.

## Unregistered Flags

Keine. Keine der neun SUMMARY-Dateien führt einen Abschnitt `## Threat Flags`; die Threat-Tabellen der Summaries bilden ausschließlich auf registrierte IDs ab.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-25 | 45 | 45 | 0 | gsd-security-auditor (Claude) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-25
