# Chinese wordings (Traditional, Taiwan), complete

This file is the source of the two Traditional Chinese catalogue files `php/l10n/zh_TW.json` and
`php/l10n/zh_TW.js`. It carries the Chinese wording of **every** key of the administration page
and the result page in one table, so that a reader can check them in one pass and not as a diff
over two files. Both files and the table come from one source in one pass, and
`test_every_language_table_carries_every_key_with_the_catalogue_wording` holds them equal cell by
cell.

**Scope: `zh_TW` only.** Traditional Chinese as written in Taiwan. Simplified Chinese (`zh_CN`)
and Hong Kong Chinese (`zh_HK`) are not shipped; the section "The language code" says why.

**This document is written in English, unlike its five siblings.** The person who vouches for
the Chinese wording reads English well and German not well enough to stand behind German prose.
Section order, table header and column names follow `docs/l10n-dutch.md`; the column names are
contract identifiers (`LANGUAGE_TABLES` in `backend/tests/test_admin_ui_contract.py` reads the
table under `| Schluessel |`). Whether the prose should be German is a question to the
maintainer and asked in the pull request.

What holds for **all** catalogues is not repeated here but stated once in
`docs/l10n-catalogues.md`: how Nextcloud finds a catalogue (section 1), the plural rules with
their origin (section 3, which now carries the `zh_TW` line), and the measurement of which form
PHP and the browser pick (section 4, with the dated addendum for `zh_TW` at the end of section 5).

## The key set, counted from the file

Counted on 15.11.2026 with `json.load` over `php/l10n/de.json` and `php/l10n/zh_TW.json`:

| Quantity | Value |
|---|---:|
| Keys in `de.json` | **366** |
| Keys in `zh_TW.json`, in the same order | **366** |
| of them with printf directives (`%s`, `%1$s`, `%n`) | **96** |
| with directives, plural keys excluded | **91** |
| plural keys (the value is a list) | **5** |
| forms per plural key | **1** |
| rows in the table below | **366** |

The forms per plural key are the line that sets this language apart: every other catalogue of
the tree carries two or three. The table carries `Findling` as a row of its own, as the Spanish
and the Dutch tables do, although `LANGUAGE_TABLE_EXCEPTIONS` would let it be left out.

## The language code

Asked of a running Nextcloud 34.0.5 on 15.11.2026 (container `nextcloud:34.0.5-apache`, `php/`
mounted as `custom_apps/findling`), with the same probe as section 1 of
`docs/l10n-catalogues.md`:

| requested language | `languageExists('findling', code)` | `getLanguageCode()` | `t('Search your file contents')` |
|---|---|---|---|
| `zh_TW` | yes | `zh_TW` | 搜尋您的檔案內容 |
| `zh_HK` | no | `en` | Search your file contents |
| `zh_CN` | no | `en` | Search your file contents |
| `zh` | no | `en` | Search your file contents |

`core/l10n/` of 34.0.5 and of 35.0.2 ships `zh_CN`, `zh_HK` and `zh_TW` and no plain `zh`, so a
`zh.json` would be a file nobody can stand on, for the reason section 1 of
`docs/l10n-catalogues.md` measured for `pt`.

**`zh_HK` is not shipped.** Hong Kong writes Traditional characters as well, but its vocabulary
differs in exactly the words this page is made of, starting with file and document. Putting the
Taiwanese words under the Hong Kong code would be the copy that the paragraph above
`L10N_PT_PT_JSON` refuses for Portuguese. A Hong Kong user sees Findling in English.

**`zh_CN` is not shipped.** Simplified Chinese is another script with another vocabulary, not a
spelling variant. A converted catalogue would be a second translation that no reader has checked.

## Word choice

So that the review is one decision per term and not 366 single cases. The line follows the
Traditional Chinese catalogues Nextcloud itself ships (`core/l10n/zh_TW.json` and the bundled
apps of 34.0.5), so that Findling reads like the pages around it.

| English | zh_TW | Why |
|---|---|---|
| file | 檔案 | Taiwanese usage and the word of the Nextcloud Files app. 文件 is reserved for document, as in 文件 for the file type chip Documents |
| document | 文件 | The counterpart of the line above. A counted document takes the counter word 份 (`%2$s 份文件中`), the noun alone is 文件 (`相似文件`) |
| folder | 資料夾 | Nextcloud's word; 文件夾 is the mainland term |
| search | 搜尋 | Nextcloud's word; 搜索 is the mainland term |
| index (noun), indexing | 索引, 建立索引 | 索引 is the ordinary noun; the activity is 建立索引, and the short form 索引 stands where a button needs it (暫停索引, 繼續索引) |
| the backend | 後端 | Nextcloud's own word for the same thing in its server and AppAPI catalogues. Where the proper name of the app is meant it stays: 外部應用程式「Findling Backend」 |
| External App | 外部應用程式 | The word of the AppAPI catalogue |
| instance | 站台 | The word Nextcloud's own catalogues use for this instance |
| run, pass (Lauf, Abgleichlauf) | 輪, 下一輪, 比對作業 | 輪 counts a pass over the files and carries the same picture as passage and doorloop. The nightly comparison is 每晚的比對作業 |
| background job | 背景作業 | Nextcloud's word (server info and calendar) |
| worker | 處理程序 | The Taiwanese term for a process; it says to an administrator what a worker is without the English word |
| OCR slot | OCR 工作槽 | A slot is a place one recognition runs in. 工作槽 keeps that picture and stays distinct from 處理程序 |
| coverage | 涵蓋率 | The share of files that are searchable |
| searchable, findable by meaning | 可以搜尋, 可依語意找到 | Two halves of one statement, built the same way |
| semantic search, full text search | 語意搜尋, 全文搜尋 | The established terms. Full text hits are 全文比對結果 |
| embedding, re-embedding | 嵌入, 重新嵌入 | The usual rendering of embedding in the vector sense. It is a technical word, and the section "Review" names it as one to check |
| profile | 設定檔 | A named set of settings. Nextcloud's 個人檔案 is the user profile and would be the wrong word here |
| Economy, Standard, Performance | 節約, 標準, 效能 | Names of the three profiles. Inside a sentence they stand in 「」; as the options of the select and after a colon they stand bare |
| pattern, wildcard | 樣式, 萬用字元 | 萬用字元 is the common Taiwanese word for a wildcard character; 樣式 is the pattern built from them |
| lookup | 查詢 | The single file lookup of the admin page |
| external storage, storage | 外部儲存空間, 儲存空間 | The words of the Files and External storage apps |
| Team Folders | 團隊資料夾 | Unlike the French and the Dutch interface, Nextcloud's Traditional Chinese catalogues translate the name (`Team folders`, 團隊資料夾), so this catalogue does too |
| trash bin | 垃圾桶 | The ordinary word |
| log | 紀錄檔 | The spelling of Nextcloud's own catalogues: 44 times against 2 times 記錄檔 over `core`, `lib` and the bundled apps of 34.0.5 |
| checksum | 檢查碼 | The word of the Files app |
| volume | 磁碟區 | The Docker volume the model file lies on |
| remedy `None.` | 無。 | One character, as short as the source |

**Address.** Chinese marks politeness with 您, and the catalogue uses it wherever the German says
Sie (`搜尋您的檔案內容`). Instructions start with 請 where the German uses the impersonal
infinitive (`請調高「可讀取的最大檔案」的數值。`). Buttons and short labels are bare verb and object
without 請 (`儲存規則`, `新增樣式`, `再試一次`), the convention of the Nextcloud interface.

## Typography

Every rule below is machine checked; the results stand in the section "Machine checks".

- **Full width punctuation in Chinese prose**: `，。：；？（）「」、`. Counted in each of the two
  files, which carry the same values: 133 full width commas, 290 full stops, 38 colons, 33 pairs of corner brackets, 24 pairs of
  full width parentheses, 14 enumeration commas, and 0 half width commas, full stops or colons
  directly after a Han character.
- **A half width space between Han characters and Latin letters, digits or placeholders**, and
  none next to full width punctuation: `%2$s 個可索引的檔案中，有 %1$s 個可以搜尋`. That is the
  spacing of Nextcloud's own Traditional Chinese catalogues (`正在顯示來自 {name} 的 %n 個結果`).
  Counted per value: 0 places where a Han character touches a Latin letter, a digit or `%`.
- **Corner brackets 「」 are the only quotation marks.** They quote field names of the page,
  profile names inside a sentence, commands and the search term: `「%s」的搜尋結果`,
  `請執行「occ findling:index --restart」`. No ASCII double quote and no curly quote stands in a
  value (0 of each).
- **Full width parentheses**, also around Latin content: `%1$s（ID %2$s）`,
  `Office 鎖定檔（~$）`. This is why `%1$s (ID %2$s)` is no exception of gate G2 here although
  every other language lists it.
- **No dash.** Chinese typography uses the double em dash 「——」 for an aside; this repository
  forbids U+2014 and U+2013, so the catalogue uses a comma or a colon instead. 0 of each.
- **No bare percent sign.** "a hundred per cent" is 百分之百, and no value needs `%%`.
- **No pipe character, no protected space** (U+00A0, U+202F) **and no ideographic space**
  (U+3000). 0 of each.
- **The placeholders are those of the key**, in kind and number. Chinese word order moves some of
  them, and then the numbered form keeps its number: `%1$s in %2$s` becomes `%2$s 中的 %1$s`.
  Seven values reorder their placeholders, all of them numbered. PHP was asked with real
  arguments and returned `34 個可索引的檔案中，有 12 個可以搜尋` and `/Docs 中的 a.pdf，修改於 2026-11-15`.
- **Unit symbols stay English**: `B`, `KB`, `MB`, `GB`, `TB`, `PB`, with a space after the number
  (`%s MB`), as Nextcloud writes them.

## Plural forms

The rule is

```
nplurals=1; plural=0;
```

read on 15.11.2026 out of `core/l10n/zh_TW.json` of Nextcloud 34.0.5 and 35.0.2, the same string
in both, and written as `"pluralForm"` into `php/l10n/zh_TW.json` and as the fourth argument of
`OC.L10N.register` into `php/l10n/zh_TW.js`. The block in section 3 of `docs/l10n-catalogues.md`
and `PLURAL_FORM_OF` carry the same line.

**One form per plural key.** Chinese marks number with a counter word and not with an ending:
`%n 天` is the whole plural of `%n day`. `FORM_COUNT_OF["zh_TW"]` is 1, written down and not
parsed out of `nplurals=`, like every other entry of that table.

