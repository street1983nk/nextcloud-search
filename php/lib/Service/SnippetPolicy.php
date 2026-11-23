<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Constants;
use OCP\Files\Cache\IFileAccess;
use OCP\Files\Config\IUserMountCache;
use OCP\Files\Folder;
use OCP\IAppConfig;
use OCP\IGroupManager;
use OCP\IUser;
use OCP\SystemTag\ISystemTagObjectMapper;
use Psr\Log\LoggerInterface;

/**
 * Which hits of a search page may show a text excerpt to the searching user
 * (owner decision E3, plan 45-22).
 *
 * A hit of a file that the user may only see under the watermark of Nextcloud
 * Office keeps its name and path and shows no excerpt: an excerpt is file
 * content, and the watermark is the statement that this user gets the content
 * only behind it. SearchService hands the ids of its survivors to allowed()
 * and asks the container for the excerpts of the answer and of nothing else.
 *
 * The way is S3 of 45-AUDIT.md ("E3 Erkennung an der Quelle"), chosen by the
 * owner (`Entscheid E3-Weg 45-22`), with public OCP APIs only and never the
 * internal PermissionManager of richdocuments. It suppresses at least what
 * richdocuments watermarks for a signed in user (PermissionManager.php
 * shouldWatermark, lines 174 to 260 of v10.3.3, v11.1.3 and v12.0.2) and
 * deliberately more where the public APIs cannot tell:
 *
 * - shareAll: every file the user does not own.
 * - shareRead: every file the user does not own, and an own file whose raw
 *   cache permissions (a) or whose node (b) lack UPDATE.
 * - shareDisabledDownload: every file the user does not own. The precise
 *   check (only a share whose attributes say download=false) needs the super
 *   share of the mount, which richdocuments reads through a storage wrapper
 *   that no public API exposes; 45-AUDIT.md, section "E3 Erkennung an der
 *   Quelle", has the sources, and the owner decision names this fallback.
 * - allGroups: every hit of a user in a group of the list, own files too.
 * - allTags: every hit whose file carries a tag of the list, for everybody.
 * - a watermark_* key this class does not know, set to yes: every hit. A new
 *   mode of a later richdocuments must not leak until this class learns it.
 * - several modes: the union.
 *
 * The link modes, hideDownload and shareTalkPublic need a public link or no
 * user at all; a search always has a signed in user, so they never apply.
 * The mime type filter of richdocuments is not rebuilt, which suppresses more
 * and never less. Neither is the verdict of a file in the index or the time it
 * was indexed part of the decision: old content that was indexed before the
 * watermark was switched on loses its excerpt like everything else (A1).
 *
 * Owning a file means: its cache entry lies on the storage of the home mount
 * of the user, mount point '/<uid>/' with a home mount provider, as in
 * ReaderCandidates. A user without such a mount owns nothing.
 *
 * Cost: without the watermark one read of the app config, which the server
 * holds in memory, and nothing else. With it, per page and not per hit: the
 * keys of the namespace once per request, one getByFileIds, the mounts of the
 * user once per request, one getTagIdsForObjects under allTags, the groups of
 * the user once per request under allGroups, and under shareRead one node per
 * own file, resolved through SearchService::readableFile() and never here.
 *
 * Fail-closed: whatever throws costs the excerpts of the page, never a hit.
 * The log line carries a counter and a class name, never a name or an id.
 *
 * Final, unlike SearchService: no test needs a double of this class, the
 * tests of SearchService run the real one on mocks of its interfaces.
 */
final class SnippetPolicy {
	/**
	 * The namespace richdocuments keeps the watermark settings in
	 * (AppConfig::WATERMARK_APP_NAMESPACE, 'files' in all three tags).
	 */
	private const NAMESPACE = 'files';

	/**
	 * Every watermark key richdocuments v10.3.3, v11.1.3 and v12.0.2 read. A
	 * key with this prefix outside the list that is set to yes is a mode this
	 * class does not know.
	 */
	private const KNOWN_KEYS = [
		'watermark_enabled',
		'watermark_text',
		'watermark_shareAll',
		'watermark_shareRead',
		'watermark_shareDisabledDownload',
		'watermark_shareTalkPublic',
		'watermark_linkSecure',
		'watermark_linkRead',
		'watermark_linkAll',
		'watermark_linkTags',
		'watermark_linkTagsList',
		'watermark_allGroups',
		'watermark_allGroupsList',
		'watermark_allTags',
		'watermark_allTagsList',
	];

