# Functional contract: docker-rotation-des-journaux

Work on `docker.lab`. The `dsoxlab-log-rotation` service must stay running and
keep its `dsoxlab.lab` label.

Three independent checks measure three different things, and the first is not
enough.

## 1. The declared driver bounds the logs

The service uses the `json-file` driver, with `max-size=1k` and `max-file=3`.

This is what was **asked of the daemon**, and it is the only thing the previous
version of this lab measured. A cap accepted by the daemon and never applied
would have satisfied it, and you would have scored the point without your
journal being bounded.

## 2. The oldest lines have been dropped

The service emits one hundred lines numbered 0 to 99, then sleeps. If rotation
bites, the first is no longer readable and the hundredth still is.

This is observable through `docker logs` alone, with no privileges, and it is
measured:

| Setting | Lines retained | First line |
| --- | --- | --- |
| `max-size=20m max-file=5` | 100 | `0` |
| `max-size=1k max-file=3` | 16 | `84` |

The check also requires the **hundredth** line to be present: a rotation
dropping recent lines instead of old ones would not leave the service
inspectable.

## 3. The retained volume fits the declared budget

The retained content does not exceed what three files of 1 kiB can keep.

This is not a restatement of check 2. Dropping old lines shows rotation runs;
fitting the budget shows it runs with the **right values**. A rotation set to
1 MiB would also drop lines, much later, and check 2 alone would accept it.

The reading does not touch `/var/lib/docker`, and that is deliberate: reading
the log files requires root, which would make the verification depend on an
environment detail. The content returned by `docker logs` is smaller than the
JSON files wrapping it anyway: if it exceeds the budget, the files exceed it too.

## What is not graded, and why we tell you

Two verifications precede the measurements without being requirements: that the
service exists and carries its label, and that its logs are readable. Without
them no check can observe anything, and a check that could not look must never
conclude green. When the read fails on a running service, the message tells you
it is not your fault.

One limit of this contract, so nobody mistakes it: checks 2 and 3 do bite, but
they never refuse **on their own**, since any error on the bounds is also seen by
check 1. They exist because they do not measure the same thing as it does: it
trusts the declaration, they look at the journal. The day the engine accepts an
option without applying it, they would be the only ones to see it.
