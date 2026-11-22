# Antworten Phase 45

## #59

Entwurf (vom Owner freigegeben 2026-11-22 08:28):

Thanks a lot for this report, and for tracing it all the way down to `readerOf()` and the secure view wrapper. That saved a lot of time.

You were right on every point: Findling picked the alphabetically first user who could see the file, the content fetch for that user was blocked by the secure view policy, no other reader was tried, and the admin page blamed the storage.

Fixed in 1.7.0:

- The owner of a file is now tried first when they can see it, then everyone else in alphabetical order.
- If the secure view policy refuses the fetch, Findling retries it as the file's owner before giving up.
- A refusal by a policy is shown as such on the admin page instead of "storage was not available".

Your two files should be indexed after the update. If they still show up under errors, please let me know.

Abgleich mit dem Fix: offen (45-21)
