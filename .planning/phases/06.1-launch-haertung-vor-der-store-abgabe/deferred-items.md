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
