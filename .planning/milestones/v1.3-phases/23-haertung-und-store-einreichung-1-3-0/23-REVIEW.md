---
phase: 23-haertung-und-store-einreichung-1-3-0
reviewed: 2026-09-27T08:00:16Z
depth: standard
files_reviewed: 29
files_reviewed_list:
  - .github/workflows/deploy-harp.yml
  - .github/workflows/docker.yml
  - .github/workflows/integration.yml
  - .github/workflows/release.yml
  - .github/workflows/resilience.yml
  - backend/appinfo/info.xml
  - backend/pyproject.toml
  - backend/src/findling/api/search.py
  - backend/src/findling/api/snippets.py
  - backend/src/findling/embed/engine.py
  - backend/src/findling/tools/one_load.py
  - backend/tests/probe_image_search.py
  - backend/tests/test_embed_engine.py
  - backend/tests/test_embed_model.py
  - backend/tests/test_measurement_scripts.py
  - backend/tests/test_one_load.py
  - backend/tests/test_search_endpoint.py
  - backend/tests/test_snippets_endpoint.py
  - backend/tests/test_store_metadata.py
  - backend/uv.lock
  - docs/admin-page.md
  - docs/audits/2026-09-phase-23/README.md
  - docs/embeddings.md
  - docs/language-analyzers.md
  - docs/measurements/2026-09-komposita-nl/README.md
  - docs/store-listing.md
  - php/appinfo/info.xml
  - php/lib/Migration/Version001300Date20260927000000.php
  - php/tests/Unit/Version001300Date20260927000000Test.php
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: resolved
resolved: 2026-09-27T08:06:55Z
resolution:
  WR-01: fixed
  WR-02: fixed
  IN-01: dokumentiert
  IN-02: dokumentiert
  IN-03: dokumentiert
---

# Phase 23: Code Review Report

**Reviewed:** 2026-09-27T08:00:16Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** resolved (2026-09-27: WR-01 und WR-02 gefixt, IN-01 bis IN-03 dokumentiert)

## Narrative Findings (AI reviewer)

## Summary

Gegenstand waren die 29 Dateien der Plaene 23-01 bis 23-09: der Kaltstart-Fix (query_may_load konstant False, Warmlauf ueber BackgroundTasks, Einwortregel auf /snippets), der F-23-01-Fix in release_if_idle, die gone-Reparatur-Migration samt PHPUnit- und Upgrade-CI-Beweis, die fastembed-Entfernung (HART-04), der Versionssprung auf 1.3.0 und die Store-Text-Gates. Das Security-Audit aus 23-08 wurde nicht wiederholt; Fokus lag auf Korrektheit, Randfaellen und Qualitaet.

Der Kern haelt der adversarialen Pruefung stand: query_may_load() ist an jeder Schalterstellung False, der Warmlauf ist ueber `_WARMING` und den Early-Return in `EmbeddingModel._load` doppelt gegen Doppel-Loads gesichert, `warm_wanted()` und `engine_state()` lesen lockfreie Properties und blockieren den Event-Loop nicht, die Einwortregel auf /snippets liest dieselben Felder wie /search (keine zweite Definition von "ein Wort"), und die Migration ist idempotent, gebandet, transaktional mit Rollback-plus-Rethrow und ohne Container-Kollaborateur; `QueueMapper::requeueAs` oeffnet selbst keine Transaktion, die Bandtransaktion der Migration umschliesst also sauber. Die CI-Beweise (Store upgrade 2b/5, Kaltstart-Nachmessung, HART-04-Abwesenheitsschritt) sind fail-closed gebaut. uv.lock ist frei von fastembed, requests, loguru, mmh3, py-rust-stemmers, urllib3 und win32-setctime; keine Restimporte in src/tests.

Gefunden wurden zwei Warnungen (ein stehengebliebener, durch Messung widerlegter Kommentar, den der L-16-04-Fix uebersehen hat, und ein TOCTOU-Randfall in release_if_idle) sowie drei Info-Befunde. Da 1.3.0 bereits im Store steht, sind beide Warnungen Kandidaten fuer Phase 24 bzw. den v1.4-Backlog, kein Hotfix noetig.

## Warnings

### WR-01: release.yml traegt die widerlegte Pfadfilter-Behauptung weiter, die L-16-04 laut Audit 23-08 entfernt hat

