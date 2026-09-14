# Phase 12: stable35-Fenster-Entscheid (HART-03)

**Angelegt:** 2026-09-14 (Plan 12-01, Task 1)
**Zweck:** Die Frist dieses Entscheids ist der 16.09.2026, zwei Tage nach
Phasenbeginn. Beide Zweige werden deshalb VORHER vollständig ausformuliert,
inklusive der fertigen Ersatztexte für den YAML-Kommentar. Am Stichtag wird nur
noch gelesen, welcher Zweig greift, und der zugehörige Text eingesetzt; es wird
an diesem Tag kein Satz mehr entworfen. Folgepläne zitieren die Optionskennung
(a oder b) und keine Zusammenfassung.

---

## Die Frage

Fällt am 16.09.2026 das `tolerate-failure: true` am stable35-Ast von
`.github/workflows/deploy-harp.yml`, oder wird der RE-CHECK mit Begründung und
neuem Termin verlängert?

### Was festgestellt ist

**Das deklarierte Versionsfenster steht bereits auf 35.** Am eigenen Baum
gelesen am 14.09.2026:

```
php/appinfo/info.xml:219      <nextcloud min-version="33" max-version="35"/>
backend/appinfo/info.xml:225  <nextcloud min-version="33" max-version="35"/>
```

Die Formulierung "auf max NC 35 heben" aus D-01 lässt in den beiden `info.xml`
also NICHTS zu tun. Sie stammt aus `11-CONTEXT.md` D-11 und ist durch den
späteren Vorentscheid V-2 vom 10.09.2026 in der anderen Lesart bestätigt worden.
Kein Folgeplan darf daraus eine Aufgabe machen: sie ist erledigt.

**Offen ist ausschliesslich `.github/workflows/deploy-harp.yml`.** Genau zwei
Dinge, beide im selben Matrixblock:

| Ort | Ist-Zustand am 14.09.2026 | Zielzustand bei NC 35 final |
|---|---|---|
| Matrixeintrag `server-version: stable35` (Zeilen 217 bis 273) | `tolerate-failure: true`, `php-version: '8.3'`, `runner: ubuntu-24.04` | `tolerate-failure: false`, der Ast wird muss-grün |
| Der RE-CHECK-Kommentarblock darüber (Zeilen 211 bis 271) | trägt `# RE-CHECK DATE: 2026-09-16.` und drei aufeinander aufbauende Entscheidungsvermerke | kommt nach seinem eigenen Wortlaut heraus |

Der Kommentar beschreibt seinen eigenen Abgang wörtlich:

> On that day this flag and this whole paragraph come out, the leg becomes
> must-be-green, and a red run is a finding rather than a reason to put the flag
> back.

Der jüngste Fortschreibe-Eintrag nennt als Nachfolge-Adresse Plan 11-11, die
Store-Einreichung der Phase 11. Diese Phase ist abgeschlossen; die Adresse
wandert damit auf Phase 12.

**Releasestand am 14.09.2026**, Quelle `gh api repos/nextcloud/server/releases`:

| Marke | Prerelease | Veröffentlicht |
|---|---|---|
| v35.0.0rc4 | ja | 2026-09-10T12:53:25Z |
| v34.0.4 | nein | 2026-09-10T13:16:15Z |
| v33.0.9 | nein | 2026-09-10T13:29:56Z |

NC 35 ist am 14.09.2026 also NICHT final. Neueste 35er-Marke ist rc4 als
Vorabversion, neueste echte Freigabe ist v34.0.4.

**Beide `stable35`-Zweige existieren.** `gh api
repos/nextcloud/server/branches/stable35` und
`gh api repos/nextcloud/app_api/branches/stable35` antworten am 14.09.2026
jeweils mit dem Zweig. Der CI-Ast fällt also nicht auf `master` zurück, und ein
roter Lauf wäre nicht mit einem falschen Auschecken zu erklären.

**Der offizielle Zeitplan** (Maintenance-and-Release-Schedule im Wiki von
`nextcloud/server`) nennt als Final-Datum für NC 35 den 2026-09-16, und zwar mit
dem wörtlichen Zusatz "date not final, but will be pre-conf".

### Was unklar ist

