---
plan: 15-08
phase: 15-messphase-eine-box-anfahrt
status: complete
completed: 2026-09-20
requirements-completed: []  # MESS-05 gehoert an 15-16
---

# 15-08 SUMMARY: Owner-Tor, die Deckelfreigabe

## Owner-Entscheid (im Wortlaut, 20.09.2026, in der Session)

Vorgelegt wurden die Rechnung (zehn Posten, 39 h 22 min mal 1,15 = 45,27 h,
aufgerundet 46 h, mal 0,115841 USD/h = 5,40 USD netto), die Deckel-Geschichte
(30 h/3,50 am 09.09., gerissen 10.09. 15:20Z, angehoben 34 h/4,00, verbraucht
31,05 h/3,5969) und die drei Stellschrauben.

- **Deckelfreigabe:** "Freigegeben, 46 h / 5,40 USD" (Datum: 20.09.2026).
- **Frage A (A-Record):** "Ich setze den Record", der Owner traegt
  loadtest.infranode.dev ein, sobald die Instanz laeuft und die IP feststeht.
- **Frage B (Snapshot-Verbleib):** "Nur den neuen Snapshot abbauen", der
  Korpus-Snapshot snap-03f1d1d9ad9262704 bleibt stehen (2,79 bis 2,99 USD je
  Monat), damit eine weitere Anfahrt ohne mehrstuendigen Neuaufbau startet.
  Vollzug in 15-14 entsprechend: der Ende-Snapshot faellt, der Korpus-Snapshot
  nicht.
- **Frage C (verkuerzte Ruhezeit):** "120 s bestaetigt" als TTL der
  Entlade-Messung, Begruendung geht ins Protokoll (D-02 konkretisiert).

## Wirkung

Das Tor der Phase ist offen: die Plaene 15-09 bis 15-16 (gated_by: 15-08)
duerfen ausgefuehrt werden. Die Anfahrt selbst ist eine BEGLEITETE Sitzung
(15-09 bis 15-14, autonomous: false) und beginnt erst, wenn der Owner die
Sitzung eroeffnet; keine Box-Stunde wartet auf einen Menschen (Volllauf
detached ueber Nacht, Stellschraube 3 aus der Vorlage, bereits eingeplant).

## Offene Vorbedingung aus 15-07 (vor der Anfahrt zu klaeren)

Der Integrationslauf 35470079862 (Commit 15-05) scheiterte am Schritt
"Log every account in and keep its session" ("the login of minimal was
refused"); auf dem Folgecommit f650c10 war Integration wieder gruen, es war
also ein Einzelfall. Vorgeschichte parity-login-probe-404 vom 11.09. steht in
deferred-items.md. Vor der Anfahrt einmal kurz bestaetigen, dass der
CI_LAUF-Kandidat (35469147833) weiter der juengste gruene ist.
