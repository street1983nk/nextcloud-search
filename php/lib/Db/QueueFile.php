<?php

declare(strict_types=1);

namespace OCA\Findling\Db;

use OCP\AppFramework\Db\Entity;

/**
 * One row of the work stock.
 *
 * Metadata only. The bytes of a file never travel through the queue, they are
 * fetched separately through the content gateway once a worker is actually
 * free, so a claimed batch stays small no matter how large the documents are.
 *
 * @method int getFileId()
 * @method void setFileId(int $fileId)
 * @method int getStorageId()
 * @method void setStorageId(int $storageId)
 * @method int getRootId()
 * @method void setRootId(int $rootId)
 * @method bool getIsUpdate()
 * @method void setIsUpdate(bool $isUpdate)
 * @method int|null getSize()
 * @method void setSize(?int $size)
 * @method string|null getLockedAt()
 * @method void setLockedAt(?string $lockedAt)
 * @method int getRetries()
 * @method void setRetries(int $retries)
 * @method bool getDirty()
 * @method void setDirty(bool $dirty)
 * @method string|null getClaimToken()
 * @method void setClaimToken(?string $claimToken)
 */
class QueueFile extends Entity {
	protected int $fileId = 0;
	protected int $storageId = 0;
	protected int $rootId = 0;
	protected bool $isUpdate = false;
	protected ?int $size = null;
	protected int $retries = 0;

	// Set while a claim is open and the file changed underneath it; the
	// acknowledgement then requeues the row instead of deleting it.
	protected bool $dirty = false;

	// Identifies the winners of one batch claim, see QueueMapper::claimBatch.
	protected ?string $claimToken = null;

	/**
	 * Deliberately a string and deliberately without a registered type.
	 *
	 * Nothing in this app reads the lock time out of an entity: the claim
	 * compares it inside the database and never in PHP, because comparing there
	 * would reintroduce exactly the race the conditional update avoids. Leaving
	 * it untyped keeps the value the driver hands back, instead of pushing it
	 * through a date conversion that only exists to be ignored.
	 */
	protected ?string $lockedAt = null;

	public function __construct() {
		$this->addType('fileId', 'integer');
		$this->addType('storageId', 'integer');
		$this->addType('rootId', 'integer');
		$this->addType('size', 'integer');
		$this->addType('retries', 'integer');
		$this->addType('isUpdate', 'boolean');
		$this->addType('dirty', 'boolean');
	}
}
