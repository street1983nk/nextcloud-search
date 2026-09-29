---
status: diagnosed
trigger: "Issue #14 (budachst, comment 2026-09-29T17:49:53Z): Team Folder files with advanced permissions are marked skipped(unreadable) although all 3 group members may read them per ACL"
created: 2026-09-29
updated: 2026-09-29
goal: find_root_cause_only
---

# Debug: issue14-acl-unreadable

## Symptoms

DATA_START
- **Expected:** A Team Folder file that a mount member may read under the groupfolders ACL is claimed and indexed through that member (QueueService::readerOf -> SearchService::readableFile).
- **Actual:** ~250k files on budachst's instance end as skipped(unreadable) ("Für die gefragten Nutzer nicht lesbar"); coverage 22 %. occ findling:diagnose 2198634 shows path `<user>/files/603330_B_plus_M/b_plus_m_baustoff_&_metall_handels_gmbh/.../Links/Steffen Lorenz_Heilbronn_151_Innendienst.jpg`, state Übersprungen, reason unreadable.
- **ACL (occ groupfolders:permissions 62):** `/` group `/a-603330` +read -write -create -delete -share; group `/u-603330` same. Subfolder `b_plus_m_baustoff_&_metall_handels_gmbh`: both groups +read +write +create +delete -share. The user group has only 3 members, `<user>` is one of them. So the 20-name cap (MAX_READER_TRIES) is not the cause.
- **Errors:** none reported besides the verdict.
- **Timeline:** after the 1.3.0 fix for issue #14 (readerOf loop over mount users instead of first alphabetical user); the previous "gone" verdict is now "unreadable".
- **Side findings:** the admin page error list shows no file ids; clicking an entry answers "Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID." (lookup apparently as the admin, who is not a member of the Team Folder).
DATA_END

## Hypotheses (initial, unverified)

1. groupfolders evaluates the ACL in the context of the ExApp claim request (AppAPI request, no or wrong session user) instead of the asked member, so isReadable() or getFirstNodeById() fails for every member.
2. Group ids with a leading `/` (SSO/LDAP style) break the ACL mapping lookup.
3. Group membership cannot be resolved in the claim/background context (user backend provides groups only at login).

## Reproduction plan

HaRP harness http://localhost:8096 (container findling-harp-nextcloud, admin password in .dev/probe-live/adminpass, untracked). Install/enable groupfolders, enable ACL on a folder, groups `/a-test` and `/u-test` with 3 members, ACL rules as above, create files, drive the real claim route (ExApp) and occ findling:diagnose; compare with a folder without ACL and with group ids without leading `/`.

## Constraints

Diagnosis and root cause only; fix only after owner approval. No push, no GitHub posts. Harness only, leave it in a clean state or document what was added. Phase 28 planning runs in parallel in .planning/phases/28-abnahme-anfahrt (do not touch).

## Current Focus

hypothesis: CONFIRMED. groupfolders' inShare heuristic (non-CLI request whose session user != mount user) demands READ+SHARE; ACL -share hides the file from every member during the HTTP claim
next_action: none (diagnose only); fix awaits owner decision

## Harness state added (clean up or keep documented)

- /var/www/html/custom_apps chown root -> www-data (needed for app:install)
- groupfolders 22.0.6 installed + enabled in findling-harp-nextcloud

## Evidence

- timestamp: 2026-09-29
  checked: QueueService::readerOf / SearchService::readableFile
  found: readerOf loops first MAX_READER_TRIES sorted users, rootFolder->getUserFolder(uid), then getFirstNodeById(fileId) + isReadable(). Null for all -> SKIP_UNREADABLE.
  implication: verdict unreadable means getFirstNodeById returned non-File or isReadable false for every tried member.

- timestamp: 2026-09-29
  checked: harness setup. users i14u1..3 (pw Pw-issue14-xyz!), groups /a-test /u-test a-plain u-plain (all 3 members each); groupfolders 1 I14SlashAcl (/a-test,/u-test, ACL on), 2 I14PlainAcl (a-plain,u-plain, ACL on), 3 I14SlashNoAcl (/a-test,/u-test, ACL off); ACL rules on 1+2 exactly as in issue (/ +read -write -create -delete -share; subfolder b_plus_m_baustoff_&_metall +read +write +create +delete -share). Test files 735-744, probe uploads 953/954/955.
  found: CLI probe (php script, getUserFolder(uid)->getFirstNodeById + SearchService::readableFile) returns a readable File for every member in all three folders, incl. slash groups. perms 11 deep / 1 top in ACL folders.
  implication: ACL rules and slash group ids evaluate correctly in CLI context.

- timestamp: 2026-09-29
  checked: real claim path: WebDAV PUT as i14u1 into each folder's subfolder -> event -> ExApp claim over HTTP -> occ findling:diagnose
  found: 953 (slash+ACL) skipped/unreadable; 954 (plain+ACL) skipped/unreadable; 955 (slash, no ACL) claimed (queued embed). Bug reproduced exactly.
  implication: leading slash irrelevant (H2 eliminated); failure is specific to ACL + HTTP claim context.

