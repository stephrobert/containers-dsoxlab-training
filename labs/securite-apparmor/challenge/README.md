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

One rule the method will not reveal on this lab, and that you need to know:
`signal (receive) peer=runc,`. Without it, a dedicated profile denies runc the
right to send SIGTERM to the service, and `docker stop` cleans nothing up: twelve
seconds, then SIGKILL and exit code 137. This service's PID 1 installs no signal
handler, so it ignores SIGTERM anyway and the denial is never even attempted:
`complain` therefore does not log it. That is the limit of the method, and it is
worth knowing: it shows what the service **attempted**, never what another
service would attempt.

The method is the real one, and the template spells it out: load in `complain`,
start the service, read the refusals the kernel logged with
`dmesg | grep 'apparmor="DENIED"'`, add the matching rule, repeat, then drop
`complain` and reload.

Change no other profile, do not disable AppArmor, do not leave the profile in
`complain`, and do not touch `/etc/apparmor.d`: a profile loaded with
`apparmor_parser` lives until it is unloaded, and cleanup removes only the one
this lab owns.

## Brief

Work on `docker.lab`, in `/opt/dsoxlab-securite-apparmor`.

1. Keep `worker` active in project `dsoxlab-securite-apparmor`,
   label `dsoxlab.lab=securite-apparmor`.
2. **Write** the `dsoxlab-securite-apparmor` profile from `profile.modele`,
   **load it** yourself, and attach it to the service. No profile is loaded to
   begin with, and the starter is `unconfined`.
3. PID 1 must report that profile in `enforce` mode, not `complain`.
4. `/lab/public.txt` must still return `public`.
5. `/lab/private.txt` must remain mode 444, but reading it must fail with
   Permission denied. **The refusal must come from omitting the read
   permission, not from a `deny` rule**: an explicit `deny` applies in
   `complain` too, and would prove nothing about the mode in force.
6. The profile must **refuse by default**: no bare `file,` `capability,` or
   `network,` rule. The check reads `/etc/shadow` from inside the container,
   which a service handling two files in `/lab` has no reason to read.

Only this new profile is in scope. Do not reload or change any existing policy.
