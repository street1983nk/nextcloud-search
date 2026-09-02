<?php

declare(strict_types=1);

namespace OCA\Findling\Command;

use OCA\Findling\Service\AdminViewService;
use OCP\IGroupManager;
use OCP\IUser;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

/**
 * The second way to the per file diagnosis: `occ findling:diagnose <reference>`.
 *
 * Why this exists although the settings page exists. It is the only way to the
 * diagnosis without a browser and without a session, and that is exactly the way
 * a support case takes: somebody has a shell on the server, a user reports that
 * one document is not found, and the answer must not depend on logging into a
 * web interface first. A session cannot be borrowed from the outside either,
 * because the admin route of this app demands the request token of a real
 * browser session, so a curl call with credentials does not reach it at all.
 * `backend/src/findling/tools/index_status.py` is the same thought on the
 * container side: the same numbers, reachable from a shell, without a signed
 * header.
 *
 * The second thing worth writing down is what this command does NOT do. It
 * calls `AdminViewService::diagnose()`, the very method the route calls, and it
 * holds no state logic of its own: not one stage of the six stage precedence
 * rule is repeated here, and no state name is even spelled in this file. So
 * there is no second precedence rule that could drift away from the page, and a
 * file that reads "excluded by a rule" in the browser reads "excluded by a rule"
 * here. All this class owns is the printing.
 *
 * The identity of the call is the one thing occ has to answer differently. There
 * is no session, so there is no session user, and `ExAppService::adminGet` needs
 * a user id because `exAppRequest` signs the AppAPI header with it. The first
 * enabled member of the admin group is taken for that, and it is used for
 * nothing else: the route of the container reads no identity, and this side
 * makes no permission decision out of it either, because an administrator on the
 * machine is allowed to be told the state of a file on their own instance. Where
 * no such member can be determined the field stays empty, `adminGet` refuses the
 * call in the one place that logs it, and the output says that the backend did
 * not answer rather than claiming a state. That case is a real one on an
 * instance whose administration was delegated to a group of another name, and
 * saying "the backend did not answer" there is honest, while a silently empty
 * answer would look like a broken command.
 *
 * No file content, ever, and for the same reason the page carries none: a text
 * excerpt is file content and stays bound to SRCH-02. What this command prints
 * is metadata and a verdict, which is what an administrator on the machine could
 * read from the disk anyway (T-04-61).
 */
class DiagnoseCommand extends Command {
	/**
	 * The ceiling on the reference, and it is the same 4096 characters
	 * SettingsController refuses above.
	 *
	 * A second copy of that number rather than a shared constant, because the
	 * controller keeps it private and the two refusals answer for different
	 * transports. What matters is that both refuse rather than cut: a cut
	 * reference would answer about a different file.
	 */
	private const MAX_REFERENCE_LENGTH = 4096;

	/** The group whose members Nextcloud treats as administrators. */
	private const ADMIN_GROUP = 'admin';

	/** Width of the label column, the same one IndexCommand prints with. */
	private const LABEL_WIDTH = 20;

	public function __construct(
		private AdminViewService $view,
		private IGroupManager $groupManager,
	) {
		parent::__construct();
	}

	protected function configure(): void {
		$this
			->setName('findling:diagnose')
			->setDescription('Say what state one file is in and why')
			->addArgument(
				'reference',
				InputArgument::REQUIRED,
				'A path the way Nextcloud keeps it, "alice/files/Ordner/x.pdf" or the short form '
					. '"alice:Ordner/x.pdf", or the numeric file id out of the error list.',
			);
	}

