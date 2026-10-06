---
created: 2026-10-01
title: Issues #21 (Limits einstellbar/Admin-UI) und #22 (Mac-Dateien ausschliessen) von budachst
area: general
---

- #21: FINDLING_MAX_CELLS (200.000) wird vom Backend gelesen, ist aber in backend/appinfo/info.xml NICHT als Deploy-Option deklariert -> Store-Installationen koennen es nicht aendern. Kandidat: deklarieren + Limits (Adressraum, Zellen) im Admin-Bereich anzeigen. Rueckfrage gestellt: out_of_memory oder too_many_cells?
- #22 OWNER-ENTSCHEID 01.10.: ._* (AppleDouble) FEST ueberspringen als excluded, keine Einstellung; Bundles offen (Rueckfrage welche Dateien/Gruende). Vorher: AppleDouble-Dateien (._*) und Mac-Bundles (.key etc., Ordner) machen den Grossteil der Fehlerliste aus. Heute nur "Ausgeschlossene Ordner", keine Muster. Owner-Entscheid offen: ._* fest ueberspringen vs. Ausschlussmuster als Einstellung.
- Slot: Phase 29 (Haertung 1.4.0) oder spaeter, Owner entscheidet.
