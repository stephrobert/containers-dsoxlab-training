# images-tester-le-contrat: write the tests that turn a broken image away

## What this lab tests

That you can test an image **from the outside**, as the people who run it do,
and that your test tells a correct image from broken ones of different kinds.
What is graded is not an image: it is the script you write.

## Measured before being written

On `docker.lab`, on 2026-11-09, with Docker Engine 29.9.2 and a service built
for the lab. One correct image and eight broken ones, each differing from the
correct one by a line or two of Dockerfile, and what a script sees:

| Image | Defect | What the outside sees |
| --- | --- | --- |
| `guichet:1.0` | none | starts, answers, counts, stops in 0.5 s with code 0, keeps its counter |
| `guichet:0.9` | listens on 127.0.0.1 only | the container is `Up`, nothing answers through the published port |
| data directory owned by root | the user cannot write | the container stops at startup, code 2 |
| error reported, exit code 0 | the check is silent | `docker wait` returns 0: for an orchestrator, success |
| no check of the variable | the service starts without it | the container is still running after 20 s |
| process in root | too many privileges | `id -u` returns 0, the service answers normally |
| writes outside its data directory | works until the filesystem is read-only | the container stops at startup under `--read-only` |
| ignores SIGTERM | not stopped by `docker stop` | code 137 after 10.2 s |
| stops cleanly, writes a wrong counter | data lost | code 0 in a fraction of a second, counter back to 0 |

The correct image is the only one for which no control refuses. Each of the
others is refused by **one** control, and only one: that is what lets a partial
script score partially.

## Why a set of images, and not one

A script that always exits 0 accepts every broken image. A script that always
exits 1 refuses the correct one. A single image tells neither from a real
test. The set mixes a correct image and broken ones of different natures, and
the checks play your script against all of them.

## Why the refusals only count if the correct image is accepted

A missing script exits non-zero. A script that refuses everything too. Both
"refuse" the broken images without measuring anything. Every refusal check
therefore requires first that your script accepts the correct image: without
it, the refusal proves nothing, and the check says so instead of crediting it.

## Why most images are not there before the grading

Only `guichet:1.0` and `guichet:0.9` exist after the setup, because the brief
names them. The others are built by the checks, at grading time, from the
correct image, and removed afterwards. A script written to recognise images by
their name would pass the first two checks and fail the others.

## What the lab does not require

The wording of your messages, the order of your controls, the language of the
script as long as `bash tester-contrat.sh <image>` runs it, and any particular
value of timeout.

## The starting state is the repository's rule

The script does not exist, so the six checks are false before any work. A setup
task verifies that both images exist and that no script is there.
