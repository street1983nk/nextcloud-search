# Slot-Leiter 1/2/4 auf arm64-CI (D-26-09, SC3), 29.09.2026

Frage: Wie viel Durchsatz bringen 2 und 4 OCR-Slots im echten Poller (`Poller.run_once`), gemessen je Stufe gegen die Rauschgrenze 1,05?

## Aufbau

- Runner: GitHub `ubuntu-24.04-arm`, Neoverse-N2, 4 Kerne, 15,9 GB RAM, Kernel 6.17.0-1022-azure (`raw/machine.txt`)
- Lauf: `measure.yml`, Job "W4 slot curve on arm64", Lauf 36523219615, manuell gestartet mit `image_ref=dev`
- Abbild: `ghcr.io/street1983nk/findling_backend:dev`, Digest `sha256:3327dd65ab563d446ba9f6f7fd2c4315f5204168846b1a78d0cea7c65da19205`, gebaut von docker.yml Lauf 36522819732
- Commit: `d91305dfa27ea0c8b95a6732f3c242f699f6bd24` (Phase 26 nach Welle 5)
- Korpus: 16 einseitige und 4 achtseitige synthetische Scans, 48 Seiten, Seed `phase-26-ladder`, Größe und sha256 je Scan in `raw/ladder-corpus.txt`
- Werkzeug: `scripts/ops/slot_ladder.py`, je Stufe 3 gezeitete Runden nach einer Anwärmrunde; cpuset wächst mit N (1 Slot auf Kern 0, 2 auf 0,1, 4 auf 0-3); `--network none`

## Ergebnis

| Slots | cpuset | Median Seiten/s | Runden (Seiten/s) | Fehlrunden | gekappte Ansprüche |
|---|---|---|---|---|---|
| 1 | 0 | 0,286 | 0,286 / 0,286 / 0,286 | 0 | 0 |
| 2 | 0,1 | 0,572 | 0,572 / 0,572 / 0,572 | 0 | 0 |
| 4 | 0-3 | 1,132 | 1,136 / 1,130 / 1,132 | 0 | 0 |

| Stufe | Faktor | Bewertung gegen 1,05 |
|---|---|---|
| 1 auf 2 | 2,000 | Zugewinn |
| 2 auf 4 | 1,979 | Zugewinn |
| 1 auf 4 gesamt | 3,958 | (ohne Schwelle) |

Rohdaten: `raw/ladder-slots-1.txt`, `raw/ladder-slots-2.txt`, `raw/ladder-slots-4.txt`, `raw/ladder-factor.txt`.

## Einordnung

- Beide Stufen liegen weit über der Rauschgrenze 1,05 (Regel 2.5 der BL-F04-Vorarbeit).
- Gegen die W4-Rohkurve (reine Slot-Probe ohne Poller, F4 = 3,955 vom 26.09.): Der echte Poller erreicht mit 3,958 praktisch die volle Obergrenze. Die seriellen Teile eines Durchgangs (Anspruch, Schreiben, Quittung) kosten auf diesem Korpus nichts Messbares.
- Die W4-Probe im selben Lauf ergab F4 = 3,976 (`raw/f4.txt`), die Obergrenze hat sich also nicht verschoben.
- K1-Rückfall der Roadmap (Faktor 1 auf 4 unter 1,5): nicht eingetreten.
- Pitfall 11: `byte_capped_claims 0` in allen drei Stufen, keine Zeile wurde vom Byte-Budget gekappt.
- Sparsam liest unabhängig davon weiter mit genau einem Slot.

## Nebenzahl Einbettung (ohne Bewertung)

- int8-Engine des Abbilds, 64 Passagen, cpuset 0-3: embed_slots 1 = 60,3 Passagen/s, embed_slots 2 = 90,4 Passagen/s (`raw/ladder-embed.txt`).

## Grenzen

- CI-Runner, keine Zielbox; 4 Kerne mit 15,9 GB RAM, also kein Speicherdruck und kein Wächtereingriff.
- Synthetischer Korpus, ein Lauf. Die AWS-Matrix-Messung (D-26-10) folgt in Phase 28.