Both sides of the page pick that one form, measured on 15.11.2026 on the Nextcloud 34.0.5
container above. PHP through `IFactory::get('findling', 'zh_TW')->n(...)`, the browser through
the global `n('findling', ...)` on the result page of a user whose language is `zh_TW`:

| count | PHP `%n day` | browser `%n day` | PHP `and %n more` | browser `and %n more` |
|---:|---|---|---|---|
| 0 | 0 天 | 0 天 | 以及另外 0 個 | 以及另外 0 個 |
| 1 | 1 天 | 1 天 | 以及另外 1 個 | 以及另外 1 個 |
| 2 | 2 天 | 2 天 | 以及另外 2 個 | 以及另外 2 個 |
| 5 | 5 天 | 5 天 | | |
| 1000000 | 1000000 天 | 1000000 天 | | |

So the split that section 4 and section 5 of `docs/l10n-catalogues.md` describe for the three
form languages, PHP on index 1 and the browser on index 2, or the two sides apart at n equal to
0, cannot occur in this language: there is only index 0.

In the table below a plural key has one form in the Chinese column and two in the German column,
separated by ` / ` as in every other table of the tree.

## The table

The three columns are generated from `php/l10n/de.json` and `php/l10n/zh_TW.json` and not typed;
the order is the order of the files. The key is the English source string the code asks for: most
keys stand in a template or a script and run through `$l->t()` or `t()`, some come from the PHP
services, and the five plural keys are composed by `n()` out of their singular and plural. In
every catalogue file it is the key of the translation.

No value and no key can contain a pipe character, `scan_pipe_character` makes sure of that, so
this table cannot break on a wording.

