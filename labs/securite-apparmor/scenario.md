# Write a policy that refuses by default

The worker holds two files in mode 444: Unix permissions allow both reads. No
AppArmor profile is loaded for this lab, and the starter is `unconfined`.

In `/opt/dsoxlab-securite-apparmor`, **write the profile, load it, and attach
it** to `worker`. `profile.modele` is a template carrying the imposed name and
the method; complete it. Keep `/lab/public.txt` readable and make
`/lab/private.txt` unreadable **by mandatory policy, not by chmod**: both files
must stay in mode 444.

**Refuse by omission, not with a `deny` rule.** An explicit `deny` applies even
in `complain` mode, so a profile built that way returns the same verdict in both
modes and proves nothing about the one in force. A permission you never name is
refused in `enforce` only, because `complain` permits and logs whatever is not
allowed. The service must create `/lab/private.txt`, so grant the write and
never name the read.

**A policy names what the service needs and refuses the rest.** A bare `file,`
rule, or a bare `capability,` or `network,` rule, allows everything and turns the
profile into a one-line blacklist. The lab checks this by reading `/etc/shadow`,
which a service handling two files in `/lab` has no reason to read.

The method is the real one, and the template spells it out: load in `complain`,
start the service, read the refusals the kernel logged with
`dmesg | grep 'apparmor="DENIED"'`, add the matching rule, repeat, then drop
`complain` and reload.

Change no other profile, do not disable AppArmor, do not leave the profile in
`complain`, and do not touch `/etc/apparmor.d`: a profile loaded with
`apparmor_parser` lives until it is unloaded, and cleanup removes only the one
this lab owns.
