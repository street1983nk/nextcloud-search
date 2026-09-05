# Das dreisprachige Testset der semantischen Suche

204 Paare aus einer Umschreibung und dem Abschnitt, den sie meint: 42 auf
Deutsch, 42 auf Englisch, 120 auf Französisch. Sie beantworten zwei Fragen, die
sich sonst nur behaupten lassen: was die selbst gebaute int8-Quantisierung des
Modells an Qualität kostet (D-02), und ob die E5-Präfixe `query: ` und
`passage: ` wirklich sitzen (D-05). Gemessen wird damit von
`scripts/dev/model_quality.py`, der Bericht liegt unter
`docs/measurements/2026-09-05-modellqualitaet/`.

Mehrsprachigkeit ist Anforderung und nicht Zugabe (D-03). Für Französisch gibt
es in der externen Messung von Elastic, an der sich diese Phase sonst
orientiert, überhaupt keine Zahl; diese Dateien sind der einzige Ort, an dem
diese Frage für das Produkt beantwortet wird.

## Die Regel, die jeden einzelnen Fall bestimmt

**Kein inhaltstragendes Wort der Anfrage darf wörtlich im zugehörigen
Abschnitt stehen.** Funktionswörter sind ausgenommen: Artikel, Pronomen,
Präpositionen, Konjunktionen, Hilfs- und Modalverben sowie Fragewörter. Die
Liste dieser Wörter steht je Sprache in `backend/tests/test_model_quality.py`.

Der Grund ist der teuerste Fehler beim Bau eines solchen Testsets. Stehen die
Wörter der Frage auch im Zieltext, dann findet **jedes** Verfahren den
Abschnitt, die Volltextsuche zuerst, und die Zahl am Ende misst die
Volltextsuche und wird als Beleg für ein Einbettungsmodell ausgegeben. Ein
solcher Fall ist nicht schwach, er ist wertlos: er kann die Frage, für die er
gebaut wurde, gar nicht beantworten.

Deshalb ist die Wortüberschneidungsregel hier kein guter Vorsatz, sondern eine
maschinelle Prüfung. `test_no_content_word_of_a_query_stands_in_its_own_passage`
zerlegt Anfrage und Abschnitt in kleingeschriebene Wörter, zieht die
Funktionswörter der jeweiligen Sprache ab und verlangt eine leere Schnittmenge.
Ein Verstoß meldet die Kennung des Falls und die verletzenden Wörter, niemals
den Text selbst. Dass die Prüfung überhaupt rot werden kann, ist eigens belegt:
`test_the_overlap_check_goes_red_on_a_case_that_would_measure_full_text_search`
führt ihr einen absichtlich lexikalischen Fall vor.

Beim Französischen kommt eine Feinheit dazu, die sonst ein Schlupfloch wäre:
der Apostroph trennt. `l'autorisation` zerfällt in `l` und `autorisation`, sonst
könnte sich ein Substantiv hinter seinem elidierten Artikel verstecken. Auch
dafür gibt es einen eigenen Test.

## Das Format

Eine Zeile JSON je Fall, vier Felder, alle vier Zeichenketten und keines leer:

| Feld | Inhalt |
|---|---|
| `id` | stabile Kennung, beginnt mit dem Sprachkürzel, je Sprache eindeutig |
| `query` | die Umschreibung, in der Zielsprache |
| `passage` | der gemeinte Abschnitt, in derselben Sprache |
| `note` | ein Satz dazu, warum dieser Fall semantisch und nicht lexikalisch ist |

Der Bestand aller `passage`-Felder einer Sprache ist zugleich die
**Ablenkermenge**: jede Anfrage konkurriert gegen alle übrigen Abschnitte
derselben Datei, also gegen 41 auf Deutsch und Englisch und gegen 119 auf
Französisch. Eine zweite Liste gibt es deshalb nicht, und sie kann folglich
auch nicht von der ersten abdriften. Damit ein Rang überhaupt entscheidbar
bleibt, prüft ein Test, dass keine zwei Abschnitte einer Sprache gleich sind.

**Eine Folge davon, die beim Lesen der Messwerte zählt:** die Ablenkermenge ist
Teil der Aufgabe. Ein MRR-Wert über 120 französische Fälle ist mit einem über 42
deutsche nicht vergleichbar, weil der französische Wert gegen dreimal so viele
Mitbewerber erkämpft ist. Vergleichbar sind ausschließlich zwei Läufe über
dieselbe Datei.

## Fallzahl je Sprache

| Datei | Fälle | Sprache der Prosa |
|---|---|---|
| `de.jsonl` | 42 | Deutsch, mit echten Umlauten und ß |
| `en.jsonl` | 42 | Englisch |
| `fr.jsonl` | 120 | Französisch, mit echten Akzenten und Cedille |

