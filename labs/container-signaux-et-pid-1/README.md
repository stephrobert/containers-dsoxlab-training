# container-signaux-et-pid-1: who is PID 1 decides everything

## What this lab tests

That a container taking the full timeout to stop is a container that gets
**killed**, and that the cause is nearly always the same: the process receiving
the signal is not the one that could hear it.

## What was measured before writing this lab, and changed its design

The common explanation says "shell form, so the shell is PID 1". **It is wrong
on this image.** Measured on 2026-10-29 on Alpine:

| Form | PID 1 | Code | Shutdown |
| --- | --- | --- | --- |
| `ENTRYPOINT ["/app.sh"]` | `app.sh` | 0 | 1 s |
| `ENTRYPOINT /app.sh` | **`app.sh`** | **0** | **1 s** |
| `ENTRYPOINT /app.sh ; echo x` | `sh` | 137 | 6 s |

Busybox optimises the single command into a direct `exec`: the shell form alone
therefore produces **no** trap. A lab built on the common explanation would have
compared two images with identical behaviour, and two of its four checks would
have been indistinguishable. It would have gone green while teaching nothing.

What really produces the defect is the most frequent real case: an entry script
that launches the application as a **child**.

| Entry script | PID 1 | Code | Shutdown | Logs |
| --- | --- | --- | --- | --- |
| `/app.sh` | `entree.sh` | 137 | 6 s | no SIGTERM |
| `exec /app.sh` | `app.sh` | 0 | 1 s | SIGTERM received |

One word separates them, and three consequences show it. It is also the fix one
writes in real life.

## The first check requires the symptom, not its correction

`fragile` must have been stopped and carry a non-zero code, and its logs must
**not** carry the signal's trace. That is deliberate: a learner must have
**seen** the defect before fixing it, otherwise they fix an instruction and not
a problem.

The refusal message even covers the case where they "fixed" that container: it
tells them to replay the lab, because the evidence is lost.

## The false-fix trap, and how it is closed

Emptying the entry script would fix the signal. It would also remove the
script's reason to exist, and a learner could do it without ever meeting `exec`.

The fourth check therefore requires `preparation-faite` to still appear in the
logs. A check that does not forbid the wrong solution ends up rewarding it.

## The starting state is broken, and that is the repo's rule

| Laid out by the setup | Starting state | Expected action | Check |
| --- | --- | --- | --- |
| `fragile` | `running`, PID 1 = `entree.sh` | stop it and observe | 1 |
| *nothing* | no `img-corrige:1.0` | build it | 2 |
| *nothing* | no `robuste` | run then stop it | 3 and 4 |

A setup task **verifies** this state before handing over, the faulty
container's PID 1 included: if the shell's optimisation ever changed, the lab
would say so instead of grading nonsense.

## A detail of the second check

It runs a throwaway container to read PID 1, and that container carries the
repo's `dsoxlab-` prefix, set by `nom_objet()`, then is removed in a `finally`.
That is the `conftest.py` discipline: the machine carries hundreds of objects,
and a container forgotten by a test would drown in them.

## What the lab does not require

A way to fix it. `exec` in the entry script, the application invoked directly by
the `ENTRYPOINT`, or an init that forwards signals all reach a PID 1 that hears
SIGTERM. The check reads the process name, not the Dockerfile.