| Schluessel | DE | ZH_TW |
|---|---|---|
| `Findling` | Findling | Findling |
| `File contents` | Dateiinhalte | 檔案內容 |
| `File contents: %s` | Dateiinhalte: %s | 檔案內容：%s |
| `File contents in a folder` | Dateiinhalte in einem Ordner | 資料夾中的檔案內容 |
| `File contents in %s` | Dateiinhalte in %s | %s 中的檔案內容 |
| `Choose the folder to search in` | Ordner für die Suche wählen | 選擇要搜尋的資料夾 |
| `Search coverage` | Deckungsgrad der Suche | 搜尋涵蓋率 |
| `%1$s of %2$s indexable files are searchable` | %1$s von %2$s indexierbaren Dateien sind durchsuchbar | %2$s 個可索引的檔案中，有 %1$s 個可以搜尋 |
| `Since version 1.6.3, every document counts only once. Until now, external storage mounted separately for each user was counted once per mount, which is why the figures can now be lower than before. This note disappears seven days after the first complete count.` | Seit Version 1.6.3 zählt jedes Dokument nur einmal. Bisher wurde ein externer Speicher, der für jeden Nutzer einzeln eingebunden ist, je Einbindung gezählt, deshalb können die Zahlen jetzt niedriger sein als vorher. Dieser Hinweis verschwindet sieben Tage nach der ersten vollständigen Zählung. | 自 1.6.3 版起，每份文件只計算一次。先前為每位使用者分別掛載的外部儲存空間，是按掛載次數重複計算，因此現在的數字可能比以前低。此提示會在第一次完整計算後七天消失。 |
| `The coverage is being counted document by document. On large instances this can take some time, and the search keeps working normally meanwhile. The figure appears here as soon as the count is finished.` | Der Deckungsgrad wird gerade pro Dokument gezählt. Auf großen Instanzen kann das einige Zeit dauern, die Suche arbeitet währenddessen normal weiter. Die Zahl erscheint hier, sobald die Zählung fertig ist. | 正在逐份文件計算涵蓋率。在大型站台上可能需要一段時間，期間搜尋仍正常運作。計算完成後，數字就會顯示在這裡。 |
| `%s files could not be read or got stuck repeatedly. They count as not searchable and lower the coverage figure.` | %s Dateien konnten nicht gelesen werden oder sind mehrfach hängen geblieben. Sie zählen als nicht durchsuchbar und senken den Deckungsgrad. | 有 %s 個檔案無法讀取或一再卡住。這些檔案算作無法搜尋，會拉低涵蓋率。 |
| `This instance has more storages than the count per document can handle. The figure is therefore counted per storage as in version 1.6.2, and a file mounted for several users can stand in it several times.` | Diese Instanz hat mehr Speicherorte, als die Zählung pro Dokument verarbeiten kann. Die Zahl wird deshalb wie in Version 1.6.2 je Speicherort gezählt, und eine Datei, die für mehrere Nutzer eingebunden ist, kann mehrfach darin stehen. | 此站台的儲存空間數量超出逐份文件計算所能處理的範圍。因此改用 1.6.2 版按儲存空間計算的方式，掛載給多位使用者的檔案可能會被重複計入。 |
| `%s files are searchable. The count of indexable files is being updated, and the share is shown again afterwards.` | %s Dateien sind durchsuchbar. Die Zahl der indexierbaren Dateien wird gerade neu ermittelt, danach erscheint der Anteil wieder. | %s 個檔案可以搜尋。可索引檔案的數量正在更新，完成後會再次顯示比例。 |
| `The share cannot be worked out right now because the backend does not answer. %s files of this instance are indexable.` | Der Anteil ist im Moment nicht berechenbar, weil das Backend nicht antwortet. %s Dateien dieser Instanz sind indexierbar. | 後端沒有回應，目前無法算出比例。此站台有 %s 個檔案可以索引。 |
| `Deliberately left out: %s` | Bewusst ausgelassen: %s | 刻意略過：%s |
| `Those files are too large, of a type Findling does not read, or excluded by a rule. They are not in the denominator above, so the coverage figure can reach a hundred per cent.` | Diese Dateien sind zu groß, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen. Sie stehen nicht im Nenner darüber, damit der Deckungsgrad 100 Prozent erreichen kann. | 這些檔案過大、屬於 Findling 不讀取的類型，或被規則排除。它們不計入上方的分母，因此涵蓋率可以達到百分之百。 |
| `Nothing is left out on purpose right now. Files that are too large, of a type Findling does not read, or excluded by a rule would be counted here, and they are not in the denominator above.` | Derzeit ist nichts bewusst ausgelassen. Hier stünden Dateien, die zu groß sind, von einem Typ, den Findling nicht liest, oder durch eine Regel ausgeschlossen, und sie zählen nicht im Nenner darüber. | 目前沒有刻意略過的檔案。過大、屬於 Findling 不讀取的類型或被規則排除的檔案會計入此處，且不計入上方的分母。 |
| `The exclusion rules were changed. The search applies them at once, the counters on this page follow once they have been worked out again.` | Die Ausschlussregeln wurden geändert. Die Suche wendet sie sofort an, die Zähler auf dieser Seite folgen, sobald sie neu ermittelt sind. | 排除規則已變更。搜尋會立即套用，本頁的計數則會在重新計算後跟上。 |
| `The content gateway did not answer on the last indexing pass. The affected files stay in the queue and are tried again; the search keeps answering.` | Das Content-Gateway hat beim letzten Indexierungslauf nicht geantwortet. Die betroffenen Dateien bleiben in der Warteschlange und werden erneut versucht; die Suche antwortet weiter. | 上一輪索引時內容閘道沒有回應。受影響的檔案會留在佇列中並再次嘗試；搜尋仍會繼續回應。 |
| `Pause indexing` | Indexierung pausieren | 暫停索引 |
| `Resume indexing` | Indexierung fortsetzen | 繼續索引 |
| `Indexing is paused for a backup. Search keeps working.` | Die Indexierung ist für ein Backup pausiert. Die Suche läuft weiter. | 索引已為備份而暫停。搜尋仍正常運作。 |
| `Pausing: the current batch finishes first. Start the backup when the status says paused.` | Pause wird vorbereitet: der laufende Stapel endet zuerst. Das Backup erst starten, wenn der Status pausiert meldet. | 暫停中：會先完成目前這一批。狀態顯示已暫停時再開始備份。 |
| `The pause state cannot be read yet, so indexing stays stopped.` | Der Pausenzustand ist noch nicht lesbar, deshalb bleibt die Indexierung angehalten. | 尚無法讀取暫停狀態，因此索引維持停止。 |
| `The backend does not know the pause yet. Update both apps to the same version.` | Das Backend kennt die Pause noch nicht. Beide Apps auf dieselbe Version aktualisieren. | 後端尚不支援暫停。請將兩個應用程式更新到相同版本。 |
| `Provisional figure, %1$s of %2$s storages have been counted through.` | Vorläufige Zahl, %1$s von %2$s Speicherorten sind durchgezählt. | 暫定數字，%2$s 個儲存空間中已計算完 %1$s 個。 |
| `External storages mounted once per user are counted once per mount here, so the same file can stand in this figure several times.` | Je Nutzer einmal eingebundene externe Speicher werden hier je Einbindung gezählt, dieselbe Datei kann daher mehrfach in dieser Zahl stehen. | 為每位使用者各掛載一次的外部儲存空間，在此按掛載次數計算，因此同一個檔案可能在這個數字中出現多次。 |
| `Findable by meaning` | Auffindbar nach Bedeutung | 可依語意找到 |
| `%1$s of %2$s indexable files can also be found by meaning` | %1$s von %2$s indexierbaren Dateien sind auch nach Bedeutung auffindbar | %2$s 個可索引的檔案中，有 %1$s 個也能依語意找到 |
| `Model: %1$s` | Modell: %1$s | 模型：%1$s |
| `Model: %1$s, re-embedding %2$s (%3$s of %4$s)` | Modell: %1$s, Neueinbettung %2$s (%3$s von %4$s) | 模型：%1$s，重新嵌入進度 %2$s（%4$s 份中已完成 %3$s 份） |
| `Economy` | Sparsam | 節約 |
| `Standard` | Standard | 標準 |
| `Performance` | Leistung | 效能 |
| `memory tight, memory.events max twice` | Speicher knapp, zweimal memory.events max | 記憶體吃緊，memory.events 的 max 已出現兩次 |
| `a slot was killed for lack of memory` | ein Slot wurde wegen Speichermangels beendet | 有一個工作槽因記憶體不足而被終止 |
| `the container ended during a multi slot pass` | der Container endete während einer Mehr-Slot-Staffel | 容器在多個工作槽同時執行時結束 |
| `Profile: chosen %1$s, in force %2$s (%3$s)` | Profil: gewählt %1$s, wirksam %2$s (%3$s) | 設定檔：已選「%1$s」，實際生效「%2$s」（%3$s） |
| `OCR slots: %1$s of %2$s, memory tight` | OCR-Slots: %1$s von %2$s, Speicher knapp | OCR 工作槽：%1$s 個（共 %2$s 個），記憶體吃緊 |
| `The semantic share cannot be worked out right now. The backend does not answer, or it does not report this figure yet.` | Der semantische Anteil ist im Moment nicht berechenbar. Das Backend antwortet nicht, oder es meldet diese Zahl noch nicht. | 目前無法算出語意搜尋的比例。後端沒有回應，或尚未回報這個數字。 |
| `The model is in memory, the semantic search is answering.` | Das Modell liegt im Speicher, die semantische Suche antwortet. | 模型已載入記憶體，語意搜尋正在回應。 |
| `The model is read when it is first needed. That is the normal state.` | Das Modell wird beim ersten Bedarf geladen. Das ist der Normalfall. | 模型會在第一次需要時才讀取。這是正常狀態。 |
| `The semantic half is switched off in the settings of the container.` | Die semantische Hälfte ist in den Einstellungen des Containers abgeschaltet. | 語意搜尋部分已在容器的設定中關閉。 |
| `There is no model in this image. The search keeps answering with full text hits, the semantic half stays empty.` | In diesem Abbild liegt kein Modell. Die Suche liefert weiterhin Volltexttreffer, die semantische Hälfte bleibt leer. | 此映像檔中沒有模型。搜尋仍以全文比對結果回應，語意搜尋部分維持空白。 |
| `Reading the model failed once and is tried again shortly. Until then the search answers with full text hits.` | Das Laden des Modells ist einmal gescheitert und wird in Kürze erneut versucht. Bis dahin liefert die Suche Volltexttreffer. | 讀取模型失敗一次，稍後會再試。在此之前，搜尋以全文比對結果回應。 |
| `The model was released to save memory. The next search answers with full text hits and loads it again in the background.` | Das Modell wurde zum Sparen freigegeben. Die nächste Suche antwortet mit Volltexttreffern und lädt es im Hintergrund nach. | 為節省記憶體，模型已釋放。下一次搜尋會以全文比對結果回應，並在背景重新載入模型。 |
| `This container does not report the state of the model yet.` | Dieser Container meldet den Zustand des Modells noch nicht. | 此容器尚未回報模型狀態。 |
| `The full text search covers every indexed document. The semantic search covers the beginning of each document, and this second figure fills up after the first index has finished.` | Die Volltextsuche deckt jedes indexierte Dokument ab. Die semantische Suche deckt den Anfang jedes Dokuments ab, und diese zweite Zahl füllt sich nach dem Erstindex nach. | 全文搜尋涵蓋所有已索引的文件。語意搜尋涵蓋每份文件的開頭部分，第二個數字會在首次索引完成後逐漸增加。 |
| `Up to date, last checked %s` | Aktuell, letzte Prüfung %s | 已是最新，上次檢查：%s |
| `Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time.` | Die Indexierung kommt seit %s nicht voran. In dieser Zeit hat weder ein Hintergrundauftrag noch das Backend etwas fertiggestellt. | 索引已有 %s 沒有進展。這段時間內，背景作業與後端都沒有完成任何工作。 |
| `No background job of this app has run yet. Background jobs may not be running.` | Noch kein Hintergrundauftrag dieser App ist gelaufen. Möglicherweise laufen die Hintergrundaufträge nicht. | 此應用程式的背景作業尚未執行過。背景作業可能沒有在運作。 |
| `Indexing is running.` | Die Indexierung läuft. | 正在建立索引。 |
| `The numbers could not be refreshed. The figures below are the last ones this page received.` | Die Zahlen konnten nicht aktualisiert werden. Die Werte unten sind die letzten, die diese Seite bekommen hat. | 無法重新整理數字。下方是本頁最後收到的數字。 |
| `_%n minute_::_%n minutes_` | %n Minute / %n Minuten | %n 分鐘 |
| `_%n hour_::_%n hours_` | %n Stunde / %n Stunden | %n 小時 |
| `_%n day_::_%n days_` | %n Tag / %n Tage | %n 天 |
| `Waiting in the queue` | Wartet in der Warteschlange | 在佇列中等候 |
| `Being processed` | Wird gerade verarbeitet | 處理中 |
| `Indexed` | Indexiert | 已索引 |
| `Skipped` | Übersprungen | 已略過 |
| `Failed` | Fehlgeschlagen | 失敗 |
| `Excluded` | Ausgeschlossen | 已排除 |
| `Excluded files are not part of the coverage figure. They are files you told Findling to leave alone.` | Ausgeschlossene Dateien zählen nicht in den Deckungsgrad. Es sind die Dateien, die Findling auf Anweisung nicht anfasst. | 已排除的檔案不計入涵蓋率。這些是您要求 Findling 不要處理的檔案。 |
| `Little disk space left. Indexing is paused so the index stays intact. Search keeps working.` | Wenig Speicherplatz frei. Die Indexierung pausiert, damit der Index unbeschädigt bleibt. Die Suche funktioniert weiter. | 磁碟空間所剩不多。索引已暫停，以保持索引完整。搜尋仍正常運作。 |
| `The index was built with an older text analysis. Run "occ findling:index --restart" to rebuild it, otherwise some hits stay missing.` | Der Index wurde mit einer älteren Textanalyse gebaut. Mit "occ findling:index --restart" neu aufbauen, sonst fehlen weiter Treffer. | 索引是以較舊的文字分析方式建立的。請執行「occ findling:index --restart」重建索引，否則部分搜尋結果會持續缺漏。 |
| `Findling is rebuilding its index so that the newly switched on languages can be searched. %1$s of %2$s documents have been carried over. Search keeps answering while this runs, and there is nothing to start or to restart.` | Findling baut seinen Index neu auf, damit die neu eingeschalteten Sprachen durchsucht werden können. %1$s von %2$s Dokumenten sind übertragen. Die Suche antwortet währenddessen weiter, und es gibt nichts zu starten oder neu zu starten. | Findling 正在重建索引，讓新啟用的語言可以被搜尋。%2$s 份文件中已轉移 %1$s 份。重建期間搜尋仍會回應，您不需要啟動或重新啟動任何東西。 |
| `Findling wants to rebuild its index for the newly switched on languages and there is not enough room: %s more are needed next to what the index already uses. Free that much, or set the environment variable FINDLING_REBUILD_FALLBACK=fullreindex to have the backend read the files again instead. Either way the backend only tries again after a restart of the container.` | Findling möchte seinen Index für die neu eingeschalteten Sprachen neu aufbauen, und es ist nicht genug Platz: %s fehlen zusätzlich zu dem, was der Index bereits belegt. Geben Sie so viel frei, oder setzen Sie die Umgebungsvariable FINDLING_REBUILD_FALLBACK=fullreindex, damit das Backend die Dateien stattdessen neu liest. In beiden Fällen versucht es das Backend erst nach einem Neustart des Containers erneut. | Findling 需要為新啟用的語言重建索引，但空間不足：除了索引目前已使用的空間外，還需要 %s。請釋出這麼多空間，或設定環境變數 FINDLING_REBUILD_FALLBACK=fullreindex，改由後端重新讀取檔案。無論哪種做法，後端都要在容器重新啟動後才會再試。 |
| `At least one app of the full text search framework (fulltextsearch, files_fulltextsearch) is enabled next to Findling. Results from the same file can then appear twice in the search bar. Disable these apps once Findling has finished its first index run.` | Mindestens eine App des Volltextsuche-Frameworks (fulltextsearch, files_fulltextsearch) ist neben Findling aktiviert. Treffer aus derselben Datei können dann doppelt in der Suchleiste erscheinen. Diese Apps deaktivieren, sobald Findlings erster Indexlauf abgeschlossen ist. | 除了 Findling 之外，至少還啟用了一個全文搜尋框架的應用程式（fulltextsearch、files_fulltextsearch）。這樣同一個檔案的結果可能會在搜尋列中出現兩次。請在 Findling 完成第一次索引後停用這些應用程式。 |
| `Languages of the index: %1$s switched on, %2$s with text in the index.` | Sprachen des Index: %1$s eingeschaltet, %2$s mit Text im Index. | 索引語言：已啟用 %1$s，索引中有文字的為 %2$s。 |
| `No numbers yet` | Noch keine Zahlen | 尚無數字 |
| `The first indexing pass has not finished. Findling started on its own, there is nothing to configure.` | Der erste Indexlauf ist noch nicht durch. Findling ist von selbst gestartet, es ist nichts einzustellen. | 第一輪索引尚未完成。Findling 已自行啟動，不需要任何設定。 |
| `The two halves of Findling report different versions: this app is %1$s, the backend is %2$s. While they disagree the search answers with no results, because a wrong answer without a word would be worse. Bring both halves to the same version.` | Die beiden Hälften von Findling melden unterschiedliche Versionen: diese App ist %1$s, das Backend ist %2$s. Solange sie nicht zusammenpassen, antwortet die Suche ohne Ergebnisse, weil eine falsche Antwort ohne Hinweis schlimmer wäre. Beide Hälften auf dieselbe Version bringen. | Findling 的兩個部分回報的版本不同：此應用程式為 %1$s，後端為 %2$s。版本不一致期間，搜尋一律不回傳結果，因為默默給出錯誤的答案會更糟。請將兩個部分更新到相同版本。 |
| `The Findling backend does not answer. The numbers below are the last ones this app recorded. Check under Apps that the External App "Findling Backend" is installed and running.` | Das Findling-Backend antwortet nicht. Die Zahlen unten sind die letzten, die diese App festgehalten hat. Unter Apps prüfen, ob die External App "Findling Backend" installiert und gestartet ist. | Findling 後端沒有回應。下方是此應用程式最後記錄的數字。請到「應用程式」確認外部應用程式「Findling Backend」已安裝且正在執行。 |
| `Estimate for the first index` | Schätzung für den Erstindex | 首次索引的估算 |
| `%1$s files, %2$s of them need OCR. About %3$s and about %4$s of index.` | %1$s Dateien, davon %2$s mit OCR. Etwa %3$s und etwa %4$s Index. | %1$s 個檔案，其中 %2$s 個需要 OCR。約需 %3$s，索引約占 %4$s。 |
| `%1$s files, %2$s of them need OCR.` | %1$s Dateien, davon %2$s mit OCR. | %1$s 個檔案，其中 %2$s 個需要 OCR。 |
| `%1$s to %2$s` | %1$s bis %2$s | %1$s 至 %2$s |
| `Counting the files, this takes a moment.` | Die Dateien werden gezählt, das dauert einen Moment. | 正在計算檔案數量，請稍候。 |
| `Startup value, being measured.` | Startwert, wird gemessen. | 初始值，測量中。 |
| `The space needed is measured as soon as the first documents are in the index.` | Der Platzbedarf wird gemessen, sobald die ersten Dokumente im Index sind. | 第一批文件進入索引後，就會測量所需空間。 |
| `The index is expected to need more space than this volume has free. Indexing pauses before the volume fills up, and search keeps working.` | Der Index braucht voraussichtlich mehr Platz, als auf diesem Datenträger frei ist. Die Indexierung pausiert, bevor der Datenträger voll wird, und die Suche funktioniert weiter. | 預估索引所需空間將超過此磁碟區的可用空間。索引會在磁碟區用滿前暫停，搜尋仍正常運作。 |
| `Findling does not wait for a confirmation. The first index has already started.` | Findling wartet auf keine Bestätigung. Der Erstindex läuft bereits. | Findling 不會等待確認。首次索引已經開始。 |
| `Files that were not indexed` | Nicht indexierte Dateien | 未索引的檔案 |
| `Files that were not indexed, grouped by reason` | Nicht indexierte Dateien, nach Grund gruppiert | 未索引的檔案，依原因分組 |
| `Every file was indexed. Nothing was skipped and nothing failed.` | Alle Dateien sind indexiert. Nichts übersprungen, nichts fehlgeschlagen. | 所有檔案都已索引。沒有略過，也沒有失敗。 |
| `Reason` | Grund | 原因 |
| `Files` | Dateien | 檔案 |
| `State` | Zustand | 狀態 |
| `Show example paths` | Beispielpfade anzeigen | 顯示範例路徑 |
| `Hide example paths` | Beispielpfade verbergen | 隱藏範例路徑 |
| `_and %n more_::_and %n more_` | und %n weitere / und %n weitere | 以及另外 %n 個 |
| `File no longer exists (ID %s)` | Datei existiert nicht mehr (ID %s) | 檔案已不存在（ID %s） |
| `%s (in the trash bin)` | %s (im Papierkorb) | %s（在垃圾桶中） |
| `%1$s (ID %2$s)` | %1$s (ID %2$s) | %1$s（ID %2$s） |
| `%1$s (in the trash bin, ID %2$s)` | %1$s (im Papierkorb, ID %2$s) | %1$s（在垃圾桶中，ID %2$s） |
| `Indexed, text truncated` | Indexiert, Text gekürzt | 已索引，文字已截斷 |
| `Unknown reason (%s)` | Unbekannter Grund (%s) | 未知原因（%s） |
| `This app does not know this code. It may come from a newer version of the backend.` | Diese App kennt diesen Code nicht. Er kann von einer neueren Fassung des Backends kommen. | 此應用程式不認得這個代碼。它可能來自較新版本的後端。 |
| `Text truncated` | Text gekürzt | 文字已截斷 |
| `The beginning of the document is searchable, the rest is not. Very long documents are cut on purpose.` | Der Anfang des Dokuments ist durchsuchbar, der Rest nicht. Sehr lange Dokumente werden bewusst gekappt. | 文件的開頭部分可以搜尋，其餘部分則不行。過長的文件會被刻意截斷。 |
| `Too large` | Zu groß | 檔案過大 |
| `Raise the value under "Largest file to read".` | Den Wert unter "Größte zu lesende Datei" erhöhen. | 請調高「可讀取的最大檔案」的數值。 |
| `File type not supported` | Dateityp nicht unterstützt | 不支援的檔案類型 |
| `None. Findling reads PDF, Office, OpenDocument, text, mails, ZIP files and images.` | Keine. Findling liest PDF, Office, OpenDocument, Text, Mails, ZIP-Dateien und Bilder. | 無。Findling 可讀取 PDF、Office、OpenDocument、純文字、郵件、ZIP 檔與圖片。 |
| `Password protected` | Passwortgeschützt | 受密碼保護 |
| `None. Without the password the content cannot be read.` | Keine. Ohne Passwort ist der Inhalt nicht lesbar. | 無。沒有密碼就無法讀取內容。 |
| `No text in the document` | Kein Text im Dokument | 文件中沒有文字 |
| `None. The document carries neither a text layer nor recognisable writing.` | Keine. Das Dokument enthält weder Textschicht noch erkennbare Schrift. | 無。這份文件既沒有文字層，也沒有可辨識的文字。 |
| `No text content` | Kein Textinhalt | 沒有文字內容 |
| `None. The file is readable but carries no text.` | Keine. Die Datei ist lesbar, enthält aber keinen Text. | 無。檔案可以讀取，但不含文字。 |
| `Spreadsheet too large` | Tabelle zu groß | 試算表過大 |
| `None. Very large spreadsheets are skipped so the container does not fall over.` | Keine. Sehr große Tabellen werden übersprungen, damit der Container nicht kippt. | 無。非常大的試算表會被略過，以免容器當機。 |
| `File no longer present` | Datei nicht mehr vorhanden | 檔案已不在 |
| `None. The file was already deleted or moved when it was read.` | Keine. Die Datei war beim Lesen schon gelöscht oder verschoben. | 無。讀取時檔案已被刪除或移動。 |
| `Image without recognisable writing` | Bild ohne erkennbare Schrift | 圖片中沒有可辨識的文字 |
| `None.` | Keine. | 無。 |
| `Excluded by a rule` | Durch Regel ausgeschlossen | 被規則排除 |
| `Remove the matching entry under "Excluded folders" or "Excluded patterns".` | Den passenden Eintrag unter "Ausgeschlossene Ordner" oder "Ausgeschlossene Muster" entfernen. | 請在「排除的資料夾」或「排除的樣式」中移除對應的項目。 |
| `System or helper file` | System- oder Hilfsdatei | 系統檔或輔助檔 |
| `None. macOS metadata files (._) and Office lock files (~$) carry no document content.` | Keine. macOS-Metadateien (._) und Office-Sperrdateien (~$) enthalten keinen Dokumentinhalt. | 無。macOS 中繼資料檔（._）與 Office 鎖定檔（~$）不含文件內容。 |
| `Old Office format under a new name` | Altes Office-Format unter neuem Namen | 使用新副檔名的舊版 Office 格式 |
| `Save the file again in the current Office format (.docx, .xlsx, .pptx).` | Datei im aktuellen Office-Format (.docx, .xlsx, .pptx) neu speichern. | 請以目前的 Office 格式（.docx、.xlsx、.pptx）重新儲存檔案。 |
| `Variant of this format that cannot be read` | Variante dieses Formats, die nicht gelesen werden kann | 無法讀取的格式變體 |
| `None. The file uses a variant or an encoding Findling cannot read, for example Word 95 or an unusual image encoding.` | Keine. Die Datei nutzt eine Variante oder Kodierung, die Findling nicht lesen kann, zum Beispiel Word 95 oder eine ungewöhnliche Bildkodierung. | 無。檔案使用了 Findling 無法讀取的變體或編碼，例如 Word 95 或少見的圖片編碼。 |
| `ZIP file over the safety limits` | ZIP-Datei über den Sicherheitsgrenzen | ZIP 檔超出安全限制 |
| `None. ZIP files that are nested too deep, too large, too densely packed or hold too many files are skipped so the container keeps running.` | Keine. ZIP-Dateien, die zu tief verschachtelt, zu groß oder zu dicht gepackt sind oder zu viele Dateien enthalten, werden übersprungen, damit der Container weiterläuft. | 無。巢狀層數過深、過大、壓縮比過高或內含檔案過多的 ZIP 檔會被略過，以確保容器持續運作。 |
| `File blocked as malicious` | Datei als bösartig gesperrt | 檔案被判定為惡意而封鎖 |
| `None. The file carries the signature of an attack (see the detail) and is not read any further, so the container keeps running. Remove or replace the file if it is not meant to be there.` | Keine. Die Datei trägt die Signatur eines Angriffs (siehe Detail) und wird nicht weiter gelesen, damit der Container weiterläuft. Die Datei entfernen oder ersetzen, wenn sie dort nicht hingehört. | 無。此檔案帶有攻擊特徵（請見詳細資訊），因此不再繼續讀取，以確保容器持續運作。如果這個檔案不該出現在這裡，請移除或替換它。 |
| `Not readable for the users asked` | Für die gefragten Nutzer nicht lesbar | 所詢問的使用者皆無法讀取 |
| `The file is still there. Check the advanced permissions of the Team Folder or the access rights on the external storage: Findling reads a file only as a user who may open it and asks the first 20 of its users in alphabetical order. A file that is locked or offline is tried again a few times.` | Die Datei ist noch vorhanden. Die erweiterten Berechtigungen des Team Folders oder die Zugriffsrechte auf dem externen Speicher prüfen: Findling liest eine Datei nur als Nutzer, der sie öffnen darf, und fragt die ersten 20 ihrer Nutzer in alphabetischer Reihenfolge. Eine gesperrte oder ausgelagerte Datei wird noch einige Male erneut versucht. | 檔案仍然存在。請檢查團隊資料夾的進階權限，或外部儲存空間上的存取權限：Findling 只會以有權開啟檔案的使用者身分讀取檔案，並依字母順序詢問該檔案的前 20 位使用者。遭鎖定或離線的檔案會再嘗試幾次。 |
| `On SMB storage without the php-smbclient extension, install this extension recommended by Nextcloud, or raise the timeout option of the storage (occ files_external:config).` | Bei SMB-Speichern ohne die Erweiterung php-smbclient diese von Nextcloud empfohlene Erweiterung installieren, alternativ die Speicher-Option timeout erhöhen (occ files_external:config). | 若使用 SMB 儲存空間且未安裝 php-smbclient 擴充功能，請安裝這個 Nextcloud 建議的擴充功能，或調高該儲存空間的逾時選項（occ files_external:config）。 |
| `The user named in front of the path may not open this file. The diagnosis is about the file itself.` | Der vor dem Pfad genannte Nutzer darf diese Datei nicht öffnen. Die Diagnose gilt der Datei selbst. | 路徑前所列的使用者無權開啟此檔案。此診斷針對的是檔案本身。 |
| `File is empty` | Datei ist leer | 檔案是空的 |
| `None. The file has 0 bytes.` | Keine. Die Datei hat 0 Byte. | 無。檔案大小為 0 位元組。 |
| `File damaged` | Datei beschädigt | 檔案已損毀 |
| `Check the file outside of Nextcloud and upload it again.` | Die Datei außerhalb von Nextcloud prüfen und neu hochladen. | 請在 Nextcloud 之外檢查檔案，然後重新上傳。 |
| `Document structure faulty` | Dokumentstruktur fehlerhaft | 文件結構有誤 |
| `Open the document in the program it came from and save it again.` | Das Dokument im Ursprungsprogramm öffnen und neu speichern. | 請以建立該文件的程式開啟它，再重新儲存。 |
| `Character set not recognised` | Zeichensatz nicht erkannt | 無法辨識字元集 |
| `Save the file as UTF-8 and upload it again.` | Die Datei als UTF-8 speichern und neu hochladen. | 請將檔案另存為 UTF-8，然後重新上傳。 |
| `Timed out while reading` | Zeitüberschreitung beim Lesen | 讀取逾時 |
| `The next run tries again.` | Wird beim nächsten Lauf erneut versucht. | 下一輪會再試一次。 |
| `Nextcloud could not open the file, often because its storage was not available. The nightly comparison tries it again up to three times, and a change to the file tries it at once.` | Nextcloud konnte die Datei nicht öffnen, oft weil ihr Speicher nicht verfügbar war. Der nächtliche Abgleich versucht es bis zu dreimal erneut, eine Änderung an der Datei sofort. | Nextcloud 無法開啟此檔案，通常是因為其儲存空間無法使用。每晚的比對作業最多會再試三次，檔案一有變更也會立即再試。 |
| `Not enough memory while reading` | Zu wenig Speicher beim Lesen | 讀取時記憶體不足 |
| `The next run tries again. If it happens again, give each document more memory: deploy Findling Backend with a larger FINDLING_EXTRACT_ADDRESS_SPACE_BYTES, for example 1073741824 (1 GiB).` | Wird beim nächsten Lauf erneut versucht. Bei Wiederholung jedem Dokument mehr Speicher geben: Findling Backend mit einem größeren FINDLING_EXTRACT_ADDRESS_SPACE_BYTES bereitstellen, zum Beispiel 1073741824 (1 GiB). | 下一輪會再試一次。如果再次發生，請給每份文件更多記憶體：以較大的 FINDLING_EXTRACT_ADDRESS_SPACE_BYTES 重新部署 Findling Backend，例如 1073741824（1 GiB）。 |
| `File was not retrievable` | Datei war nicht abrufbar | 無法取得檔案 |
| `Stuck repeatedly` | Mehrfach hängen geblieben | 一再卡住 |
| `Findling does not try this file again. Use the lookup to check whether it opens outside of Nextcloud.` | Findling versucht diese Datei nicht mehr. Über die Diagnose prüfen, ob sie sich außerhalb von Nextcloud öffnen lässt. | Findling 不會再嘗試這個檔案。請用查詢功能確認它在 Nextcloud 之外能否開啟。 |
| `Text recognition failed` | Texterkennung fehlgeschlagen | 文字辨識失敗 |
| `Text recognition not available` | Texterkennung nicht verfügbar | 無法使用文字辨識 |
| `The backend could not start Tesseract. Check the log of the External App.` | Das Backend konnte Tesseract nicht starten. Das Protokoll der External App prüfen. | 後端無法啟動 Tesseract。請檢查外部應用程式的紀錄檔。 |
| `Look up one file` | Einzelne Datei prüfen | 查詢單一檔案 |
| `Path or file ID` | Pfad oder Datei-ID | 路徑或檔案 ID |
| `A path as Nextcloud stores it, or the numeric ID from the list above.` | Ein Pfad, wie Nextcloud ihn führt, oder die Zahl aus der Liste oben. | Nextcloud 儲存的路徑，或上方清單中的數字 ID。 |
| `Look up file` | Datei prüfen | 查詢檔案 |
| `Looking up a single file needs JavaScript. Everything above stays complete without it.` | Die Einzelprüfung braucht JavaScript. Alles darüber bleibt auch ohne vollständig lesbar. | 查詢單一檔案需要 JavaScript。即使沒有 JavaScript，上方的所有內容仍然完整。 |
| `No file at this path, and no file with this ID.` | Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID. | 此路徑下沒有檔案，也沒有這個 ID 的檔案。 |
| `Not seen yet` | Noch nicht gesehen | 尚未掃描到 |
| `State unknown right now` | Zustand im Moment unbekannt | 目前狀態不明 |
| `File ID: %s` | Datei-ID: %s | 檔案 ID：%s |
| `Error class: %s` | Fehlerklasse: %s | 錯誤類別：%s |
| `Detail: %s` | Detail: %s | 詳細資訊：%s |
| `Last checked %s` | Zuletzt geprüft: %s | 上次檢查：%s |
| `The lookup did not work. Nothing about this file has changed.` | Die Prüfung hat nicht funktioniert. An dieser Datei hat sich nichts geändert. | 查詢失敗。這個檔案沒有任何變更。 |
| `The state of this file is unknown right now because the backend does not answer.` | Der Zustand dieser Datei ist im Moment unbekannt, weil das Backend nicht antwortet. | 後端沒有回應，因此目前無法得知這個檔案的狀態。 |
| `This file has not reached the queue. The next comparison run picks it up.` | Diese Datei ist noch nicht in der Warteschlange angekommen. Der nächste Abgleichlauf holt sie ab. | 這個檔案尚未進入佇列。下一輪比對作業會處理它。 |
| `It was indexed before and is recorded again on the next comparison run.` | Sie war vorher indexiert und wird beim nächsten Abgleichlauf neu erfasst. | 它先前已索引過，下一輪比對作業會重新記錄。 |
| `This file was indexed and has since been deleted. It is out of the index with it.` | Diese Datei war indexiert und ist inzwischen gelöscht. Damit ist sie auch aus dem Index heraus. | 這個檔案曾被索引，之後已被刪除，也已一併從索引中移除。 |
| `In the trash bin` | Im Papierkorb | 在垃圾桶中 |
| `Restore the file. The next comparison run picks it up.` | Die Datei wiederherstellen. Der nächste Abgleichlauf holt sie ab. | 請還原檔案。下一輪比對作業會處理它。 |
| `Storage is not indexed` | Speicherort wird nicht indexiert | 此儲存空間未建立索引 |
| `Findling reads the home directories of your users. Team Folders and external storage are settings of their own.` | Findling liest die Heimatverzeichnisse der Nutzer. Team Folders und externer Speicher sind eigene Einstellungen. | Findling 會讀取使用者的家目錄。團隊資料夾與外部儲存空間有各自的設定。 |
| `This is a folder` | Das ist ein Ordner | 這是資料夾 |
| `Enter the path of a file. A folder has no state of its own.` | Den Pfad einer Datei eingeben. Ein Ordner hat keinen eigenen Zustand. | 請輸入檔案的路徑。資料夾本身沒有狀態。 |
| `Attempts so far: %s` | Bisherige Versuche: %s | 目前已嘗試次數：%s |
| `The next background run picks this file up (%s).` | Der nächste Hintergrundlauf holt diese Datei ab (%s). | 下一輪背景作業會處理這個檔案（%s）。 |
| `The content of this file is searchable.` | Der Inhalt dieser Datei ist durchsuchbar. | 這個檔案的內容可以搜尋。 |
| `_A worker holds this file. The claim runs out in %n second if nothing acknowledges it._::_A worker holds this file. The claim runs out in %n seconds if nothing acknowledges it._` | Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunde aus, wenn ihn niemand quittiert. / Ein Arbeiter hält diese Datei. Der Anspruch läuft in %n Sekunden aus, wenn ihn niemand quittiert. | 某個處理程序正持有這個檔案。若無任何確認，持有權會在 %n 秒後失效。 |
| `Rules and limits` | Regeln und Grenzen | 規則與限制 |
| `Excluded folders` | Ausgeschlossene Ordner | 排除的資料夾 |
| `Prefix match on the path as the lists on this page show it, without wildcards. For wildcards use "Excluded patterns". Example: Backups` | Präfix-Vergleich auf dem Pfad, wie ihn die Listen dieser Seite zeigen, ohne Platzhalter. Für Platzhalter "Ausgeschlossene Muster" verwenden. Beispiel: Backups | 以本頁清單所顯示的路徑做開頭比對，不支援萬用字元。需要萬用字元請使用「排除的樣式」。範例：Backups |
| `Add exclusion` | Ausschluss hinzufügen | 新增排除項目 |
| `Remove exclusion %s` | Ausschluss %s entfernen | 移除排除項目 %s |
| `No folder is excluded.` | Kein Ordner ist ausgeschlossen. | 沒有排除任何資料夾。 |
| `Excluded patterns` | Ausgeschlossene Muster | 排除的樣式 |
| `Matched against the path as the lists on this page show it. * stands for any number of characters, also across folders. ? stands for exactly one character within a name. Upper and lower case count. Examples: %1$s and %2$s` | Vergleich mit dem Pfad, wie ihn die Listen dieser Seite zeigen. * steht für beliebig viele Zeichen, auch über Ordner hinweg. ? steht für genau ein Zeichen innerhalb eines Namens. Groß- und Kleinschreibung zählt. Beispiele: %1$s und %2$s | 與本頁清單所顯示的路徑比對。* 代表任意數量的字元，也可跨越資料夾。? 代表名稱中的恰好一個字元。區分大小寫。範例：%1$s 與 %2$s |
| `No pattern is set.` | Kein Muster ist gesetzt. | 尚未設定任何樣式。 |
| `Add pattern` | Muster hinzufügen | 新增樣式 |
| `Remove pattern %s` | Muster %s entfernen | 移除樣式 %s |
| `Largest file to read` | Größte zu lesende Datei | 可讀取的最大檔案 |
| `Files above this size are recorded as skipped (too large) and never read.` | Größere Dateien werden als übersprungen (zu groß) vermerkt und nie gelesen. | 超過此大小的檔案會記錄為已略過（檔案過大），且永遠不會被讀取。 |
| `The backend of this instance reads at most %s MB. This ceiling is a deploy option, see "Limits per file".` | Das Backend dieser Instanz liest höchstens %s MB. Diese Obergrenze ist eine Deploy-Option, siehe "Grenzen je Datei". | 此站台的後端最多讀取 %s MB。此上限是部署選項，請見「每個檔案的限制」。 |
| `Limits per file` | Grenzen je Datei | 每個檔案的限制 |
| `Largest file the backend reads: %1$s (%2$s)` | Größte Datei, die das Backend liest: %1$s (%2$s) | 後端可讀取的最大檔案：%1$s（%2$s） |
| `Memory one document may use while it is read: %1$s (%2$s)` | Speicher, den ein Dokument beim Lesen belegen darf: %1$s (%2$s) | 讀取單份文件時可使用的記憶體：%1$s（%2$s） |
| `Cells read per spreadsheet file: %1$s (%2$s)` | Gelesene Zellen je Tabellendatei: %1$s (%2$s) | 每個試算表檔案讀取的儲存格數：%1$s（%2$s） |
| `Pages read per scanned document: %1$s (%2$s)` | Gelesene Seiten je gescanntem Dokument: %1$s (%2$s) | 每份掃描文件讀取的頁數：%1$s（%2$s） |
| `Pages read per scanned document: %1$s, from the profile %2$s` | Gelesene Seiten je gescanntem Dokument: %1$s, aus dem Profil %2$s | 每份掃描文件讀取的頁數：%1$s，來自設定檔「%2$s」 |
| `These limits are deploy options of Findling Backend. To change one, run %s, which keeps the data, and deploy Findling Backend again with the new value.` | Diese Grenzen sind Deploy-Optionen von Findling Backend. Zum Ändern %s ausführen, was die Daten behält, und Findling Backend mit dem neuen Wert erneut bereitstellen. | 這些限制是 Findling Backend 的部署選項。若要變更，請執行會保留資料的 %s，再以新數值重新部署 Findling Backend。 |
| `Steps in the documentation` | Schritte in der Dokumentation | 說明文件中的步驟 |
| `Index Team Folders` | Team Folders indexieren | 索引團隊資料夾 |
| `Index external storage` | Externen Speicher indexieren | 索引外部儲存空間 |
| `External storage can be slow or charged per request. Indexing reads every file once.` | Externer Speicher kann langsam oder pro Zugriff kostenpflichtig sein. Die Indexierung liest jede Datei einmal. | 外部儲存空間可能較慢，或按請求次數計費。建立索引時會讀取每個檔案一次。 |
| `The next run applies the new rules. Nothing restarts.` | Der nächste Lauf übernimmt die neuen Regeln. Es startet nichts neu. | 下一輪會套用新規則。不會重新啟動任何東西。 |
| `Save rules` | Regeln speichern | 儲存規則 |
| `Rules saved. The next run applies them.` | Regeln gespeichert. Der nächste Lauf übernimmt sie. | 規則已儲存。下一輪會套用。 |
| `The rules were not saved. Nothing changed.` | Die Regeln wurden nicht gespeichert. Es hat sich nichts geändert. | 規則未儲存。沒有任何變更。 |
| `Enter a size between %1$s and %2$s MB.` | Eine Größe zwischen %1$s und %2$s MB eingeben. | 請輸入介於 %1$s 到 %2$s MB 之間的大小。 |
| `B` | B | B |
| `KB` | KB | KB |
| `MB` | MB | MB |
| `GB` | GB | GB |
| `TB` | TB | TB |
| `PB` | PB | PB |
| `Enter a folder path.` | Einen Ordnerpfad eingeben. | 請輸入資料夾路徑。 |
| `This path is already excluded.` | Dieser Pfad ist bereits ausgeschlossen. | 此路徑已被排除。 |
| `A folder path may be at most %s bytes long.` | Ein Ordnerpfad darf höchstens %s Byte lang sein. | 資料夾路徑最長為 %s 位元組。 |
| `At most %s folders can be excluded.` | Höchstens %s Ordner lassen sich ausschließen. | 最多可排除 %s 個資料夾。 |
| `The entry must not contain . or .. as a folder name.` | Der Eintrag darf . oder .. nicht als Ordnernamen enthalten. | 項目不得以 . 或 .. 作為資料夾名稱。 |
| `Enter a pattern.` | Ein Muster eingeben. | 請輸入樣式。 |
| `A pattern may be at most %s characters long.` | Ein Muster darf höchstens %s Zeichen lang sein. | 樣式最長為 %s 個字元。 |
| `At most %s patterns are allowed.` | Höchstens %s Muster sind erlaubt. | 最多可設定 %s 個樣式。 |
| `This pattern is already in the list.` | Dieses Muster steht bereits in der Liste. | 此樣式已在清單中。 |
| `Use a single *: it already matches across folders.` | Einen einfachen * verwenden: Er gilt bereits über Ordner hinweg. | 請只用一個 *：它已能跨資料夾比對。 |
| `Brackets, braces and the backslash are not allowed. Only * and ? are wildcards.` | Eckige und geschweifte Klammern sowie der Backslash sind nicht erlaubt. Nur * und ? sind Platzhalter. | 不允許使用方括號、大括號與反斜線。只有 * 和 ? 是萬用字元。 |
| `A leading ! is not supported. Patterns only exclude.` | Ein führendes ! wird nicht unterstützt. Muster schließen nur aus. | 不支援以 ! 開頭。樣式只能用來排除。 |
| `The entry contains a control character.` | Der Eintrag enthält ein Steuerzeichen. | 項目中含有控制字元。 |
| `A pattern needs at least one character besides * and ?, otherwise it would exclude everything.` | Ein Muster braucht mindestens ein Zeichen außer * und ?, sonst schlösse es alles aus. | 樣式除了 * 和 ? 之外，至少還需要一個字元，否則會排除所有內容。 |
| `This entry has no * or ?. Add it under "Excluded folders" instead.` | Dieser Eintrag enthält weder * noch ?. Ihn stattdessen unter "Ausgeschlossene Ordner" eintragen. | 此項目沒有 * 或 ?。請改為加到「排除的資料夾」。 |
| `Removing an entry takes effect within %1$s hours, when the next comparison run picks those files up again. Run "%2$s" to apply it at once.` | Einen Eintrag zu entfernen wirkt innerhalb von %1$s Stunden, wenn der nächste Abgleichlauf diese Dateien wieder aufnimmt. Mit "%2$s" sofort übernehmen. | 移除項目會在 %1$s 小時內生效，也就是下一輪比對作業重新處理這些檔案時。執行「%2$s」可立即套用。 |
| `Remove indexed content? Excluding %1$s also removes %2$s already indexed documents under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %1$s entfernt außerdem %2$s bereits indexierte Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | 要移除已索引的內容嗎？排除 %1$s 也會將該路徑下 %2$s 份已索引的文件從索引中移除。磁碟上的檔案本身不受影響。 |
| `Remove indexed content? Excluding %s also removes the documents already indexed under that path from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente unter diesem Pfad aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | 要移除已索引的內容嗎？排除 %s 也會將該路徑下已索引的文件從索引中移除。磁碟上的檔案本身不受影響。 |
| `Remove indexed content? Excluding %s also removes the already indexed documents that match that pattern from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente, auf die dieses Muster passt, aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | 要移除已索引的內容嗎？排除 %s 也會將符合該樣式的已索引文件從索引中移除。磁碟上的檔案本身不受影響。 |
| `Remove indexed content? Excluding %s also removes the already indexed documents that match these patterns from the index. The files themselves stay untouched on disk.` | Indexierte Inhalte entfernen? Der Ausschluss von %s entfernt außerdem die bereits indexierten Dokumente, auf die diese Muster passen, aus dem Index. Die Dateien selbst bleiben unverändert auf der Platte. | 要移除已索引的內容嗎？排除 %s 也會將符合這些樣式的已索引文件從索引中移除。磁碟上的檔案本身不受影響。 |
| `at least %s` | mindestens %s | 至少 %s |
| `Exclude and remove` | Ausschließen und entfernen | 排除並移除 |
| `Keep files indexed` | Dateien indexiert lassen | 保留這些檔案的索引 |
| `Search` | Suchen | 搜尋 |
| `Search term` | Suchbegriff | 搜尋字詞 |
| `invoice 2026` | Rechnung 2026 | 發票 2026 |
| `Search file names only` | Nur Dateinamen durchsuchen | 只搜尋檔名 |
| `Results for "%s"` | Treffer für „%s“ | 「%s」的搜尋結果 |
| `Search results` | Suchergebnisse | 搜尋結果 |
| `%1$s in %2$s` | %1$s in %2$s | %2$s 中的 %1$s |
| `last opened` | zuletzt geöffnet | 上次開啟 |
| `Similar documents` | Ähnliche Dokumente | 相似文件 |
| `Similar documents to %s` | Ähnliche Dokumente zu %s | 與 %s 相似的文件 |
| `Similar to: %s` | Ähnlich zu: %s | 相似於：%s |
| `Back to the results` | Zurück zu den Treffern | 返回搜尋結果 |
| `No similar documents found` | Keine ähnlichen Dokumente gefunden | 找不到相似文件 |
| `None of your other files is close enough in content. Files that have not yet been prepared for the semantic search, or that contain no text, have no similar documents.` | Keine Ihrer anderen Dateien ist inhaltlich nah genug. Dateien, die noch nicht für die semantische Suche erfasst sind oder keinen Text enthalten, haben keine ähnlichen Dokumente. | 您的其他檔案在內容上都不夠接近。尚未為語意搜尋準備好或不含文字的檔案，不會有相似文件。 |
| `This file is not available` | Diese Datei ist nicht verfügbar | 無法使用此檔案 |
| `Show all results` | Alle Treffer anzeigen | 顯示所有結果 |
| `Opens the Findling results page` | Öffnet die Findling-Ergebnisseite | 開啟 Findling 搜尋結果頁面 |
| `Previous page` | Vorherige Seite | 上一頁 |
| `Next page` | Nächste Seite | 下一頁 |
| `Page %s` | Seite %s | 第 %s 頁 |
| `More results exist. Narrow the search to see them.` | Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen. | 還有更多結果。請縮小搜尋範圍以查看。 |
| `Search your file contents` | Durchsuchen Sie den Inhalt Ihrer Dateien | 搜尋您的檔案內容 |
| `Type a word from a document. Findling searches the text inside your files, scanned PDFs included.` | Geben Sie ein Wort aus einem Dokument ein. Findling durchsucht den Text in Ihren Dateien, auch in gescannten PDFs. | 輸入文件中的字詞。Findling 會搜尋您檔案中的文字，包括掃描的 PDF。 |
| `No file contains "%s"` | Keine Datei enthält „%s“ | 沒有檔案包含「%s」 |
| `Try another word, a part of a compound word, or check the spelling.` | Versuchen Sie ein anderes Wort, ein Teilwort oder prüfen Sie die Schreibweise. | 請試試其他字詞、複合詞的一部分，或檢查拼字是否正確。 |
| `Other files contain this word, but none that you may open.` | Andere Dateien enthalten dieses Wort, aber keine, die Sie öffnen dürfen. | 有其他檔案包含這個字詞，但您都無權開啟。 |
| `The search is not answering right now` | Die Suche antwortet gerade nicht | 搜尋目前沒有回應 |
| `Findling could not reach its backend. Your files are unchanged. Try again in a moment, and tell your administrator if it stays that way.` | Findling konnte sein Backend nicht erreichen. Ihre Dateien sind unverändert. Versuchen Sie es gleich noch einmal und sagen Sie der Administration Bescheid, wenn es dabei bleibt. | Findling 無法連線到它的後端。您的檔案沒有任何改變。請稍後再試，如果情況持續，請通知您的系統管理員。 |
| `Try again` | Erneut versuchen | 再試一次 |
| `Findling is not ready to search` | Findling ist nicht suchbereit | Findling 尚未準備好搜尋 |
| `The two halves of Findling report different versions. Your administrator has to update both together.` | Die beiden Hälften von Findling melden unterschiedliche Versionen. Die Administration muss beide zusammen aktualisieren. | Findling 的兩個部分回報的版本不同。您的系統管理員必須同時更新兩者。 |
| `The index is still being built, so results can be missing.` | Der Index wird noch aufgebaut, deshalb können Treffer fehlen. | 索引仍在建立中，因此可能缺少部分結果。 |
| `File type` | Dateityp | 檔案類型 |
| `PDF` | PDF | PDF |
| `Documents` | Dokumente | 文件 |
| `Spreadsheets` | Tabellen | 試算表 |
| `Presentations` | Präsentationen | 簡報 |
| `Images` | Bilder | 圖片 |
| `Text` | Text | 純文字 |
| `Time range` | Zeitraum | 時間範圍 |
| `Today` | Heute | 今天 |
| `Last 7 days` | Letzte 7 Tage | 過去 7 天 |
| `Last 30 days` | Letzte 30 Tage | 過去 30 天 |
| `This year` | Dieses Jahr | 今年 |
| `Remove filter %s` | Filter %s entfernen | 移除篩選條件 %s |
| `Reset all filters` | Alle Filter zurücksetzen | 重設所有篩選條件 |
| `Sort by` | Sortieren nach | 排序方式 |
| `Relevance` | Relevanz | 相關性 |
| `Last modified` | Zuletzt geändert | 最近修改 |
| `Oldest first` | Älteste zuerst | 最舊的在前 |
| `Modified on %s` | Geändert am %s | 修改於 %s |
| `%1$s in %2$s, modified on %3$s` | %1$s in %2$s, geändert am %3$s | %2$s 中的 %1$s，修改於 %3$s |
| `No results with the active filters` | Keine Treffer mit den aktiven Filtern | 目前的篩選條件下沒有結果 |
| `Remove a filter or widen the time range.` | Entfernen Sie einen Filter oder erweitern Sie den Zeitraum. | 請移除篩選條件或擴大時間範圍。 |
| `Reset filters` | Filter zurücksetzen | 重設篩選條件 |
| `Performance profile` | Leistungsprofil | 效能設定檔 |
| `How much of the server's hardware Findling may use. Without a change Findling stays on Economy.` | Wie viel der Server-Hardware Findling nutzen darf. Ohne Änderung bleibt Findling bei Sparsam. | Findling 可以使用多少伺服器硬體資源。若不變更，Findling 會維持「節約」。 |
| `Detected: cores %1$s, memory %2$s` | Erkannt: Kerne %1$s, Speicher %2$s | 偵測到：%1$s 個核心，記憶體 %2$s |
| `This backend does not report its hardware yet.` | Dieses Backend meldet seine Hardware noch nicht. | 此後端尚未回報其硬體資訊。 |
| `Suggested for this hardware: %s` | Vorschlag für diese Hardware: %s | 建議此硬體使用：%s |
| `In force: %s` | Wirksam: %s | 目前生效：%s |
| `Chosen %1$s, in force %2$s: Findling sees less hardware than the chosen profile requires.` | Gewählt %1$s, wirksam %2$s: Findling sieht weniger Hardware, als das gewählte Profil verlangt. | 已選「%1$s」，實際生效「%2$s」：Findling 偵測到的硬體少於所選設定檔的需求。 |
| `Profile` | Profil | 設定檔 |
| `%s (suggested)` | %s (Vorschlag) | %s（建議） |
| `One OCR slot, as before.` | Ein OCR-Slot, wie bisher. | 一個 OCR 工作槽，與先前相同。 |
| `At most half of the hardware Findling sees, up to %s OCR slots.` | Höchstens die Hälfte der Hardware, die Findling sieht, bis zu %s OCR-Slots. | 最多使用 Findling 偵測到的一半硬體，最多 %s 個 OCR 工作槽。 |
| `Everything but one core, up to %s OCR slots.` | Alles bis auf einen Kern, bis zu %s OCR-Slots. | 保留一個核心，其餘全部使用，最多 %s 個 OCR 工作槽。 |
| `More accurate search model (fp32)` | Genaueres Suchmodell (fp32) | 較精確的搜尋模型（fp32） |
| `Downloaded once during the check, about %s from the Findling release on GitHub. Needs more memory than int8.` | Wird bei der Prüfung einmal geladen, etwa %s aus dem Findling-Release auf GitHub. Braucht mehr Speicher als int8. | 在檢查期間從 GitHub 上的 Findling 發行版本下載一次，約 %s。比 int8 需要更多記憶體。 |
| `Re-embedding of %1$s documents, estimated about %2$s. Full text search stays fully available.` | Neueinbettung von %1$s Dokumenten, geschätzt etwa %2$s. Die Volltextsuche bleibt voll verfügbar. | 將重新嵌入 %1$s 份文件，預估約需 %2$s。全文搜尋仍可完整使用。 |
| `Re-embedding of %s documents. Full text search stays fully available.` | Neueinbettung von %s Dokumenten. Die Volltextsuche bleibt voll verfügbar. | 將重新嵌入 %s 份文件。全文搜尋仍可完整使用。 |
| `Choose a different profile or model to check it.` | Ein anderes Profil oder Modell wählen, um es zu prüfen. | 請選擇其他設定檔或模型來進行檢查。 |
| `Changing the profile needs JavaScript. Everything above stays complete without it.` | Das Profil zu ändern braucht JavaScript. Alles darüber bleibt ohne es vollständig. | 變更設定檔需要 JavaScript。即使沒有 JavaScript，上方的所有內容仍然完整。 |
| `The check calculates with these values from environment variables:` | Die Prüfung rechnet mit diesen Werten aus Umgebungsvariablen: | 檢查會使用以下來自環境變數的數值計算： |
| `OCR resolution %1$s dpi, set by %2$s` | OCR-Auflösung %1$s dpi, gesetzt durch %2$s | OCR 解析度 %1$s dpi，由 %2$s 設定 |
| `OCR limit %1$s pages per file, set by %2$s` | OCR-Deckel %1$s Seiten je Datei, gesetzt durch %2$s | OCR 上限每個檔案 %1$s 頁，由 %2$s 設定 |
| `Embedding batch size %1$s, set by %2$s` | Einbettungs-Stapelgröße %1$s, gesetzt durch %2$s | 嵌入批次大小 %1$s，由 %2$s 設定 |
| `Index writer memory %1$s, set by %2$s` | Speicher des Indexschreibers %1$s, gesetzt durch %2$s | 索引寫入器記憶體 %1$s，由 %2$s 設定 |
| `Apply and check` | Übernehmen und prüfen | 套用並檢查 |
| `Apply` | Übernehmen | 套用 |
| `Stay on Economy` | Bei Sparsam bleiben | 維持「節約」 |
| `Check again` | Erneut prüfen | 重新檢查 |
| `Check %s` | %s prüfen | 檢查「%s」 |
| `Check running: %s` | Prüfung läuft: %s | 檢查進行中：%s |
| `Check running.` | Prüfung läuft. | 檢查進行中。 |
| `waiting for the indexing batch` | Indexstaffel abwarten | 正在等待索引批次 |
| `downloading the model, %1$s of %2$s` | Modell herunterladen, %1$s von %2$s | 正在下載模型，%1$s / %2$s |
| `verifying the model file` | Modelldatei prüfen | 正在驗證模型檔案 |
| `loading the model` | Modell laden | 正在載入模型 |
| `OCR with one slot` | OCR mit einem Slot | 以一個工作槽執行 OCR |
| `calculating memory` | Speicher rechnen | 正在計算記憶體 |
| `OCR with %s slots` | OCR mit %s Slots | 以 %s 個工作槽執行 OCR |
| `cleaning up` | aufräumen | 正在清理 |
| `Indexing pauses during the check and continues afterwards.` | Die Indexierung pausiert während der Prüfung und läuft danach weiter. | 檢查期間索引會暫停，結束後繼續。 |
| `Fits` | Passt | 合適 |
| `Fits narrowly` | Passt knapp | 勉強合適 |
| `Does not fit` | Passt nicht | 不合適 |
| `Checked: %1$s with %2$s, %3$s` | Geprüft: %1$s mit %2$s, %3$s | 已檢查：「%1$s」搭配 %2$s，%3$s |
| `Saved. %s applies from the next indexing round.` | Gespeichert. %s gilt ab der nächsten Indexrunde. | 已儲存。「%s」將從下一輪索引開始套用。 |
| `Nothing was saved. %s stays in force.` | Nichts gespeichert. %s bleibt wirksam. | 未儲存任何變更。「%s」維持生效。 |
| `The downloaded model file was deleted again.` | Die geladene Modelldatei wurde wieder gelöscht. | 為檢查而下載的模型檔案已刪除。 |
| `Memory reserve too thin: %1$s left, %2$s needed.` | Speicherreserve zu knapp: %1$s übrig, %2$s nötig. | 記憶體餘裕過小：剩餘 %1$s，需要 %2$s。 |
| `Not enough memory: %1$s OCR slots need about %2$s, %3$s are available.` | Zu wenig Speicher: %1$s OCR-Slots brauchen etwa %2$s, verfügbar sind %3$s. | 記憶體不足：%1$s 個 OCR 工作槽約需 %2$s，可用 %3$s。 |
| `Not enough memory for the fp32 model: it needs about %1$s, %2$s are available.` | Zu wenig Speicher für das fp32-Modell: Es braucht etwa %1$s, verfügbar sind %2$s. | 記憶體不足以使用 fp32 模型：約需 %1$s，可用 %2$s。 |
| `A test slot was ended for lack of memory.` | Ein Prüf-Slot wurde wegen Speichermangel beendet. | 有一個測試工作槽因記憶體不足而被終止。 |
| `The measurement took longer than %s.` | Die Messung dauerte länger als %s. | 測量時間超過 %s。 |
| `The model could not be downloaded. Check that github.com and release-assets.githubusercontent.com are reachable.` | Das Modell ließ sich nicht herunterladen. Prüfen, ob github.com und release-assets.githubusercontent.com erreichbar sind. | 無法下載模型。請確認可以連線到 github.com 與 release-assets.githubusercontent.com。 |
| `The download took longer than %s.` | Der Download dauerte länger als %s. | 下載時間超過 %s。 |
| `The model file does not match its checksum and was deleted.` | Die Modelldatei passt nicht zu ihrer Prüfsumme und wurde gelöscht. | 模型檔案與其檢查碼不符，已刪除。 |
| `The model file placed on the volume does not match its checksum. Replace or remove it.` | Die auf dem Volume abgelegte Modelldatei passt nicht zu ihrer Prüfsumme. Die Datei ersetzen oder entfernen. | 放在磁碟區上的模型檔案與其檢查碼不符。請替換或移除它。 |
| `Not enough disk space for the fp32 model.` | Zu wenig Platz auf dem Datenträger für das fp32-Modell. | 磁碟空間不足以存放 fp32 模型。 |
| `The available memory could not be read.` | Der verfügbare Speicher ließ sich nicht lesen. | 無法取得可用記憶體容量。 |
| `Findling sees fewer CPU cores or less memory than this profile requires. Standard requires at least 3 cores and 6 GB of memory, Performance at least 6 cores and 12 GB. If the backend container has a memory or CPU limit, that limit counts.` | Findling sieht weniger CPU-Kerne oder weniger Arbeitsspeicher, als dieses Profil verlangt. Standard verlangt mindestens 3 Kerne und 6 GB Arbeitsspeicher, Leistung mindestens 6 Kerne und 12 GB. Ist der Backend-Container begrenzt, zählt diese Grenze. | Findling 偵測到的 CPU 核心數或記憶體少於此設定檔的需求。「標準」至少需要 3 個核心與 6 GB 記憶體，「效能」至少需要 6 個核心與 12 GB。如果後端容器設有記憶體或 CPU 限制，則以該限制為準。 |
| `The check was interrupted by a restart of the backend.` | Die Prüfung wurde durch einen Neustart des Backends unterbrochen. | 檢查因後端重新啟動而中斷。 |
| `The running indexing batch did not end within %s.` | Die laufende Indexstaffel endete nicht innerhalb von %s. | 執行中的索引批次未在 %s 內結束。 |
| `The check stopped with an error.` | Die Prüfung brach mit einem Fehler ab. | 檢查因錯誤而停止。 |
| `The check needs the backend, and it does not answer right now. Nothing was saved.` | Die Prüfung braucht das Backend, und es antwortet gerade nicht. Nichts gespeichert. | 檢查需要後端，但後端目前沒有回應。未儲存任何變更。 |
| `This backend version cannot run the check. Bring both halves of Findling to the same version.` | Diese Backend-Version kann die Prüfung nicht fahren. Beide Hälften von Findling auf dieselbe Version bringen. | 此後端版本無法執行檢查。請將 Findling 的兩個部分更新到相同版本。 |
| `A check is already running. Its result appears here.` | Eine Prüfung läuft bereits. Ihr Ergebnis erscheint hier. | 已有檢查正在進行。結果會顯示在這裡。 |
| `The index is being rebuilt right now. The check is possible afterwards.` | Der Index wird gerade neu aufgebaut. Die Prüfung ist danach möglich. | 索引目前正在重建。重建完成後才能檢查。 |
| `The profile was not saved. Nothing changed.` | Das Profil wurde nicht gespeichert. Es hat sich nichts geändert. | 設定檔未儲存。沒有任何變更。 |
| `The memory guard lowered the profile: chosen %1$s, in force %2$s (%3$s).` | Der Speicherwächter hat das Profil abgesenkt: gewählt %1$s, wirksam %2$s (%3$s). | 記憶體防護機制已調降設定檔：已選「%1$s」，實際生效「%2$s」（%3$s）。 |
| `The fp32 model is not available. The search uses int8.` | Das fp32-Modell ist nicht verfügbar. Die Suche nutzt int8. | 無法使用 fp32 模型。搜尋改用 int8。 |
| `fp32 is set, but Findling sees too little memory for it. The search uses int8.` | fp32 ist gesetzt, aber Findling sieht zu wenig Arbeitsspeicher dafür. Die Suche nutzt int8. | 已設定 fp32，但 Findling 偵測到的記憶體不足。搜尋改用 int8。 |
| `fp32 is only available in Standard and Performance. The search uses int8.` | fp32 gibt es nur in Standard und Leistung. Die Suche nutzt int8. | fp32 僅能在「標準」與「效能」下使用。搜尋改用 int8。 |
| `fp32 stays active under Economy. To go back to int8, choose Standard or Performance and clear the tick.` | fp32 bleibt unter Sparsam aktiv. Zurück zu int8: Standard oder Leistung wählen und das Häkchen entfernen. | 在「節約」下 fp32 仍維持啟用。若要改回 int8，請選擇「標準」或「效能」並取消勾選。 |
| `The fp32 model is being downloaded.` | Das fp32-Modell wird heruntergeladen. | 正在下載 fp32 模型。 |
| `No check yet.` | Noch keine Prüfung. | 尚未檢查。 |
| `Choose a profile and check it on this server. Until then Economy stays in force.` | Ein Profil wählen und auf diesem Server prüfen. Bis dahin bleibt Sparsam wirksam. | 請選擇設定檔並在此伺服器上檢查。在此之前維持「節約」。 |

