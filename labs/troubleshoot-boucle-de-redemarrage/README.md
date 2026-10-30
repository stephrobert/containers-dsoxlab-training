# troubleshoot-boucle-de-redemarrage: the policy fixes nothing

## What this lab tests

That a restart policy corrects no defect. It only decides what happens
**after** the failure, and three containers sharing the same defect get out of
it in three different ways:

| Policy | What it gives | What it tells you |
| --- | --- | --- |
| capped | the engine relaunches N times, then gives up | the failure is frozen, so readable |
| endless | it relaunches indefinitely | the failure is noisy, and still there |
| endless, cause lifted | it catches up on its own | lifting the cause was enough |

The reflex gesture is to make the noise stop: remove the policy, or destroy the
container. Both work, and neither fixes anything.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Policy | State | RestartCount | Exit code |
| --- | --- | --- | --- |
| `on-failure:4` | `exited` | frozen at **4** | the script's |
| `always` | `restarting` | **10 in 60 s** | the script's |
| `always`, cause lifted | `running` | frozen | moot |

And the fact carrying the second half of the lab: **the container under the
endless policy came back on its own**, measured at about a minute after the
missing file was laid down, without touching it. The engine waits between two
attempts, and that delay grows. Relaunching the container merely skips the
wait.

The capped container, for its part, did not come back: the engine had given up.

## Why the capped container is the witness

It carries **two** of the three answers, and its two values are stable
precisely because the engine gave up: the count no longer moves, and the code
stays the one of the last attempt.

The brief forbids repairing it, and a check verifies it stayed `exited`. A
relaunched container starts over, with neither restart count nor exit code: the
question would be moot. It is the rule this section has drawn out, and its
fourth application: **a diagnostic value is never read from the object the
repair modifies.**

## Why two policies, and drawn at random

`always` and `unless-stopped` produce **exactly the same loop**. They differ on
one point only, which has nothing to do with it, and that is the fate of a
container stopped by hand when the engine restarts.

The setup draws one at random on each pass. So the question cannot be guessed,
it has to be read, and read **before** repairing: removing the policy would
make it disappear.

The ceiling and the failure code are drawn the same way. The code avoids 0, 1,
2 and the 125-127 range, which each have a meaning in this catalogue and would
steer the diagnosis by elimination.

## Why the fourth check requires the policy intact

Removing the policy makes the loop stop **without fixing anything**: the
container stops being relaunched, and the defect is whole. That is the mistake
this lab exists to prevent, and a check looking only at "the container no
longer loops" would reward it.

So it requires three things at once: the container runs with its script's
trace, its policy is still the one of the start, and the healthy container is
**the one of the start**, recognised by its identifier and not by its name. A
namesake recreated after a clean slate would carry the same name, and that is
precisely the gesture carrying away a running service.

## Why the check grants time, but not always

The engine's delay reaches the minute. A learner lifting the cause and grading
right away would be refused for having done exactly the right thing, and would
conclude that recreating is the way.

So the check waits up to 150 seconds, **but only when the cause is lifted**: it
first verifies the presence of the file that was missing, and refuses without
waiting when it is still absent. A `check` played without having fixed
anything answers at once.

## Why the setup observes the loop on the count

Measured on 2026-10-30: between two attempts, the looping container passes
through `running` while its script fails. A check on the state is therefore
true half of the time, and the setup's first draft failed right there.

The restart count, for its part, never goes back down. It is the stable proof
that a container is looping.

## A cleanup trap, paid in advance

The containers go away **before** their configuration. Two of them carry a
restart policy, and the engine relaunches them as long as they exist: removing
the directory first would leave one of them looping on a vanished
configuration, filling the engine's journal.

## What the lab does not require

A path. The missing file can be laid down by any means, and the recovery can
come from letting the engine catch up as well as from handing it back the
wheel. The three values are read in the inspection, which can be questioned in
several ways.
