# Phase 14: Kontext und Owner-Entscheide

## Owner-Entscheid 19.09.2026: engineState-Wortwahl (MEM-05)

**Zweig B: das sechste Wort `unloaded`.** Entschieden vom Owner am 19.09.2026
in der Session, nach Vorlage beider Zweige mit Preisschild (Analyse im
Sitzungsprotokoll). Begruendung in Kurzform: der Schalter braucht eine
sichtbare Rueckmeldung (Phase-15-A/B-Messung, Support-Fall "erste Suche
langsam"), und "genau ein Laden je warmem Fenster" ist am Zustandsverlauf
cold -> ready -> unloaded -> ready nachvollziehbar. Kostenfolge bewusst
akzeptiert: ENGINE_STATES an zwei Stellen, zwei Satztabellen, sechs
Katalogdateien in drei Sprachen (der neue franzoesische Wortlaut faellt
unter die Owner-Abnahme, er ist Muttersprachler), das Gate-Literal der
Engine-Satzzeile, docs/admin-page.md (dort steht heute "kein sechstes
Wort", der Satz ist nachzuziehen).

## Owner-Auftrag fuer spaeter (nicht diese Phase, NICHT verlieren)

Phase 16 (Store-Einreichung 1.2.0) bekommt einen eigenen Task mit
Owner-Checkpoint: Store-Texte ergaenzen + README aktualisieren, beides dem
Owner VOR der Einreichung zeigen (Owner-Ansage 19.09.2026).

## Leitplanken aus dem Research (technisch, vom Planner umzusetzen)

- Wellenschnitt: Wave 1 ist ausschliesslich der Vorpruefflauf (MEM-01);
  sein dokumentiertes Ergebnis gibt den Rest frei. Die Messerwartung steht
  VOR dem Lauf fest (Schwelle im Ablaufdokument).
- may_load: Empfehlung des Researchers uebernehmen, die Degradation haengt
  am Schalter, sonst misst die eine Box-Anfahrt zwei Aenderungen.
- _idle_announced ist ein Log-Merker und taugt nicht als Entladebedingung;
  der Poller braucht eine saubere busy-Auskunft.
- onnxruntime bleibt auf 1.30.0 eingefroren (bis nach Phase 15).
