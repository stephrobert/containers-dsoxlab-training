# Correlation is not log volume

[Français](README.fr.md) | [Challenge](challenge/README.md)

For a neutral shopping service, one fresh request ID should identify ingress,
downstream work and the business response. JSON traces should contain only an
allowlist of useful fields, never a dump of request headers.

```sh
docker compose -p tutorial-shop logs --no-color
docker exec tutorial-shop-calculator cat /sys/fs/cgroup/cpu.max
docker exec tutorial-shop-calculator cat /sys/fs/cgroup/cpu.stat
```

These names are not installed by this challenge. A CPU quota is different
from a share: `cpu.max` states the effective budget. Compare `usage_usec`,
`nr_throttled` and `throttled_usec` before and after a bounded business load.
Counter deltas, request results and component identities jointly establish
attribution; log size and configured memory limits do not.

The supplied application's deployment switches are `CORRELATE` and `SAFE_LOGS`
(`"0"` or `"1"`), independently for each component. No coding is required.
`ROLE` chooses gateway or worker. `/quote?quantity=N` accepts 1 through 20
and returns a total at 125 cents per item, with `X-Request-ID` correlation.
The worker burns 0.12 seconds of thread CPU per accepted quote.

Concurrency and request count must be bounded. The tests use 16 fresh requests,
four clients, a quarter-CPU worker and one-CPU gateway. Positive cgroup deltas
and at least 0.10 CPU seconds per request distinguish real work from startup;
worker usage must exceed gateway usage by a factor of two. These are test
budgets, not invented course performance percentages.

Source anchor: local `orchestrateurs/docker-compose.mdx`,
`Configuration avancée`. Human explanation is evaluated separately.

## Author validation

Local fixture tests: `python3 -m unittest discover -s labs/compose-correlation-et-saturation/author_tests -v`.
VM protocol: `LAB_HOME=$PWD python3 scripts/valider-labs.py --double-passage --lab compose-correlation-et-saturation`.
On `docker.lab`, 2026-11-01: zero/full/zero/full, 214 seconds for the complete
protocol, Docker state restored. Component readiness probes precede load;
declaration recreation rejects non-persistent manual quota changes.
