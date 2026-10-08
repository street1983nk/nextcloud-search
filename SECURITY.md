# Security Policy

## Supported versions

Only the latest release of `findling` and `findling_backend` in the
[Nextcloud App Store](https://apps.nextcloud.com/apps/findling) is supported.
Both apps carry the same version; please update before reporting.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

- Preferred: GitHub private vulnerability reporting, via "Report a
  vulnerability" under the Security tab of this repository
- Alternative: mail to admin@infranode.dev

You will get a first answer within 7 days. Please include the Findling
version, your Nextcloud version, and steps to reproduce.

## Scope

Findling ships two apps: the `findling` companion app (PHP) and the
`findling_backend` External App (a Python container). Reports for both belong
here. The promises worth attacking: every search result is permission checked
by Nextcloud before it is shown, the routes that return indexed content are
not reachable from the browser, and nothing leaves your server. A report that
breaks one of these is the most valuable kind.
