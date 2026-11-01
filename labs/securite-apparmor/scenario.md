# Two readable files, one mandatory denial

The worker contains two mode-444 files. Unix permissions allow both reads.
A dedicated AppArmor profile is already loaded, but the starter container is
unconfined and does not use it.

In `/opt/dsoxlab-securite-apparmor`, confine `worker` with the existing
`dsoxlab-securite-apparmor` profile. Keep `/lab/public.txt` readable and make
`/lab/private.txt` unreadable through mandatory policy, not chmod.

Do not modify other profiles, switch AppArmor off, use complain mode or edit
`/etc/apparmor.d`. Cleanup unloads only the newly created lab profile.