Dass diese Zahlen mit den Dateien übereinstimmen, hält ein Test fest
(`test_the_readme_states_the_true_number_of_cases`); eine Zahl in Prosa driftet
sonst von dem weg, was sie zählt. Die Untergrenze je Sprache steht als
`MINIMUM_CASES` in `backend/tests/test_model_quality.py`.

### Warum Französisch dreimal so viele Fälle trägt

Nicht aus Sorgfaltsgründen, sondern wegen einer Zahl. Die erste Messung vom
05.09.2026 fand auf 42 französischen Fällen einen MRR-Rückgang der selbst
quantisierten int8-Fassung von 9,24 Prozent gegenüber fp32, also jenseits der
5-Prozent-Grenze, die Plan 06-03 als Abbruchregel gesetzt hatte. Derselbe
Befund lag mit t = -2,03 aber gerade eben an der Grenze dessen, was 42 Fälle
überhaupt von Null unterscheiden können: er ließ sich weder bestätigen noch
verwerfen. Der Owner hat am 05.09.2026 entschieden, zuerst das Testset zu
verbreitern statt die Quantisierung auf eine so dünne Zahl hin umzubauen. 120
Fälle halbieren den Standardfehler etwa. Die Fälle `fr-01` bis `fr-42` sind
dabei unverändert geblieben; `fr-43` bis `fr-120` sind hinzugekommen und
gehorchen derselben Regel, maschinell geprüft im selben Testlauf.

## Herkunft und Lizenz

| Quelle | Was daraus stammt | Lizenz |
|---|---|---|
| `scripts/dev/build_corpus.py` (dieses Repositorium) | 20 der 42 deutschen Abschnitte, nämlich `de-02` bis `de-19`, `de-41` und `de-42`: die Pachtvereinbarung, die Ratsvorlage, der Bescheid, die Kündigung, der Schweizer und der österreichische Fall sowie die sechs kurzen Belege aus dem Bildpfad. Die längeren sind wörtlich übernommen, die kurzen Belege sind aus ihren Einzelzeilen zu einem Satz zusammengezogen, ohne ein Wort zu ändern | AGPL-3.0-or-later, wie das übrige Repositorium |
| selbst verfasst für diesen Zweck | die übrigen 22 deutschen Abschnitte (`de-01` und `de-20` bis `de-40`), alle englischen und alle französischen Abschnitte, sämtliche Anfragen und sämtliche Anmerkungen | AGPL-3.0-or-later |
| selbst verfasst am 05.09.2026 für die Nachmessung | die 78 französischen Fälle `fr-43` bis `fr-120`, in denselben Gattungen wie die ersten 42 und über dreißig weitere Sachgebiete verteilt: Vereinsförderung, Wahlen, Schule und Kinderbetreuung, Personenstand, Friedhof, Bauordnung, Verkehr und Parken, Wasser und Abwasser, Abfall, Abgaben, Vergabe, Ratsarbeit, Haushalt, Sozialhilfe, Archiv, Gefahrenabwehr, Nahverkehr, Energie, Gesundheit, Verwaltungsdigitalisierung, Nachbarschaft und Landwirtschaft | AGPL-3.0-or-later |

**Nichts davon ist übersetzt.** Die englischen und die französischen Fälle sind
in ihrer Sprache verfasst worden, in denselben Gattungen wie die deutschen:
Behördenpost, Rechnungen und Zahlungserinnerungen, Sitzungsprotokolle und
Ratsvorlagen. Eine übersetzte Anfrage gegen einen übersetzten Abschnitt würde
die Übersetzung mitmessen, und zwar unsichtbar: ein Rückgang stünde dann
zwischen Modell und Übersetzer und wäre keinem von beiden zuzurechnen.

Die deutschen Abschnitte aus `build_corpus.py` sind dort ebenfalls erfunden;
das steht als Regel im Kopf jener Datei und ist die Antwort desselben
Repositoriums auf dieselbe Frage. Kein Text in diesem Verzeichnis stammt aus
einem heruntergeladenen Bestand, denn ein unbekanntes Muster trägt eine
unbekannte Lizenz.

## Keine personenbezogenen Daten

In diesen Dateien stehen **keine echten personenbezogenen Daten**. Sämtliche
Namen, Anschriften, Aktenzeichen, Beträge, Durchwahlen und Ortsangaben sind
erfunden; die wiederkehrenden Namen Musterhausen, Sommer und Berg stammen aus
dem Referenzkorpus dieses Repositoriums und bezeichnen niemanden. Dieses
Verzeichnis wird mit dem Repositorium veröffentlicht, und was hier steht, steht
öffentlich (T-06-10).

## Wie geprüft wird

```bash
cd backend && uv run python -m pytest tests/test_model_quality.py -q
```

Derselbe Testlauf prüft die Wohlgeformtheit jeder Zeile, die Eindeutigkeit der
Kennungen, die Fallzahl, die Wortüberschneidungsregel, die echten Umlaute,
Akzente und die Cedille sowie die Abwesenheit von Geviert- und Halbgeviertstrich
in diesen fünf Dateien.
