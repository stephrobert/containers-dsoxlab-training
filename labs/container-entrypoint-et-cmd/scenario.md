# The argument was passed, and it did not have the same effect

## The situation

A team ships two images that do the same job. On the first, passing an argument
to `docker run` changes the command executed. On the second, the same argument
replaces nothing: it adds to what was already running.

Nobody understands why, and the discussion circles around the idea that one of
the two images must be "badly made". Both are correct. They simply do not
declare their command the same way, and that difference cannot be seen by
looking at the image: it is seen in what happens when you pass it something.

Two rules explain everything. This lab does not state them for you: it has you
produce the four situations where they show.

## The goal

Both images are already built on the machine, and **their Dockerfiles are
readable** in `/opt/lab-entrypoint`:

```text
img-cmd:1.0          declares only a CMD
img-entrypoint:1.0   declares an ENTRYPOINT and a CMD
```

Produce four containers. Each must **remain**: it is in its logs that what ran
is read, and a `--rm` would erase the evidence.

| Container | From | What its logs must show |
| --- | --- | --- |
| `defaut` | `img-cmd:1.0`, no argument | `defaut-de-limage` |
| `remplace` | `img-cmd:1.0` | `remplacement-total`, **instead of** the default |
| `complete` | `img-entrypoint:1.0` | the entrypoint prefix **and** `complement-cmd` |
| `contourne` | `img-entrypoint:1.0` | `sans-prefixe`, **without** the prefix |

The brief also sits in `/opt/MISSION.md`.

## What is graded

What was **executed**, read in the logs of the four containers. Not what the
images declare: the setup wrote that, and checking it would teach you nothing.

Each check also verifies an **absence**, and that is what makes it serious: a
container whose logs carry both the default and your text has replaced nothing,
and a container that keeps the prefix has overridden nothing.