## Exceptions for the completeness gate G2

Gate G2, today `test_every_catalogue_value_carries_a_wording_of_its_language`, demands that no
value is empty and none equals its English source string. In Chinese eight keys do on purpose.
It is a named list and deliberately not a threshold; every entry carries its reason.

- `Findling`: the name of the app, the same word in every language.
- `PDF`: the proper name of a file format, the same abbreviation in every language.
- `B`, `KB`, `MB`, `GB`, `TB`, `PB`: the unit symbols of the sizes on the admin page, which
  Nextcloud's Traditional Chinese interface writes the English way.

`%1$s (ID %2$s)` is **not** on the list, unlike in every other language of the tree, because
the full width parentheses make the value `%1$s（ID %2$s）` differ from its key.

The list was not guessed. Two runs, in this order:

| run | result |
|---|---|
| no entry for `zh_TW` in the table | `AssertionError: languages without a list of exceptions: ['zh_TW']` |
| empty mapping `"zh_TW": {}` | sixteen findings, eight keys over two files, the first of them `zh_TW.json: 'Findling' is still the English source string` |

The same eight keys with the same reasons stand in `VALUES_THAT_MAY_EQUAL_THEIR_KEY["zh_TW"]` in
`backend/tests/test_admin_ui_contract.py`.

