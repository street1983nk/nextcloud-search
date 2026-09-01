<?php

declare(strict_types=1);

namespace OCA\Findling\AppInfo;

use OCA\Findling\Listener\FileEventListener;
use OCA\Findling\Search\Provider;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
	public const APP_ID = 'findling';

	/**
	 * The ExApp counterpart in the External Apps section of the store. Both ids
	 * are frozen, see docs/store-identity.md: the app certificate is bound to
	 * them and a rename costs a new signing round.
	 */
	public const BACKEND_APP_ID = 'findling_backend';

	public function __construct(array $urlParams = []) {
		parent::__construct(self::APP_ID, $urlParams);
	}

	/**
	 * The provider registration belongs here and not in boot(). Registering it
	 * in boot() fails silently: no error, no entry in the provider list, no
	 * result group in the search bar. The same is true for the event listeners
	 * below, and for the same reason: boot() runs too late for the dispatcher.
	 */
	public function register(IRegistrationContext $context): void {
		$context->registerSearchProvider(Provider::class);

		// A loop and not four calls, because this list is the answer to "how
		// many ways are there from a file event into the queue". COMP-03 allows
		// exactly one, and one class registered for a list of events is a claim
		// a reader can check by counting lines. The class names are written out
		// here so that the list is complete on its own.
		//
		// Share is missing on purpose. It needs a counterpart in the container
		// before it may be queued (plan 03-04); an event without one would be a
		// row that travels through the whole queue to do nothing.
		//
		// Rename joined the list with plan 03-02, once the container had the
		// metadata job that runs it without a download, and the three events of
		// a deletion joined it with plan 03-03.
		//
		// The last two of them live in the trash bin app, which an admin may
		// have disabled. A listener on a class that does not exist on the
		// instance is harmless: the dispatcher compares class names as strings,
		// so the entry simply never matches an event. Nothing has to load the
		// class either, because the compiler resolves the constant into a
		// string without asking the autoloader.
		foreach ([
			\OCP\Files\Events\Node\NodeCreatedEvent::class,
			\OCP\Files\Events\Node\NodeWrittenEvent::class,
			\OCP\Files\Events\Node\NodeTouchedEvent::class,
			\OCP\Files\Events\Node\NodeCopiedEvent::class,
			\OCP\Files\Events\Node\NodeRenamedEvent::class,
			\OCP\Files\Events\Node\NodeDeletedEvent::class,
			\OCA\Files_Trashbin\Events\MoveToTrashEvent::class,
			\OCA\Files_Trashbin\Events\NodeRestoredEvent::class,
		] as $event) {
			$context->registerEventListener($event, FileEventListener::class);
		}
	}

	public function boot(IBootContext $context): void {
	}
}
