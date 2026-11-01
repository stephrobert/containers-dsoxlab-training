# Challenge

Implement `/opt/lab-compose-ci/ci.sh` using [the runtime contract](../scenario.md).
Four state-based checks run successful jobs, a failing test, fresh committed
source revisions and uncommitted-source refusal. Accepted archives are reloaded
and compared to the actual source commit, image ID and SHA-256. Failed tests
publish nothing. All fail before implementation. Reports come from actual
application tests and artifacts, not inferred YAML.