## Machine checks

Run on 15.11.2026 over the two generated files, not by eye:

| Check | Result |
|---|---|
| Key set of `zh_TW.json` equal to `de.json`, in the same order | yes, 366 of 366, missing 0 |
| `zh_TW.js` carries the same values as `zh_TW.json`, form for form | yes (`test_the_two_halves_of_every_language_carry_the_same_values`) |
| Every key of `zh_TW.json` has a row in this file, with the catalogue wording | yes (`test_every_language_table_carries_every_key_with_the_catalogue_wording`) |
| Placeholder parity key against value, over all 96 keys with directives | 0 deviations |
| Plural keys with exactly **one** form | 5 of 5 |
| `pluralForm` equal to the block in section 3 of `docs/l10n-catalogues.md` | yes, in both files |
| U+2014 and U+2013 (dashes) | 0 |
| Emoji and dingbats (`[\U0001f000-\U0001faff☀-➿️]`) | 0 |
| U+00A0, U+202F (protected spaces), U+3000 (ideographic space) | 0 |
| Bare percent signs, a `%` without a recognised directive | 0 in keys and in all forms |
| Pipe characters | 0 in keys and in all forms |
| ASCII double quotes and curly quotes in values | 0 |
| A Han character touching a Latin letter, a digit or `%` without a space | 0 |
| A half width comma, full stop or colon directly after a Han character | 0 |
| Value identical to the English source string | 8, all named above |
| LF, UTF-8 without BOM, final newline | both files and this document, checked byte by byte |
| The caster against the unchanged stock, before the first new file | 16 of 16 shipped files recast byte for byte (`de`, `de_DE`, `es`, `fr`, `it`, `nl`, `pt_PT`, `pt_BR`, each `.json` and `.js`) |
| Entries in `L10N_CATALOGUES` | 18 |
| `cd backend && uv run pytest -q tests/test_admin_ui_contract.py` | 214 passed |
| `cd backend && uv run pytest -q` | 7236 passed, 240 skipped, 5 failed; the five are OCR and HEIC cases of `test_ocr.py` and `test_image_heic.py` that fail the same way on the unchanged `main` on the machine this ran on, because they depend on the Tesseract of the host |
| ruff check, ruff format --check, pyright, vulture | all green |
| The vocabulary gate of `backend/tests/test_public_artifacts.py` over this file | green; the stem it blocks does not occur in Chinese |
| Loading on a running Nextcloud 34.0.5 | `zh_TW` resolves to the catalogue, see "The language code" |
| The CI step "The result page answers in every new language (core lang)", run by hand for `zh_TW` | HTTP 200, `搜尋您的檔案內容` present, the English title absent, `<html lang="zh-TW">` |

