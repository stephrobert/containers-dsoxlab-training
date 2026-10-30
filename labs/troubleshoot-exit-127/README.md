# troubleshoot-exit-127: a grid, not a symptom

## What this lab tests

That an exit code is a **diagnosis**, and that two neighbouring codes say two
opposite things.

A troubleshooting lab is not taught with a symptom: it is taught with a **grid**,
and a grid needs neighbouring cases that can be compared. Hence three failures
rather than one.

It is the first of the section's four troubleshooting labs.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Cause | Code | Log | Status |
| --- | --- | --- | --- |
| command not found | 127 | **empty** | **`created`** |
| file not executable | 126 | empty | `exited` |
| command that fails | its own code | what it wrote | `exited` |

## The distinction that is worth the whole lab

When the command is not found, the container **never started**. Its status stays
`created`, its log is empty, and the diagnosis is in the inspection's
`.State.Error`, which nobody looks at:

```text
unable to start container process: exec: "…": executable file not found in $PATH
```

However, **if a shell wraps the command, the log speaks**, because the shell did
start. Measured: `sh: /tmp/inexistant: not found`.

The same code 127, two opposite situations, and the log is what separates them.
That is what explains the lost hour in the scenario: you search the image for a
cause the inspection announced in one line.

## Why three failures, and why the check verifies they differ

Two neighbouring codes are only learned one against the other. So the second
check also verifies that the two codes **differ**: a grid with two cells holding
the same value is not a grid.

The setup verifies it too before setting the lab, which protects it from a future
drift: if an image change made two failures identical, the lab would stop rather
than teach a false distinction.

## The repair uses the same image, and that is graded

The repaired container must derive from the **same image** as the failures. That
is what demonstrates the image was not at fault.

Repairing by changing image would prove the opposite of the lesson, and the check
explicitly refuses it. **Knowing what is not responsible rules out half the
leads**: it is the most profitable conclusion of any troubleshooting.

## No code is hardcoded

The three expected values are read from the containers at grading time. A test
carrying `127` would be wrong the day the setup changed its failures, and the lab
would die of an unrelated change.

The reference solution applies the same rule: it **reads** the three answers, and
it also consults the error field, which no question asks for. Its `failed_when`
requires finding the expected trace there, so it **proves** it instead of
mentioning it: a reference solution is also a teaching document.

## One setup detail that is not negligence

The setup's three `docker run` carry `failed_when: false`. That is deliberate:
all three commands fail, which is the lab's whole object, and without that line
the setup would stop on the first failure it had just set up.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | three keys, three **empty** values | fill them in | 1, 2 and 3 |
| three failures | stopped, three distinct codes | diagnose them | 1, 2 and 3 |
| *nothing* | `repare` absent | start it on the same image | 4 |

## What the lab does not require

A path. The codes can be read from the inspection as well as the container list,
and the repair uses any command that exists and lasts.
