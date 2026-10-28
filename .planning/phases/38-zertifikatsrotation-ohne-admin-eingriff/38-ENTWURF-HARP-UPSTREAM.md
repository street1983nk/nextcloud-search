# ENTWURF, Owner sendet, vor dem Senden HaRP main erneut lesen, Research gültig bis 27.11.2026

Issue-Entwurf für nextcloud/HaRP. Nicht gepostet. Vor dem Senden prüfen, ob HaRP inzwischen selbst neu verteilt (start.sh, haproxy_agent.py) und ob #107 wieder offen ist.

---

**Title:** Redistribute FRP client certificates to running ExApps when the CA is regenerated

**Problem**

ExApps embed the FRP certificates at install time (README, section on certificate expiry). `start.sh` regenerates `/certs/frp` only when it is missing, which is right, but without a persistent `/certs` volume every HaRP restart issues a new CA `harp.nc`. From then on every running ExApp fails with `x509: certificate signed by unknown authority` until it is unregistered and registered again. We saw this on TrueNAS (fixed there in truenas/apps #6254), and #107 raised the same concern about renewal.

**Proposal**

After `start.sh` (or the agent at startup) has generated new certificates, call the existing `_install_frp_certificates` for every running `nc_app_*` container, so the copies inside the ExApps match the new CA again. frpc reads the certificate files on every dial, so the ExApps reconnect without a restart. An alternative is a documented AppAPI call that redistributes the certificates without a re-register.

**Compatibility**

Only an additional distribution of the same files to the same path, no format change. ExApps that never use mutual TLS are not affected.

I am happy to write a PR for this if the approach sounds right to you.
