<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The error list gets the index its sort order needs.
 *
 * findling_file_state has carried one index since it was created, on state
 * alone, because until now the only question asked of it was "how many rows per
 * state". The error list of phase 4 asks a second one: the most recently judged
 * rows of one state and one reason, newest first, twenty at a time. That is a
 * state lookup followed by a sort, and with only findling_fs_state in place the
 * sort runs over every row the state matches.
 *
 * On a small instance that costs nothing and this index is dead weight. On a
 * hundred thousand rows with a page that polls every five seconds it is the
 * difference between an index range scan and a full sort per poll, and the
 * admin who opens this page is by definition the admin whose instance has a lot
 * of rows in this table. The index is cheap, it is backwards compatible and it
 * needs no data migration, so it is added rather than measured first.
 *
 * *findling_fs_upd (state, updated_at)* and not (state, updated_at, file_id):
 * the second sort key of the query breaks ties inside one second and is there
 * for a stable order across pages, not for the lookup, so carrying it in the
 * index would widen every entry for a tie break that touches a handful of rows.
 * findling_fs_state stays: it still answers the counting query without a sort,
 * which is the one every render of the page runs first. The name is nineteen
 * characters, well inside the thirty a Nextcloud index name may have.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001000Date20260904000000 extends SimpleMigrationStep {
	/**
	 * Every step is guarded so a second run is a no-op. Nextcloud can replay a
	 * migration after a failed upgrade, and a migration that throws on the
	 * second run turns a recoverable upgrade into a broken instance.
	 */
	public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
		/** @var ISchemaWrapper $schema */
		$schema = $schemaClosure();
		if (!$schema->hasTable('findling_file_state')) {
			return null;
		}

		$table = $schema->getTable('findling_file_state');
		$changed = false;

		if (!$table->hasIndex('findling_fs_upd')) {
			$table->addIndex(['state', 'updated_at'], 'findling_fs_upd');
			$changed = true;
		}

		return $changed ? $schema : null;
	}
}
