# Diagnose one hop at a time

[Français](README.fr.md) | [Challenge](challenge/README.md)

Separate routing, listening services and forwarding rules. In a neutral
container-only topology, inspect the route selected by the client and the
rules in the router's own network namespace:

```sh
docker exec tutorial-edge-client ip route get 192.0.2.10
docker exec tutorial-edge-router nft -a list ruleset
```

Those names and addresses are not this lab's correction. A reachable router
control endpoint does not prove forwarding works. A router-to-server probe
shows the second hop; an end-to-end business request exercises FORWARD.
Read counters before and after fresh probes, including denied paths.

Default deny, established-return handling and narrow source/destination/port
matches are complementary. Removing a whole table is not a targeted fix.
Keep filtering inside the router; no global host firewall or sysctl command
belongs in this exercise.

Only namespace-scoped NET_ADMIN is added to the route-setting containers.
No privileged containers, host networking, host PID/IPC namespace or API
socket mounts are needed. Tools are installed by the pinned lab Dockerfile,
not on the workstation. The two dedicated bridges reject overlapping
pre-existing subnets at setup.

The bridges are not declared `internal`: Docker's host-side isolation for
internal bridges can reject a packet addressed to the other subnet before it
reaches the container router. No host filtering rule is changed to bypass that
behavior. Explicit routes and the router's default-deny rules define the lab paths.

Source anchor: local `docker/network.mdx`, `Dépannage réseau Docker`.
The functional test checks permitted and refused paths again after recreation.

## Author validation

Local constraints: `python3 -m unittest discover -s labs/reseau-pare-feu-cible/author_tests -v`.
VM protocol: `LAB_HOME=$PWD python3 scripts/valider-labs.py --double-passage --lab reseau-pare-feu-cible`.
On `docker.lab`, 2026-11-01: zero/full/zero/full, 145 seconds for the complete
protocol, Docker state restored. Actual HTTP hops and drop-counter increments
were exercised, not merely a configuration parse. Human review remains separate.
