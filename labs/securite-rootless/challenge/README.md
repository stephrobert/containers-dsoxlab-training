# Functional contract: securite-rootless

Tests inspect the real rootless daemon and the UID of its systemd process on
`docker.lab`. A workload in its separate image store must expose HTTP only on
nonprivileged loopback, allow a network peer, refuse a networkless peer and
preserve fresh volume data across two recreations. Trial objects have unique
bounded names and are removed, including after partial allocation failure.
The prepared starter state earns no points.
