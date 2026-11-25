# Configure persistent Docker log defaults

The lesson changes `daemon.json` methodically. This course shows its blind
spots: what validation catches and lets through, a setting that reloading does
not apply, containers already created, a merge that erases, and an error
swallowed in silence.

You work in `~/essai-demon`. The challenge uses `/etc/docker/daemon.json`: this
course changes it too, after keeping a copy, and puts it back at the end.

Related page: [Administer the Docker daemon and its contexts](https://www.stephane-robert.info/en/docs/docker/administer-the-docker-daemon-and-its-contexts/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-configurer-le-demon
```

You are connected to `docker.lab`, where the engine runs. The first command
keeps the current configuration. `pose` writes the configuration, `relance`
restarts the daemon (`reset-failed` prevents systemd from refusing several
restarts in a row), `cree` shows the logging of a container created now. **Keep
the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-demon && cd ~/essai-demon
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sudo test -f /etc/docker/daemon.json && sudo cp -a /etc/docker/daemon.json origine.json
relance() { sudo systemctl reset-failed docker; sudo systemctl restart docker; local r=$?; sleep 3; return $r; }
pose() { echo "$1" | sudo tee /etc/docker/daemon.json > /dev/null; }
cree() { docker create --name "essai-$1" "${@:2}" "$IMAGE" true > /dev/null && docker inspect "essai-$1" --format '{{.HostConfig.LogConfig.Type}} {{json .HostConfig.LogConfig.Config}}'; }
valide() { echo "$1" > essai.json; sudo dockerd --validate --config-file essai.json 2>&1 | tail -1 | grep -oE "invalid character.*|cannot unmarshal [a-z]+|don't match any.*|configuration OK"; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔎 Exercise 1: what validation catches

Have six wrong files validated:

```bash
valide '{"log-driver": "json-file",}'
valide '{"log-opts": {"max-file": 2}}'
valide '{"log-drivr": "json-file"}'
valide '{"log-opts": {"max-siz": "10m"}}'
valide '{"log-opts": {"max-size": "10x"}}'
valide '{"log-driver": "inconnu"}'
```

```text
invalid character '}' looking for beginning of object key string
cannot unmarshal number
don't match any configuration option: log-drivr
configuration OK
configuration OK
configuration OK
```

Validation sees the extra comma, the number without quotes and the unknown key.
It does not read the content of `log-opts`, nor the driver's name: the last
three files are declared good. `configuration OK` means "the file can be read",
not "the setting works".

## 🔄 Exercise 2: a setting that reloading does not apply

Apply a configuration by restarting, change it, then only reload:

```bash
pose '{"log-opts": {"max-size": "2m"}, "labels": ["zone=a"]}'
relance
docker info --format '{{.Labels}}'; cree un
pose '{"log-opts": {"max-size": "7m"}, "labels": ["zone=b"]}'
sudo systemctl reload docker; sleep 2
docker info --format '{{.Labels}}'; cree deux
```

```text
[zone=a]
json-file {"max-size":"2m"}
[zone=b]
json-file {"max-size":"2m"}
```

Both settings are in the same file. Reloading took the label and left the old
size: log values need a restart. Check each setting by its effect, never by the
command's success.

## 🧊 Exercise 3: containers already created

Restart to apply the new size, then compare the old container with three new
ones:

```bash
relance
docker inspect essai-un --format '{{json .HostConfig.LogConfig.Config}}'
cree trois
cree quatre --log-opt max-file=3
cree cinq --log-driver local
```

```text
{"max-size":"2m"}
json-file {"max-size":"7m"}
json-file {"max-file":"3","max-size":"7m"}
local {}
```

The first one keeps the value of its creation, and the restart changes nothing.
An option passed at creation is added to the daemon's values. Changing the
driver discards them all: the `cinq` container has no declared limit.

## 🧨 Exercise 4: a merge that erases

Add a key to an existing configuration, in two ways:

```bash
python3 - <<'EOF'
import json
avant = {"debug": True, "log-opts": {"labels": "equipe", "max-size": "5m"}}
print(json.dumps({**avant, "log-opts": {"max-file": "2"}}))
print(json.dumps({**avant, "log-opts": {**avant["log-opts"], "max-file": "2"}}))
EOF
```

```text
{"debug": true, "log-opts": {"max-file": "2"}}
{"debug": true, "log-opts": {"labels": "equipe", "max-size": "5m", "max-file": "2"}}
```

Replacing `log-opts` as a whole loses `labels` and `max-size`, without any
error. You must merge inside. Always compare the old and the new file before
restarting.

## 🤐 Exercise 5: an error swallowed in silence

Break the file and reload, then set an impossible size and restart:

```bash
pose '{"labels":,}'
sudo systemctl reload docker; echo "reload: $?"; sleep 2
docker info --format '{{.Labels}}'
sudo journalctl -u docker -n 20 -o cat --no-pager | grep -o 'Error reloading configuration' | tail -1
pose '{"log-opts": {"max-size": "10x"}}'
relance; echo "restart: $?"
docker run --rm "$IMAGE" true 2>&1 | grep -o "invalid suffix.*"
```

```text
reload: 0
[zone=b]
Error reloading configuration
restart: 0
invalid suffix: 'x'
```

Reloading returns 0, keeps the old configuration and only writes the error in
the service's log. The restart succeeds with an impossible size, and the first
container started is the one that fails. Always finish with a test container.

## 🧹 Cleanup

```bash
cd ~
if [ -f ~/essai-demon/origine.json ]; then sudo cp -a ~/essai-demon/origine.json /etc/docker/daemon.json; else sudo rm /etc/docker/daemon.json; fi
relance
docker rm -f essai-un essai-deux essai-trois essai-quatre essai-cinq > /dev/null
rm -rf ~/essai-demon
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-configurer-le-demon
dsoxlab check docker-configurer-le-demon
```

```text
╭─ Result: docker-configurer-le-demon ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests     │
╰──────────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: bounded logs for every new container, without
losing a setting.

```bash
dsoxlab run docker-configurer-le-demon
dsoxlab challenge docker-configurer-le-demon
```
