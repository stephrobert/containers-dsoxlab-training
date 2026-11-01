# Scenario

A second Docker engine is prepared for dsoxlab-rootless. The rootful system daemon must remain untouched.

The daemon uses the dedicated account's systemd **user** service, not a
system-wide service with `User=`. Read the UID in
`/opt/dsoxlab-securite-rootless/state.json`, then run `systemctl --user`
as `dsoxlab-rootless` with `XDG_RUNTIME_DIR=/run/user/<uid>` and
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus`.
Setup owns this account and enables its user manager through lingering;
cleanup disables lingering and removes only this account's resources.

## Mission

The dedicated service is active, its process belongs to the unprivileged
account and its daemon reports rootless mode. Its separate engine must run a
real HTTP workload, allow the authorized network peer and refuse a
networkless peer. Fresh data in a named volume must survive container recreation.

The checks use a nonprivileged loopback port and a VM-local pinned image.
Explain the separate image store, UID mapping and limitations of rootless
networking. This lab does not qualify native privileged ports or high availability.
