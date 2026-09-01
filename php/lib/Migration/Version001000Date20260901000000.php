<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\DB\Types;
use OCP\IDBConnection;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The queue after its first audit: a dirty mark, a claim token, and an index
 * that matches the one query the queue exists for.
 *
 * *dirty* is the answer to the lost-update race of the audit (bug H4). A file
 * that changes while its row is claimed used to get its lock cleared, and the
 * acknowledgement of the old bytes then deleted the row: the new version
 * vanished from the queue and the index kept the old text. Now the changed row
 * is marked instead of unlocked, and the acknowledgement turns the mark into a
 * fresh, free row rather than deleting it.
 *
 * *claim_token* lets one conditional UPDATE claim a whole batch (perf H4). The
 * winner set of that statement cannot be read back by timestamp, because two
 * collectors claiming within the same second are indistinguishable; a random
 * token per claim call is unambiguous.
 *
 * *findling_q_free (locked_at, id)* matches "the free rows, oldest first",
 * which is the query every claim starts with (perf H3). It replaces the plain
 * locked_at index, and it only works because NULL stops meaning "free": the
 * free mark becomes the epoch, so the free condition is one closed range
 * instead of an OR that no index serves. The rows are rewritten below.
 *
 * *findling_q_stor* is dropped: no query ever used it (perf M6).
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001000Date20260901000000 extends SimpleMigrationStep {
	public function __construct(
		private IDBConnection $db,
	) {
	}

	/**
	 * Every change is guarded so a second run is a no-op. Nextcloud can replay
	 * a migration after a failed upgrade, and a migration that throws on the
	 * second run turns a recoverable upgrade into a broken instance.
	 */
	public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
		/** @var ISchemaWrapper $schema */
		$schema = $schemaClosure();
		if (!$schema->hasTable('findling_queue')) {
			return null;
		}

		$table = $schema->getTable('findling_queue');
		$changed = false;

		if (!$table->hasColumn('dirty')) {
			$table->addColumn('dirty', Types::BOOLEAN, ['notnull' => true, 'default' => false]);
			$changed = true;
		}

		if (!$table->hasColumn('claim_token')) {
			$table->addColumn('claim_token', Types::STRING, ['notnull' => false, 'length' => 32]);
			$changed = true;
		}

		if ($table->hasIndex('findling_q_stor')) {
			$table->dropIndex('findling_q_stor');
			$changed = true;
		}

		if ($table->hasIndex('findling_q_locked')) {
			$table->dropIndex('findling_q_locked');
			$changed = true;
		}

		if (!$table->hasIndex('findling_q_free')) {
			$table->addIndex(['locked_at', 'id'], 'findling_q_free');
			$changed = true;
		}

		return $changed ? $schema : null;
	}

	/**
	 * NULL stops meaning "free" here. Rows written before this step carry NULL
	 * in locked_at; from now on the free mark is the epoch, and a row the new
	 * code would never see again is rewritten so that it stays claimable.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$qb = $this->db->getQueryBuilder();
		$qb->update('findling_queue')
			->set('locked_at', $qb->createNamedParameter(new \DateTime('@0'), IQueryBuilder::PARAM_DATE))
			->where($qb->expr()->isNull('locked_at'));
		$qb->executeStatement();
	}
}
