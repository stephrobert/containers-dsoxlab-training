# Three containers down, three different causes

A processing chain runs on this machine, as three containers: `collecteur`
collects, `expediteur` forwards, `scribe` records. This morning all three are
down, and **the three failures are independent**.

**`collecteur` has exited.** It does not restart, and nobody has read its exit
code.

**`expediteur` restarts endlessly.** You can watch it come back, again and
again.

**`scribe` takes ten seconds to stop**, and the report it writes is cut off
before the end.

None of these three findings states the cause. Establishing them is your job,
and they are not the same.

## What is expected at the end

1. `collecteur` is **running**, from the `lab-trois-pannes:1.0` image.
2. `expediteur` is **running**, it no longer restarts, and **its restart policy
   is kept**: the policy is not the failure.
3. `scribe` is **running**, and it stops in an orderly way: a `docker stop` must
   return in **under ten seconds**, with exit code **0 or 143**, and the report
   must be **complete**.
4. The complete report, the run's reference included, is copied **onto the
   host**, into
   `/opt/lab-trois-pannes/diagnostic.txt`.
5. **No container of this lab is left stopped.**

The report is written inside the container, in `/var/log/scribe.txt`. It is
complete when it carries **its opening line and its closing line**.

To get the copy: fix the scribe's failure, stop it in an orderly way, copy its
report, then **start it again**. Check 5 requires that no container be left
stopped.

The full brief is also on the machine, in `/opt/lab-trois-pannes/MISSION.md`.

## What you do not have to write

The `lab-trois-pannes:1.0` image is provided and carries all three roles: there
is **nothing to build**. It reads the `ROLE` variable, and each role has its own
requirements. Its logs and its exit codes state them.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No command is
imposed.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**a lost or truncated report fails the test**, even with everything else in
place. The first two failures cost time; that one costs data, and lost data does
not come back.

Four hints are available, and **they cost points**: `dsoxlab hint`.
