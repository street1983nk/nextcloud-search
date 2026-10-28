<?php

declare(strict_types=1);

/*
 * Helper of the SMB ACL measurement (plan 39-04, measurement A6). Runs on a
 * throwaway CI runner only, from the root of the Nextcloud server checkout.
 *
 *   php smb_acl_probe.php <server-root> creds <uid>
 *       prints "stored" or "missing": whether the mount mechanism
 *       "Log-in credentials, save in database" holds credentials for <uid>.
 *   php smb_acl_probe.php <server-root> seed <uid>
 *       stores <uid> and the password from PROBE_PASS under the identifier of
 *       that mechanism, which is exactly what Nextcloud does on the first
 *       mount setup after a login. Used only if the login did not store them.
 *   php smb_acl_probe.php <server-root> readable <uid> <path>
 *       prints "node=<bool> storage=<bool>": isReadable() of the node in the
 *       user folder (permissions as the scanner recorded them) and
 *       isReadable() of the SMB storage itself for the same file, which is the
 *       method F3 of the dedup note is about. "not_listed" when the path does
 *       not resolve, "error:<class>" on anything else.
 *
 * Nothing secret is printed: no password, no option of the mount.
 */

if (PHP_SAPI !== 'cli') {
	exit(2);
}

$serverRoot = $argv[1] ?? '';
$command = $argv[2] ?? '';
$uid = $argv[3] ?? '';
if ($serverRoot === '' || $uid === '') {
	fwrite(STDERR, "usage: smb_acl_probe.php <server-root> creds|seed|readable <uid> [path]\n");
	exit(2);
}

require_once $serverRoot . '/lib/base.php';

const LOGIN_CREDENTIALS = 'password::logincredentials/credentials';

$credentials = \OCP\Server::get(\OCP\Security\ICredentialsManager::class);

switch ($command) {
	case 'creds':
		echo $credentials->retrieve($uid, LOGIN_CREDENTIALS) === null ? "missing\n" : "stored\n";
		break;

	case 'seed':
		$password = getenv('PROBE_PASS');
		if (!is_string($password) || $password === '') {
			fwrite(STDERR, "PROBE_PASS is empty\n");
			exit(2);
		}
		$credentials->store($uid, LOGIN_CREDENTIALS, ['user' => $uid, 'password' => $password]);
		echo "seeded\n";
		break;

	case 'readable':
		$path = $argv[4] ?? '';
		try {
			$folder = \OCP\Server::get(\OCP\Files\IRootFolder::class)->getUserFolder($uid);
			$node = $folder->get($path);
			$storage = $node->getStorage();
			$nodeReadable = $node->isReadable() ? 'true' : 'false';
			$storageReadable = $storage->isReadable($node->getInternalPath()) ? 'true' : 'false';
			echo 'node=' . $nodeReadable . ' storage=' . $storageReadable . "\n";
		} catch (\OCP\Files\NotFoundException) {
			echo "not_listed\n";
		} catch (\Throwable $e) {
			echo 'error:' . get_class($e) . "\n";
		}
		break;

	default:
		fwrite(STDERR, "unknown command\n");
		exit(2);
}
