# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. **Three
containers share the same defect**, and they get out of it in three ways:

```text
appli-plafond    the engine GAVE UP relaunching it
appli-sans-fin   the engine keeps relaunching it, again and again
appli-saine      runs, and must keep running
```

**Start by reading `appli-sans-fin`'s traces.** They say what is missing, and
they say it as many times as there were attempts.

The first three answers go into `/opt/lab-boucle/reponses.txt`, one line per
entry, with no space around the equals sign.

## 1. How many times the engine relaunched `appli-plafond`

On the `tentatives=` line.

Its policy carries a **ceiling**: the engine relaunches until it is reached,
then it gives up. That is what sets it apart from the other one, whose count is
still climbing, and that is why the question is asked about it: its value no
longer moves.

The ceiling is declared in its policy, and the count of the attempts actually
made is elsewhere in the same inspection.

**Do not repair `appli-plafond`**: a relaunched container starts over, with
neither count nor exit code. A check verifies it stayed stopped.

## 2. The exit code of `appli-plafond`

On the `code=` line.

It is the code of the **last attempt**, and it is the script's own. It is not
read in the traces: the traces say what is missing, the inspection says with
which code the process left. The two sources are complementary, and that is the
lab's method.

## 3. The restart policy of `appli-sans-fin`

On the `politique=` line.

Write it as **the engine declares it**, that is, the value of the policy's name
in its inspection.

It cannot be guessed: **two different policies produce exactly the same endless
loop**, and they differ on one point only, which has nothing to do with it.
Read it **before** repairing: removing it would make it disappear.

## 4. Repair, without silencing the loop

```text
appli-sans-fin   must RUN, have produced its trace, and KEEP its policy
appli-saine      must be INTACT, the container of the start
```

Lift the cause, and **hand the engine back the wheel**. It catches up on its
own, in about a minute: it waits between two attempts, and that delay grows.
Relaunching the container merely skips the wait.

Removing the policy would be the reflex gesture, and it is the wrong one: the
loop would stop because the container would stop being relaunched, and the
defect would be untouched. **The policy is not at fault, the cause is.**

Starting from a clean slate would be worse: it would carry away `appli-saine`,
which was running, and nothing said it was useless. The check recognises it by
its identifier, not by its name.

## What is not graded

The command you typed. The missing file can be laid down by any means, the
recovery can come from letting the engine catch up as well as from handing it
back the wheel, and the three values can be questioned in several ways.
