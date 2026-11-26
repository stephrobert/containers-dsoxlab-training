# Write a policy that refuses by default

## The situation

On `docker.lab`, the `worker` of project `dsoxlab-securite-apparmor` creates two
files in mode 444, `/lab/public.txt` and `/lab/private.txt`. Unix permissions let
both be read. The service is `unconfined`, and no profile is loaded for it. The
project is in `/opt/dsoxlab-securite-apparmor`, with `profile.modele`, a template
to complete.

## Mission

1. **Write** the `dsoxlab-securite-apparmor` profile from `profile.modele`,
   **load it**, and attach it to `worker`.
2. PID 1 reports that profile in `enforce` mode.
3. `/lab/public.txt` returns `public`. `/lab/private.txt` stays in mode 444, and
   reading it fails with Permission denied.
4. The profile **refuses by default**: no bare `file,`, `capability,` or
   `network,`. The check tries to read `/etc/shadow` from the container.

**The refusal comes from an omission, not from a `deny` rule**: a `deny` applies in
`complain` too, and would prove nothing about the mode in force. The service must
be able to create `/lab/private.txt`: grant it the write, not the read.

## The method

Load the profile in `complain`, start the service, and note what the kernel would
have refused. In `complain`, it records it as `ALLOWED`:

```bash
sudo dmesg | grep 'apparmor="ALLOWED"'
```

Add the matching rule, repeat, then remove `complain` and reload. Once in
`enforce`, a refusal reads `DENIED`.

This method shows what the service attempted. Here it will not show
`signal (receive) peer=runc,`, because this PID 1 ignores SIGTERM. Add it anyway:
without it, `docker stop` cannot cleanly stop a service that handles that signal.

Keep the project and the `dsoxlab.lab=securite-apparmor` label. Change no other
profile, do not disable AppArmor and do not touch `/etc/apparmor.d`: a profile
loaded with `apparmor_parser` lives until it is removed, and the cleanup removes
only this lab's.
