# A YAML budget is not proof of enforcement

Docker on `docker.lab` uses cgroup v2. Pinned Alpine is already available.
No workload runs initially.

## Mission

Write `/opt/lab-compose-resources/compose.yaml`, project `dsoxlab-ressources`.
Start exactly one service `worker` using the supplied pinned Alpine reference
and `sleep infinity`, without mounts, extra capabilities, privileges or a host
cgroup namespace.

Apply these hard limits:

- memory: exactly 128 MiB;
- CPU: exactly 0.5 core of quota, not a relative CPU weight;
- processes: exactly 64.

Inspect Docker HostConfig and effective `/sys/fs/cgroup/memory.max`, `cpu.max`
and `pids.max` inside the container. The budgets must survive force-recreation
without manual `docker update`, builds or downloads.

The check runs a bounded three-second busy loop and requires the CPU cgroup's
throttling counters to increase. It does not allocate excessive memory, create
a fork bomb or measure an OOM event; those are separate topics.
Cleanup removes only this project's resources and leaves the base image.
