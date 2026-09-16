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

---

## Die fertigen Ersatztexte für deploy-harp.yml

Beide Texte sind wortwörtlich einsetzbar. Plan 12-02 kopiert den Text des
greifenden Zweiges und ersetzt darin nur die spitz geklammerten Platzhalter
durch die am Stichtag gelesenen Tatsachen. Die Sprache der YAML-Kommentare
bleibt Englisch, wie der bestehende Block. Die Einrückung ist die des
Ist-Zustands: zehn Leerzeichen vor dem Kommentarzeichen oberhalb des
Matrixeintrags, zwölf Leerzeichen innerhalb des Eintrags.

In BEIDEN Zweigen bleibt der Matrixeintrag `- server-version: stable35` stehen,
und `php-version: '8.3'` sowie `runner: ubuntu-24.04` bleiben unverändert.

### Ersatztext Option a

Ersetzt den gesamten Bereich von Zeile 211 bis Zeile 273 der heutigen
`.github/workflows/deploy-harp.yml`, also den einleitenden Zweig-Hinweis, den
ganzen RE-CHECK-Absatz und den Matrixeintrag. Der lange Absatz entfällt und
wird durch einen kurzen Vermerk ersetzt, der Datum, Plan, Aktenzeichen dieser
Notiz, die gelesene Belegzeile und die Laufnummer des grünen Beweislaufs nennt.

```yaml
          # stable35 was the branch under development when this matrix was
          # written, and it is not any more: <FINAL-TAG> of <FINAL-DATUM> is the
          # first 35 tag that "gh api repos/nextcloud/server/releases" reports
          # without the prerelease marker. The RE-CHECK paragraph that used to
          # stand here named 2026-09-16 as the day it comes out, and this is that
          # removal and not a paraphrase of it.
          #
          # Done on 2026-09-16 by plan 12-02 on the evidence D-02 asks for
          # (.planning/phases/12-messwerkzeug-runbook-und-terminentscheid/
          # 12-STABLE35-ENTSCHEID.md, option a): the release status alone was not
          # enough, so this leg ran green against stable35 on the tree of that day
          # in run <RUN-ID> before the flag came out. From here the leg is
          # must-be-green, and a red run is a finding rather than a reason to put
          # the flag back. The entry itself stays regardless, because
          # backend/tests/test_lockstep_versions.py checks that the matrix covers
          # every version of the declared window 33 to 35.
          - server-version: stable35
            php-version: '8.3'
            tolerate-failure: false
            runner: ubuntu-24.04
```

### Ersatztext Option b

Das Flag bleibt. Der bestehende RE-CHECK-Absatz wird nach dem vorhandenen
Fortschreibemuster ergänzt, und die Terminzeile wird umgeschrieben statt
gelöscht, damit der Absatz seine Wirkung behält. Zwei Eingriffe:

**Eingriff 1**, ersetzt den heutigen RE-CHECK-Block (Zeilen 243 bis 247):

```yaml
            # RE-CHECK DATE: <NEUER-RE-CHECK>. On that day this flag and this
            # whole paragraph come out, the leg becomes must-be-green, and a red
            # run is a finding rather than a reason to put the flag back. The plan
            # that holds the follow-through is the store submission of phase 16,
            # because it is the next step that cannot ship without a statement
            # about the window it declares.
```

**Eingriff 2**, wird unmittelbar vor der Zeile `tolerate-failure: true`
eingefügt, also als jüngster Eintrag am Ende der Vermerkskette:

```yaml
            #
            # Decided on 2026-09-16 by plan 12-02, option b of
            # .planning/phases/12-messwerkzeug-runbook-und-terminentscheid/
            # 12-STABLE35-ENTSCHEID.md: Nextcloud 35 is still not final on the day
            # the RE-CHECK falls due, so the date moves and the decision is
            # written down rather than skipped. The reading behind it, from
            # "gh api repos/nextcloud/server/releases" on 2026-09-16: the newest
            # 35 tag is <NEUESTE-35-MARKE>, marked prerelease, and the newest
            # release that is not a prerelease is <NEUESTE-FREIGABE>. The declared
            # window stays at min-version 33 and max-version 35, both info.xml
            # stay as they are, this entry stays, and
            # backend/tests/test_lockstep_versions.py stays unchanged. The new
            # RE-CHECK DATE above is <NEUER-RE-CHECK>, the day before the store
            # submission of phase 16 begins, and that submission is the new
            # address of the follow-through.
            tolerate-failure: true
            runner: ubuntu-24.04
```

