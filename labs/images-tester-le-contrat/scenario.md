# The image that builds, and that nobody can use

## The situation

The build is green. The image is in the local store, the pipeline says it
passed, and the team that receives it starts it on Monday morning.

By ten o'clock, three things have gone wrong, and none of them was visible
the evening before. One container started, but nothing answers on the port it
published. One refuses to say why it stopped. One was killed after ten seconds
instead of stopping, and the counter it kept in memory went with it.

Nobody tested the image **from the outside**, the way the people who run it
do. The unit tests of the code passed, and they could not have caught any of
this: the defects are in the image, not in the program.

## The goal

The context is in `/opt/dsoxlab-images-tester-le-contrat`. The service there is a
**guichet**, a small counter that hands out numbered tickets. Two images are
already built from it:

```text
guichet:1.0   meets the contract
guichet:0.9   an older build, which does not
```

Write **`/opt/dsoxlab-images-tester-le-contrat/tester-contrat.sh`**. It takes an
image name, starts that image the way a user would, and exits:

```text
0         the image meets the contract
non-zero  it does not, and the output says which control refused it
```

The brief is also laid down in `/opt/dsoxlab-images-tester-le-contrat/MISSION.md`.

## What a user of the image may expect

| Expectation | What it means for the guichet |
| --- | --- |
| It starts | it answers `GET /ouvert` with a 200 on port `8099`, reached through a published port |
| It does its work | `POST /ticket` answers 201 and hands out the next number, `GET /tickets` returns how many were handed out |
| It is configured | without `GUICHET_SITE` it stops at once, with a non-zero code and a message that names the variable; with it, `/ouvert` mentions the site |
| It asks for no privilege | the process is not root, and the service still runs when the container is started with a read-only filesystem, its data directory `/var/lib/guichet` being the only writable place |
| It stops when asked | `docker stop` ends it in well under the ten-second grace period, with exit code 0 or 143, and the counter is still there when the same data directory is mounted again |

## What is graded

Your **script**, played by the checks against a set of images. One of them
meets the contract and must be accepted. The others are broken in different
ways, and you have not seen them all: each must be refused with a non-zero
code.

A script that always exits 0 accepts every broken image. A script that always
exits 1 refuses the correct one, and then none of its refusals counts. Only a
script that tells them apart is graded.

Whatever the script creates, it removes: containers and volumes. A test that
leaves its debris behind poisons the next one.

The language is yours, as long as `bash tester-contrat.sh <image>` runs it.
Do not change the daemon configuration, and do not remove `guichet:1.0`: the
checks derive their own images from it.
