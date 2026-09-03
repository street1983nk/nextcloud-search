# Phase 5: Härtung und Store-Einreichung v1.0 - Pattern Map

**Mapped:** 2026-09-03
**Files analyzed:** 24 (15 neu, 9 geändert; die Review-Reste-Positionen aus D-20 sind als Gruppe geführt)
**Analogs found:** 21 / 24

Alle Zeilenangaben stammen aus dem Arbeitsbaum vom 03.09.2026. Sprache der
Codebasis ist Englisch (Kommentare, Docstrings, Testnamen), Betriebsdoku ist
Deutsch. Das gilt für alles Neue unverändert.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.github/workflows/deploy-harp.yml` [NEU] | ci-workflow | batch / lifecycle | `.github/workflows/php.yml` (Rahmen) + `integration.yml:91-141` (Jobrumpf) | role-match |
| `.github/workflows/integration.yml` (Job `search-parity`, Matrix) | ci-workflow | request-response | derselbe Datei: `integration.yml:1099-1123` + `:944-959` + `:973-1009` | exact |
| `.github/actions/setup-test-nc/action.yml` (pgsql, groupfolders, `APP_VERSION`, Bind-Adresse) | ci-composite-action | config | dieselbe Datei: `:70-81`, `:102-122`, `:181-194` | exact |
| `scripts/dev/build_load_corpus.py` [NEU] | utility / generator | file-I/O | `scripts/dev/build_corpus.py` (Erzeuger) + `backend/src/findling/tools/index_status.py:153-164` (CLI) | exact (Erzeugung) / role-match (CLI) |
| `scripts/dev/compose-harp.yaml` [NEU] | config | - | `scripts/dev/compose.yaml` | exact |
| `scripts/ops/hetzner_box.sh` [NEU] | ops-script | request-response (REST) | `scripts/dev/measure_wordlist.sh` (Rahmen) + `scripts/dev/register-exapp.sh:53-81,130-138` (Warteschleife, Geheimnis) | role-match |
| `scripts/ops/rss_sampler.sh` [NEU] | utility / sampler | streaming | `scripts/dev/measure_wordlist.sh` (Rahmen) + `resilience.yml:446-511` (Messregel) | role-match |
| `php/lib/Repair/AppUninstallStep.php` [NEU] | repair-step | event-driven (Lifecycle) | `php/lib/Repair/AppInstallStep.php` | exact |
| `php/lib/Command/PurgeCommand.php` [NEU] | occ-command | batch (destruktiv) | `php/lib/Command/IndexCommand.php` | exact |
| `php/lib/Migration/Version001000Date2026XXXX.php` [NEU, nur falls Schema] | migration | - | `php/lib/Migration/Version001000Date20260904000000.php` | exact |
| `backend/tests/test_store_metadata.py` [NEU] | test (Textgate) | transform | `backend/tests/test_admin_ui_contract.py` (Gate C) | exact |
| `backend/tests/test_lockstep_versions.py` [NEU] | test (Paritätsgate) | transform | `backend/tests/test_allowlist_parity.py` | exact |
| `php/appinfo/info.xml` (Store-Texte EN/DE/FR, Screenshots, 1.0.0, purge-Command, repair-steps/uninstall) | config / store-metadata | - | dieselbe Datei `:9-62` + `backend/appinfo/info.xml:33-62` | exact |
| `backend/appinfo/info.xml` (Store-Texte EN/DE/FR, Screenshots, 1.0.0, image-tag) | config / store-metadata | - | dieselbe Datei `:33-73` | exact |
| `php/lib/Service/ExAppService.php` (Major.Minor-Lockstep) | service | request-response | dieselbe Datei `:282-340` (`adminGet`) | exact |
| `backend/src/findling/api/status.py` (`appVersion` aus `APP_VERSION`) | api-endpoint | request-response | dieselbe Datei `:71-111`, `:137-189` | exact |
| `scripts/dev/register-exapp.sh` (`APP_VERSION`, Routenliste, DI-04-01/02) | dev-script | config | dieselbe Datei `:144-155`, `:183-190` | exact |
| `.github/workflows/docker.yml` (Sec-M7 einmal bauen und per Digest testen, `timeout-minutes`) | ci-workflow | batch | dieselbe Datei `:88-108`, `:201-225` | exact |
| Release-/Signier-Job (neuer Job in `php.yml` oder `.github/workflows/release.yml`) [NEU] | ci-workflow | batch | `php.yml:74-116` (Store-Pfad) + `docs/certificates.md:140-176` (Ablauf und Secret-Regeln) | role-match |
| `docs/performance.md` [NEU] | docs (deutsch) | - | `docs/admin-page.md:1-25` (Ton, Zwei-Leser-Regel) + `docs/ocr.md` (Messbericht) | role-match |
| `docs/uninstall.md` [NEU] | docs (deutsch) | - | `docs/admin-page.md` + `docs/reconcile.md` | role-match |
| `docs/store-listing.md` [NEU] | docs (dreisprachig) | - | `docs/store-identity.md` (Register) | partial |
| `docs/testing.md` (neue Gates eintragen) | docs (englisch) | - | dieselbe Datei `:39-47` (Gate-Tabelle) | exact |
| Review-Reste D-20 (Gruppe, ~25 Positionen in bestehenden Dateien) | mixed | mixed | jeweils die umgebende Datei; siehe Abschnitt "Review-Reste" | exact |

## Pattern Assignments

### `php/lib/Repair/AppUninstallStep.php` (repair-step, event-driven)

**Analog:** `php/lib/Repair/AppInstallStep.php` (67 Zeilen, ganze Datei gelesen)

Das ist der wichtigste Analogtreffer der Phase, weil das Analog genau die Falle
schon behandelt, die Pitfall 1 der Recherche beschreibt: der Install-Step läuft
bei jedem Enable erneut, deshalb hat er eine Absichtsmarke im appconfig, und
genau diese Mechanik ist die empfohlene Form für den Uninstall-Step.

**Imports und Konstruktor** (`AppInstallStep.php:5-45`):
```php
namespace OCA\Findling\Repair;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCP\BackgroundJob\IJobList;
use OCP\IAppConfig;
use OCP\Migration\IOutput;
use OCP\Migration\IRepairStep;
use Psr\Log\LoggerInterface;

class AppInstallStep implements IRepairStep {
	public const FIRST_INDEX_SCHEDULED = 'first_index_scheduled';

	public function __construct(
		private IJobList $jobList,
		private IAppConfig $appConfig,
		private LoggerInterface $logger,
	) {
	}
```

**Marke plus Idempotenz plus "nie werfen"** (`AppInstallStep.php:47-66`), das exakte
Skelett, das der Uninstall-Step spiegelt (Marke prüfen, sonst No-op mit Logzeile,
alles in try/catch, `$output->warning` statt Exception):
```php
	public function getName(): string {
		return 'Schedule the first index of Findling';
	}

