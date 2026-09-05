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


---

## DI-06-02: `reset_for_reindex` hat keinen Aufrufer im Produktivcode

**Gefunden:** Plan 06-07, Task 3, beim Verdrahten der vier Loeschstellen.

**Befund:** `Store.reset_for_reindex` wird ausserhalb der Testsuite von nichts
gerufen. Der Neuaufbau laeuft heute ueber die angehobene Generation
(`start_rebuild_on_drift`) plus `occ findling:index --restart`, und die alten
Zeilen verschwinden dabei durch das erneute Urteil und nicht durch diesen
Aufruf. Die Methode ist damit eine API ohne Nutzer.

**Warum trotzdem verdrahtet:** Der Plan verlangt sie ausdruecklich als eine der
vier Stellen, und die Verdrahtung ist richtig, sobald sie einen Aufrufer
bekommt. Ohne Aufrufer bedeutet sie aber: Ein Modellwechsel leert den
Vektorbestand heute nicht von selbst.

**Schliessform:** Entweder bekommt der Neuaufbauweg einen Aufruf von
`reset_for_reindex`, oder die `embedding_version`-Marke bekommt beim Drift
einen eigenen Weg, der `forget_all` ruft. Das gehoert zu dem Plan, der die
Marke schreibt (offen seit 06-04, siehe unten).

---

## DI-06-03: `embedding_version` wird weiterhin von niemandem geschrieben

**Gefunden:** Plan 06-07, uebernommen aus 06-04 und 06-06.

**Befund:** Die Marke steht auf `unknown`. Seit diesem Plan gibt es zum ersten
Mal einen abgeschlossenen Einbettungslauf, der sie stempeln koennte, aber der
Zeitpunkt "der Bestand ist vollstaendig" ist eine Aussage ueber die ganze
Instanz und nicht ueber einen Durchgang, und dieser Plan hat keinen Zaehler
dafuer.

**Schliessform:** Plan 06-**09** rechnet den Deckungsgrad des Vektorbestands
(`chunk_count`/`vector_count` aus 06-04). Sobald diese Zahl existiert, ist
"vollstaendig" eine Bedingung, die man stempeln kann, nach dem Muster von
`stamp_after_rebuild`.

**Nachtrag 05.09.2026 (Plan 06-08):** Die Zeile stand hier zuerst mit der
Nummer 06-08, uebernommen aus den Zusammenfassungen von 06-06 und 06-07, die
die Statusseite unter dieser Nummer fuehren. Plan 06-08 ist der Ausschnitt fuer
rein semantische Treffer und rechnet keinen Deckungsgrad; die Statusseite ist
06-09. DI-06-02 und DI-06-03 sind mit 06-08 also ausdruecklich **nicht**
geschlossen.