	protected function execute(InputInterface $input, OutputInterface $output): int {
		$argument = $input->getArgument('reference');
		$reference = is_string($argument) ? trim($argument) : '';

		if ($reference === '' || strlen($reference) > self::MAX_REFERENCE_LENGTH) {
			// A static sentence, and the value is not part of it. What arrives in
			// this argument is a file name, and the output of this command is
			// read out of a terminal that is usually being logged somewhere, so
			// the refusal names the case and never the input (T-04-38).
			$output->writeln('<error>Malformed file reference.</error>');

			return Command::INVALID;
		}

		$answer = $this->view->diagnose($reference, $this->adminUserId());

		if ($answer['found'] !== true) {
			// Not an error of this command, so not an error exit either: "this
			// reference names no file on this instance" is an answer, and it is
			// the answer a mistyped path, a deleted file and a reference this app
			// refuses to interpret all get. Three distinguishable answers here
			// would turn the argument into a way of asking which users exist.
			$output->writeln('<comment>This reference does not name a file on this instance.</comment>');
			$output->writeln('');
		}

		$this->report($output, $answer);

		return Command::SUCCESS;
	}

	/**
	 * The answer, in the column form of IndexCommand.
	 *
	 * Every field of it, including the ones that are empty, because a column
	 * that disappears when it has nothing in it leaves the reader unable to tell
	 * "no reason code" from "this command does not print reason codes". A dash
	 * stands where there is nothing.
	 *
	 * @param array{
	 *     found:bool, fileId:int, path:string, uid:string, trashed:bool,
	 *     shares:int, state:string, reason:string, label:string, remedy:string,
	 *     checkedAt:int, backendReachable:bool, note:string
	 * } $answer
	 */
	private function report(OutputInterface $output, array $answer): void {
		$output->writeln('Verdict');
		$this->line($output, 'state', $answer['state']);
		$this->line($output, 'reason code', $answer['reason']);
		$this->line($output, 'label', $answer['label']);
		$this->line($output, 'remedy', $answer['remedy']);
		$output->writeln('');

		$output->writeln('File');
		$this->line($output, 'file id', $answer['fileId'] > 0 ? (string)$answer['fileId'] : '');
		$this->line($output, 'path', $answer['path']);
		$this->line($output, 'owner', $answer['uid']);
		$this->line($output, 'in the trash bin', $answer['trashed'] ? 'yes' : 'no');
		$this->line($output, 'shared', $answer['shares'] > 0 ? (string)$answer['shares'] : 'no');
		$output->writeln('');

		$output->writeln('Sources');
		$this->line(
			$output,
			'last checked',
			$answer['checkedAt'] > 0 ? date('Y-m-d H:i:s', $answer['checkedAt']) : '',
		);
		$this->line($output, 'backend answered', $answer['backendReachable'] ? 'yes' : 'no');

		if ($answer['note'] !== '') {
			$output->writeln('');
			$output->writeln($answer['note']);
		}

		if (!$answer['backendReachable'] && $answer['note'] === '') {
			// The distinction this whole phase is about, and it has to survive the
			// move to a terminal: with the container silent nothing here may be
			// read as "not indexed", so the sentence says which half is missing.
			// Only where the answer carries no note of its own, because the note
			// of a verdict that fell to the silent container already says it, and
			// saying it twice reads like a defect of the command.
			$output->writeln('');
			$output->writeln('<comment>The backend did not answer, so whatever only the index knows is missing above.</comment>');
		}
	}

	/**
	 * One label and one value, with a dash for nothing.
	 */
	private function line(OutputInterface $output, string $label, string $value): void {
		$output->writeln(sprintf('  %-' . self::LABEL_WIDTH . 's %s', $label, $value === '' ? '-' : $value));
	}

	/**
	 * The identity the call to the container travels under, without a session.
	 *
	 * The first enabled member of the admin group, and an empty string when there
	 * is none. Empty is left empty rather than filled with a fixed name, exactly
	 * as `AdminViewService::userId()` does it for the page: a call under an
	 * identity nobody chose would succeed while answering for a user that may not
	 * exist, and failing in `ExAppService`, where the failure has a log line, is
	 * the readable outcome.
	 */
	private function adminUserId(): string {
		$group = $this->groupManager->get(self::ADMIN_GROUP);
		if ($group === null) {
			return '';
		}

		foreach ($group->getUsers() as $user) {
			if ($user instanceof IUser && $user->isEnabled()) {
				return $user->getUID();
			}
		}

		return '';
	}
}