	public function run(IOutput $output): void {
		try {
			if ($this->appConfig->getValueBool(Application::APP_ID, self::FIRST_INDEX_SCHEDULED)) {
				$output->info('Findling has already scheduled its first index, leaving it alone.');
				return;
			}

			$this->jobList->add(SchedulerJob::class);
			$this->appConfig->setValueBool(Application::APP_ID, self::FIRST_INDEX_SCHEDULED, true);

			$output->info('Findling will start indexing with the next run of the background jobs.');
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not schedule the first index during the installation', ['exception' => $e]);
			$output->warning('Findling could not schedule its first index. Run "occ findling:index --restart" to start it by hand.');
		}
	}
```

**Tabellennamen kommen aus den Konstanten, nicht abgeschrieben** (gemessen, nicht
geraten):
```php
QueueMapper::TABLE_NAME       // 'findling_queue'         php/lib/Db/QueueMapper.php:35
ScanStatsService::TABLE_NAME  // 'findling_scan_stats'    php/lib/Service/ScanStatsService.php:43
FileStateService::TABLE_NAME  // 'findling_file_state'    php/lib/Service/FileStateService.php:47
```

**Die drei Background-Jobs, die entfernt werden müssen** (Namen aus
`IndexCommand::restart()`, `php/lib/Command/IndexCommand.php:91-99`):
```php
$this->jobList->remove(StorageCrawlJob::class);
$this->jobList->remove(SchedulerJob::class);
// plus SubtreeExpandJob, der in IndexCommand nicht vorkommt: php/lib/BackgroundJobs/SubtreeExpandJob.php
```

**Registrierung in info.xml** (`php/appinfo/info.xml:61`, eine Zeile, Pflicht wegen
des Schema-Patterns für Klassennamen):
```xml
<repair-steps><install><step>OCA\Findling\Repair\AppInstallStep</step></install></repair-steps>
```
Der Uninstall-Block wird in dieselbe Zeile bzw. als `<uninstall>` daneben
gesetzt, ohne umgebenden Zeilenumbruch; `php/appinfo/info.xml:46-52` begründet das
ausdrücklich ("The schema pattern for a PHP class name allows no surrounding
whitespace").

---

### `php/lib/Command/PurgeCommand.php` (occ-command, batch, destruktiv)

**Analog:** `php/lib/Command/IndexCommand.php` (145 Zeilen, ganze Datei gelesen).
Zweitanalog für Ausgabeform und Sicherheitsregeln der Ausgabe:
`php/lib/Command/DiagnoseCommand.php:93-122`.

**Imports und Konstruktor** (`IndexCommand.php:5-45`):
```php
namespace OCA\Findling\Command;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\BackgroundJobs\SchedulerJob;
use OCA\Findling\Repair\AppInstallStep;
use OCP\IAppConfig;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Helper\QuestionHelper;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Question\ConfirmationQuestion;
```

**configure/execute** (`IndexCommand.php:47-80`): Name im Schema `findling:<verb>`,
Lesen ist die Vorgabe, das Zerstörende braucht die ausdrückliche Option:
```php
	protected function configure(): void {
		$this
			->setName('findling:index')
			->setDescription('Show the state of the Findling index, or start it over')
			->addOption('restart', null, InputOption::VALUE_NONE,
				'Queue a fresh crawl of every mount. Expensive: every document is read again.');
	}
```

**Die Bestätigung, exakt zu übernehmen** (`IndexCommand.php:131-144`). Wichtig ist
`!$input->isInteractive() -> true`: CI ruft mit `--no-interaction` (siehe
`integration.yml:963-966`, wo genau dieser Stolperstein dokumentiert ist).
```php
	private function confirm(InputInterface $input, OutputInterface $output): bool {
		if (!$input->isInteractive()) {
			return true;
		}

		$helper = $this->getHelper('question');
		if (!$helper instanceof QuestionHelper) {
			return true;
		}

		$output->writeln('<comment>This queues a crawl of every mount and reads every document of this instance again.</comment>');

		return (bool)$helper->ask($input, $output, new ConfirmationQuestion('Start over? [y/N] ', false));
	}
```

**Ausgabe-Regel aus DiagnoseCommand** (`DiagnoseCommand.php:97-105`): eine
Verweigerung nennt den Fall und niemals den Eingabewert, weil Terminal-Ausgabe
protokolliert wird (T-04-38). Für `findling:purge` heisst das: sagen, was gelöscht
wird (Tabellennamen sind Metadaten, das ist erlaubt), nie einen Pfad oder
Dateinamen.

**Registrierung** (`php/appinfo/info.xml:62`, eine Zeile):
```xml
<commands><command>OCA\Findling\Command\IndexCommand</command><command>OCA\Findling\Command\DiagnoseCommand</command></commands>
```

---

### `backend/tests/test_store_metadata.py` (test, Textgate über beide info.xml)

**Analog:** `backend/tests/test_admin_ui_contract.py` (Gate C, 298 Zeilen, ganze
Datei gelesen). Das ist derselbe Gegenstand in derselben Bauform: ein pytest, der
Nicht-Python-Quellen als Text liest und beurteilt, weil auf der
Entwicklungsmaschine kein PHP existiert.

**Kopf, Pfade und die Dash/Emoji-Muster** (`test_admin_ui_contract.py:33-77`).
Die beiden Dash-Konstanten sind bewusst als Escape geschrieben, damit die
Gate-Datei die Zeichen nicht selbst trägt, die sie fernhalten soll:
```python
from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TEMPLATE = REPO_ROOT / "php" / "templates" / "admin.php"

EM_DASH = "\u2014"
EN_DASH = "\u2013"

_EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\ufe0f]")
```

**Befundsammler statt Assertion pro Datei** (`test_admin_ui_contract.py:128-143`):
jede Funktion gibt eine Liste von Meldungen zurück, die Datei und Grund nennen;
der Test behauptet `== []`:
```python
def scan_prose(name: str, source: str) -> list[str]:
    """Findings that apply to all three files alike: dashes and emoji."""
    violations: list[str] = []

    if EM_DASH in source:
        violations.append(f"{name}: carries an em dash")
    if EN_DASH in source:
        violations.append(f"{name}: carries an en dash")
    if _EMOJI.search(source) is not None:
        violations.append(f"{name}: carries an emoji; every icon on this page is inline SVG")

    return violations
```

**Antivakuitätsklausel und Selbsttests** (`test_admin_ui_contract.py:166-183`,
`:234-298`). Beides ist Pflicht, nicht Zierde: ein Gate, dessen einzige Aussage
"der Baum ist sauber" ist, bleibt grün, wenn jemand seinen Rumpf löscht.
```python
def test_the_three_files_of_the_page_exist() -> None:
    # The anti vacuity clause. Every scanner below returns an empty list for a
    # file that is not there, so a gate that lost its files would look perfect.
    missing = [path.name for path in (TEMPLATE, STYLESHEET, SCRIPT) if not path.is_file()]

    assert missing == []


def test_the_clean_samples_are_clean() -> None:
    assert scan_prose("sample.js", _CLEAN_SCRIPT) == []


