# A CI job that actually tests the application

Work on `docker.lab` in `/opt/lab-compose-ci`. The source, Dockerfile,
Compose stack and integration test are supplied; `ci.sh` currently refuses
to run. No hosted CI account is required.

Implement an executable POSIX `ci.sh`. Its environment contract is:
`PROJECT` (unique Compose project), `SOURCE_DIR` (absolute build context),
`ARTIFACT_DIR` (existing report directory), `EXPECTED_VALUE`, `TEST_FAIL`
(0 normally, 1 forces an actual test failure). Use the supplied Compose
file and test, without replacing their logic. A normal manual run is:

```sh
cd /opt/lab-compose-ci
mkdir -p artifacts
PROJECT=dsoxlab-ci-manual SOURCE_DIR="$PWD/source" ARTIFACT_DIR="$PWD/artifacts" \
EXPECTED_VALUE=release-one TEST_FAIL=0 ./ci.sh
```

Each run must build the given source, start only the API, wait for healthy,
execute the tests container, retain its `result.json`, return the test status,
and remove this project's containers, networks and volumes even on failure.
Changing `value.txt` must change the tested release on the next run. No host
ports, global prune or removal of base images. Keep the ownership labels.

The evaluator runs real jobs, injects failing tests and changes the source;
valid YAML or a hand-written success report earns nothing. Setup needs network
for apt and the pinned Python base. Jobs need no package download or outbound
network after that; Compose v2 with `up --wait` and BuildKit are required.
