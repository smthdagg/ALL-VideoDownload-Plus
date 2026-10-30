# Navigation and Cookie consolidation — 2026-10-28

Start, Settings and the visible Telegram command list now share one role-aware model. Administrators get a separate User management entry; personal preferences and Cookie import are available to approved users under Settings.

Settings categories: Download preferences, Cookies & accounts, Interface & language, Files & activity, Advanced settings. Download actions are grouped under Download tools on Start. Cookie upload is the sole visible account-update flow. Previously posted Cookie buttons redirect to it; obsolete per-platform admin update commands are excluded from all updated command scopes.

The command scopes are replaced deterministically rather than merged with old Telegram commands: start/settings/cookie/help, plus users for administrator chats. Underlying advanced handlers remain compatible. Navigation targets are tested against actual command handlers; administrator visibility, absence of duplicate buttons and legacy Cookie routing are covered.

Verification:97 local tests pass; generated sources compile; full generator reruns successfully. Candidate image retains the existing dependency stack. Deployment verification and privacy review are recorded separately from public source. No account IDs, hostnames, tokens or Cookie values are needed in this document.
