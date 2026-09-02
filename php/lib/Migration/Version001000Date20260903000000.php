<?php

declare(strict_types=1);

namespace OCA\Findling\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

/**
 * The denominator of the coverage figure gets a home.
 *
 * findling_scan_stats holds one row per storage with the counters the crawl
 * already produces while it walks a mount. It lives in the Nextcloud database
 * and not in the container, and that is not a matter of convenience: the
 * coverage figure is indexed against indexable files, the numerator is what the
 * container put into the index, and the denominator is what the Nextcloud file
 * list says could be indexed at all. Only this side owns the file list, so only
 * this side can count it. A counter in the container would be a second answer
 * to a question this side already answers, and the reconcile would spend every
 * night repairing the difference between the two.
 *
 * Every column is a number or a timestamp. There is no path, no file name and
 * no mimetype in this table, on purpose: it is read by an administration page
 * that renders what it finds, and a table that cannot hold a file name cannot
 * leak one (T-04-19).
 *
 * finished_at is set at exactly one place, the existing termination condition
 * of StorageCrawlJob (nothing behind the cursor any more, so the mount is done
 * and gets no successor). A row without finished_at therefore means: this
 * number is a lower bound, and the page has to label it as provisional and say
 * how many of how many mounts are through. An estimate that quietly corrects
 * itself upwards looks like a defect.
 *
 * No foreign key on storage_id, and the reason is that a mount disappears in
 * normal operation: a user is deleted, a Team Folder is removed, an external
 * storage is unmounted. A constraint here would turn an ordinary event into an
 * upgrade error or a failed cron round, and the row of a mount that is gone
 * costs a few bytes and answers the question "what did the last scan see".
 *
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
 */
class Version001000Date20260903000000 extends SimpleMigrationStep {
	/**
	 * The table is guarded by a hasTable() check so a second run is a no-op.
	 * Nextcloud can replay a migration after a failed upgrade, and a migration
	 * that throws on the second run turns a recoverable upgrade into a broken
	 * instance.
	 */
	public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
		/** @var ISchemaWrapper $schema */
		$schema = $schemaClosure();
		$changed = false;

		if (!$schema->hasTable('findling_scan_stats')) {
			$table = $schema->createTable('findling_scan_stats');

			// The Nextcloud storage id, not a key of our own: there is exactly
			// one scan row per mount, and making that the primary key is what
			// makes the counter upsert idempotent without a select in front of
			// it. Two crawl slices of the same mount can never produce two rows.
			$table->addColumn('storage_id', Types::BIGINT, ['notnull' => true, 'length' => 64]);

			// Files the crawl looked at in this mount. This is the raw sighting
			// count and not yet the denominator: the two deliberate omissions
			// below are subtracted from it, which is why they are counted
			// separately instead of being left out here.
			$table->addColumn('files_seen', Types::BIGINT, ['notnull' => true, 'default' => 0]);
			$table->addColumn('bytes_seen', Types::BIGINT, ['notnull' => true, 'default' => 0]);

			// Pictures, which never carry a text layer, so OCR is certain for
			// them. Kept apart from pdf_seen because before a run the OCR share
			// is an interval and not a value, and one mixed number would hide
			// which end of that interval it came from.
			$table->addColumn('ocr_candidates', Types::BIGINT, ['notnull' => true, 'default' => 0]);
			$table->addColumn('pdf_seen', Types::BIGINT, ['notnull' => true, 'default' => 0]);

			// The two deliberate omissions. They are what the page shows as
			// "deliberately left out" next to the fraction, and they are not in
			// the denominator: a coverage figure that can never reach a hundred
			// per cent says nothing at all.
			$table->addColumn('over_cap', Types::BIGINT, ['notnull' => true, 'default' => 0]);
			$table->addColumn('excluded', Types::BIGINT, ['notnull' => true, 'default' => 0]);

			// A mirror of the job argument, so the page can show progress inside
			// a mount without reading the job list.
			$table->addColumn('cursor_file_id', Types::BIGINT, ['notnull' => true, 'default' => 0]);

			// Nullable, and the null is the message: set only at the termination
			// condition of the crawl, so its absence means the counters of this
			// mount are a lower bound. See the class docblock above.
			$table->addColumn('finished_at', Types::DATETIME, ['notnull' => false]);

			$table->addColumn('updated_at', Types::DATETIME, ['notnull' => true]);

			// Fifteen characters including the prefix. Nextcloud rejects an
			// index name above thirty, and every name of this app carries the
			// findling_ prefix so that an index of ours is recognisable in a
			// database an admin is looking at for the first time.
			$table->setPrimaryKey(['storage_id'], 'findling_ss_id');

			$changed = true;
		}

		return $changed ? $schema : null;
	}
}
