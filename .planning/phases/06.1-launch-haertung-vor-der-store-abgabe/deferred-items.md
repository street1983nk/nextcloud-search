# Deferred items, Phase 06.1

Befunde, die waehrend der Ausfuehrung dieser Phase aufgefallen sind und
ausserhalb des Plans lagen, in dem sie aufgefallen sind. Kein Fix hier, nur der
Befund und der Ort, an den er gehoert.

---

## DI-06.1-01 (gefunden in Plan 06.1-01): der Store-Satz steht nicht mehr in der README

**Gefunden:** beim vollstaendigen Backend-Lauf vor dem Abschluss von Plan
06.1-01, also nicht durch dessen Aenderungen. Betroffen ist keine der vier
Dateien dieses Plans.

**Was:** `tests/test_store_metadata.py::test_the_measured_sentence_reads_the_same_in_all_three_places`
ist rot, mit der Meldung `README.md: does not carry the measured sentence of
05-14`. Das Gate verlangt, dass der gemessene Satz aus Plan 05-14 wortgleich in
`README.md`, `php/appinfo/info.xml` und `backend/appinfo/info.xml` steht:

> A full index and OCR run over 50,000 files and 20 GB on a 4-GB ARM64 box
> peaked at 422 MB of resident anonymous memory, under a hard 2 GB limit
> enforced by the kernel, with no OOM kill.

Die README traegt ihn nicht mehr. Der letzte Eingriff an dieser Stelle ist
`80e93c1 docs(06-11): die Zahlen des Semantiklaufs eingesetzt, RSS-Store-Zahl
ersetzt`, also die Uebernahme der Zahlen aus dem Semantiklauf; die beiden
info.xml sind dabei nicht mitgezogen worden.

**Warum nicht hier behoben:** Plan 06.1-01 schliesst DI-05-36 und fasst
`main.py`, `config.py`, `test_lifecycle.py` und `resilience.yml` an. Der
Store-Satz gehoert zu Pflichtpunkt 7 dieser Phase, und die Zahl darin steht
ausserdem unter Vorbehalt: Pflichtpunkt 1 (die zweite Modellinstanz) senkt die
Grundlast und wird auf der Box nachgemessen, danach ist der Satz ohnehin neu zu
setzen. Ihn jetzt aus der README zurueckzuschreiben hiesse, eine Zahl zu
zementieren, die diese Phase gerade veraendert.

**Wohin es gehoert:** in den Plan dieser Phase, der die Store-Texte und die
Zahlen nach der Nachmessung anfasst (Pflichtpunkt 7), zusammen mit der
Dreisprachigkeit und dem Vokabular-Gate. Das Gate bleibt bis dahin rot und ist
damit die Erinnerung an genau diesen Schritt.


<!-- merged from worktree-agent-aafc87dfd0da36800 -->

# Zurückgestellte Funde der Phase 06.1

Befunde, die während der Ausführung auffielen, aber nicht zum jeweiligen Plan
gehören. Nicht gefixt, damit eine Ersparnis oder ein Fix seinen Posten behält.

## 06.1-02 (06.09.2026)

**`tests/test_store_metadata.py::test_the_measured_sentence_reads_the_same_in_all_three_places` ist rot.**

- Meldung: `README.md: does not carry the measured sentence of 05-14`
- Zustand vor Plan 06.1-02, nicht von ihm verursacht: der Plan fasst nur
  `backend/src/findling/embed/`, `api/resources.py` und `worker/poller.py` an,
  der Test liest ausschließlich `README.md` und die beiden `appinfo/info.xml`.
- Wahrscheinliche Ursache: Commit `80e93c1` ("die Zahlen des Semantiklaufs
  eingesetzt, RSS-Store-Zahl ersetzt") hat den gemessenen Satz im README
  geändert, ohne die beiden `info.xml` nachzuziehen.
- Zuständig: Pflichtpunkt 7 dieser Phase (Store-Vorgaben, dreisprachige Texte
  konsistent). Die Zahl muss dort ohnehin nach der Nachmessung aus 06.1-18 neu
  gesetzt werden, also gehört die Korrektur in denselben Griff und nicht hierhin.
- Restlicher Suitenstand am selben Baum: 1372 grün, 13 übersprungen, 1 rot.


<!-- merged from worktree-agent-ad8e6dc70eb379132 -->

# Zurueckgestellte Befunde der Phase 06.1

Befunde, die waehrend der Ausfuehrung aufgefallen sind und ausserhalb des Plans
liegen, in dem sie gefunden wurden. Sie werden hier notiert und nicht nebenbei
behoben, weil eine Korrektur ausserhalb des Plans in keinem Commit steht, den
jemand spaeter suchen wuerde.

## Aus Plan 06.1-05 (Randpfade der Extraktion)

- **`tests/test_store_metadata.py::test_the_measured_sentence_reads_the_same_in_all_three_places` ist rot,
  bereits auf dem Basiscommit `e40dc51` und ohne Bezug zu diesem Plan.**
  Meldung: `README.md: does not carry the measured sentence of 05-14`.
  Betroffen sind `README.md` und die beiden `appinfo/info.xml`, also der
  Store-Text, nicht der Extraktions- oder Indexpfad. Gehoert zu den
  Store-Vorgaben (Pflichtpunkt 7) und damit in einen der Plaene, die den
  Store-Text bearbeiten. Der Rest der Suite ist gruen (1403 passed, 13 skipped).