def test_a_dash_and_an_emoji_are_reported() -> None:
    assert len(scan_prose("sample.js", _CLEAN_SCRIPT + "// a dash " + EM_DASH + "\n")) == 1
    assert len(scan_prose("sample.js", _CLEAN_SCRIPT + "// a face \U0001f600\n")) == 1
```

**Was dieses neue Gate zusätzlich zu prüfen hat** (aus Pitfall 9 und Pattern 4 der
Recherche, als Zeilen im selben Stil): `summary` je Sprache unter 128 Zeichen,
`lang`-Werte nur aus `de`/`fr`/`en` (kein `de_DE`), jede Screenshot-URL `https` und
unter 256 Zeichen, kein leeres `description`, und die Nachzieh-Regel: fehlt eine
der drei Sprachen an einem Element, das die anderen haben, ist der Test rot.
Zielfelder sind `php/appinfo/info.xml`, `backend/appinfo/info.xml` und `README.md`.

---

### `backend/tests/test_lockstep_versions.py` (test, Paritätsgate über zwei Dateien)

**Analog:** `backend/tests/test_allowlist_parity.py` (114 Zeilen, ganze Datei
gelesen). Gleicher Gegenstand: zwei Quellen, die dasselbe sagen müssen, per Text
verglichen, mit Meldung, die die Seite nennt.

**Quelle als Text lesen, weil sie nicht importierbar ist**
(`test_allowlist_parity.py:37-51`):
```python
PHP_STORAGE_SERVICE = Path(__file__).resolve().parents[2] / "php" / "lib" / "Service" / "StorageService.php"


def _php_mimetypes() -> set[str]:
    """The ALLOWED_MIMETYPES constant of the PHP companion, read out of its source."""
    source = PHP_STORAGE_SERVICE.read_text(encoding="utf-8")
    block = re.search(r"const ALLOWED_MIMETYPES = \[(.*?)\];", source, re.DOTALL)
    assert block is not None, "the ALLOWED_MIMETYPES constant is no longer where this gate looks for it"
    return set(re.findall(r"'([a-z0-9.+/-]+)'", block.group(1)))
```

**Drift in beide Richtungen, mit Seitenangabe** (`test_allowlist_parity.py:54-64`,
`:83-90`): genau die Form, die der Lockstep-Vergleich braucht (php-`<version>`,
backend-`<version>`, backend-`<image-tag>`, plus der git-Tag-Vergleich, den
`docker.yml:88-108` schon in bash führt):
```python
def _drift(python_types: set[str], php_types: set[str]) -> list[str]:
    return [f"{name} is missing from the PHP crawl" for name in sorted(python_types - php_types)] + [
        f"{name} is missing from the Python extractor" for name in sorted(php_types - python_types)
    ]


def test_the_message_names_the_type_and_the_side_it_is_missing_from() -> None:
    # The self test of the gate, and the answer to "would this actually go red".
    assert _drift({"image/webp"}, set()) == ["image/webp is missing from the PHP crawl"]
```

**Die bash-Fassung derselben Prüfung, die es schon gibt** (`docker.yml:88-108`), aus
der die Extraktionsausdrücke wörtlich übernommen werden können:
```bash
backend_version=$(sed -n 's:.*<version>\(.*\)</version>.*:\1:p' backend/appinfo/info.xml)
php_version=$(sed -n 's:.*<version>\(.*\)</version>.*:\1:p' php/appinfo/info.xml)
[ "${backend_version}" = "${tag}" ] || { echo "backend version does not match the git tag"; fail=1; }
```

---

### `.github/workflows/deploy-harp.yml` (ci-workflow, install/run/uninstall über NC 32/33/34)

**Analoge:** Rahmen aus `.github/workflows/php.yml:1-34`, Jobrumpf aus
`.github/workflows/integration.yml:90-141`.

**Workflow-Rahmen** (`php.yml:1-34`): Pfadfilter, `permissions: contents: read`,
`concurrency` mit `cancel-in-progress`, und gepinnte Fremdstände als `env`. Die
Digest-Pinnung des HaRP-Images gehört genau an diese Stelle, nach dem Muster
`APPSTORE_SHA`:
```yaml
on:
  push:
    paths:
      - 'php/**'
      - 'backend/appinfo/**'
      - '.github/workflows/php.yml'

permissions:
  contents: read

concurrency:
  group: php-${{ github.ref }}
  cancel-in-progress: true

env:
  # Pinned commit in nextcloud/appstore, deliberately not master.
  APPSTORE_SHA: 5c4373d7d026a8f7c7838cc9990fecaf19e8e682
```

**Jobrumpf mit Matrix, Deadline und der zwingenden Checkout-Reihenfolge**
(`integration.yml:91-141`). Die Kommentarzeile `:101-104` nimmt die
Matrix-Erweiterung dieser Phase ausdrücklich vorweg:
```yaml
  walking-skeleton:
    name: walking-skeleton
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        # One server version only. The full stable32 / stable33 / stable34 matrix
        # becomes a scheduled run in phase 5, otherwise pull request feedback
        # gets slow.
        server-version: ['stable34']
        php-version: ['8.2']

    steps:
      # These two checkouts stay in the job and stay in this order. actions/checkout
      # empties its target directory, so the server checkout at the workspace root
      # has to come first.
      - name: Check out nextcloud/server
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v5.0.0
        with:
          repository: nextcloud/server
          ref: ${{ matrix.server-version }}
          submodules: recursive

      - name: Check out findling
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v5.0.0
        with:
          path: findling-src

      - name: Set up the test Nextcloud with both halves and register the ExApp
        uses: ./findling-src/.github/actions/setup-test-nc
        with:
          server-version: ${{ matrix.server-version }}
          php-version: ${{ matrix.php-version }}
          exapp-secret: ${{ env.EXAPP_SECRET }}
          exapp-port: ${{ env.EXAPP_PORT }}
```

**Achtung, Sec-M8 betrifft genau diese Zeilen:** `integration.yml:124` benutzt
`actions/checkout@3d3c42e5...`, `setup-test-nc/action.yml:84` benutzt
`actions/checkout@fbc6f399...`, beide mit dem Kommentar `# v5.0.0`. Ein neuer
Workflow darf nicht den dritten Stand einführen; die Vereinheitlichung ist Teil
von D-20.

**Was der Daemon-Registrierung ersetzt wird** (`setup-test-nc/action.yml:210-214`,
der heutige `manual-install`-Pfad, den PKG-03 ablöst):
```bash
timeout 10 ./occ app_api:daemon:register --net host \
  manual_install "Manual Install" manual-install http localhost http://localhost:8080
```

