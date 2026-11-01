# Linux capabilities

Linux splits root authority into capabilities. Docker's default subset is
smaller than host root's, but may still exceed an application's needs.
`cap_drop` removes capabilities; `cap_add` restores explicitly required ones.
Recreation is necessary: editing Compose does not change an existing process.

For a neutral disposable project `demo-clock`, compare `docker inspect`'s
`HostConfig.CapDrop` and `CapAdd` with `CapEff` in `/proc/1/status`.
The mask is hexadecimal: bit 0 is CHOWN, bit 10 is NET_BIND_SERVICE. A declared
option and a kernel-observed capability are different evidence.

A high-port HTTP service generally needs no capability at all. Do not assume a
successful low-port bind proves NET_BIND_SERVICE: the network namespace's
`ip_unprivileged_port_start` can make those ports unprivileged.

See [the challenge](challenge/README.md). The engine must already be available.
Setup and cleanup preserve existing images and daemon settings.
