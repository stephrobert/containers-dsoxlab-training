# 'Up' says nothing about the service

The lesson declares a probe and sets its bounds. This course adds five
situations: the code that makes the verdict, the account that plays the probe,
the history of state changes, a container stopped then started again, and a
probe inherited from a base.

You work in `~/essai-pouls`, on `essai-*` containers. The challenge uses
`service-surveille`: do not touch it during the course.

Related page: [Test the contract of an image](https://www.stephane-robert.info/en/docs/docker/test-an-image-contract/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-healthcheck
```

You are connected to `docker.lab`, where the engine runs. The `sonde` function
starts a container with a health command, played every second. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-pouls && cd ~/essai-pouls
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sonde() { docker run -d --init --name essai-sonde --health-interval 1s --health-retries 2 --health-cmd "$1" ${2:-} "$IMAGE" sleep 600 > /dev/null; sleep 4; }
etat() { docker inspect essai-sonde --format '{{.State.Status}} {{.State.Health.Status}}'; }
retire() { docker rm -f essai-sonde > /dev/null; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔢 Exercise 1: the code that makes the verdict

Give the probe three exit codes:

```bash
for code in 0 1 137; do sonde "exit $code"; etat; docker inspect essai-sonde --format '{{(index .State.Health.Log 0).ExitCode}}'; retire; done
```

```text
running healthy
0
running unhealthy
1
running unhealthy
137
```

Zero means healthy, everything else means unhealthy. The exact code stays in
the log: 137 is the one of a killed probe, which is not the same failure as a 1.

## 👤 Exercise 2: the account that plays the probe

Start the container under an ordinary account, with a probe that reads a file
reserved for root:

```bash
sonde 'id -u; cat /etc/shadow' '--user 4242'
etat
docker inspect essai-sonde --format '{{(index .State.Health.Log 0).Output}}'
retire
```

```text
running unhealthy
4242
cat: can't open '/etc/shadow': Permission denied
```

The probe runs under the container's account. The service may well work: the
probe is the one not allowed to look. First try it by hand with `docker exec`,
under the same account.

## 📜 Exercise 3: the history of changes

Take a container from unhealthy to healthy, then read what the engine recorded:

```bash
DEBUT=$(date +%s)
sonde 'test -f /tmp/pret'
docker ps --filter health=unhealthy --format '{{.Names}}'
docker exec essai-sonde touch /tmp/pret
sleep 3
docker ps --filter health=unhealthy -q | wc -l
docker events --since "$DEBUT" --until "$(date +%s)" --filter container=essai-sonde --filter event=health_status --format '{{.Action}}'
```

```text
essai-sonde
0
health_status: unhealthy
health_status: healthy
```

`docker ps --filter health=unhealthy` lists the unhealthy ones of the machine,
and `docker events` keeps the changes, including past ones. A monitoring system
reads one or the other: the engine does nothing with that state.

## ⏹️ Exercise 4: a container stopped then started again

Make the probe unhealthy, stop the container, then start it again:

```bash
docker exec essai-sonde rm /tmp/pret
sleep 4
docker stop --timeout 1 essai-sonde > /dev/null
etat
docker start essai-sonde > /dev/null
etat
retire
```

```text
exited unhealthy
running starting
```

A stopped container keeps its last health state: `exited unhealthy` does not
say why it stopped. At startup, the state goes back to `starting`, and the
probe must conclude again.

## 🧬 Exercise 5: a probe inherited from a base

Build an image with a probe, then three images that start from it:

```bash
printf 'FROM %s\nHEALTHCHECK --interval=1s CMD test -f /tmp/pret\n' "$IMAGE" > socle.Dockerfile
docker build -q -f socle.Dockerfile -t essai-pouls:socle . > /dev/null
printf 'FROM essai-pouls:socle\nENV X=1\n' > a.Dockerfile
printf 'FROM essai-pouls:socle\nHEALTHCHECK NONE\n' > b.Dockerfile
printf 'FROM essai-pouls:socle\nHEALTHCHECK --retries=9 CMD true\nHEALTHCHECK CMD false\n' > c.Dockerfile
for f in a b c; do docker build -q -f $f.Dockerfile -t essai-pouls:$f . > /dev/null 2>&1; docker image inspect essai-pouls:$f --format '{{json .Config.Healthcheck}}'; done
```

```text
{"Test":["CMD-SHELL","test -f /tmp/pret"],"Interval":1000000000}
{"Test":["NONE"]}
{"Test":["CMD-SHELL","false"]}
```

The probe is inherited, with its bounds, even if your Dockerfile does not
mention it. `HEALTHCHECK NONE` removes it. Two instructions do not add up: the
last one wins as a whole, and the nine retries are gone.

## 🧹 Cleanup

```bash
cd ~
docker images 'essai-pouls' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-pouls
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset images-healthcheck
dsoxlab check images-healthcheck
```

```text
╭─── Result: images-healthcheck ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a service that goes quiet without dying, and
a probe to write for it.

```bash
dsoxlab run images-healthcheck
dsoxlab challenge images-healthcheck
```