**Bestehendes Beweismuster für "die Messung darf nicht fehlen"**
(`resilience.yml:502-511`): ein Job, der grün wird, ohne dass etwas gemessen wurde,
ist der Fehlerfall, den Pitfall 3 als Warnsignal nennt ("ein Deploy-Job, der grün
wird, ohne dass `docker ps` den ExApp-Container zeigt"):
```bash
if [ -z "${before}" ] || [ -z "${after_first}" ] || [ -z "${after_second}" ]; then
  echo "docker stats returned nothing, so the memory figures do not exist"
  exit 1
fi
```

---

### `.github/workflows/integration.yml`, neuer Job `search-parity` (ci-workflow, request-response)

**Analog:** derselbe Datei, Job `index-search-e2e`. Alles, was der Paritätstest
braucht, steht dort bereits: Nutzer anlegen, Instanz leeren, Korpus einspielen,
Share über die OCS-API, Warteschleife bis alles beurteilt ist, und der
Mengenvergleich als Positiv-plus-Negativprobe.

**Fixture-Aufbau: Instanz leeren, zwei Nutzer, Korpus** (`integration.yml:916-934`):
```bash
./occ config:system:set skeletondirectory --value=''
rm -rf data/admin/files/* data/admin/files/.[!.]* 2>/dev/null || true
OC_PASS="${OWNER_PASS}" ./occ user:add --password-from-env "${OWNER_USER}"
OC_PASS="${COLLEAGUE_PASS}" ./occ user:add --password-from-env "${COLLEAGUE_USER}"
./occ files:scan --all
echo "files on the instance before the corpus: $(find data/*/files -type f 2>/dev/null | wc -l)"
```

**Share anlegen, Szenario 2 und 6 wörtlich** (`integration.yml:944-959`). `-s` ohne
`-f` ist Absicht, die `statuscode`-Prüfung ist die Antivakuitätsklausel des
Szenarios, und der `files:scan` danach ist der Grund, aus dem ein Share überhaupt
in der Mount-Cache-Sicht ankommt:
```bash
curl -s -u "${OWNER_USER}:${OWNER_PASS}" \
  -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
  -d "path=/corpus/${SHARED_FILE}" \
  -d 'shareType=0' \
  -d "shareWith=${COLLEAGUE_USER}" \
  -d 'permissions=1' \
  'http://localhost:8080/ocs/v2.php/apps/files_sharing/api/v1/shares' | tee share.json
jq -e '.ocs.meta.statuscode == 200' share.json > /dev/null \
  || { echo "::error::the share was not created, so the permission case would prove nothing"; cat share.json; exit 1; }
./occ files:scan --all
```

**Der OCS-Suchaufruf als Funktion, plus eine `fail`-Funktion je Szenario**
(`integration.yml:1099-1123`). Das ist die Vorlage für die beiden Aufrufe je
Marker; für den Paritätstest wird der Provider parametrisiert (`files` und
`findling`) und `--data-urlencode 'limit=100'` ergänzt (ohne `limit` vergleicht der
Test zwei auf fünf gekürzte Listen, siehe Pattern 2 der Recherche):
```bash
search() {
  curl -sfS -G -u "${COLLEAGUE_USER}:${COLLEAGUE_PASS}" \
    -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
    --data-urlencode "term=$1" \
    'http://localhost:8080/ocs/v2.php/search/providers/findling/search' -o "$2"
}
fail() { echo "::error::$1"; cat "$2"; exit 1; }

search 'Genehmigung' colleague-shared.json
jq -e '.ocs.data.entries | length == 1' colleague-shared.json > /dev/null \
  || fail "the second user does not find the file that was shared with him" colleague-shared.json
```

**Die Warteschleife mit Deadline und laufender Ausgabe** (`integration.yml:973-1009`),
unverändert übernehmbar, weil der Paritätstest erst vergleichen darf, wenn jede
Fixture-Datei ein Verdikt hat:
```bash
expected=$(( EXPECTED_INDEXED + EXPECTED_SKIPPED + EXPECTED_FAILED ))
deadline=$(( $(date +%s) + DRAIN_TIMEOUT ))
while :; do
  ...
  echo "draining: open=${open} indexed=${indexed} skipped=${skipped} failed=${failed}"
  if [ "${open}" -eq 0 ] && [ "${judged}" -ge "${expected}" ]; then
    echo "the queue is empty and ${judged} files have a verdict"
    break
  fi
  if [ "$(date +%s)" -ge "${deadline}" ]; then
    echo "::error::the crawl did not finish within ${DRAIN_TIMEOUT} seconds"
    exit 1
  fi
  sleep 5
done
```

**Crawl anstossen, mit den beiden dokumentierten Stolpersteinen**
(`integration.yml:961-971`):
```bash
# --no-interaction: occ treats this shell as interactive, so the restart
# confirmation would default to No and the queue would stay empty.
./occ findling:index --restart --no-interaction
timeout 60 ./occ background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once
# stop_after with an underscore. The dashed spelling does not exist.
timeout 120 ./occ background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop_after 60
```

**Der symmetrische Mengenvergleich selbst** hat im Repo kein Analog in bash; die
Recherche gibt ihn als Python-Schnipsel vor (05-RESEARCH.md, Abschnitt "Code
Examples"). Wo er als Python-Datei landet, gilt die Regel aus
`test_allowlist_parity.py:54-64`: `missing` und `extra` getrennt melden und
getrennt benennen.

---

### `.github/actions/setup-test-nc/action.yml` (ci-composite-action, Erweiterung)

**Analog:** dieselbe Datei. Vier Stellen sind zu erweitern, jede hat dort ihr
Muster:

**Eingaben mit Begründung und Vorgabewert** (`:14-63`), Vorlage für ein neues
`groupfolders`-Flag und den `pgsql`-Dialekt:
```yaml
  database:
    description: >-
      Dialect handed to maintenance:install, sqlite or mysql. ...
    required: false
    default: sqlite
```

**Extensions-Liste, bewusst ohne Verzweigung nach Eingabe** (`:70-81`) - `pgsql,
pdo_pgsql` gehören hier hinzu, nicht in einen bedingten Zweig:
```yaml
        # pdo_mysql and mysqli are installed unconditionally although a sqlite
        # run never touches them: an extension list that depends on an input is
        # a second place where the dialect is decided.
        extensions: mbstring, iconv, fileinfo, intl, sqlite, pdo_sqlite, mysqli, pdo_mysql, gd, zip
```

**Installationszweig plus Beweis des tatsächlichen Dialekts** (`:102-122`):
```bash
./occ config:system:get dbtype   # printed rather than assumed
```

**`APP_VERSION` wird hier schon gesetzt** (`:181-194`), das ist der Ort für D-11 auf
der CI-Seite; `register-exapp.sh:149` ist der Zwilling für die Dev-Maschine:
```bash
export APP_VERSION="${{ inputs.exapp-version }}"
```
Achtung: `exapp-version` steht dort noch auf dem Vorgabewert `'0.1.0'`
(`action.yml:60-63`), während beide info.xml auf `0.3.0` stehen. Für die
Lockstep-Prüfung muss dieser Vorgabewert aus der info.xml kommen oder vom Job
gesetzt werden, sonst schlägt das neue Gate in CI aus dem falschen Grund an.

**Sec-L7 betrifft genau diese Datei** (`:106` ff.): `inputs.*` wird direkt in `run:`
interpoliert. Da diese Phase neue Eingaben hinzufügt, ist die Härtung (Werte über
`env:` in die Shell geben) hier fällig, nicht später.

---

### `scripts/dev/build_load_corpus.py` (utility/generator, file-I/O)

**Analog:** `scripts/dev/build_corpus.py` (1181 Zeilen; gelesen: Kopf `:1-79`,
Registrierung und `main` `:1110-1181`; Funktionsinventar per grep). Zweitanalog für
die CLI: `backend/src/findling/tools/index_status.py:153-164`.

**Imports und Determinismus-Fundament** (`build_corpus.py:53-79`): stdlib-first,
Pillow als bereits gepinnte Ausnahme, feste Ids statt Zufall:
```python
from __future__ import annotations

import hashlib
import io
import struct
import zipfile
import zlib
from collections.abc import Sequence
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CORPUS_DIR = Path(__file__).resolve().parents[2] / "testdata" / "corpus"

# Fixed document id, so a rebuild produces the same encrypted PDF byte for byte.
DOC_ID = hashlib.md5(b"findling-reference-corpus", usedforsecurity=False).digest()
```

**Reproduzierbares ZIP und feste Zeitstempel** (`build_corpus.py:306-309`,
`_reproducible_zip`): DOCX/XLSX/ODT des Lastkorpus erben das, sonst ist der Korpus
nicht reproduzierbar:
```python
ZIP_TIMESTAMP = (2026, 9, 1, 12, 0, 0)

def _reproducible_zip(parts: dict[str, str], *, stored_first: str | None = None) -> bytes:
```

**Schrift per SHA-256 festgenagelt und Glyphen-Assert** (`build_corpus.py:471-524`):
für die Scan-Seiten des Lastkorpus unverändert gültig, weil jede gerenderte Seite
aus genau einer Schrift kommen muss:
```python
FONT_DIR = Path(__file__).resolve().parents[2] / "testdata" / "fonts"
DEJAVU_SANS = FONT_DIR / "DejaVuSans.ttf"
GLYPH_PROBE = "Strasse Jänner Grundstücksverkehrsgenehmigung"

def _font(size: int) -> ImageFont.FreeTypeFont:
    digest = hashlib.sha256(payload).hexdigest()   # refuses to render if it moved
```

**Prüfungen vor dem ersten Byte, dann schreiben mit Prüfsumme je Datei**
(`build_corpus.py:1163-1181`). Das ist genau die Form, die D-02/das Threat-Register
für "synthetisch belegt statt behauptet" verlangt: Seed und Prüfsumme über die
Dateiliste ausgeben:
```python
def main() -> int:
    # Both checks run before the first byte is written.
    _assert_every_glyph_exists(GLYPH_PROBE)
    _assert_terms_stand_in_one_file(FILES)

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for name, payload in FILES.items():
        target = CORPUS_DIR / name
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        print(f"{name} bytes={len(payload)} sha256={digest}")
    print(f"files={len(FILES)} total bytes={sum(len(payload) for payload in FILES.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Unterschied, der bewusst neu ist:** `build_corpus.py` hält alle Nutzlasten als
`FILES`-Dict im Speicher (`:1117-1160`). Für 20 GB ist das unmöglich; der neue
Generator schreibt streamend und hält nur die laufende Prüfsumme. Die
Verteilungstabelle steht in 05-RESEARCH.md, Pitfall 5.

**CLI-Muster** (`index_status.py:153-164`), inklusive der Regel, dass der
Rückgabewert 0 auch für den leeren Fall gilt:
```python
    parser = argparse.ArgumentParser(description="Report the operating state of one Findling volume as JSON.")
    parser.add_argument("--db", type=Path, required=True, help="path of state.db inside APP_PERSISTENT_STORAGE")
    parser.add_argument("--index", type=Path, default=None, help="index directory, by default next to the database")
    args = parser.parse_args(argv)

    report = collect(args.db, index_directory(args.db, args.index))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0
```

---

### `scripts/ops/rss_sampler.sh` und `scripts/ops/hetzner_box.sh` (ops-scripts)

**Analog (Rahmen):** `scripts/dev/measure_wordlist.sh` (66 Zeilen, ganze Datei
gelesen). POSIX `sh`, `set -eu`, Argumentvalidierung mit eigener Fehlermeldung und
Exitcode 2, Werkzeugprüfung mit Klartext, Pfadauflösung über `CDPATH=`:
```sh
#!/bin/sh
set -eu

VARIANT="${1:-full}"

case "$VARIANT" in
    full | nouns) ;;
    *)
        echo "measure_wordlist: variant has to be full or nouns, got '$VARIANT'" >&2
        exit 2
        ;;
