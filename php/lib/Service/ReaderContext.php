<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\IUserManager;
use OCP\IUserSession;

/**
 * Run a lookup as the member it is asked for, and only for that span (#14).
 *
 * Why this exists at all: groupfolders (22.0.6, MountProvider::getGroupFolderStorage)
 * builds the mount of a Team Folder member with in_share=true whenever the
 * request is not a CLI run and the active user of the request is not that
 * member. Under in_share the ACL wrappers (ACLCacheWrapper, ACLStorageWrapper)
 * raise the minimum a path needs from READ to READ plus SHARE, and a path that
 * misses it is dropped from the cache, so the node is hidden. A Team Folder whose
 * advanced permissions grant +read and -share is therefore readable for every
 * member in their own browser session and hidden from every member in the three
 * requests where Findling asks on their behalf: the ExApp claim and the content
 * gateway (active user: nobody) and the admin lookup (active user: the admin).
 * occ runs with OC::$CLI set and never sees any of it, which is why the defect
 * was invisible to occ findling:diagnose.
 *
 * The switch has to cover the FIRST mount setup of that member in the request
 * and the lookup after it. groupfolders fixes the flag once, when the mount is
 * built, and a mount built before the switch stays refused for the rest of the
 * request (measured on the harness, see .planning/debug/issue14-acl-unreadable.md).
 * The lookup is inside as well because the setup of a mount can be lazy and
 * happen in the lookup itself.
 *
 * What the switch is and is not. setVolatileActiveUser() sets the active user of
 * this request only: no session write, no login event, no hook. setUser() would
 * write the session and is never called here. The previous user is restored in
 * finally with the very object getUser() returned before the switch, because a
 * null handed back to the session means "reload from the session storage" and
 * not "nobody"; passing the old value back is the only restore that cannot guess
 * wrong. The member only gets the minimum READ that the member has in their own
 * session, and SearchService::readableNode still asks for the read bit.
 *
 * Mounts built during the switch stay cached for the rest of the request with
 * in_share=false. That is accepted: the three callers do no further work for
 * another user after the lookup, and the next request builds its mounts fresh.
 *
 * Incognito caveat: in incognito mode (cron) getUser() answers null whatever the
 * active user is, so the switch does nothing there. None of the three callers
 * runs in that mode, and a CLI run never sets in_share in the first place.
 *
 * An unknown uid is not switched to. The work runs unchanged, so the answer for
 * a user that does not exist stays word for word what it was before (the
 * NoUserException path of the gateway, the null of the path lookup), and the
 * switch cannot be used to find out which users exist (T-04-38).
 *
 * This is the only file of the app that may change the active user; a gate in
 * backend/tests/test_php_acl_boundary.py holds it to that.
 */
final class ReaderContext {
	public function __construct(
		private IUserSession $userSession,
		private IUserManager $userManager,
	) {
	}

	/**
	 * The result of $work, computed with $uid as the active user of the request.
	 *
	 * @template T
	 * @param \Closure(): T $work
	 * @return T
	 */
	public function actAs(string $uid, \Closure $work): mixed {
		$previous = $this->userSession->getUser();
		if ($previous !== null && $previous->getUID() === $uid) {
			return $work();
		}

		$member = $this->userManager->get($uid);
		if ($member === null) {
			return $work();
		}

		$this->userSession->setVolatileActiveUser($member);
		try {
			return $work();
		} finally {
			$this->userSession->setVolatileActiveUser($previous);
		}
	}
}