---

## Vollzug am 16.09.2026

Gefüllt von Plan 12-02 am Stichtag.

- **Datum des Vollzugs:** 2026-09-16
- **Gelesener Releasestand,** `gh api repos/nextcloud/server/releases --jq '.[] | "\(.tag_name) prerelease=\(.prerelease) \(.published_at)"' | head -12`, abgesetzt am 2026-09-16:

  | Marke | Prerelease | Veröffentlicht |
  |---|---|---|
  | v35.0.0 | **nein** | 2026-09-15T21:40:41Z |
  | v35.0.0rc4 | ja | 2026-09-10T12:53:25Z |
  | v34.0.4 | nein | 2026-09-10T13:16:15Z |
  | v33.0.9 | nein | 2026-09-10T13:29:56Z |
  | v32.0.15 | nein | 2026-09-10T13:54:33Z |
  | v35.0.0rc3 | ja | 2026-09-03T12:29:49Z |

  Nachgeprüft am selben Tag auf der Einzelmarke: `gh api
  repos/nextcloud/server/releases --jq '.[] | select(.tag_name=="v35.0.0")'`
  antwortet mit `prerelease=false` UND `draft=false`. Die Freigabe ist also
  weder eine Vorabversion noch ein unveröffentlichter Entwurf.

  Ebenfalls am 2026-09-16 nachgelesen, damit der CI-Ast nicht auf `master`
  zurückfällt: `gh api repos/nextcloud/server/branches/stable35` antwortet mit
  `5390633955c90e089680234e280c37a3f74d4a58`, `gh api
  repos/nextcloud/app_api/branches/stable35` mit
  `bc55cb4b1f93893dd8146d5c9663e658fd46e8c0`. Beide Zweige stehen.

- **Greifender Zweig (a oder b):** a. Eingetragen als greifender Zweig a nach
  der Regel aus D-01: die erste 35er-Marke ohne Prerelease-Kennzeichen ist da
  (v35.0.0 vom 15.09.2026), also ist NC 35 am Stichtag final und der Zweig für
  den nicht finalen Fall entfällt.
- **Beleg:** Die Entscheidung ruht auf der gelesenen API-Antwort und nicht auf
  dem Kalender: der Zeitplan nannte den 16.09.2026 mit dem Zusatz "date not
  final", die Freigabe kam tatsächlich am Abend des 15.09.2026 (UTC). Nach D-02
  trägt der Release-Status den Vollzug allein NICHT; dazu gehört der grüne
  `deploy-harp`-Lauf gegen `stable35` auf dem Stand des Baumes von heute, dessen
  Laufnummer unten einzutragen ist.
- **Laufnummer des Beweislaufs (nur Option a):** (offen, Task 2 nach
  Owner-Freigabe)
- **Vollzogen am / durch Plan:** (offen, Task 2 nach Owner-Freigabe)

### Vollzugs-Checkliste

1. Datum prüfen: es ist der 16.09.2026 oder später, und der Entscheid ist noch
   nicht vollzogen.
2. Releasestand lesen mit `gh api repos/nextcloud/server/releases` und die
   Antwort oben eintragen.
3. Zweig bestimmen: 35er-Marke ohne Prerelease-Kennzeichen vorhanden gleich
   Option a, sonst Option b.
4. Bei Option a den Beweislauf von `deploy-harp.yml` starten, abwarten und die
   Laufnummer notieren; ein roter Lauf ist ein Befund und wird gelesen, bevor
   irgendetwas geändert wird.
5. Ersatztext einsetzen: den Block des greifenden Zweiges nach
   `.github/workflows/deploy-harp.yml` kopieren und die Platzhalter durch die
   gelesenen Tatsachen ersetzen.
6. Notiz füllen: die Felder dieses Abschnitts vollständig ausfüllen, damit der
   Entscheid nicht nur im YAML-Kommentar lebt.
7. Owner-Bestätigung einholen: den vollzogenen Entscheid mit Zweig, Beleg und
   Laufnummer vorlegen.