esac

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)

if ! command -v docker >/dev/null 2>&1; then
    echo "measure_wordlist: docker is required, there is no Debian word list on this machine" >&2
    exit 1
fi
```

**Warteschleife mit Zähler und sprechendem Abbruch** (`register-exapp.sh:68-81`),
Vorlage für "warte auf die Box", "warte auf AIO", "warte auf den ExApp-Container":
```sh
printf 'waiting for %s\n' "${NEXTCLOUD_URL}"
i=0
while [ "${i}" -lt 60 ]; do
	if curl -sf "${NEXTCLOUD_URL}/status.php" >/dev/null 2>&1; then
		break
	fi
	i=$((i + 1))
	sleep 2
done
if [ "${i}" -ge 60 ]; then
	printf 'nextcloud did not answer on %s/status.php\n' "${NEXTCLOUD_URL}" >&2
	exit 1
fi
```

**Geheimnis-Behandlung** (`register-exapp.sh:53-60`, `:128-138`): erzeugen statt
festschreiben, mit `umask 077` schreiben, nie ins Repo. Gilt für `HCLOUD_TOKEN`
(nur aus der Umgebung lesen, nie loggen) und den HaRP-`HP_SHARED_KEY`:
```sh
new_secret() {
	if command -v openssl >/dev/null 2>&1; then
		openssl rand -hex 16
		return
	fi
	od -vAn -N16 -tx1 /dev/urandom | tr -d ' \n'
}

(
	umask 077
	printf '%s\n' "${BACKEND_SECRET}" >"${SECRET_FILE}"
)
```

**Messregel für den Sampler** (`resilience.yml:446-511`): der bestehende
Messschritt nimmt `docker stats --no-stream --format '{{.MemUsage}}'` und prüft
ausdrücklich, dass eine Zahl da ist. Der neue Sampler ersetzt die Quelle
(`memory.stat` `anon`), behält aber die Regel: eine fehlende Messung ist ein
Fehlschlag, eine schlechte Zahl ist ein Ergebnis.
```bash
before=$(docker stats --no-stream --format '{{.MemUsage}}' findling_measure)
echo "${MEASURE_PREFIX} rss before-first-search ${before}"
...
if [ -z "${before}" ] || ...; then
  echo "docker stats returned nothing, so the memory figures do not exist"
  exit 1
