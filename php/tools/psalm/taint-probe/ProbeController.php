<?php

declare(strict_types=1);

// Positive control of the Psalm taint gate (scripts/ci/psalm_taint_gate.sh).
//
// This file holds two deliberate taint flows. It lives outside lib/ and tests/
// on purpose, so it is neither analysed by the real gate run nor autoloaded by
// the unit suite. Only the gate copies it into lib/TaintProbe/ of the CI runner
// workspace (or of the local mirror), runs Psalm a second time and demands that
// both flows are reported, then deletes the copy again. A gate that cannot see
// these two flows is blind and proves nothing about the app.
//
// - show(): a route parameter echoed unescaped. Psalm reports TaintedHtml only
//   with the AppFrameworkTainter plugin, so this proves the plugin is active.
// - lookup(): IRequest::getParam() into a query expression. Psalm reports
//   TaintedSql through the taint annotations of nextcloud/ocp, so this proves
//   the OCP version under analysis still carries them.
//
// Never copy it to lib/Controller/: the route security tests of the unit suite
// enumerate that directory and would fail on a controller without routes.

namespace OCA\Findling\TaintProbe;

use OCP\AppFramework\Controller;
use OCP\IDBConnection;
use OCP\IRequest;

final class ProbeController extends Controller {
	public function __construct(
		IRequest $request,
		private IDBConnection $db,
	) {
		parent::__construct('findling', $request);
	}

	public function show(string $needle): void {
		echo $needle;
	}

	public function lookup(): void {
		$qb = $this->db->getQueryBuilder();
		$qb->select('*')
			->from('findling_probe')
			->where($qb->expr()->eq('name', $this->request->getParam('column')));
		$qb->executeQuery();
	}
}
