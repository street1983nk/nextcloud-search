---
phase: 46-findling-1-7-1
plan: 06
subsystem: release
tags: [rel-08, audit, ci]
requires: [46-05]
provides: [46-AUDIT.md, audited_head 1a0abda0, ci_head 6003b353, status_46_06 passed]
duration: ca. 1 Tag mit drei Push-Runden
completed: 2026-11-27
---

# 46-06: Delta-Audit, Push, grüner Kandidat 1.7.1

## Ergebnis

- Audit v1.7.0..HEAD (b24f84e2): 16 Prüfpunkte, Threat-Register T-46-01 bis T-46-13, Docker-Gates vor dem Push grün (PHPUnit 1451 Tests, Psalm-Taint OCP 33/34/35, php-cs-fixer, zizmor, actionlint).
- Push 1 (0deaf620): Python gates rot (shellcheck-Pfade, V-46-06-02), coverage-e2e rot (Aufruf über findling-src auf matrix.src, V-46-06-01). Fix per TDD e448e02b/2fa545a9.
- Push 2 (a66b016c): Python gates rot am nicht nachgezogenen PHP-Baumhash (von der Hauptsitzung behoben, ce8a5021, Push 1180c9a4 grün); coverage-e2e: Rücksprung-Schritt rot (V-46-06-03, Ursache: Versionssperre D-11 der 1.6.2-Begleit-App gegen die vom Kopf 1.7 gespeicherte Version; Testerwartung, kein Produktfehler). Fix nach Owner-"Ja" per TDD e16c2b56/22e13f0a, Doku 1a0abda0.
- Push 3 (6003b353): alle Pflichtläufe und coverage-e2e 45995128241 grün; Belege in 46-AUDIT.md "## Nachtrag 46-06: grüner Kandidat". audited_head 1a0abda0, ci_head 6003b353, status_46_06 passed (885a7f58).

## Lehren

- Vor jedem Push die volle Python-Suite lokal (der PHP-Baumhash hängt an php/ und fällt nur dort auf).
- Bei Skripten, die in mehreren Checkouts laufen, den Checkout und das Arbeitsverzeichnis jedes Aufrufers am Code prüfen; die Gates dafür (checkout_findings, shellcheck_findings) sind jetzt da.
- Prüfschritte, die von Hand Versionen tauschen, müssen den Admin-Handgriff nachbilden (gemerkte Version der anderen Hälfte).
