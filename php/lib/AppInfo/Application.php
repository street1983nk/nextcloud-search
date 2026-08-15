<?php

declare(strict_types=1);

namespace OCA\Findling\AppInfo;

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
	 * result group in the search bar.
	 */
	public function register(IRegistrationContext $context): void {
		$context->registerSearchProvider(Provider::class);
	}

	public function boot(IBootContext $context): void {
	}
}
