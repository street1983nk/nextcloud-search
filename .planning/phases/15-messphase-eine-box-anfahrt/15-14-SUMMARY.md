---
plan: 15-14
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-21
requirements-completed: []
---

# 15-14 SUMMARY: Endmessung, Kostenhistorie, Abbau

## Task 1: Endmessung und Kostenhistorie (vor jedem zerstoerenden Schritt)

- Endstand des Index (90-bestand.txt): **52.137 indexiert, 44 uebersprungen,
  6 fehlgeschlagen**, Korpus 19G, state.db-Marken vollstaendig
  (embedding_version multilingual-e5-small/int8/384/1024, tantivy v0.26.0).
- Vektorbestand (96-vektorbestand.txt): erhoben.
- Box geparkt (aws_box.sh stop): **Laufzeit 25,75 h, Kosten 2,9831 USD netto**.
- Kostenhistorie (93-kosten-und-verbleib.txt), committet auf origin VOR dem
  Abbau (Commit df1d11c belegt die Reihenfolge): Deckel 46 h / 5,40 USD,
  verbraucht 25,75 h / 2,98 USD, **Differenz 20,25 h / 2,42 USD unter dem
  Deckel. Deckel gehalten: JA.** Auch die Untergrenze 31 h / 3,59 USD
  unterschritten, weil der Volllauf mit 19 h 20 min schneller war als v1.1.

## Task 2: Verbleib des Korpus-Snapshots (Owner-Checkpoint)

Owner am 21.09.: **"Abbauen, Korpus-Snapshot behalten."** Konsistent mit 15-08
Frage B. snap-03f1d1d9ad9262704 bleibt (purpose=findling-corpus-keep,
~55,4 GB, 2,79-2,99 USD/Monat), damit eine weitere Anfahrt ohne Neuaufbau
startet. Kein Ende-Snapshot erzeugt (der Korpus liegt bereits im bleibenden).

## Task 3: Abbau, mit Rueckleseprobe je Ressourcenart

aws_box.sh destroy (mit FINDLING_STATE_BACKUP), je gegen die API verifiziert:
- Instanz terminiert, "is gone, verified against the api".
- Datentraeger geloescht (purpose=findling-phase5), verifiziert weg.
- Security Group geloescht, verifiziert weg.
- Tag-Sweep: "nothing that carries purpose=findling-phase5 exists any more".
- box.env entfernt (Sicherung ausserhalb des Repos).

Zwei Reste ausserhalb von destroy geschlossen:
- **Schluesselpaar** (Abweichung 1 aus 15-09: destroy loescht es nicht): von
  Hand entfernt, describe-key-pairs meldet InvalidKeyPair.NotFound. Nachtrag
  15-15: cmd_destroy soll es aufnehmen.
- **A-Record** loadtest.infranode.dev: nach dem Abbau ueber die Cloudflare-API
  entfernt (success), weil die Zielinstanz nicht mehr existiert.

## Was bleibt

Korpus-Snapshot (gewollt), die committeten Rohdaten des Laufverzeichnisses, die
box.env-Sicherung und die Kontopasswoerter (beide ausserhalb des Repos). Keine
laufenden Box-Kosten mehr ausser dem Snapshot.

## Verification

- Drei Endmess-Rohdateien mit ihren Zahlen: GRUEN.
- 93-kosten-und-verbleib.txt mit BOX_LAST_UPTIME_HOURS/COST, committet auf
  origin vor dem Abbau: GRUEN.
- 07-snapshot-und-abbau.txt: findling-phase5 und findling-corpus-keep genannt,
  Geheimnis-Gate (ausser dem committeten Snapshot) leer: GRUEN.
- Abbau je Ressourcenart gegen die API rueckgelesen: GRUEN.

## Naechster Schritt

15-15 (autonom): die Runbook-Nachtraege aus allen Befunden der Anfahrt.
Danach 15-16 (Owner-Checkpoint): MESS-05 und MEM-02 abhaken, Bodensatz-Zahl
vorlegen.
