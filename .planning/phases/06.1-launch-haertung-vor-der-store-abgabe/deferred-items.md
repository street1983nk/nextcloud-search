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
