<?php

/**
 * SPDX-FileCopyrightText: 2020 Nextcloud GmbH and Nextcloud contributors
 * SPDX-License-Identifier: MIT
 */
// Copied unchanged from nextcloud/server build/psalm/AppFrameworkTainter.php,
// branch master at commit 3a161f74fb6710eca56c0b250aadb81db9e9c625
// (blob 448922d25a5de9113979675250387d0dd999605f), fetched 2026-11-21.
// It turns every parameter of a public method of an OCP\AppFramework\Controller
// into a taint source; without it Psalm does not see route parameters as input.
// Works with vimeo/psalm 6.x only (Psalm 7 removed Psalm\Type\TaintKindGroup).
use Psalm\CodeLocation;
use Psalm\Plugin\EventHandler\AfterFunctionLikeAnalysisInterface;
use Psalm\Plugin\EventHandler\Event\AfterFunctionLikeAnalysisEvent;
use Psalm\Type\TaintKindGroup;

class AppFrameworkTainter implements AfterFunctionLikeAnalysisInterface {
	public static function afterStatementAnalysis(AfterFunctionLikeAnalysisEvent $event): ?bool {
		if ($event->getStatementsSource()->getFQCLN() === null) {
			return null;
		}
		if (!$event->getCodebase()->classExtendsOrImplements($event->getStatementsSource()->getFQCLN(), \OCP\AppFramework\Controller::class)) {
			return null;
		}
		if (!($event->getStmt() instanceof PhpParser\Node\Stmt\ClassMethod)) {
			return null;
		}
		if (!$event->getStmt()->isPublic() || $event->getStmt()->isMagic()) {
			return null;
		}
		foreach ($event->getStmt()->params as $i => $param) {
			$expr_type = new Psalm\Type\Union([new Psalm\Type\Atomic\TString()]);
			$expr_identifier = (strtolower($event->getStatementsSource()->getFQCLN()) . '::' . strtolower($event->getFunctionlikeStorage()->cased_name) . '#' . ($i + 1));
			$event->getCodebase()->addTaintSource(
				$expr_type,
				$expr_identifier,
				TaintKindGroup::ALL_INPUT,
				new CodeLocation($event->getStatementsSource(), $param)
			);
		}

		return null;
	}
}
