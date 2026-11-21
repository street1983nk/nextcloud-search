# Phase 44: PHP-Sicherheits-Gates - Context

**Gathered:** 2026-11-21
**Status:** Ready for planning
**Source:** Owner-Vorgaben vom 21.11.2026 (ersetzen discuss-phase)

<domain>
## Phase Boundary

Die noch offenen Gates aus Phase 42 (Kriterium 3) kommen in CI: Psalm mit Taint-Analyse gegen OCP 33, 34 und 35 (SARIF selbst ausgezählt), php-cs-fixer mit nextcloud/coding-standard als dry-run, zizmor und actionlint für alle Workflows unter .github/workflows. Requirements PRUEF-02, PRUEF-03, PRUEF-04; Erfolgskriterien 1 bis 5 in .planning/ROADMAP.md, Phase 44.

Nicht Teil dieser Phase: neue Funktionen, Release 1.7.0 (Phase 45), PHPStan, Rector, Infection.

</domain>

<decisions>
## Implementation Decisions

### Gates
- D-01: Psalm mit Taint-Analyse läuft in CI als Matrix gegen nextcloud/ocp 33, 34 und 35. Der Job zählt die Befunde selbst aus der SARIF-Ausgabe und wird bei mindestens einem offenen Befund rot, weil Psalm mit Report-Datei sonst mit 0 endet (PRUEF-02).
- D-02: php-cs-fixer mit nextcloud/coding-standard läuft in CI als dry-run (`--dry-run --diff`) und ist auf dem Phasenkopf grün (PRUEF-03).
- D-03: zizmor und actionlint prüfen jeden Workflow unter .github/workflows in CI; ein neuer Befund ab Medium macht den Job rot (PRUEF-04).
- D-04: Jedes neue Gate braucht einen Negativtest bzw. eine Positivkontrolle: das Gate muss nachweislich rot werden (eingebaute Taint-Strecke, Stilverstoß, Workflow-Befund ab Medium), danach zurückgesetzt.
- D-05: Alle neuen Gates laufen auch lokal grün; das lokale Rezept ist dokumentiert. Ein Strukturgate verhindert das stille Entfernen der Gates aus den Workflows (Muster wie die Gate-Präsenz-Tests aus Phase 42).

### Befunde
- D-06: Security hat höchste Priorität. Befunde werden bevorzugt echt behoben. Akzeptieren (Baseline, Suppression, zizmor-Ignore) nur mit dokumentierter Owner-Entscheidung; dafür steht im Plan ein Checkpoint (autonomous: false), keine Annahme durch den Executor.
- D-07: Keine Änderung des Produktverhaltens außer echten Sicherheitsfixes. Jede Codeänderung an der PHP-App (php/lib, php/appinfo) bekommt einen Test.
- D-08: Der einmalige Formatierungs-Commit durch php-cs-fixer ist reine Stiländerung ohne Verhaltensänderung und wird durch die vorhandene PHPUnit-Suite abgesichert.

### Arbeitsregeln
- D-09: Commits nur als street1983nk <k.cherif@outlook.de> (`git -c user.name=street1983nk -c user.email=k.cherif@outlook.de commit`), ohne Claude- oder Session-Trailer, ohne closes/fixes #N. `gsd-sdk query commit` wird nicht verwendet.
- D-10: Push nur nach Owner-Frage: jeder Plan, der CI-Läufe auf GitHub braucht, enthält vor dem Push einen Checkpoint.
- D-11: Kein `python -c` und kein `python -` (Skripte als Dateien). Docker strikt seriell, fremde Container nie anfassen.
- D-12: Texte (Doku, Kommentare in Prosa, Commit-Texte) auf Deutsch mit echten Umlauten, keine Gedankenstriche U+2013/U+2014, keine Emojis. Vor jedem Commit auf Gedankenstriche prüfen.
- D-13: secure-phase schließt die Phase ohne offene Threats.

### Claude's Discretion
- Wahl der genauen Werkzeugversionen (gepinnt, mindestens zwei Wochen alt), Psalm-Level, Plugin-Auswahl, Stubs für OCA\AppAPI, Aufteilung in Jobs und Workflows, Form des SARIF-Zählers (Skriptdatei, jq oder PHP), Ort der Doku.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Herkunft und Anforderungen
- `.planning/REQUIREMENTS.md` - PRUEF-02, PRUEF-03, PRUEF-04
- `.planning/ROADMAP.md` - Phase 44, Erfolgskriterien 1 bis 5
- `.planning/milestones/v1.6-ROADMAP.md` - Phase 42, Kriterium 3 (ca. Zeilen 207 bis 234)
- `.planning/phases/42-php-sicherheits-gates/42-RESEARCH-GATES.md` - Recherche 04.11.2026 zu Psalm, php-cs-fixer, zizmor, actionlint
- `.planning/phases/42-php-sicherheits-gates/42-VERIFICATION.md` - Stand der Phase-42-Gates

### Bestehende Gates und Rezepte
- `.github/workflows/php.yml` - vorhandene PHP-Jobs (PHPUnit, Routen-Gate, composer-hygiene)
- `scripts/dev/phpunit_docker.sh` - lokales PHPUnit-Rezept (Docker)
- `tests/test_php_route_gate_presence.py` - Muster für Strukturgates gegen stilles Entfernen

</canonical_refs>

<specifics>
## Specific Ideas

- Psalm-Exit-Code-Falle wie im Nextcloud-Server übernehmen: SARIF schreiben, selbst zählen, bei mehr als 0 Befunden rot.
- Negativtest Psalm: absichtlich eingebaute Taint-Strecke (z. B. Request-Parameter ungefiltert in eine Antwort oder SQL), nur temporär oder als Fixture, die das Gate nachweislich rot färbt.

</specifics>

<deferred>
## Deferred Ideas

- PHPStan, Rector, Infection (laut Recherche 42 erst bei Bedarf).

</deferred>

---

*Phase: 44-php-sicherheits-gates*
*Context gathered: 2026-11-21 aus Owner-Vorgaben*