fi
```
Der `MEASURE_PREFIX` ist selbst ein Muster: jede Messzeile trägt ein festes
Präfix, damit sie aus einem Joblog herausgefiltert werden kann. Für
`docs/performance.md` ist das die Brücke zwischen CSV und Bericht.

**Kill-Resume-Drill als Vorbild für D-05** (`resilience.yml:148-332`): Container
mitten im Lauf töten (`:201` `kill -9`), Zähler im Moment des Kills protokollieren
(`:210`), auf demselben Volume neu starten (`:218-227`), danach behaupten, dass
nichts verloren und nichts doppelt ist (`:286-332`). Der ARM-Lauf spielt dasselbe
Skript mit `docker kill` auf echter Hardware durch.

---

### `scripts/dev/compose-harp.yaml` (config)

**Analog:** `scripts/dev/compose.yaml` (49 Zeilen, ganze Datei gelesen). Zu erben
sind: `name:` als Projektname, das Pinnen des Server-Images auf dieselbe Linie wie
die CI (`nextcloud:34.0.3-apache`, Kommentar `:14-16`), `FINDLING_PORT` als
überschreibbarer Port, `extra_hosts: host.docker.internal:host-gateway` und der
Bind-Mount, dessen Verzeichnisname exakt die App-Id sein muss:
```yaml
name: findling-dev

services:
  app:
    image: nextcloud:34.0.3-apache
    container_name: findling-nextcloud
    ports:
      - "${FINDLING_PORT:-8080}:80"
    environment:
      NEXTCLOUD_TRUSTED_DOMAINS: "localhost host.docker.internal"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - nextcloud:/var/www/html
      # The directory name has to be exactly the app id, otherwise the class
      # autoloader never finds the provider and the app stays invisible.
      - ../../php:/var/www/html/custom_apps/findling
```
Neu und ohne Analog im Repo: der HaRP-Dienst mit `/var/run/docker.sock` und der
Digest-Pinnung; Vorlage dafür ist der `docker run`-Block in 05-RESEARCH.md,
Pattern 1.

---

### `php/appinfo/info.xml` und `backend/appinfo/info.xml` (store-metadata)

**Analog:** die beiden Dateien selbst. Drei Muster sind zwingend zu erben.

**Elementreihenfolge und der Grund für die einzeiligen Blöcke**
(`php/appinfo/info.xml:46-52`):
```xml
	<!--
		The two blocks below sit in the order the store schema prescribes, which
		is: dependencies, background jobs, the repair block, two factor
		providers, commands. Each of them is written on one line on purpose. The
		schema pattern for a PHP class name allows no surrounding whitespace, so
		an indented class name on its own line fails the validation.
	-->
	<repair-steps><install><step>OCA\Findling\Repair\AppInstallStep</step></install></repair-steps>
	<commands><command>OCA\Findling\Command\IndexCommand</command><command>OCA\Findling\Command\DiagnoseCommand</command></commands>
```
Per XSD-Sequenz aus der Recherche gehört `screenshot` zwischen `repository` und
`dependencies`, also VOR den heutigen `dependencies`-Block in `:42-45`.

**Versionskommentar als Vertrag** (`php/appinfo/info.xml:26-33` und
`backend/appinfo/info.xml:17-31`): jeder Bump schreibt hin, warum er passiert, und
nennt die drei Stellen, die zusammenpassen müssen. Der 1.0.0-Bump erbt diese
Pflicht.
```xml
	<!--
		Both halves of Findling carry the same major and minor version, so that
		nobody ends up with a companion app and a backend that disagree about
		the protocol between them. ...
	-->
	<version>0.3.0</version>
```

**Privacy-Absatz, der schon ehrlich ist** (`backend/appinfo/info.xml:37-52`): das
ist die Vorlage für den Privacy-Block aus D-12 in allen drei Sprachen, und es ist
auch die Lösung von Sec-L1, weil die PHP-Fassung (`php/appinfo/info.xml:13-25`)
den gespeicherten Dokumenttext heute nicht nennt:
```
What is stored, so that nobody has to guess: the text extracted from every
indexed document is kept in this app's own volume, because the short excerpts
shown under a search result are cut out of it on demand. A backup of that
volume, including the ones an all-in-one setup takes, therefore contains the
text of your indexed documents. None of it is sent anywhere.
```

**Der Store-Validierungspfad, der beide Dateien schon prüft** (`php.yml:97-103`),
also der Ort, an dem die dreisprachigen Blöcke automatisch mitgeprüft werden:
```bash
for f in php/appinfo/info.xml backend/appinfo/info.xml; do
  xsltproc "${RUNNER_TEMP}/pre-info.xslt" "$f" | xmllint --noout --schema "${RUNNER_TEMP}/info.xsd" -
done
```

---

### `php/lib/Service/ExAppService.php` (service, request-response, Lockstep-Prüfung)

**Analog:** `adminGet` in derselben Datei (`:282-340`). Die vier Fehlerfälle in
dieser Reihenfolge sind das Muster, an das die Versionsabfrage andockt: AppAPI
liefert bei Transportfehlern ein Array statt eines Response-Objekts, 4xx/5xx
kommen als normale Antwort, ein 2xx verspricht keinen parsebaren und keinen
begrenzten Body.
```php
	public function adminGet(string $path, string $userId, array $params): ?array {
		$appApi = $this->publicFunctions($userId);
		if ($appApi === null) {
			return null;
		}

		$response = $appApi->exAppRequest(
			Application::BACKEND_APP_ID, $path, $userId, 'GET', $params,
			['timeout' => self::ADMIN_REQUEST_TIMEOUT_SECONDS],
		);

		// Case 1 first, always: AppAPI catches every transport exception and
		// hands back an array, so a stopped backend arrives at this line.
		if (is_array($response)) {
			$this->logger->warning('Findling: backend unreachable for the admin page', [
				'path' => $path, 'error' => $response['error'] ?? 'unknown',
			]);
			return null;
		}
		// Case 2: 4xx and 5xx arrive as an ordinary response object.
		if ($response->getStatusCode() >= 400) { ... return null; }
		// Case 3: bounded body before the parser sees it.
		if (!is_string($responseBody) || strlen($responseBody) > self::MAX_BODY_BYTES) { ... return null; }
		// Case 4.
		$decoded = json_decode($responseBody, true);
		if (!is_array($decoded)) { ... return null; }

		return $decoded;
	}
```

**Konstanten mit Begründung, nicht als Zahl im Code** (`:64-143`): die
Lockstep-Prüfung bringt bestenfalls keine neue Konstante mit, aber wenn doch, dann
in dieser Form (privater `const` mit Absatz darüber).

**Die eigene Version holt die PHP-Seite über `IAppManager`** (`use OCP\App\IAppManager;`,
`:9`), also über eine Abhängigkeit, die schon injiziert ist. Die Gegenseite kommt
aus `/status` (siehe nächster Abschnitt); `info.xml` kann keine App-zu-App-Abhängigkeit
erklären, was `php/appinfo/info.xml:2-8` und `ExAppService.php:342-349` beide
ausdrücklich festhalten.

---

### `backend/src/findling/api/status.py` (api-endpoint, `appVersion` melden)

**Analog:** dieselbe Datei. Zwei Muster:

**Antwortmodell mit Vorgabewerten für jedes Feld** (`:71-111`):
```python
class StatusResponse(BaseModel):
    """The operating state of one container.

    Every field defaults, so the answer for a container that has nothing yet is
    the same shape as the answer for one that has been running for a month.
    """

    indexed: int = 0
    ...
    indexVersion: int = 0
    analyzerVersion: int = 0
    wordlistHash: str = ""
    note: str = ""
