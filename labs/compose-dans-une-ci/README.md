# Compose in local CI

Challenge, c4, 45 minutes. Read [the mission](scenario.md).
Run real integration tests without a hosted runner; the evaluator checks exit
codes, fresh source and cleanup on both paths.

Runtime: Debian 13 VM, Docker, BuildKit, Compose v2 (`up --wait`), Python 3,
POSIX shell and `timeout`. Setup fetches apt packages and a digest-pinned Python
image; CI itself is offline. Only `/opt/lab-compose-ci` and labelled lab
resources are removed. No global Docker operations or workstation execution.
Preexisting base IDs are recorded before pulls; only newly seeded, unshared
bases can be removed, without force or parent-image pruning.
The encrypted reference is in `solution/compose-dans-une-ci/solution.yaml`.
