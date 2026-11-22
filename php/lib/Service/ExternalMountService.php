<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\App\IAppManager;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;
use OCP\L10N\IFactory;
use Psr\Log\LoggerInterface;

/**
 * The external storage an admin set up, as the admin page lists it (EXCL-04).
 *
 * The page offers every admin mount of files_external as one checkbox, set
 * means indexed (D-45-01), and the route of the rules stores the ids that are
 * not set. This service only reads: one query against oc_external_mounts, no
 * write, no cache over the request.
 *
 * Only admin mounts are listed (type StorageService::ADMIN_MOUNT_TYPE). A mount
 * a user set up for himself is his business and not the admin's, and the
 * exclusion in StorageService ignores the id of a personal mount anyway
 * (D-45-03), so listing one would offer a switch that does nothing.
 *
 * No class of files_external is imported or called. The app can be disabled
 * or missing, the Psalm stubs of OCP do not know its classes, and its
 * BackendService builds every backend with its configuration form, which is
 * far more than a list of names needs. The question whether the app runs is
 * asked through isEnabledForAnyone, for the reason ParallelSearchService
 * writes out: an app enabled for a group only is enabled for somebody. With
 * the app off, the list is empty without a single query.
 *
 * The display name of a backend comes from BACKEND_NAMES, a copy of the texts
 * files_external sets, translated through the catalogue of files_external in
 * the language of the page; an identifier that is not in the table is shown
 * as it is and never handed to the catalogue. The mount point is handed back raw, markup included: escaping is the
 * business of the template, which prints it through p().
 *
 * A failed read logs one warning with a counter and no value, never a mount
 * point or an id (T-04-51), and leaves the list empty, so the page still
 * renders.
 */
final class ExternalMountService {
	/** The app id of files_external. */
	public const APP_ID_FILES_EXTERNAL = 'files_external';

	/**
	 * The display names of the files_external backends by the identifier
	 * oc_external_mounts.storage_backend carries, the texts of setText() in
	 * apps/files_external/lib/Lib/Backend/*.php of stable33. Nextcloud 34 and
	 * 35 lengthen most of them ("SMB/CIFS (Windows network share)"); the short
	 * form is kept so one table serves the whole supported window. The legacy
	 * identifiers come from addIdentifierAlias() and from the two backends
	 * that never got a short identifier (SFTP_Key, SMB_OC).
	 *
	 * @var array<string, string>
	 */
	public const BACKEND_NAMES = [
		'amazons3' => 'S3 Storage',
		'dav' => 'WebDAV',
		'ftp' => 'FTP',
		'local' => 'Local',
		'owncloud' => 'Nextcloud',
		'sftp' => 'SFTP',
		'smb' => 'SMB/CIFS',
		'swift' => 'OpenStack Object Storage',
		'\OC\Files\Storage\AmazonS3' => 'S3 Storage',
		'\OC\Files\Storage\DAV' => 'WebDAV',
		'\OC\Files\Storage\FTP' => 'FTP',
		'\OC\Files\Storage\Local' => 'Local',
		'\OC\Files\Storage\OwnCloud' => 'Nextcloud',
		'\OC\Files\Storage\SFTP' => 'SFTP',
		'\OC\Files\Storage\SFTP_Key' => 'SFTP with secret key login',
		'\OC\Files\Storage\SMB' => 'SMB/CIFS',
		'\OC\Files\Storage\SMB_OC' => 'SMB/CIFS using OC login',
		'\OC\Files\Storage\Swift' => 'OpenStack Object Storage',
	];

	public function __construct(
		private IAppManager $appManager,
		private IDBConnection $db,
		private IFactory $l10nFactory,
		private LoggerInterface $logger,
	) {
	}

	/** True when files_external is enabled for everyone or for a group. */
	public function enabled(): bool {
		return $this->appManager->isEnabledForAnyone(self::APP_ID_FILES_EXTERNAL);
	}

	/**
	 * Every admin mount, sorted by mount point in the language of the page and
	 * by id where two mount points are equal.
	 *
	 * duplicate is true when another entry shows the same mount point with the
	 * same display name, so the page adds the id to tell the two apart.
	 *
	 * @return list<array{id: int, mountPoint: string, backend: string, duplicate: bool}>
	 */
	public function adminMounts(): array {
		if (!$this->enabled()) {
			return [];
		}

		try {
			$mounts = $this->read();
		} catch (\Throwable) {
			$this->logger->warning('Findling: could not read the external storage set up by an admin', ['failed' => 1]);

			return [];
		}

		$this->sort($mounts);

		$seen = [];
		foreach ($mounts as $mount) {
			$key = $mount['mountPoint'] . "\0" . $mount['backend'];
			$seen[$key] = ($seen[$key] ?? 0) + 1;
		}

		$out = [];
		foreach ($mounts as $mount) {
			$mount['duplicate'] = $seen[$mount['mountPoint'] . "\0" . $mount['backend']] > 1;
			$out[] = $mount;
		}

		return $out;
	}

	/** @return list<array{id: int, mountPoint: string, backend: string, duplicate: bool}> */
	private function read(): array {
		$qb = $this->db->getQueryBuilder();
		$qb->select('mount_id', 'mount_point', 'storage_backend')
			->from('external_mounts')
			->where($qb->expr()->eq('type', $qb->createNamedParameter(StorageService::ADMIN_MOUNT_TYPE, IQueryBuilder::PARAM_INT)));

		// The catalogue of files_external in the language of the page, so the
		// list says "Lokal" under German like Nextcloud does (finding
		// V-45-10-01). The short names of BACKEND_NAMES are keys of that
		// catalogue in 34.0.3 (de, fr, zh_TW read on the dev instance); a key a
		// later version drops comes back as the English text, which is what
		// the list showed before.
		$l10n = $this->l10nFactory->get(self::APP_ID_FILES_EXTERNAL);

		$mounts = [];
		$result = $qb->executeQuery();
		try {
			while (is_array($row = $result->fetch())) {
				$id = (int)($row['mount_id'] ?? 0);
				if ($id <= 0) {
					continue;
				}

				$identifier = (string)($row['storage_backend'] ?? '');
				$name = self::BACKEND_NAMES[$identifier] ?? null;
				$mounts[] = [
					'id' => $id,
					'mountPoint' => (string)($row['mount_point'] ?? ''),
					'backend' => $name === null ? $identifier : $l10n->t($name),
					'duplicate' => false,
				];
			}
		} finally {
			$result->closeCursor();
		}

		return $mounts;
	}

	/**
	 * Sorts by mount point with the collator of the page language where intl
	 * is there, case-insensitively otherwise, and by id on a tie.
	 *
	 * @param list<array{id: int, mountPoint: string, backend: string, duplicate: bool}> $mounts
	 */
	private function sort(array &$mounts): void {
		$collator = null;
		if (class_exists(\Collator::class)) {
			try {
				$collator = new \Collator($this->l10nFactory->findLanguage());
			} catch (\Throwable) {
				// An unknown locale with intl exceptions switched on: the
				// case-insensitive order below is good enough for a list.
				$collator = null;
			}
		}

		usort($mounts, static function (array $a, array $b) use ($collator): int {
			$order = $collator !== null ? $collator->compare($a['mountPoint'], $b['mountPoint']) : false;
			if (!is_int($order)) {
				$order = strcasecmp($a['mountPoint'], $b['mountPoint']);
			}

			return $order !== 0 ? $order : $a['id'] <=> $b['id'];
		});
	}
}
