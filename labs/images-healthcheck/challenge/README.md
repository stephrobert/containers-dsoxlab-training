# What is asked

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

## 1. The container must reach the healthy state

The image must declare a probe, and the container must become **healthy** while
the service is working.

A container without a probe does not have an "unknown" state: it has **no**
health field at all. Confusing the two sends you looking for a probe that works
badly where there is none.

## 2. It must turn unhealthy when the pulse goes stale

This is the heart of the lab.

The service goes quiet, and **its process keeps running**. Measured: a probe
watching the process declares the service healthy while its pulse ages. What
has to be probed is the **work**, and the pulse is its proof: its
**freshness**, not its existence.

The pulse file is always there, even when mute. Only its timestamp ages.

## 3. It must return healthy when the service resumes

A probe reports the **current** state, not what it saw once.

Without this check, a probe keeping a trace of its first failure, in a file or a
flag, would pass the two previous ones: it would conclude healthy, then
unhealthy, and stay there for ever.

## 4. The declared bounds must be coherent

```text
timeout < interval       otherwise the probes stack up
at least 2 retries       otherwise a hiccup declares it sick
a start period           otherwise a slow service is judged before it begins
```

## A surprise, and what the lab does not make of it

**An unhealthy container stays running.** The engine does not stop it, does not
restart it, does not warn anyone: a probe informs, it repairs nothing.

So no check expects a stop. That would measure a belief.

## What is not graded

The probe's form, nor its exact values. The delays granted are **computed**
from the bounds your image declares: a cautious probe is not penalised, and a
probe that never concludes is not accepted.