```
`appVersion: str = ""` gehört hier hinein, camelCase wie die Nachbarn, und ist
etwas anderes als `indexVersion`/`analyzerVersion`, die Index-Formatmarken sind
(`:114-126`, `:177-178`).

**Wo ein Wert aus der Umgebung statt aus der Datenbank kommt** (`:137-154`,
`_volume()`): das ist der Zweig, in dem `APP_VERSION` gelesen wird, denn er
antwortet auch für einen Container ohne Zustandsdatenbank:
```python
def _volume() -> StatusResponse:
    """Everything this container can say without opening the state database."""
    resolved = settings()
    free, total = resources.disk_bytes()
    return StatusResponse(
        lowDisk=resources.low_disk(),
        diskFreeBytes=free,
        diskTotalBytes=total,
        indexBytes=index_bytes(resolved.index_dir),
        maxFileBytes=resolved.max_file_bytes,
    )
```

**Jedes Feld wird namentlich gesetzt, kein Spread** (`:157-189`, mit Begründung
T-04-06 im Docstring). Der Test dazu ist `backend/tests/test_status_endpoint.py`,
das Gate für die Privatheitsgrenze steht in `docs/testing.md:47`.

---

### `docs/performance.md`, `docs/uninstall.md` (docs, deutsch)

**Analog:** `docs/admin-page.md:1-25`. Ton, Adressatenregel und Leitsatz sind dort
gesetzt und für einen Messbericht wie für eine Deinstallationsdoku direkt
übernehmbar:
```
# Die Statusseite: welche Zahl woher kommt und was die vier Schalter tun

Sie ist für zwei Leser geschrieben. Für den Admin, der eine Zahl auf der Seite
nachrechnen will, bevor er ihr glaubt, ... Und für den Entwickler, der in einem
Jahr auf eine Zahl stösst, die nicht zu einer anderen passt, und sonst annehmen
müsste, das sei ein Fehler.
```

**Zweitanalog für "was ein Beweis nicht beweist"** (`docs/testing.md:75-121`): jede
Aussage wird mit ihrer Grenze aufgeschrieben. Für `docs/performance.md` ist das die
Pflicht, `memory.peak` und den File-Cache-Anteil neben die `anon`-Zahl zu legen und
zu erklären, warum die Store-Zahl aus `anon` kommt (Pitfall 10). Für
`docs/uninstall.md` ist es die Pflicht, die Versionsabhängigkeit der Checkbox zu
nennen (Pitfall 2) und zu sagen, was `--rm-data` nicht mitnimmt (das Image bleibt
liegen, siehe Runtime State Inventory).

**Store- und Signierdoku** (`docs/certificates.md:140-176`) ist das Analog für den
Release-Abschnitt: Befehl, dann Secret-Regeln, dann Checkliste vor der Abgabe:
```bash
php nextcloud/occ integrity:sign-app --privateKey=findling.key --certificate=findling.crt --path=<php-app-dir>
```
```
- Write the secret to a file under $RUNNER_TEMP, never into the checkout, and remove
  it in a step that runs even when the job fails.
- The signing job runs only on tags from the default branch, never on pull requests
  from forks.
```

---

### Review-Reste aus D-20 (Gruppe, Änderungen in bestehenden Dateien)

Diese Positionen brauchen kein fremdes Analog: das Muster ist jeweils die
umgebende Datei, und die Recherche nennt Datei und Zeile. Was für alle gilt:

| Position | Ort | Pattern, dem die Änderung folgt |
|----------|-----|--------------------------------|
| DI-04-03 Skip-Verdikte an die NC-Seite | `php/lib/Controller/QueueController.php:154-182` (`acknowledgeDocuments`), `php/lib/Service/FileStateService.php:209` (`record`) | Verdikt und Queue-Zeile in einer Transaktion, Kommentar `QueueController.php:141-143`; Reason-Codes stehen in `FileStateService::REASONS` (`:95`) und `STATE_REASONS` (`:143`), das Drift-Gate dazu ist `backend/tests/test_extract_errors.py` |
| DI-04-04 Versionsmarken nach Rebuild neu stempeln | `php/lib/Command/IndexCommand.php:91-99` (`restart`), Marken in `backend/src/findling/api/status.py:177-178` | `restart()` löscht die Marke, entfernt beide Jobs und legt den Scheduler neu an; das Neustempeln gehört in dieselbe Methode bzw. in den Container-Zweig, der `read_meta` schreibt |
| Gruppe-B-IN-03 `failed(repeatedly_stuck)` erreicht die Container-DB nie | `php/lib/Service/QueueService.php:151`, `php/lib/Db/QueueMapper.php:487`, `backend/.../reconcile.py:364` | Vor dem Volllauf beheben (Empfehlung der Recherche); Muster ist die Verdikt-Übergabe oben |
| Perf-LOW `CHUNK_SIZE`, `_pending_bytes`-Vollkopie | `backend/src/findling/nc/client.py:88`, `index/writer.py:177,220` | Beide sind auf 20 GB spürbar, gehören also vor den ARM-Lauf |
| IN-06 `_OPEN`/`_MARKS` ohne Lock | `backend/src/findling/api/resources.py:58-59,156-194` | mittlerer Aufwand, einziger nicht kosmetischer Rest der Phase-4-Infos |
| IN-01..IN-05, IN-07 | `store/repo.py:915`, `php/l10n/de.json:10`, `templates/admin.php:191` gegen `js/admin.js:318`, `PathResolverService.php:204`, `Settings/Section.php:22-27`, `ExclusionService.php:207-225` | Kleinteilig, in Sammelplänen bündeln; Gate C (`test_admin_ui_contract.py`) hält Template, CSS und JS mit |
| Sec-M7 Smoke-Test prüft Build A, ghcr bekommt Build B | `.github/workflows/docker.yml:122` gegen `:204` | Einmal bauen, per Digest pushen, `pull @digest`, Smoke gegen den Digest; das Digest-Handling existiert schon in `:214-225` |
| Sec-M8 Action-SHA-Kommentare | `integration.yml:124` (`3d3c42e5`) gegen `setup-test-nc/action.yml:84` (`fbc6f399`), beide `# v5.0.0` | Vereinheitlichen und die Prüfung skripten |
| Sec-L8 zwei `setup-uv`-Majors | `python.yml` (`@20cfd1bf # v10.0.1`) gegen `setup-test-nc/action.yml:149` (`@d0cc045d # v6`) | Exakte Version pinnen, Owner-Regel |
| Perf-LOW `timeout-minutes` fehlt | `docker.yml`, `php.yml`, `python.yml`, `resilience.yml` | Vorlage: `integration.yml:97` mit Begründung im Kommentar `:94-96` |

## Shared Patterns

