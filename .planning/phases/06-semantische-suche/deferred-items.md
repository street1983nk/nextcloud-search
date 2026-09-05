# Zurückgestellte Punkte, Phase 6

Fundstellen, die während der Ausführung aufgefallen sind, aber nicht von der
jeweiligen Aufgabe verursacht wurden. Sie werden hier festgehalten und nicht
nebenbei repariert.

## DI-06-01: `ruff format` prüft die Markdown-Dateien des Repositoriums nicht

**Gefunden:** 05.09.2026, beim Abschluss von 06-02 und 06-03.

**Befund:** `python.yml` ruft `uv run ruff format --check .` mit dem
Arbeitsverzeichnis `backend`, deckt also 91 Dateien ab und ist grün. Ruff
formatiert seit einiger Zeit auch Python-Codeblöcke in Markdown, wenn man ihm
die Dateien übergibt. Ruft man dieselbe Prüfung eine Ebene höher auf
(`uv run ruff format --check ..`), meldet sie **neun** Markdown-Dateien als
umformatierbar:

- `.planning/phases/02-indexkern-und-volltextsuche/02-RESEARCH.md`
- `.planning/phases/03-aktualit-t-und-ocr/03-PATTERNS.md`
- `.planning/phases/03-aktualit-t-und-ocr/03-RESEARCH.md`
- `.planning/phases/04-admin-sichtbarkeit-und-diagnose/04-PATTERNS.md`
- `.planning/phases/05-h-rtung-und-store-einreichung-v1-0/05-PATTERNS.md`
- `.planning/phases/05-h-rtung-und-store-einreichung-v1-0/05-RESEARCH.md`
- `.planning/phases/06-semantische-suche/06-PATTERNS.md`
- `.planning/research/ARCHITECTURE.md`
- `docs/performance.md`

**Warum nicht repariert:** Alle neun sind vorbestehend und stammen aus den
Phasen 2 bis 6; keine davon wurde in 06-02 oder 06-03 angefasst. Eine
Umformatierung würde Codebeispiele in Planungs- und Rechercheunterlagen ändern,
also Text, der als historischer Stand gilt.

**Schliessform:** Entweder eine bewusste Entscheidung, dass Markdown ausserhalb
der Formatprüfung bleibt (dann gehört ein Satz dazu in `python.yml`), oder ein
eigener Lauf, der die neun Dateien in einem Rutsch formatiert und danach den
Prüfumfang von `backend` auf die Wurzel hebt. Beides ist eine
Aufräumaufgabe und kein Blocker: `docs/performance.md` ist die einzige der neun,
die Nutzer je zu sehen bekommen, und ihr Codeblock ist inhaltlich richtig.
