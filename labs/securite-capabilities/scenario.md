# A service with too many privileges

A small worker was deployed with Docker's default root capabilities. Its only
required privilege is binding a privileged port. Ownership changes are not part
of its job.

In `/opt/dsoxlab-securite-capabilities`, reduce the running `worker` to exactly
NET_BIND_SERVICE. Keep the project `dsoxlab-securite-capabilities`, its lab label
and `/proof`. The checker observes both Docker's configuration and PID 1's
effective capability mask, then attempts a harmless ownership change.

Only this disposable project is in scope. Do not change the daemon, use
privileged mode or touch another container.
