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

The fourth check requires two things, each for a reason:

- **at least two attempts**, otherwise a one-second hiccup declares a healthy
  service sick;
- a **start period**, otherwise a service that takes time to get ready is
  judged before it has begun.

The **timeout** is not checked, and that is measured: the interval counts from
the **end** of a probe, never between two starts. A probe that lasts six seconds
under a two-second interval therefore stacks nothing up. Measured on Docker
Engine 29.1.3: a single probe in flight at any instant, and exactly two seconds
between the end of one probe and the start of the next. The timeout serves
another purpose: it bounds a probe that never returns, and is chosen just above
the probe's normal duration.

## What is graded

The **system state**, and the delays granted are **computed**: each check reads
the bounds your image declares and derives from them the time it waits. A
hard-coded value would refuse a cautious probe, or accept one that never
concludes.

The third check is the one you do not expect: it puts the service back to work
and requires the return to healthy. A probe keeping a trace of its first
failure would pass the other two, and would serve only once.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The context is
in `/opt/lab-sante/appli`:

```text
Dockerfile   it WORKS, and declares NO probe
servir.sh    the service, beating a pulse into /var/run/pouls every second
```

Build under the name `appli:surveillee`, run under the name
`service-surveille`, and inspect it: there is no health field.

Then make the service mute without killing its process, with
`docker exec service-surveille touch /tmp/muet`, and look at what the engine
says about the container. Nothing.

### 1. The container must reach the healthy state

The image must declare a probe, and the container must become **healthy** while
the service is working.

A container without a probe does not have an "unknown" state: it has **no**
health field at all. Confusing the two sends you looking for a probe that works
badly where there is none.

### 2. It must turn unhealthy when the pulse goes stale

This is the heart of the lab.

The service goes quiet, and **its process keeps running**. Measured: a probe
watching the process declares the service healthy while its pulse ages. What
has to be probed is the **work**, and the pulse is its proof: its
**freshness**, not its existence.

The pulse file is always there, even when mute. Only its timestamp ages.

### 3. It must return healthy when the service resumes

A probe reports the **current** state, not what it saw once.

Without this check, a probe keeping a trace of its first failure, in a file or a
flag, would pass the two previous ones: it would conclude healthy, then
unhealthy, and stay there for ever.

### 4. The declared bounds must be coherent

```text
at least 2 retries       otherwise a hiccup declares it sick
a start period           otherwise a slow service is judged before it begins
```

The timeout, however, is not checked: the interval counts from the end of a
probe, so nothing stacks up. Measured on Docker Engine 29.1.3.

### A surprise, and what the lab does not make of it

**An unhealthy container stays running.** The engine does not stop it, does not
restart it, does not warn anyone: a probe informs, it repairs nothing.

So no check expects a stop. That would measure a belief.

### What is not graded

The probe's form, nor its exact values. The delays granted are **computed**
from the bounds your image declares: a cautious probe is not penalised, and a
probe that never concludes is not accepted.
