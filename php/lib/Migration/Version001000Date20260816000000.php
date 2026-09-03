<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The two tables the pull model is built on.
 *
 * findling_queue is the work stock. Nextcloud fills it, the container asks for
 * work and acknowledges it, and nobody ever pushes anything into the container.
 * Back pressure then happens by itself: a container that cannot keep up simply
 * asks less often, and a container that is gone lets the queue grow instead of
 * dropping work on the floor.
 *
 * findling_file_state is the return channel. Everything the container could not
 * process ends up there with a reason code, which is what makes the diagnosis
 * page of phase 4 possible without asking the container. Two sources of truth
 * about the same fact is exactly the failure mode this app exists to avoid.
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001000Date20260816000000 extends SimpleMigrationStep {
	/**
	 * Both tables are guarded by a hasTable() check so a second run is a no-op.
	 * Nextcloud can replay a migration after a failed upgrade, and a migration
	 * that throws on the second run turns a recoverable upgrade into a broken
	 * instance.
	 */
	public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
		/** @var ISchemaWrapper $schema */
		$schema = $schemaClosure();
		$changed = false;

		if (!$schema->hasTable('findling_queue')) {
			$table = $schema->createTable('findling_queue');

			$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true, 'length' => 64]);
			$table->addColumn('file_id', Types::BIGINT, ['notnull' => true, 'length' => 64]);
			$table->addColumn('storage_id', Types::BIGINT, ['notnull' => true, 'length' => 64]);
			$table->addColumn('root_id', Types::BIGINT, ['notnull' => true, 'length' => 64]);

			// Not called 'update'. That word is a reserved identifier in several
			// dialects, and a column named after a keyword only fails on the one
			// database nobody tested against.
			//
			// Nullable, and that is not a matter of taste either: Nextcloud 32
			// refuses every boolean column that is NotNull, with "is type Bool
			// and also NotNull, so it can not store false"
			// (MigrationService::ensureOracleConstraints, stable32). The check is
			// gone in 33, 34 and 35, so this column was NotNull for four phases
			// and the app could not be enabled on the oldest version it claims to
			// support; the version matrix of the deploy job found it. The default
			// stays false, so an insert that omits the column gets false and never
			// NULL, and every writer of this app sets it anyway.
			$table->addColumn('is_update', Types::BOOLEAN, ['notnull' => false, 'default' => false]);

			// Nullable on purpose: the size is what lets the batch endpoint stop
			// at a byte budget, and a row whose size is unknown must still be
			// queueable rather than rejected.
			$table->addColumn('size', Types::BIGINT, ['notnull' => false, 'length' => 64]);

			// NULL means free. Everything else is a claim that expires, see
			// QueueMapper::LOCK_TIMEOUT.
			$table->addColumn('locked_at', Types::DATETIME, ['notnull' => false]);

			// How often this row was handed out. Three deliveries without an
			// acknowledgement end as failed(repeatedly_stuck) instead of circling
			// forever, which is what IDX-06 means by a visible end state.
			$table->addColumn('retries', Types::SMALLINT, ['notnull' => true, 'default' => 0]);

			$table->setPrimaryKey(['id'], 'findling_q_id');

			// This index IS the deduplication, and it is the reason there is no
			// select before the insert anywhere in this app. Two crawl jobs that
			// look at the same file at the same time both find nothing in such a
			// select and both insert; the unique index turns that race into a
			// caught conflict, which QueueMapper::enqueue() resolves into an
			// update of the existing row. A second enqueue of the same file is
			// never a second job.
			$table->addUniqueIndex(['file_id'], 'findling_q_fileid');

			// The crawl walks one mount at a time, so it asks for exactly this
			// pair when it wants to know what is already queued for that mount.
			$table->addIndex(['storage_id', 'root_id'], 'findling_q_stor');

			// Every claim reads by lock state before it reads anything else.
			$table->addIndex(['locked_at'], 'findling_q_locked');

			$changed = true;
		}

		if (!$schema->hasTable('findling_file_state')) {
			$table = $schema->createTable('findling_file_state');

			// The Nextcloud file id, not a key of our own: there is exactly one
			// state per file, and making that the primary key means the return
			// channel cannot accumulate duplicates for the same file.
			$table->addColumn('file_id', Types::BIGINT, ['notnull' => true, 'length' => 64]);

			// indexed | skipped | failed. Short on purpose, and validated against
			// a closed list in FileStateService before it ever gets here.
			$table->addColumn('state', Types::STRING, ['notnull' => true, 'length' => 16]);

			// A reason code, never a file name. The length is the second half of
			// that guarantee: no path fits in 32 characters, so even a defect on
			// the container side cannot turn this column into a leak.
			$table->addColumn('reason', Types::STRING, ['notnull' => false, 'length' => 32]);

			$table->addColumn('updated_at', Types::DATETIME, ['notnull' => true]);

			$table->setPrimaryKey(['file_id'], 'findling_fs_id');

			// The status page of phase 4 counts by state, nothing else.
			$table->addIndex(['state'], 'findling_fs_state');

			$changed = true;
		}

		return $changed ? $schema : null;
	}
}