What no machine can check is the language. That is the subject of the section below.

## Review

**Drafted on 15.11.2026** with the assistance of Claude (Anthropic) for the contributor who
proposed Chinese support in issue #53, and run against the gates listed under "Machine checks". A
second, independent machine review read every value against its English and German source and
the place it is rendered; its eleven findings (mostly profile names that needed 「」 inside a
sentence) are applied in the table above.

**State of the human review: approved on 20.11.2026.** Unlike the four machine translated
languages of milestone v1.3 (decision E-17-5), this catalogue is not left to the community review
alone: the contributor is a native speaker from Taiwan, reviewed it before the pull request was
opened and approved it as it stands, including the terms below.

**Where the native review looked first**, all kept as they stand:

1. The three profile names 節約, 標準 and 效能. 節約 is the closest word to "Economy" for a mode
   that saves resources; 省資源 or 經濟 are the alternatives.
2. 工作槽 for the OCR slot and 處理程序 for the worker, two technical terms without an
   established Taiwanese UI convention.
3. 輪 for a run (下一輪, 下一輪比對作業), chosen over 執行 because it counts passes.
4. 嵌入 and 重新嵌入 for embedding, the term of the field but not of every administrator.

**Not open for rework:** the single plural form and the rule `nplurals=1; plural=0;`. Whoever
wants to change them refutes the measurement in the section "Plural forms" first.
