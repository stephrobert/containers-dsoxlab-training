# Move the engine up without the gateway noticing

The lesson backs up, enables `live-restore` and upgrades. This course prepares
the upgrade without changing anything: reading a version, comparing it,
simulating, knowing whether a container was restarted, and recognising who runs
it.

You install nothing: all the commands on packages are reads or simulations. The
challenge uses `passerelle-sms` and its volume: do not touch them.

Related page: [Upgrade Docker Engine and back up its configuration](https://www.stephane-robert.info/en/docs/docker/upgrade-docker-engine-without-stopping-containers/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-mettre-a-jour-le-moteur
```

You are connected to `docker.lab`, where the engine runs. Its version is the
lab's starting one. **Keep the same terminal until the cleanup**: the variables
only exist in it.

```bash
mkdir -p ~/essai-montee && cd ~/essai-montee
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.8.2
```

The outputs of this course come from a Docker 29.8.2, the lab's starting version, on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔢 Exercise 1: reading a version

Ask for the installed version, the one the repository offers, and the
components:

```bash
apt-cache policy docker-ce | sed -n '2,3p'
apt-cache madison docker-ce | awk '{print $3}' | grep -c '^5:29\.'
dpkg -S /usr/bin/docker /usr/bin/dockerd /usr/bin/containerd
docker version --format 'client {{.Client.Version}}, serveur {{.Server.Version}}'
```

```text
  Installed: 5:29.8.2-1~debian.13~trixie
  Candidate: 5:29.10.1-1~debian.13~trixie
39
docker-ce-cli: /usr/bin/docker
docker-ce: /usr/bin/dockerd
containerd.io: /usr/bin/containerd
client 29.8.2, serveur 29.8.2
```

Installing without naming a version takes the candidate, hence the most recent.
The client, the daemon and containerd come from three different packages:
upgrading one does not upgrade the others. The `5:` prefix and the suffix are
part of the version to write.

## ⚖️ Exercise 2: comparing two versions

Look for the most recent of two versions, in three ways:

```bash
printf '29.9.2\n29.10.0\n' | sort | tail -1
printf '29.9.2\n29.10.0\n' | sort -V | tail -1
dpkg --compare-versions 29.9.2 lt 29.10.0 && echo '29.9.2 est plus ancienne'
dpkg --compare-versions 5:29.9.2-1 gt 29.10.0-1 && echo 'et pourtant 5:29.9.2-1 gagne'
```

```text
29.9.2
29.10.0
29.9.2 est plus ancienne
et pourtant 5:29.9.2-1 gagne
```

A text sort gets it wrong, `sort -V` does not. The last result surprises: the
number before the colon, the epoch, comes before everything else. Always
compare complete versions, as the package carries them.

## 🧪 Exercise 3: simulating

Ask `apt-get` what it would do, for a version that exists and one that does
not:

```bash
CIBLE=$(apt-cache madison docker-ce | awk 'NR==1{print $3}')
apt-get -s install "docker-ce=$CIBLE" 2>&1 | grep -E 'held packages will be changed|upgraded'
apt-get -s install docker-ce=1.2.3 2>&1 | grep -o "Version '1.2.3' for 'docker-ce' was not found"
apt-mark showhold | wc -l
docker version --format '{{.Server.Version}}'
```

```text
The following held packages will be changed:
The following packages will be upgraded:
1 upgraded, 0 newly installed, 0 to remove and 5 not upgraded.
Version '1.2.3' for 'docker-ce' was not found
6
29.8.2
```

`-s` installs nothing, and does not require being root. The simulation already
announces that held packages would change: this is the moment to find out.
Count the held packages before, to find the same number after.

## 🕰️ Exercise 4: knowing whether a container was restarted

Restart a container by hand, then kill its process, and read three fields
again:

```bash
docker run -d --init --restart unless-stopped --name essai-temoin "$IMAGE" sleep 600 > /dev/null
lit() { docker inspect essai-temoin --format '{{.State.Pid}} {{.State.StartedAt}} {{.RestartCount}}'; }
A=$(lit); docker restart --timeout 1 essai-temoin > /dev/null; B=$(lit)
sudo kill -9 "$(docker inspect essai-temoin --format '{{.State.Pid}}')"; sleep 2; C=$(lit)
echo "compteurs : ${A##* } ${B##* } ${C##* }"
[ "${A%% *}" = "${B%% *}" ] && echo 'meme processus' || echo 'processus change apres restart'
```

```text
compteurs : 0 0 1
processus change apres restart
```

A `docker restart` does not count in `RestartCount`: only a restart by the
policy does. A counter at zero therefore proves nothing. Note the PID and the
start time before the intervention, and compare them after.

## 🧬 Exercise 5: recognising who runs it

Go up from the container's process to its parent:

```bash
PERE=$(ps -o ppid= -p "$(docker inspect essai-temoin --format '{{.State.Pid}}')" | tr -d ' ')
ps -o comm= -p "$PERE"
ps -o ppid= -p "$PERE" | tr -d ' '
docker info --format 'live-restore={{.LiveRestoreEnabled}}'
```

```text
containerd-shim
1
live-restore=false
```

The parent is `containerd-shim`, itself attached to process 1: the Docker
daemon is not in the chain. This is why a container **can** survive its stop.
If it still dies, it is because the daemon stops it on purpose, which
`live-restore` changes.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-temoin > /dev/null
rm -rf ~/essai-montee
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-mettre-a-jour-le-moteur
dsoxlab check docker-mettre-a-jour-le-moteur
```

```text
╭─ Result: docker-mettre-a-jour-le-moteur ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests         │
╰──────────────────────────────────────────╯
```

0 out of 5: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: an exact version to reach, and a gateway that
must feel nothing.

```bash
dsoxlab run docker-mettre-a-jour-le-moteur
dsoxlab challenge docker-mettre-a-jour-le-moteur
```