Ob NC 35 am 16.09.2026 tatsächlich final ist. Der Zeitplan nennt das Datum
selbst als nicht endgültig. Beobachtet ist die Kadenz der Vorabversionen: rc3 am
03.09.2026, rc4 am 10.09.2026, jeweils an einem Mittwoch. Die daraus abgeleitete
Vermutung, es könne am 17.09.2026 ein rc5 folgen, ist eine Extrapolation dieser
Kadenz ohne Quelle; der Zeitplan nennt kein rc5. Die Vermutung trägt keinen
Entscheid, sie begründet nur, warum Option b hier gleichwertig ausformuliert ist
und nicht als Randfall.

### Die Leitplanke, die für beide Optionen gilt

**Erstens: der stable35-Matrixeintrag darf NICHT entfernt werden, nur sein Flag
darf fallen.** `backend/tests/test_lockstep_versions.py:387` prüft, dass die
CI-Matrix jede Version des deklarierten Fensters abdeckt
(`_window_findings(("33","35"), ("33","35"), ["33","34","35"]) == []`). Wer den
Eintrag beim Aufräumen des Kommentars mitnimmt, macht diesen Test rot, und zwar
mit einer Meldung über das Fenster und nicht über den Kommentar.

**Zweitens: ein roter Lauf am Stichtag ist ein Befund und kein Grund, das Flag
zurückzusetzen.** Das steht so im Kommentar, der damit ersetzt wird ("a red run
is a finding rather than a reason to put the flag back"), und die Ersetzung darf
diese Regel nicht verlieren.

**Drittens: die Warnung vor den Uninstall-Gate-Schwellen derselben Strecke steht
daneben.** Befund A aus Plan 11-11 hält fest, dass die Fremdinstallations- und
Upgrade-Strecke von `deploy-harp.yml` an diesen Schwellen scheitern kann, ohne
dass das etwas über NC 35 aussagt. Ein roter Lauf ist deshalb erst zu lesen und
dann zu bewerten.

### Option a: NC 35 ist final (D-01 und D-02)

Greift, wenn `gh api repos/nextcloud/server/releases` am 16.09.2026 eine
35er-Marke ohne Prerelease-Kennzeichen zeigt.

**Beweisgrundlage, wörtlich aus D-02:** NC-35-final-Check PLUS die bestehende
`deploy-harp`-Fremdinstallations- und Upgrade-Strecke grün gegen stable35. Der
Release-Status allein reicht NICHT. Es braucht einen Lauf von
`.github/workflows/deploy-harp.yml` auf dem aktuellen Stand des Baumes, dessen
Laufnummer im Vermerk steht. Bekannt ist, dass dieser Ast am 07.09.2026 im Lauf
34114937751 allein grün war; das ist ein Hinweis auf geringes Risiko und kein
Ersatz für den neuen Lauf.

**Vollzug:** Der RE-CHECK-Absatz entfällt und wird durch den Vermerk aus
Abschnitt "Ersatztext Option a" ersetzt, `tolerate-failure: true` wird zu
`tolerate-failure: false`, der Matrixeintrag selbst bleibt stehen.

**Was das für das Fenster in v1.2.0 heisst:** nichts mehr. Max NC 35 gilt in
beiden `info.xml` bereits. Ein separates 1.1.x nur für das Fenster entfällt
damit ersatzlos; die Zusage max NC 35 bekommt in v1.2.0 lediglich den Beweis,
den sie bisher nicht hatte.

### Option b: NC 35 ist nicht final (D-03)

Greift, wenn am 16.09.2026 die neueste 35er-Marke weiterhin eine Vorabversion
ist.

**Vollzug:** Der Entscheid wird dokumentiert, statt ihn stillschweigend
verstreichen zu lassen. Das Fenster bleibt unverändert bei min 33 und max 35,
`tolerate-failure: true` bleibt stehen, der RE-CHECK-Absatz wird nach dem
vorhandenen Fortschreibemuster um einen Eintrag ergänzt (Abschnitt "Ersatztext
Option b"), und die Zeile `# RE-CHECK DATE:` wird auf einen neuen Termin
umgeschrieben statt gelöscht.

**Neuer Termin und neue Adresse:** spätestens der Tag vor Beginn der
Store-Einreichung der Phase 16; diese Einreichung ist zugleich die neue
Nachfolge-Adresse. Damit hängt der Entscheid an einem Arbeitsschritt, der
ohnehin stattfindet, und nicht an einem Kalendereintrag, den niemand liest.

**Phase 12 gilt mit diesem dokumentierten Entscheid als erfüllt.** HART-03
verlangt einen vollzogenen und belegten Entscheid, nicht ein bestimmtes
Ergebnis.
