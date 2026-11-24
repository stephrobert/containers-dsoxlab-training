# Interrogate a running container

The lesson gives four commands for four questions: logs, address, port and
written file. This course puts you in front of five other cases: an error that
`grep` does not see in the logs, a lost start command, a container on several
networks, a port already taken, and a container without the tool you need.

You work on `essai-guichet`. The challenge uses `greffier`, already running: do
not touch it during the course.

Related page: [Inspect a running container with Docker](https://www.stephane-robert.info/en/docs/docker/inspect-a-running-container/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-inspecter-un-conteneur
```

You are connected to `docker.lab`, where the engine runs. Start the practice
container, which the exercises make you query. **Keep the same terminal until
the cleanup**: the variables only exist in it.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker run -d --name essai-guichet -e MODE=demo -v essai-donnees:/donnees \
  --restart on-failure:3 -p 127.0.0.1:8099:8000 "$IMAGE" \
  sh -c 'echo "guichet ouvert"; echo "ERREUR cle absente" >&2; exec nc -lk -p 8000 -e cat' > /dev/null
sleep 1
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on
24 November 2026. The addresses will differ on your side.

## 📜 Exercise 1: the error `grep` does not see

`docker logs` returns the standard output and the error output of the container
separately. Hide the error output, then count the `ERREUR` lines with and
without it:

```bash
docker logs essai-guichet 2> /dev/null
docker logs essai-guichet 2> /dev/null | grep -c ERREUR
docker logs essai-guichet 2>&1 | grep -c ERREUR
```

```text
guichet ouvert
0
1
```

A pipe only passes the standard output. Without `2>&1`, `grep` does not receive
the error message and you could conclude it does not exist. Write
`docker logs <name> 2>&1 | grep …` by reflex.

## 🧾 Exercise 2: find the start command again

The original `docker run` command is written nowhere on the host. The engine
keeps its settings, provided you know where to ask for them:

```bash
docker container inspect essai-guichet --format 'image    {{.Config.Image}}
commande {{json .Config.Cmd}}
env      {{json .Config.Env}}
reprise  {{.HostConfig.RestartPolicy.Name}}:{{.HostConfig.RestartPolicy.MaximumRetryCount}}
montages {{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{end}}
ports    {{json .HostConfig.PortBindings}}'
```

```text
image    alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
commande ["sh","-c","echo \"guichet ouvert\"; echo \"ERREUR cle absente\" >&2; exec nc -lk -p 8000 -e cat"]
env      ["MODE=demo","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
reprise  on-failure:3
montages volume essai-donnees -> /donnees
ports    {"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":"8099"}]}
```

`Config` describes what the container runs: image, command, variables.
`HostConfig` describes what you asked from the host: restart, ports. `Mounts`
gives the mounted data. With these six lines, you can start the same container
again. `PATH` comes from the image and not from the command line. Variables are
shown in clear text: a password passed with `-e` can be read by anyone who can
query the engine.

## 🌐 Exercise 3: a container on two networks

Attach the container to a second network, then ask for its address with the two
forms of the lesson:

```bash
docker network create essai-arriere > /dev/null
docker network connect essai-arriere essai-guichet
docker container inspect essai-guichet --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
docker container inspect essai-guichet --format '{{range $nom, $c := .NetworkSettings.Networks}}{{println $nom $c.IPAddress}}{{end}}'
```

```text
172.17.0.3172.18.0.2
bridge 172.17.0.3
essai-arriere 172.18.0.2
```

Without a separator, the two addresses stick together into a useless value, and
a script would notice nothing. The second form names each network, and `println`
ends each line. Use it as soon as a container can have several networks.

## 🚪 Exercise 4: who holds this port?

Try to publish a port already taken, then look for who holds it. The filters of
`docker ps` also answer for a volume and for a network:

```bash
docker run --rm -p 127.0.0.1:8099:80 "$IMAGE" true 2>&1 | grep -o 'Bind for.*'
docker ps --filter publish=8099 --format '{{.Names}} {{.Ports}}'
docker ps --filter volume=essai-donnees --format '{{.Names}}'
docker ps --filter network=essai-arriere --format '{{.Names}}'
```

```text
Bind for 127.0.0.1:8099 failed: port is already allocated
essai-guichet 127.0.0.1:8099->8000/tcp
essai-guichet
essai-guichet
```

The error message does not name the culprit. `--filter publish=8099` gives it at
once. `volume=` and `network=` answer the same question before you remove a
volume or a network: who still uses it?

## 🧰 Exercise 5: a container without the tool you want

The image does not hold `ss`. Instead of installing something in it, enter only
the container's network from the host, with the tools of the host:

```bash
docker exec essai-guichet ss -ltn
PID=$(docker container inspect essai-guichet --format '{{.State.Pid}}')
sudo nsenter --target "$PID" --net ss -ltn
sudo cat /proc/$PID/root/etc/alpine-release
```

```text
OCI runtime exec failed: exec failed: unable to start container process: exec: "ss": executable file not found in $PATH
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port
LISTEN 0      4096      127.0.0.11:33341      0.0.0.0:*
LISTEN 0      1                  *:8000             *:*
3.24.3
```

`docker exec` fails: the program does not exist in the image. `nsenter --net`
runs the `ss` of the host in the container's network: port 8000 is open. The
`127.0.0.11` line is the DNS server that Docker sets up in the containers of a
network you created. `/proc/<pid>/root` gives access to the container's files in
the same way, here the Alpine version.

## 🧹 Cleanup

```bash
docker rm -f essai-guichet > /dev/null
docker network rm essai-arriere
docker volume rm essai-donnees
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-arriere
essai-donnees
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-inspecter-un-conteneur
dsoxlab check docker-inspecter-un-conteneur
```

```text
╭─ Result: docker-inspecter-un-conteneur ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests        │
╰─────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: get four pieces of information from a
container without documentation, without stopping it.

```bash
dsoxlab run docker-inspecter-un-conteneur
dsoxlab challenge docker-inspecter-un-conteneur
```
