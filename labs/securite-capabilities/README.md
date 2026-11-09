# Linux capabilities

Linux splits root authority into capabilities. Docker's default subset is
smaller than host root's, but it may still exceed what an application needs.
`cap_drop` removes capabilities, `cap_add` gives back the ones that are
explicitly required. Recreation is necessary: editing Compose does not change an
existing process.

## What the lab shows

A launcher confines its jobs with `chroot`. Measured on `docker.lab`, on
2026-11-09, Docker Engine 29.9.2, Compose 5.6.1, the same alpine service in five
configurations:

| Configuration | The launcher | PID 1 effective mask |
| --- | --- | --- |
| Docker default | works | `0xa80425fb` |
| all dropped | **stops at startup**, `chroot: can't change root directory: Operation not permitted` | `0x0` |
| all dropped, one capability given back (`CAP_SYS_CHROOT`) | works | `0x40000` |
| all dropped, `CAP_CHOWN` given back instead | **stops at startup** | `0x1` |
| all dropped, `CAP_SYS_CHROOT` and `CAP_CHOWN` | works, **and an ownership change succeeds** | `0x40001` |

The last line is the trap: a service that works with a superfluous capability
passes every functional test. Only the effective mask and a real ownership change
tell it from the minimum.

## Evidence is not one thing

What Docker was asked (`HostConfig.CapDrop` and `CapAdd`), what the kernel applies
(`CapEff` in `/proc/1/status`, a hexadecimal mask), and what the container can
still do are three different pieces of evidence. The first two can differ: Docker
29 writes the names with their `CAP_` prefix.

## What the lab does not accept

- privileged mode, which gives every capability back whatever `cap_drop` says;
- a second capability, even one that looks harmless: the launcher needs one;
- a list of capabilities to drop one by one, which lets through whatever a future
  image would add.

## About ports

A successful bind on a low port proves nothing about `NET_BIND_SERVICE`: the
engine sets `net.ipv4.ip_unprivileged_port_start=0` inside the container, so a
container with no capability at all listens on port 80. That capability is not
the one this lab is about.

See [the challenge](challenge/README.md). The engine must already be available.
Setup and cleanup preserve existing images and daemon settings.