	/**
	 * The mount providers of the server that build a home mount, as strings so
	 * that nothing is loaded; the same two as in ReaderCandidates.
	 */
	private const HOME_MOUNT_PROVIDERS = [
		'OC\Files\Mount\LocalHomeMountProvider',
		'OC\Files\Mount\ObjectHomeMountProvider',
	];

	/**
	 * The rules of this request, read once: null before the first read, false
	 * for a watermark that is off.
	 *
	 * @var array{unknown:bool,foreign:bool,shareRead:bool,groups:list<string>|null,tags:list<string>|null}|false|null
	 */
	private array|false|null $rules = null;

	/** @var array<string,int|null> the home storage of a user, per request */
	private array $homeStorages = [];

	/** @var array<string,bool> whether a user is in a listed group, per request */
	private array $listedMembers = [];

	public function __construct(
		private IAppConfig $appConfig,
		private IFileAccess $fileAccess,
		private IUserMountCache $mountCache,
		private ISystemTagObjectMapper $tagMapper,
		private IGroupManager $groupManager,
		private LoggerInterface $logger,
	) {
	}

	/**
	 * The ids of a page that may show an excerpt, in their order.
	 *
	 * @param IUser $user the searching user
	 * @param Folder $userFolder the folder of the run, for the node of an own
	 *                           file under shareRead
	 * @param list<int> $fileIds the survivors of the recheck
	 * @return list<int>
	 */
	public function allowed(IUser $user, Folder $userFolder, array $fileIds): array {
		if ($fileIds === []) {
			return [];
		}

		try {
			$rules = $this->rules();
			if ($rules === false) {
				return $fileIds;
			}

			$blocked = $this->blocked($rules, $user, $userFolder, $fileIds);
		} catch (\Throwable $e) {
			$this->logger->warning('Findling: could not tell whether hits are under the watermark, showing no excerpts on this page', [
				'count' => count($fileIds),
				'class' => $e::class,
			]);

			return [];
		}

		return array_values(array_filter($fileIds, static fn (int $fileId): bool => !isset($blocked[$fileId])));
	}

	/**
	 * The rules of the watermark that reach a search, or false when it is off.
	 *
	 * 'no' is off and every other value is on, as in PermissionManager.php
	 * line 175 and SecureViewService::isEnabled(); a mode is on with exactly
	 * 'yes'. The switch is read the way richdocuments decides whether its
	 * storage wrapper exists at all (Application.php v12.0.2 line 139), and
	 * only behind a switch that is on does this class read anything else.
	 *
	 * @return array{unknown:bool,foreign:bool,shareRead:bool,groups:list<string>|null,tags:list<string>|null}|false
	 */
	private function rules(): array|false {
		if ($this->rules !== null) {
			return $this->rules;
		}

		if ($this->appConfig->getValueString(self::NAMESPACE, 'watermark_enabled', 'no') === 'no') {
			return $this->rules = false;
		}

		// All keys, the lazy ones too, and each value is read the way it is
		// stored: richdocuments reads them through IConfig, which does not
		// care whether a key is lazy.
		$keys = $this->appConfig->getKeys(self::NAMESPACE);
		$on = function (string $key) use ($keys): bool {
			if (!in_array($key, $keys, true)) {
				return false;
			}

			return $this->appConfig->getValueString(self::NAMESPACE, $key, 'no', $this->appConfig->isLazy(self::NAMESPACE, $key)) === 'yes';
		};
		$list = function (string $key) use ($keys): array {
			if (!in_array($key, $keys, true)) {
				return [];
			}
			$value = $this->appConfig->getValueString(self::NAMESPACE, $key, '', $this->appConfig->isLazy(self::NAMESPACE, $key));

			return $value === '' ? [] : explode(',', $value);
		};

		$unknown = false;
		foreach ($keys as $key) {
			if (str_starts_with($key, 'watermark_') && !in_array($key, self::KNOWN_KEYS, true) && $on($key)) {
				$unknown = true;
				break;
			}
		}

		return $this->rules = [
			'unknown' => $unknown,
			'foreign' => $on('watermark_shareAll') || $on('watermark_shareRead') || $on('watermark_shareDisabledDownload'),
			'shareRead' => $on('watermark_shareRead'),
			'groups' => $on('watermark_allGroups') ? $list('watermark_allGroupsList') : null,
			'tags' => $on('watermark_allTags') ? $list('watermark_allTagsList') : null,
		];
	}

