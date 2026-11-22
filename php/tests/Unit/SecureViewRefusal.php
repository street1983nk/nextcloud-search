<?php

declare(strict_types=1);

namespace OCA\Findling\Tests\Unit;

use OCP\Files\ForbiddenException;

/**
 * The refusals the content gateway has to tell apart (issue #59), built
 * without richdocuments.
 *
 * The real one, measured on the reproduction of plan 45-17 (45-AUDIT.md, "Ein
 * echter Secure-View-Logeintrag"): an OCP ForbiddenException with the message
 * 'Download blocked due the secure view policy', thrown in
 * SecureViewWrapper::checkFileAccess and called from SecureViewWrapper::fopen,
 * so the first frame of its trace is the one of checkFileAccess. richdocuments
 * is not in the autoload space of the test checkout, and the class must not be
 * loaded by the gateway either, so the trace is set on the exception instead of
 * being produced by a stand-in class of that name.
 */
final class SecureViewRefusal {
	public const MESSAGE = 'Download blocked due the secure view policy';
	public const WRAPPER = 'OCA\\Richdocuments\\Storage\\SecureViewWrapper';

	/**
	 * The refusal of the secure view, with the frames of the real log entry.
	 */
	public static function real(): ForbiddenException {
		return self::forbidden(self::MESSAGE, [
			self::frame(self::WRAPPER, 'checkFileAccess', 47),
			self::frame(self::WRAPPER, 'fopen', 1233),
			self::frame('OC\\Files\\View', 'basicOperation', 1062),
		]);
	}

	/**
	 * The same message, and the frame of checkFileAccess only further up: the
	 * first frame belongs to somebody else.
	 */
	public static function frameFurtherUp(): ForbiddenException {
		return self::forbidden(self::MESSAGE, [
			self::frame('OCA\\Other\\Storage\\Wrapper', 'fopen', 12),
			self::frame(self::WRAPPER, 'checkFileAccess', 47),
			self::frame(self::WRAPPER, 'fopen', 1233),
		]);
	}

	/**
	 * The frame of checkFileAccess, and another message.
	 */
	public static function otherMessage(): ForbiddenException {
		return self::forbidden('Access denied by access control', [
			self::frame(self::WRAPPER, 'checkFileAccess', 47),
			self::frame(self::WRAPPER, 'fopen', 1233),
		]);
	}

	/**
	 * The refusal of files_accesscontrol (I-45-17-03): another message and
	 * another origin.
	 */
	public static function accessControl(): ForbiddenException {
		return self::forbidden('Access denied by access control', [
			self::frame('OCA\\FilesAccessControl\\Operation', 'checkFileAccess', 118),
			self::frame('OCA\\FilesAccessControl\\StorageWrapper', 'fopen', 249),
		]);
	}

	/**
	 * @param list<array<string, mixed>> $trace
	 */
	private static function forbidden(string $message, array $trace): ForbiddenException {
		$exception = new ForbiddenException($message, false);
		(new \ReflectionProperty(\Exception::class, 'trace'))->setValue($exception, $trace);

		return $exception;
	}

	/**
	 * @return array<string, mixed>
	 */
	private static function frame(string $class, string $function, int $line): array {
		return ['file' => 'SecureViewWrapper.php', 'line' => $line, 'function' => $function, 'class' => $class, 'type' => '->'];
	}
}
