# ENTWURF, Owner sendet, nicht gepostet; vor jedem "Closes #33"

Antwort auf street1983nk/nextcloud-search Issue #33 (FlattusBlastus, TrueNAS). Englisch, kurz. Erst diese Antwort posten, danach darf ein Commit das Issue schließen.

<!-- answer -->
Thanks a lot for the full log, it pointed straight at the cause. HaRP on TrueNAS kept its certificates outside a persistent volume, so every restart issued a new CA and the backend was left with the old client certificate. TrueNAS fixed that in truenas/apps #6254, merged on 27 October. After that app update, either copy the three certificate files into the backend once with the command in https://github.com/street1983nk/nextcloud-search/blob/main/docs/harp-tunnel.md#repair-without-re-registering, or re-register the app without --rm-data, which keeps your index. Findling 1.6.0 also names this state clearly in the container log and picks up copied files without a re-register or a restart. Could you let me know if that brings your tunnel back?
<!-- /answer -->
