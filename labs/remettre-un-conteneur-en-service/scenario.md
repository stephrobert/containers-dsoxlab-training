# The shop cannot find its catalogue

## The situation

On Friday, two teams deployed their services on the same machine, each on their
own, each with their own commands. On Monday morning the online shop shows an
error page: it cannot find its catalogue any more.

The database container is running. The application container is running. Both
answer when questioned from the inside. And yet the application reaches nothing.

The weekly audit, which arrived the same morning, adds an apparently unrelated
line: **the database is reachable from the outside**.

## What is in place

```text
boutique    the application. It looks for its database under the name `base`,
            hardcoded in its configuration, and that name cannot change.

catalogue   the database. It listens on its port 80 and answers a token.
```

Both are built on the image `lab-diagnostic:1.0`.

## What is expected at the end

1. From `boutique`, the name `base` resolves to an address `catalogue` actually
   carries.
2. From `boutique`, a connection to `base` port 80 returns the token.
3. `catalogue` publishes **no** port.
4. From `boutique`, the name `catalogue` resolves **as well**: operations must
   keep designating the container by its real name.
5. Preserve the supplied image and mount `dsoxlab-diagnostic-data` at `/data`.
   Implement executable `/opt/lab-diagnostic/recreate.sh`, without arguments.
   It actually replaces `catalogue` without losing a fresh value written to
   `/data/jeton`; the replacement serves that exact value from `boutique`
   and remains unexposed. Label any added network
   `dsoxlab.lab=reseau-diagnostic-dns`; no global prune is permitted.

The brief is also written to `/opt/MISSION.md`.

## This is an assessment

**Nothing will be explained to you again.** The networking labs of the course
taught what is needed: the default network and its limits, a dedicated network
and its name resolution, port publishing and its three postures. This one
measures.

Five checks of equal weight, **75 points to pass**, and everything is graded on
the real state of the engine. The checks' messages name the symptom, not the
move: making the link is your job.
The course's data-preservation requirement is critical: reaching the numerical
threshold alone does not replace success on that requirement.

Four hints exist, from the vaguest to the most explicit, and they cost points.

## Two pieces of advice that are not hints

Keep the containers' **names**: the checks look for them by name, and the fourth
point already tells you why.

And do not settle for a connection that succeeds to conclude that a service
answers. Docker's proxy accepts a connection before anything is listening: read
the answer. That is true in this lab as in your production.
