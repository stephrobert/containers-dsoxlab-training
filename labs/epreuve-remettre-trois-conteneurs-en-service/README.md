# epreuve-remettre-trois-conteneurs-en-service: the troubleshooting module's test

## What this test measures

Diagnosis, three times over, through three different routes. It closes the
"Observe and troubleshoot a container" module and re-explains nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and one of them is critical.

## The three failures, and they do not share a cause

| Container | Visible symptom | Planted cause | What it teaches |
| --- | --- | --- | --- |
| `collecteur` | exited, does not restart | missing environment variable, exit **78** | an exit code is there to be read, and 78 means "invalid configuration" |
| `expediteur` | restarts endlessly | unknown mode, exit **64**, `always` policy | the policy is not the failure: it makes it visible |
| `scribe` | ten seconds to stop, report cut off | its PID 1 is a `sh`, which does not forward `SIGTERM` | who is PID 1 decides what receives signals |

**That is the point of the test**: one method of diagnosis, three distinct
conclusions. A learner who applies the same move to all three fixes one at best.

## Why the restart policy has to be kept

It is the most tempting false fix: removing `--restart always` makes the symptom
vanish in one command, and fixes nothing. The container then exits once and goes
quiet, which is worse than before, since the failure becomes invisible.

The check therefore requires both together: no more restarting, **and** the
policy in place. And it measures stability **over time**, through two readings
twelve seconds apart: a restart counter read once is zero on a container that
has just been recreated, whether it is fixed or about to loop.

## The critical requirement

**A lost or truncated report fails the test**, even at 80 points. The first two
failures cost time; that one costs data.

A report is complete when it carries its opening line **and** its closing line.
The closing line is written only by the program's shutdown handler: it therefore
exists only if the program received its signal. That is what makes this check
fair rather than arbitrary: it does not measure a file size, it measures whether
the program got to finish its work.

## Why the checks are not in the brief's order

The orderly-shutdown check has to **stop** the scribe: that is the only way to
measure a shutdown duration and an exit code, and no reading after the fact
replaces it. It is therefore played **last**, after the one that requires no
container be left stopped.

The reverse order would fail that one **because of the test itself**, which is
the flaw a test must never have: measuring its own trace.

## Three facts measured by one check, and why

The shutdown duration, the exit code and the report's integrity share the **same
cause**. Splitting them would give three checks for one single skill, and the
marking would weigh the same attainment three times: a learner who understands
signals would earn three fifths of the test, and one who does not would lose
three.

## What the test does not measure

Volumes, networks, image building. None of that is on this module's syllabus.
