# epreuve-mettre-un-service-en-marche: the first module's test

## What this test measures

Making a host usable, then running a named and configured service on it, without
destroying what has to be preserved. It closes the first module and re-explains
nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and one of them is critical.

## The four obstacles planted, stated nowhere in the brief

| Obstacle | Visible symptom | What it teaches |
| --- | --- | --- |
| the service is stopped **and disabled** | nothing runs, and nothing would come back after a reboot | "started" and "enabled" are two distinct facts |
| the account is no longer in the `docker` group | the daemon is reported unreachable | a permission refusal looks like a daemon failure |
| a **stopped** container occupies the requested name | `docker run` fails on a name conflict | a stopped container keeps its name |
| a witness container, stopped as well | it looks like the previous obstacle | what is in the way and what looks like it are not the same thing |

The second obstacle is the most instructive of the set: the message it produces
points at the daemon, while the cause is in the account's groups. That is the
confusion which costs beginners the most time.

## The critical requirement, and why it is there

**Deleting or restarting `journal-de-bord` fails the test**, even at 80 points.
That container looks exactly like the obstacle: stopped, from the same image,
created before it, hence first in a sort by date. The difference is that it
carries the trace of an incident, and the brief asks for it to be kept.

This requirement reproduces a real situation: the container a too-broad
`docker rm` takes away is the one that carried the trace. A marking scheme that
let that loss be made up for would issue a certificate to someone who destroys
evidence.

It must stay **stopped**, not merely present: restarting it can overwrite what it
carried, and "as it is" means as it is.

## The fifth check, and why it recomputes the truth

Predicting `.Path` and `.Args` before running the command means predicting what
the engine keeps from an ENTRYPOINT and what a command-line argument replaces.
The check does not compare the answer against values written in the test: it
**creates the container described, without starting it**, reads what the engine
kept, then removes it under a unique name.

Two reasons. The first is not to freeze into a test what a version of the engine
could change. The second matters more: the prediction is measured **against the
engine**, not against the opinion of whoever wrote the test.

## What this lab touches on the machine, and what it gives back

It is the most intrusive setup in the catalogue, and that is inherent to the
subject: it touches the **service** and the **groups**, not only containers.
Everything it changes, it records beforehand in
`/root/.lab-mise-en-marche-state.json`, and `cleanup` puts it back as it found
it:

- the engine is restarted **first**, because the validation cycle queries the
  engine after cleanup and can conclude nothing from a silent daemon;
- the "enabled" state is restored **as it was**, keeping the exact string from
  `systemctl is-enabled`: `static` and `masked` are not handled like `disabled`,
  and blindly re-enabling would change the machine in the other direction;
- membership of the `docker` group is restored as it was. If the account was not
  in it, it is not put back: the lab gives back what it found, not what it
  thinks desirable.

## What the test does not measure

Building images, volumes, published ports. None of that is on this module's
syllabus.
