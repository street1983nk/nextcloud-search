<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\IDBConnection;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The queue learns what kind of work a row is.
 *
 * Until now every row meant the same thing: download this file and extract its
 * text. Phase 3 adds four more meanings (a permission change, a deletion, a
 * rename, a scan that has to go through OCR), and they differ in what the
 * container has to do, in what it is allowed to need, and in how long it may
 * take. That is a property of the row, so it is a column.
 *
 * *kind* is a short string and not an integer, because the value travels into
 * the source object and from there into the container, where a number would
 * have to be translated back on both sides of a process boundary. The closed
 * list of valid values lives in QueueMapper::KINDS and nowhere else.
 *
 * *findling_q_kind (kind, locked_at, id)* is the same index as findling_q_free,
 * with the kind in front. It answers "the free rows of one kind, oldest first",
 * which is the query the claim of this phase starts with, once per kind and in
 * a fixed order. findling_q_free stays: it still answers the same question
 * without a kind, which is what the counters and the acknowledgement need.
 *
 * Priority is deliberately not a column here. A priority in ORDER BY would
 * devalue both indexes and buy nothing that the fixed order of the claim calls
 * does not already buy, and that order additionally allows a different batch
 * size per kind, which OCR needs (see QueueService::KIND_BATCH).
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001000Date20260902000000 extends SimpleMigrationStep {
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

		if (!$table->hasColumn('kind')) {
			// notnull with a default rather than a nullable column: "no kind" is
			// not a state this queue has, and every row written before this
			// migration was a content job by definition. Length 16 is above the
			// longest member of the closed list with room to spare, and short
			// enough that the index below stays narrow.
			$table->addColumn('kind', Types::STRING, [
				'notnull' => true,
				'default' => 'content',
				'length' => 16,
			]);
			$changed = true;
		}

		if (!$table->hasIndex('findling_q_kind')) {
			$table->addIndex(['kind', 'locked_at', 'id'], 'findling_q_kind');
			$changed = true;
		}

		return $changed ? $schema : null;
	}

	/**
	 * A column added with a default carries the existing rows on all three
	 * dialects, so this is a safety net and not the actual data migration: it
	 * repairs a row that came out of a partially applied upgrade with an empty
	 * kind, which the claim would then never look at again, because it asks per
	 * kind and no kind is spelled like that.
	 */
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$qb = $this->db->getQueryBuilder();
		$qb->update('findling_queue')
			->set('kind', $qb->createNamedParameter('content'))
			->where($qb->expr()->orX(
				$qb->expr()->isNull('kind'),
				$qb->expr()->eq('kind', $qb->createNamedParameter('')),
			));
		$qb->executeStatement();
	}
}