**File:** `.github/workflows/release.yml:172-177`
**Outcome:** fixed (Commit dd7e408, Kommentar auf die gemessene Wahrheit umgestellt, Check unverändert als Defense in depth)
**Issue:** Der Kommentar ueber dem Schritt "On a tag, the tag and both info.xml versions have to agree" begruendet die Duplikation mit: "docker.yml is path filtered on backend/**, so a release tag placed on a commit that does not touch the backend skips it entirely." Genau diese Aussage ist im selben Repository durch Messung widerlegt: docker.yml:19-24 (und der in 23-08 korrigierte Kopfkommentar von release.yml selbst, Zeilen 20-25) halten fest, dass der Pfadfilter einen Tag-Push nachweislich NICHT aufhaelt (Tag v1.0.0 auf einem store/media/**-Commit, Run 34140924599). Das 23-08-SUMMARY behauptet, die Kommentare in docker.yml UND release.yml wuerden das nicht mehr behaupten (L-16-04, Commit ea293cc); diese zweite Stelle in release.yml wurde uebersehen. Ein spaeterer Leser koennte auf Basis der falschen Begruendung den (weiterhin sinnvollen) Doppel-Check entfernen oder falsche Schluesse ueber das Tag-Verhalten von docker.yml ziehen.
**Fix:** Kommentar auf die gemessene Wahrheit umstellen, den Check selbst behalten (Defense in depth), z. B.:
```yaml
# Duplicates the check docker.yml already performs on a tag, and the
# duplication is the point: this workflow builds the file the store
# downloads, so it verifies the version itself instead of trusting
# another workflow. (The paths filter of docker.yml has been measured
# NOT to hold a tag push back, L-16-04; this check does not depend on
# that observation in either direction.)
```

### WR-02: release_if_idle liest last_use vor dem Lock und kann eine soeben benutzte Engine freigeben (TOCTOU)

**File:** `backend/src/findling/embed/engine.py:459-481`
**Outcome:** fixed (RED-Test 2a69aad, Fix b96525d: last_use unter _LOCK erneut gelesen, vor der Marker-Löschung; idle-Guard in EmbeddingModel.release() als v1.4-Backlog in deferred-items.md notiert)
**Issue:** `release_if_idle` liest `held.last_use()` (Zeile 459) und prueft die Ruhespanne AUSSERHALB von `_LOCK`. Unter dem Lock wird nur die Identitaet des Halters geprueft (Zeile 469), nicht die Aktualitaet der Ruhespanne. Eine Suche, die zwischen dem last_use-Read und `held.release()` auf derselben Instanz einbettet (und `_last_use` auf jetzt setzt), verhindert die Freigabe nicht: `EmbeddingModel.release()` (model.py:660-670) verweigert nur, solange ein Batch IN FLIGHT ist, nicht, wenn er gerade fertig wurde. Folge: Die Gewichte werden unmittelbar nach einer Nutzung freigegeben, die naechste Suche desselben Nutzers antwortet rein lexikalisch und bezahlt einen Hintergrund-Reload. Der Fall ist selten (Tick der Release-Task muss mit dem Ende einer Ruhespanne und einer gleichzeitigen Suche zusammenfallen) und seit Phase 14 vorhanden, aber die Funktion wurde in dieser Phase (F-23-01) angefasst, und der Docstring dokumentiert nur den Instanztausch-Fall (T-14-20), nicht diesen.
**Fix:** `held.last_use()` unter `_LOCK` erneut lesen (lockfreier, billiger Read) und bei einer bewegten Uhr False antworten:
```python
with _LOCK:
    if _held(model_dir) is not held:
        return False
    stamp = held.last_use()
    if stamp is None or time.monotonic() - stamp < ttl_seconds:
        return False
    _WARM_WANTED = False
```
Das schliesst das Fenster nicht vollstaendig (der Embed laeuft unter `model._lock`, nicht unter `_LOCK`), verkleinert es aber von "Dauer der Idle-Pruefung" auf Mikrosekunden. Ein vollstaendiger Schluss braeuchte eine idle-since-Prueffung in `EmbeddingModel.release()` unter dessen eigenem Lock; als v1.4-Backlog-Notiz festhalten.

## Info

### IN-01: Restrennfenster des F-23-01-Fixes: ein request_warm im Freigabefenster ueberlebt die Freigabe unverdient

**File:** `backend/src/findling/embed/engine.py:466-481` und `backend/src/findling/api/search.py:305-326`
**Outcome:** dokumentiert (kein Fix in 1.3.0; durch den WR-02-Umbau mit verkleinert, Eintrag in deferred-items.md)
**Issue:** Jede hybride Runde ruft `request_warm()` VOR dem Embed (one_round baut die SemanticSide, fordert an, dann embeddet candidate_round). Setzt eine Suche den Marker, nachdem `release_if_idle` ihn unter `_LOCK` geloescht hat, aber bevor `held.release()` `_engine` nullt, und wird ihr Embed noch von der warmen Engine beantwortet, dann ueberlebt ein Marker die Freigabe, dem keine abgewiesene Suche gegenuebersteht. Der naechste Tick der Warm-/Release-Task laedt die Gewichte zurueck, ohne dass jemand sucht: das Symptom von F-23-01 in einem sehr schmalen Fenster. Selbstheilend und selten; die Kosten sind ein einzelner unnoetiger Lade-/Freigabezyklus.
**Fix:** Wird durch den WR-02-Umbau mit verkleinert; alternativ den Marker erst NACH `held.release()` (bei True) loeschen, dann faellt der Fall mit dem dokumentierten "a search refused after the release sets it anew" zusammen. Als Randnotiz zum bestehenden F-23-01-Kommentar dokumentieren.

### IN-02: Migrationsausgabe zaehlt Bandgroessen statt requeue-Ergebnis und sagt "1 files"

**File:** `php/lib/Migration/Version001300Date20260927000000.php:107-110`
**Outcome:** dokumentiert (kein Fix in 1.3.0, Backlog; Eintrag in deferred-items.md)
**Issue:** `$total += count($band)` zaehlt jede skipped(gone)-Zeile als "requeued", waehrend `QueueMapper::requeueAs` einen genaueren Wert zurueckgibt (dirty-Zeilen und Zeilen mit pendender Loeschung, `KIND_DELETE`, zaehlt er bewusst nicht). Die Info-Zeile "requeued %d files once judged gone" kann also ueberzeichnen; dazu die Grammatik "requeued 1 files" bei genau einem Treffer. Rein diagnostisch, das Verhalten der Migration (Requeue plus Loeschung je Band in einer Transaktion) ist korrekt.
**Fix:** Rueckgabewert verwenden und Wortlaut praezisieren, z. B. `$total += $this->queueMapper->requeueAs($band, QueueMapper::KIND_CONTENT);` mit Meldung "handed %d gone verdicts back to the content track" (Testliterale in Version001300Date20260927000000Test.php muessten mitziehen); Backlog, kein Hotfix.

### IN-03: monkeypatch-Restore der test_one_load-Fixture stellt einen eventuell veralteten _WARM_WANTED-Wert wieder her

**File:** `backend/tests/test_one_load.py:150-155`
**Outcome:** dokumentiert (Testhygiene, kein Fix in 1.3.0; Eintrag in deferred-items.md)
**Issue:** Die Fixture setzt den Marker per `monkeypatch.setattr(engine_module, "_WARM_WANTED", False)`. monkeypatch stellt beim Teardown den VOR-Testwert wieder her: hatte eine fruehere Suite den Marker auf True stehen lassen, kommt dieses True nach jedem one_load-Test zurueck und kann in spaetere Suiten ohne eigenen Guard lecken. test_embed_engine.py (`no_warm_request`, Zeilen 1177-1189) und test_search_endpoint.py (`warm_ground`) loeschen bewusst auf BEIDEN Seiten; diese Fixture nennt dieselbe Absicht im Kommentar, erreicht sie aber nur zur Setup-Zeit.
**Fix:** Wie in `no_warm_request` explizit auf beiden Seiten setzen:
```python
engine_module._WARM_WANTED = False
yield volume
engine_module._WARM_WANTED = False
```
Nur Testhygiene, ausgelieferter Code ist nicht betroffen.

---

## Was geprueft und fuer sauber befunden wurde (Auszug)

- **engine.py:** query_may_load() konstant False mit Seam-Begruendung; warm() clears `_WARM_WANTED` beim Uebernehmen (ein fehlgeschlagener Warmlauf laeuft in den Cooldown von `_load`, kein Thundering-Reload); `warm_wanted` verlangt Anforderung + Halter + Artefakte (D-03 haelt: ohne Suche bleibt der Container kalt); `loaded`/`artifacts_absent` sind lockfrei, `warm_wanted()` im Handler blockiert den Event-Loop nicht waehrend eines laufenden Loads.
- **search.py / snippets.py:** BackgroundTasks statt loser Task (M-16-01 geschlossen); Einwort-, Operator-, titleOnly- und Sortier-Regel auf /search, dieselben drei Felder ohne Sort auf /snippets (SnippetsRequest hat bewusst kein sort-Feld, Lockstep-Gate); /snippets fordert keinen Warmlauf an, eine Auslösestelle genuegt; Fehlerpfade loggen nur Typnamen.
- **one_load.py / test_one_load.py:** Treiber geht den echten Handlerweg (`if warm_wanted(): warm()`); Anti-Vakuitaet in allen vier Phasen; Mutationstest fuer eine Suche, die nicht mehr anfordert, inklusive Gegenprobe ohne Mutation.
- **Migration + Test:** SELECT und DELETE binden exakt skipped UND gone; DELETE wiederholt beide Bedingungen plus file_id-IN-Band (kein Loeschen fremder Urteile); Rollback plus Rethrow; 2500 Zeilen = 3 Baender in 3 Transaktionen; Konstruktor per Reflection auf genau IDBConnection + QueueMapper; changeSchema nicht ueberschrieben.
- **deploy-harp.yml (2b/5):** Saat fail-closed (0 Treffer vorher, genau 1 Urteil, 0 Queue-Zeilen, 0 Treffer nach dem Saeen); docker-pause-Fenster mit Trap auf jedem Ausweg; moved_by_seed nur fuer die drei betroffenen Zaehler, alle uebrigen unchanged-Zeilen wortgleich erhalten (D-10 "nicht aufweichen" eingehalten); 3b prueft Urteil weg UND Titel des Treffers; Warteschleife fail-closed (awk-Parsefehler kann die Schleife nicht vorzeitig gruen machen, weil seed=1 mitgefordert ist).
- **integration.yml:** Dreistufiger Kaltstart mit Trefferpflicht (jq -e, HTTP-Code), 120-s-Deadline gegen Haenger, Dauer gedruckt und nie zugesichert; nicht-kalter Zustand wird ehrlich als "WARM, NOT COMPARABLE" gedruckt statt rot.
- **docker.yml:** HART-04-Schritt prueft im gepushten Digest mit `--network none` Abwesenheit (fastembed, requests) UND Anwesenheit (tokenizers, numpy); laut 23-02 in beide Richtungen von Hand rot/gruen getestet.
- **pyproject/uv.lock:** fastembed-Pin entfernt, tokenizers==0.23.2 und numpy==2.5.2 als direkte Kanten auf unveraenderten Versionen; keine der sechs entfernten Abhaengigkeiten mehr im Lockfile; keine Restimporte.
- **info.xml beide Haelften:** Version 1.3.0 und image-tag 1.3.0 im Gleichlauf; Sprachzeile direkt vor dem 4-Punkte-Grenzblock in allen sechs Texten; 730,2/730.2/730,2-Mo-Zahl konsistent; neuer Text von FINDLING_EMBED_IDLE_RELEASE_SECONDS beschreibt das D-01-Verhalten korrekt; keine Em-Dashes.
- **Doku:** embeddings.md Abschnitt 10 benennt Kaltstart und Ladefenster (D-08) inklusive der leeren zweiten /search; admin-page.md praezisiert cold/unloaded in Spalte 3 (Owner-Entscheid "So lassen" fuer den UI-Text); Komposita-Bericht 4.3 nennt je Zahl die Quelle (41,9 = m7g 5.2, 42,1 = grundlast-fein); language-analyzers.md-Kurzliste zeichengleich zum EN-Store-Block, per Gate gehalten.
- **test_store_metadata.py:** RESIDENT_FIGURE-, Grenzlisten-, Sprachzeilen- und Doku-Vergleichs-Gates mit 5 Mutationsfaellen; kaputtes XML ist ein Befund und keine Ausnahme.

---

_Reviewed: 2026-09-27T08:00:16Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