	/**
	 * The ids of a page that may not show an excerpt, as keys.
	 *
	 * @param array{unknown:bool,foreign:bool,shareRead:bool,groups:list<string>|null,tags:list<string>|null} $rules
	 * @param list<int> $fileIds
	 * @return array<int,true>
	 */
	private function blocked(array $rules, IUser $user, Folder $userFolder, array $fileIds): array {
		$all = array_fill_keys($fileIds, true);
		if ($rules['unknown']) {
			return $all;
		}

		if ($rules['groups'] !== null && $this->inListedGroup($user, $rules['groups'])) {
			return $all;
		}

		$blocked = [];
		if ($rules['foreign']) {
			$home = $this->homeStorage($user);
			$entries = $this->fileAccess->getByFileIds($fileIds);
			foreach ($fileIds as $fileId) {
				$entry = $entries[$fileId] ?? null;
				if ($entry === null || $home === null || $entry->getStorageId() !== $home) {
					$blocked[$fileId] = true;
					continue;
				}

				if ($rules['shareRead'] && !$this->ownFileIsUpdatable($userFolder, $fileId, $entry->getPermissions())) {
					$blocked[$fileId] = true;
				}
			}
		}

		if ($rules['tags'] !== null) {
			$open = array_values(array_filter($fileIds, static fn (int $fileId): bool => !isset($blocked[$fileId])));
			if ($open !== []) {
				$tagsOf = $this->tagMapper->getTagIdsForObjects(array_map('strval', $open), 'files');
				foreach ($open as $fileId) {
					foreach ($tagsOf[(string)$fileId] ?? [] as $tagId) {
						if (in_array((string)$tagId, $rules['tags'], true)) {
							$blocked[$fileId] = true;
							break;
						}
					}
				}
			}
		}

		return $blocked;
	}

	/**
	 * Whether an own file is updatable for its owner, by both readings of the
	 * owner decision: (a) the raw permissions of its cache row, (b) the node of
	 * the user, which carries what a storage wrapper takes away. A node that
	 * does not resolve or throws is not updatable.
	 */
	private function ownFileIsUpdatable(Folder $userFolder, int $fileId, int $rawPermissions): bool {
		if (($rawPermissions & Constants::PERMISSION_UPDATE) === 0) {
			return false;
		}

		try {
			$node = SearchService::readableFile($userFolder, $fileId);
		} catch (\Throwable) {
			return false;
		}

		return $node !== null && $node->isUpdateable();
	}

	/**
	 * The numeric id of the storage of the home mount of a user, or null.
	 */
	private function homeStorage(IUser $user): ?int {
		$uid = $user->getUID();
		if (array_key_exists($uid, $this->homeStorages)) {
			return $this->homeStorages[$uid];
		}

		$home = null;
		foreach ($this->mountCache->getMountsForUser($user) as $mount) {
			if ($mount->getMountPoint() === '/' . $uid . '/'
				&& in_array($mount->getMountProvider(), self::HOME_MOUNT_PROVIDERS, true)) {
				$home = $mount->getStorageId();
				break;
			}
		}

		return $this->homeStorages[$uid] = $home;
	}

	/**
	 * Whether a user is in a group of the list, as PermissionManager asks it
	 * (isInGroup per listed group, the list split at commas, nothing trimmed).
	 *
	 * @param list<string> $groups
	 */
	private function inListedGroup(IUser $user, array $groups): bool {
		$uid = $user->getUID();
		if (!array_key_exists($uid, $this->listedMembers)) {
			$this->listedMembers[$uid] = array_intersect($groups, $this->groupManager->getUserGroupIds($user)) !== [];
		}

		return $this->listedMembers[$uid];
	}
}
