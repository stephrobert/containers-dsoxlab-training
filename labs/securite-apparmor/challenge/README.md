# Brief

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
