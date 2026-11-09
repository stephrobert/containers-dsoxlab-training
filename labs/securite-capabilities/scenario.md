# A service that stops when everything is taken away

A small job launcher was deployed with Docker's default capabilities. It runs
each of its jobs inside a **cell**: a directory it confines the job to with
`chroot`. It reports its state every second in `/run/lanceur/etat`.

The security review asks for the least privilege, and the advice is known:
drop every capability, then give back what the service needs. Nobody knows
which one that is. Dropping all of them and restarting is not enough: **the
launcher stops at startup**.

In `/opt/dsoxlab-securite-capabilities`, recreate the running `worker` so that
it runs again with **a single capability**, the one that makes it start, and
nothing else. Keep the project `dsoxlab-securite-capabilities`, its lab label
and `/proof`. The checks read both what Docker was asked and what the kernel
applies to PID 1, read the launcher's own report, then try a harmless ownership
change.

Only this disposable project is in scope. Do not change the daemon, do not use
privileged mode, and do not touch another container.
