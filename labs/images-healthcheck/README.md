# images-healthcheck: "up" says nothing about the service

## What this lab tests

That a running container says nothing about the work, and that a probe watching
the **process** says no more. The most frequent failure is not the process
dying: it is the service going quiet without dying.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Situation | What the engine declares |
| --- | --- |
| no probe | **no** health state, the field does not exist |
| probe on the pulse's freshness, service healthy | `healthy` in 2 s |
| the same, service mute and process alive | `unhealthy` in 8 s |
| the same, service resumed | back to `healthy` in 2 s |
| probe on the **process**, service mute | **`healthy`**, pulse stale |

The last line is the lab, and it is measured, not inferred.

## Why a pulse, and not a port

The first draft served on a port with `nc`, and the probe **never** reached the
healthy state. The cause had nothing to do with the subject: a busybox `nc -l`
serves one connection only, and the synchronisation between the probe and the
loop decided the verdict.

A pulse depends on no network, no client, no connection time. It keeps the only
property that matters: the service can stop working without its process dying.

## Why no check bears on ports or on a stop

**An `unhealthy` container stays running**, measured: the engine does not stop
it, does not restart it, does not warn anyone. A probe informs; it repairs
nothing without an orchestrator to read it.

A check expecting a stop would measure a widespread belief, and a lab that
grades a belief teaches it. It is the same decision as in `images-non-root`,
where the measurement showed a non-root process listening below 1024 and where
no check bears on ports.

## Why the delays are computed, not written

Each check reads the bounds the image declares, and derives from them the time
it grants: the start period, then as many intervals as there are retries, each
possibly lasting up to its timeout, plus one interval of margin.

A hard-coded delay would refuse a cautious probe, or accept one that never
concludes. A floor remains in place, so that a very fast probe is not judged on
a synchronisation coincidence.

## Why the third check exists

A probe keeping a trace of its first failure, in a file or a flag, would pass
the first two: healthy, then unhealthy, and unhealthy for ever. The third puts
the service back to work and requires the return to healthy.

A probe reports the **current** state. One that can only speak once monitors
nothing.

## A reading defect, caught by the cycle

The test and the solution assumed bounds in whole nanoseconds. Measured: the
engine returns a **formatted duration**, `5s`, and `1m30s` for ninety seconds.

On the shell side, `test -lt` answered "Illegal number: 2s". On the Python side,
`int("2s")` raised, the function returned an empty dictionary, and the first
check announced **"no probe declared" on an image that carried one**. The
message accused the opposite of what was true.

The bounds are now read through `.Seconds`, which Go exposes on a duration:
there is no `1m30s` to parse, so no parser to get wrong.

## The starting state is broken, and that is the repository's rule

Neither the image nor the container exists: the four checks are false before any
work. A setup task verifies that the base exists, that the learner's image does
not, and that the starting Dockerfile carries **no** probe.

## What the lab does not require

A probe's form, nor precise values. The token is drawn by the setup, the bounds
are the image's, and the delays follow from them: nothing is hard-coded in the
checks.
