# An "up" container that no longer works

## The situation

The dashboard is green. The container has been "up" for three days, its process
is running, its consumption is normal.

And the service has processed nothing for two hours.

Nobody knows, because nothing was watching the **work**: the monitoring watched
the process, and the process never died.

## The goal

The context is in `/opt/lab-sante/appli`. The service there beats a **pulse**:
it writes the time into `/var/run/pouls` every second, as long as it is
working.

Build the Dockerfile as it stands under the name `appli:surveillee`, run it
under the name `service-surveille`, and inspect it. It has **no** health state:
the field does not exist.

Now make the service mute, without killing its process:

```bash
docker exec service-surveille touch /tmp/muet
```

The container is still "up". Its pulse is stale. Nobody knows.

Add a probe, rebuild, relaunch. `service-surveille` must:

```text
reach the HEALTHY state while the service is working
turn UNHEALTHY when the pulse goes stale, the process still alive
RETURN to HEALTHY when the service resumes
declare coherent bounds
```

The brief is also laid down in `/opt/MISSION.md`.

## What is measured, and what decides the lab

| Situation | What the engine declares |
| --- | --- |
| no probe | **no** health state, the field does not exist |
| probe on the pulse's freshness, service healthy | `healthy` in 2 s |
| the same, service mute and process alive | `unhealthy` in 8 s |
| the same, service resumed | back to `healthy` in 2 s |
| probe on the **process**, service mute | **`healthy`**, pulse stale |

The last line is the lab. A probe watching the process sees nothing, and that
is measured: it declares the service healthy while its pulse ages.

## A surprise this lab does not grade

**An `unhealthy` container stays running.** The engine does not stop it, does
not restart it and does not warn anyone. A probe **informs**; it repairs
nothing, and it decides nothing without an orchestrator to read it.

So no check expects a stop: that would measure a belief.

## The bounds are not details

The fourth check requires three things, each for a reason:

- the **timeout below the interval**, otherwise a slow probe is still running
  when the next one starts, and the engine stacks them up on a service that is
  already struggling;
- **at least two attempts**, otherwise a one-second hiccup declares a healthy
  service sick;
- a **start period**, otherwise a service that takes time to get ready is
  judged before it has begun.

## What is graded

The **system state**, and the delays granted are **computed**: each check reads
the bounds your image declares and derives from them the time it waits. A
hard-coded value would refuse a cautious probe, or accept one that never
concludes.

The third check is the one you do not expect: it puts the service back to work
and requires the return to healthy. A probe keeping a trace of its first
failure would pass the other two, and would serve only once.
