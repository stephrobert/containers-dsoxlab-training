# Brief

Work on `docker.lab`, in `/opt/dsoxlab-images-tester-le-contrat`. The context of
the service is in `guichet/`. The images `guichet:1.0` (correct) and
`guichet:0.9` (not) are already built.

Write **`tester-contrat.sh`** in that directory. `bash tester-contrat.sh
<image>` must exit 0 when the image meets the contract below, and a non-zero
code otherwise.

## 1. It accepts the correct image, and leaves nothing behind

`bash tester-contrat.sh guichet:1.0` exits 0. When it returns, no container and
no volume it created remains, whatever the outcome.

## 2. It refuses an image that does not start, or cannot be reached

The service answers `GET /ouvert` with a 200 on port `8099`, **through a
published port**. An image that runs but is not reachable that way, or that
stops at startup, is refused. Do not wait a fixed time: bound the wait.

## 3. It refuses a badly checked configuration

Without `GUICHET_SITE`, the service must stop quickly, with a **non-zero** code
and a message that names the variable. An image that stops with code 0, or that
starts anyway, is refused.

## 4. It refuses an image that asks for too much

The process must not run as root, and the service must still run when the
container is started read-only, with `/var/lib/guichet` as its only writable
place.

## 5. It refuses an image that stops badly

`docker stop` must end the container in well under ten seconds, with code 0 or
143, and the counter must survive: after mounting the same data directory in a
new container, `GET /tickets` returns the number of tickets handed out before
the stop.

## 6. It refuses what it cannot judge

With no argument, or with the name of an image that does not exist, it exits
non-zero.

## What is not graded

The wording of your messages, the order of your controls, and the language of
the script, as long as `bash tester-contrat.sh <image>` runs it.

Two images are named in this brief. The checks play your script against others,
which you have not seen: do not write a script that recognises them by name.