- timestamp: 2026-09-29
  checked: groupfolders 22.0.6 source lib/Mount/MountProvider.php:233, ACL/ACLCacheWrapper.php:43, ACL/ACLStorageWrapper.php:41
  found: `$inShare = !OC::$CLI && (getCurrentUID() === null || getCurrentUID() !== $user->getUID());` When inShare, ACL wrappers require READ+SHARE (minPermissions = READ|SHARE), else permissions collapse to 0 and formatCacheEntry returns false (node hidden).
  implication: in the ExApp claim request the session user is not the mount user, so every member's mount is built as "in share"; with -share in the ACL every file is hidden -> getFirstNodeById null for everyone -> unreadable. CLI (occ diagnose, cron) has OC::$CLI=true and does not hit this.

- timestamp: 2026-09-29
  checked: web-context emulation (php script, \OC::$CLI=false) for 953/955, session user none / admin / i14u1
  found: session none or admin: 953 null for all three members, 955 File for all. session i14u1: 953 File only for i14u1, null for u2/u3.
  implication: readability depends exactly on session user == asked member. Mechanism confirmed.

- timestamp: 2026-09-29
  checked: falsification test: folder 2 subfolder ACL -> +share, new upload 956 via WebDAV
  found: 956 claimed and indexed through the real HTTP claim; 954 (same folder, before flip) stays unreadable. ACL reverted to -share afterwards.
  implication: the share bit alone decides; H2 (slash) and H3 (group resolution) eliminated.

- timestamp: 2026-09-29
  checked: fix direction probe: IUserSession::setVolatileActiveUser(member) (OCP since 29) before getUserFolder(member), restore in finally
  found: all three members get readableFile=File for 953. BUT if the member's mount was already set up earlier in the same process without the swap, the swap does not help (mount cached per request): u1 stays null.
  implication: swap must happen before the first mount setup of that user in the request; readerOf's per-claim folder cache and any earlier getUserFolder in the request are the pitfalls.

- timestamp: 2026-09-29
  checked: side finding. GET /index.php/apps/findling/admin/diagnose?ref=... as admin (HTTP); admin/overview errors.examples; php/js/admin.js:870ff
  found: overview examples carry fileId+path+reference (resolved:true). The click sends the path when one exists. ref=953 -> found; ref=i14u2/files/I14SlashAcl/... (ACL, -share) -> found:false; same form for no-ACL 955 and for +share 956 -> found. PathResolverService::fileIdForUser/fileIdOverMounts call getUserFolder(member)->get(path) inside the admin request (session=admin) -> inShare -> hidden.
  implication: side finding has the same root cause. (Minor aside: ref=i14u1/files/... fails even for the no-ACL file 955 while i14u2/files/... works; the owner form apparently only accepts the reported owner uid. Not investigated further.)

## Eliminated

- hypothesis: H2 group ids with leading `/` break the ACL mapping
  evidence: plain group ids (folder 2) fail identically (954); slash groups resolve fine in CLI and when session user == member
  timestamp: 2026-09-29
- hypothesis: H3 group membership not resolvable in claim context
  evidence: same membership, only share bit flipped -> readable (956); session swap -> readable
  timestamp: 2026-09-29
- hypothesis: H1 as stated (ACL evaluated for the wrong user)
  evidence: refined, ACL rules ARE evaluated for the asked member (ACLManager per mount user); what depends on the session user is groupfolders' in_share flag, which raises the minimum from READ to READ+SHARE
  timestamp: 2026-09-29

## Resolution

root_cause: groupfolders (22.0.6, MountProvider::getGroupFolderStorage L233) builds a Team Folder mount with in_share=true whenever the request is not CLI and the session user is not the mount user. With in_share the ACL wrappers (ACLCacheWrapper L43, ACLStorageWrapper L41) treat a path as readable only if the ACL grants READ AND SHARE, otherwise the cache entry is dropped (node hidden). Findling's claim (QueueController GET /queues/documents, ExApp request, session user = none/ExApp) and content gateway (GatewayController L74) and the admin path lookup (PathResolverService, session = admin) all call getUserFolder(member) in such a request. budachst's ACL denies share everywhere (-share), so every member's node is hidden, readerOf finds no reader -> skipped(unreadable) for ~250k files. occ findling:diagnose runs in CLI (in_share=false) and therefore cannot see the problem.
fix: (not applied, diagnose only)
verification: reproduced on HaRP harness: 953/954 unreadable, 955 no-ACL indexed, 956 +share indexed
files_changed: []

## Harness state left in place (documented)

- custom_apps owner www-data; groupfolders 22.0.6 enabled
- users i14u1 i14u2 i14u3 (pw Pw-issue14-xyz!); groups /a-test /u-test a-plain u-plain
- groupfolders 1 I14SlashAcl, 2 I14PlainAcl (ACL as in issue, -share), 3 I14SlashNoAcl
- files 735-744, 953-956 (states in oc_findling_file_state)
- temp scripts in container /tmp removed; cookie jar i14admin removed
