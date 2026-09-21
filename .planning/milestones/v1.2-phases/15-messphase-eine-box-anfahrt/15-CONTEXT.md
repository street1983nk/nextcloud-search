# Phase 15: Kontext und Owner-Entscheide

## Owner-Entscheide 19.09.2026 (in der Session, nach Vorlage des Research)

1. **Filter und Sortierung bekommen einen EIGENEN MESSBLOCK auf der Box**
   (Sortierung auf grossem Bestand, Blaettern unter Filter). Geschaetzt
   +1 bis 2 h Box-Zeit; der Deckel im Rechenblatt zieht entsprechend mit.
2. **Ruhezeit verkuerzt mit Begruendung:** die Entlade-Messungen stellen
   die TTL klein (60 bis 120 s) statt der 900 s des Vorschlagswerts; die
   Abweichung wird im Protokoll begruendet (derselbe Mechanismus, Stunden
   gesparte Box-Zeit). Der 900-s-Vorschlagswert selbst bleibt eine
   gekennzeichnete Schaetzung (Owner-Entscheid aus 14-12).
3. **Snapshot wird nach der Anfahrt ABGEBAUT** (Kriterium 5 verlangt den
   Box-Abbau ohnehin); der Snapshot-Hash ist protokolliert, eine
   Nachmessung baut aus dem Hash neu.

## Begruendete Vorentscheide (Orchestrator, aus zwingender Logik)

- **Abbild der Box:** das aktuelle Multi-arch-Release-Image (Stand
  Phase-14-Abschluss, CI-Lauf gruen auf 6355b45) per Digest. Zwingend,
  weil Kriterium 5 den MEM-01-Schalter misst, den nur dieses Abbild
  traegt. Der Runbook-Widerspruch (baumhash-gleich als Abbruchbedingung
  gegen den noetigen Abbildwechsel) wird aufgeloest durch einen
  dokumentierten Abbildwechsel-Block VOR Messbeginn: gewechselt wird
  einmal, vor der ersten Messung, danach gilt baumhash-gleich wieder.
- **Belegkriterium fuer den 900-s-Vorschlag:** der Planner legt das
  Vorab-Kriterium fest (Muster 14-01: Erwartung VOR dem Lauf), Richtung:
  belegt werden die FOLGEN einer Frist (RSS auf Grundlast nach Ablauf,
  erste Suche haelt die Decke), nicht die Frist selbst.

## Leitplanken aus dem Research (Planner setzt um)

- Wellenform: Welle A ohne Box (autonom: fehlende Skripte aus
  2026-09-vergleichsmessung-m7g kopieren, nie editieren; Schritt-8-Skript
  NEU bauen; Abbildwechsel-Block + drop_caches ins Runbook; Rechenblatt
  aktualisieren inkl. neuem Messblock), Welle B = Owner-Checkpoint
  Deckelfreigabe mit Datum, Welle C = begleitete Box-Sitzung (nicht
  autonom: A-Record, Deckel, 26-h-Lauf).
- Reihenfolgenkonflikt: "kalt" wird HERGESTELLT (Containerneustart +
  drop_caches nach den waermenden Schritten), nicht bewahrt; die Zeile
  gehoert in die Ablaufdatei, bevor die Box steht.
- Mitreisende Belege: MEM-02 ("Rueckkehr zur Grundlast nach einem
  Indexlauf") und die duenne 1,5-s-Marge der ersten Suche nach Entladung
  (14-12-Messauftrag).
- onnxruntime bleibt bis nach der Anfahrt auf 1.30.0.
