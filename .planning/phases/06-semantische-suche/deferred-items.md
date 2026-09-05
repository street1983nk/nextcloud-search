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

**Nachtrag 05.09.2026 (Plan 06-09), gilt für DI-06-02 und DI-06-03:** Die
Deckungsgradzahl existiert jetzt. Der Container meldet `embedded` neben
`indexed`, und damit ist "der Bestand ist vollständig" zum ersten Mal eine
Bedingung statt einer Vermutung: `embedded == indexed` bei `indexed > 0`. Beide
Punkte bleiben trotzdem offen, und der Grund ist nicht Zeitmangel, sondern die
Richtung des Schreibens.

Plan 06-09 baut drei lesende Flächen: `GET /status`, `GET /diagnose` und die
Admin-Seite. Beide Punkte brauchen einen **Schreibvorgang auf dem Indexweg**:
DI-06-03 einen Stempel der Marke `embedding_version`, DI-06-02 einen Aufruf von
`reset_for_reindex` beziehungsweise `forget_all`, wenn diese Marke driftet. Das
gehört in den Poller, neben `Poller._stamp_if_rebuilt`, und nicht in eine Statusroute. Eine
Statusroute, die beim Lesen etwas stempelt, wäre außerdem genau die Sorte
Nebenwirkung, die dieses Projekt an drei Stellen ausdrücklich ausschließt
(`open_read_only`, `PRAGMA query_only`, und der Testfall "asking for the status
changes nothing").

**Was jetzt klar ist und der nächste Plan nicht neu herleiten muss:**

1. Die Bedingung für "vollständig" ist `embedded == indexed` bei
   `indexed > 0`, mit `VectorStore.document_count()` als Zähler. Sie ist
   bewusst nicht `chunk_count`/`vector_count`: die beiden zählen Chunks und
   stehen für die Frage "ist der Löschweg heil", nicht für "trägt jedes
   Dokument einen Vektor".
2. Der Stempel gehört nicht in `expected_versions()`. Diese Menge ist die
   Marke des Volltextindex, und ein Sprung darin erzwingt den Volltext-Reindex,
   den D-21 ausschließt. `VECTOR_ONLY_MARKS` trennt die Embedding-Marke aus
   genau diesem Grund, und sie bleibt getrennt.
3. Die Ordnung bei einem Drift ist zwingend: erst `forget_all`, dann die neue
   Marke, dann die Wiedervorlage der Dokumente. Umgekehrt stünde die Marke der
   neuen Fassung über einem Bestand der alten, und das ist der Zustand, den
   niemand mehr bemerkt.

**Schliessform, präzisiert:** ein eigener Plan auf dem Indexweg, spätestens
vor dem Tag `v1.0.0` aus Plan 06-12. Vor dem Tag, weil ein ausgeliefertes
Release, das einen Modellwechsel nicht bemerkt, still schlechtere Treffer liefert
und dafür keine Anzeige hat. Die billige Alternative, falls die Zeit nicht
reicht, ist eine bewusste Entscheidung mit einem Satz in `docs/embeddings.md`:
ein Modellwechsel verlangt `occ findling:index --restart`, und die App sagt das,
statt es zu können. Auch diese Alternative ist eine Entscheidung und keine
Lücke, aber sie muss getroffen und aufgeschrieben werden.