### Textgates über Nicht-Python-Quellen
**Quelle:** `backend/tests/test_admin_ui_contract.py` (Gate C), `backend/tests/test_allowlist_parity.py`, `backend/tests/test_readonly_gate.py` (Gate A), `backend/tests/test_php_trust_boundary.py` (Gate B)
**Apply to:** `test_store_metadata.py`, `test_lockstep_versions.py`, jedes neue Gate der Phase
Drei Eigenschaften sind Pflicht, alle drei sind in `docs/testing.md:30-37`
festgeschrieben: Befunde als Liste mit Datei und Grund, eine Antivakuitätsklausel
(fehlende Quelle ist rot, nicht grün) und Selbsttests gegen ein saubere und ein
schmutzige Textprobe.

### Fehlerbehandlung und Logging auf der PHP-Seite
**Quelle:** `php/lib/Controller/QueueController.php:173-179`, `php/lib/Service/ExAppService.php:302-337`, `php/lib/Repair/AppInstallStep.php:62-65`
**Apply to:** `AppUninstallStep.php`, `PurgeCommand.php`, jede Änderung an `ExAppService`
```php
} catch (\Throwable $e) {
	// Same rule as above: no library message in the log.
	$this->logger->error('Findling: could not acknowledge a batch', ['exception' => $e]);
	return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
}
```
Statischer Satz plus `exception`-Feld, nie eine Bibliotheksmeldung und nie ein
Pfad. Der Uninstall-Step darf zusätzlich gar nicht werfen (siehe
`AppInstallStep.php:28-32`: ein fehlgeschlagener Repair-Step nimmt die
Installation mit).

### Idempotenz von Lifecycle-Schritten
**Quelle:** `php/lib/Repair/AppInstallStep.php:23-26` (Marke), `php/lib/Migration/Version001000Date20260904000000.php:43-63` (`hasTable`/`hasIndex`-Wächter)
**Apply to:** `AppUninstallStep.php`, jede neue Migration
```php
	public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
		$schema = $schemaClosure();
		if (!$schema->hasTable('findling_file_state')) {
			return null;
		}
		...
		return $changed ? $schema : null;
	}
```
Für den Uninstall bedeutet das `tableExists()` vor `dropTable()`, weil der Schritt
bei jedem Disable erneut läuft und potenziell bevor die Tabellen existieren.

### CI-Härtung: Pinnen, Deadline, Beweis der Messung
**Quelle:** `php.yml:28-33` (`APPSTORE_SHA`), `integration.yml:94-97` + `:116-118`, `resilience.yml:502-511`
**Apply to:** `deploy-harp.yml`, der Paritätsjob, der Release-Job, jede Änderung an `docker.yml`
Jeder Fremdstand wird per SHA oder Digest gepinnt und der Kommentar muss stimmen
(Sec-M8), jeder Job trägt `timeout-minutes`, und ein Job, der grün wird, ohne dass
die tragende Messung stattgefunden hat, ist ein Fehlschlag.

### Privatheitsgrenze Container nach PHP
**Quelle:** `backend/src/findling/api/status.py:157-163` (kein Spread über `files`), `backend/appinfo/info.xml:108-157` (Zweckbindung je Route), `docs/testing.md:47`
**Apply to:** `appVersion` in `/status`, alles, was der Paritätsjob und der Messbericht ausgeben
Zahlen, Codes und fileids ja; Pfade, Titel und Text nein. Der Messbericht und die
CSV des Samplers enthalten deshalb Dateizahlen und Byte-Zahlen, keine Namen.

### Nur-Lesen-Invariante
**Quelle:** `backend/tests/test_readonly_gate.py` (Gate A), `test_write_allowlist_has_exactly_three_entries`
**Apply to:** Uninstall-Räumung, Lastkorpus-Erzeugung auf der Box
Die Schreib-Allowlist hat exakt drei Einträge, und ein vierter Weg fällt durchs
Gate. Die Volume-Löschung läuft deshalb über AppAPI (`--rm-data`) und nicht als
neue Schreibroute im Container. Der Lastkorpus wird ausserhalb dieser Grenze
erzeugt (direkt ins Datenverzeichnis, dann `chown` und `occ files:scan`).

### occ-Aufrufe in CI
**Quelle:** `integration.yml:961-971`
**Apply to:** jeder neue Job und jedes ops-Skript, das occ ruft
`--no-interaction` bei allem Destruktiven (occ hält die CI-Shell für interaktiv),
`--stop_after` mit Unterstrich bei `background-job:worker`, und `timeout` vor jedem
occ-Aufruf, der hängen kann.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| HaRP-Dienst in `scripts/dev/compose-harp.yaml` und im Deploy-Job | ci / config | lifecycle | HaRP ist in diesem Repo nie gelaufen. Beide Registrierungspfade sind `manual-install` (`setup-test-nc/action.yml:210-214`, `register-exapp.sh:177-181`), der Docker-Smoke-Test startet das Image ohne AppAPI. Vorlage ist ausschliesslich 05-RESEARCH.md Pattern 1 plus die AppAPI-Quellen |
| `scripts/ops/hetzner_box.sh`, REST-Teil | ops-script | request-response | Es gibt im Repo keinen Aufruf gegen eine fremde Cloud-API. Rahmen von `measure_wordlist.sh` erben, Aufrufe wörtlich aus 05-RESEARCH.md, Abschnitt "Hetzner-Box und Volume per API" |
| `docs/store-listing.md`, dreisprachige Fassung | docs | - | Kein mehrsprachiges Artefakt im Repo. Vorbild ist das Schwesterprojekt nextcloud-mcp-connector (EN/DE/FR, keine Backticks, keine Tabellen in der Description, leere info.xml-Elemente verursachen einen Store-500) |
| Store-Medien (Screenshots, Header-Bild) | asset | - | Kein Bild-Asset im Repo. Regeln stehen in D-13 und in der Bildpost-Linie des Owners; Screenshots von der Dev-Instanz, nicht aus CI (`integration.yml`-Korpus heisst `09-bescheid.pdf` und enthält zehn kaputte PDFs) |
| Symmetrischer Mengenvergleich als Skript | test-helper | transform | Es gibt kein bidirektionales Mengen-Diff in bash im Repo. Die Python-Fassung steht in 05-RESEARCH.md; die Meldungsform kommt aus `test_allowlist_parity.py:54-64` (`missing` und `extra` getrennt benennen) |

## Metadata

**Analog search scope:** `php/lib/**`, `php/appinfo`, `backend/tests/**`,
`backend/src/findling/api`, `backend/src/findling/tools`, `scripts/dev`,
`scripts/ci`, `.github/workflows`, `.github/actions`, `docs/**`
**Files scanned:** 28 gelesen (davon 3 gross und nur abschnittsweise:
`integration.yml`, `build_corpus.py`, `resilience.yml`), plus grep-Inventare über
`php/lib`, `backend/tests` und `backend/src`
**Pattern extraction date:** 2026-09-03
**Projektregeln, die für alles Neue gelten:** Code und Kommentare englisch,
Betriebsdoku deutsch mit echten Umlauten, keine Em- oder En-Dashes, keine Emojis,
Icons als SVG, `uv run python -m pytest` (nicht `uv run pytest`), kein
Co-Authored-By-Trailer.
