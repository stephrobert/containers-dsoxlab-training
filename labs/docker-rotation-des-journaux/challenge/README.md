# A chatty service fills the disk

## The situation

On `docker.lab`, the `dsoxlab-log-rotation` service writes a bounded stream, but
its log is allowed to become far too big. Only this service is concerned: the
daemon's defaults must not change.

## Mission

The service keeps its `json-file` logs in files of 1 KiB at most, three files
kept. It must stay running and keep its `dsoxlab.lab` label. The brief is also
written to `/opt/dsoxlab-docker-rotation-des-journaux/MISSION.md`.

## What is graded

### 1. The declared driver bounds the logs

The service uses the `json-file` driver, with `max-size=1k` and `max-file=3`.

This is what was **asked of the daemon**. The next two checks measure what it
does with it.

### 2. The oldest lines have been dropped

The service emits one hundred lines numbered 0 to 99, then sleeps. If rotation
bites, the first is no longer readable and the hundredth still is.

This is observable through `docker logs` alone, with no privileges, and it is
measured:

| Setting | Lines retained | First line |
| --- | --- | --- |
| `max-size=20m max-file=5` | 100 | `0` |
| `max-size=1k max-file=3` | 16 | `84` |

The check also requires the **hundredth** line to be present: a rotation
dropping recent lines instead of old ones would not leave the service
inspectable.

### 3. The retained volume fits the declared budget

The retained content does not exceed what three files of 1 kiB can keep.

This is not a restatement of check 2. Dropping old lines shows rotation runs;
fitting the budget shows it runs with the **right values**. A rotation set to
1 MiB would also drop lines, much later, and check 2 alone would accept it.

The reading does not touch `/var/lib/docker`, and that is deliberate: reading
the log files requires root, which would make the verification depend on an
environment detail. The content returned by `docker logs` is smaller than the
JSON files wrapping it anyway: if it exceeds the budget, the files exceed it too.
