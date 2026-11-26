# Qualify a rootless Docker engine

The lesson installs a rootless engine and measures its network and its limits.
This course prepares the account that carries it, without Docker: a user
service without a session, a wrongly designated bus, a service that goes out
with the account, a root that is not one, and a forbidden port.

You work on the `essai-r` account, created then removed here. The challenge
uses the `dsoxlab-rootless` account: do not touch it during the course.

Related page: [Run Docker in rootless mode](https://www.stephane-robert.info/en/docs/docker/run-docker-in-rootless-mode/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-rootless
```

You are connected to `docker.lab`, where the engine runs. `R` runs a command as
the `essai-r` account. **Keep the same terminal until the cleanup**: the
variables only exist in it.

```bash
mkdir -p ~/essai-sans-root && cd ~/essai-sans-root
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sudo useradd -r -m -s /bin/bash essai-r
NUM=$(id -u essai-r)
R() { sudo -u essai-r "$@"; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🚪 Exercise 1: an account without a session

Query the account's service manager, then allow it to live without a session:

```bash
R systemctl --user is-active default.target 2>&1 | grep -o 'not defined'
ls -d /run/user/$NUM 2>&1 | grep -o 'No such file'
sudo loginctl enable-linger essai-r && sleep 2
systemctl is-active user@$NUM
sudo stat -c '%U %a' /run/user/$NUM
```

```text
not defined
No such file
active
essai-r 700
```

A system account has neither session nor service manager as long as nobody logs
in. `enable-linger` starts that manager without a session, and creates the
runtime directory, reserved for the account.

## 🧭 Exercise 2: a wrongly designated bus

Make the request again without a variable, with a wrong one, with the right
one, then in another way:

```bash
R systemctl --user is-active default.target 2>&1 | grep -o 'not defined'
R env XDG_RUNTIME_DIR=/run/user/1 systemctl --user is-active default.target 2>&1 | grep -o 'No such file or directory'
R env XDG_RUNTIME_DIR=/run/user/$NUM systemctl --user is-active default.target
sudo systemctl --user -M essai-r@ is-active default.target
```

```text
not defined
No such file or directory
active
active
```

`sudo -u` changes the account without opening a session: the variable is still
missing. The two errors read differently, one says nothing is designated, the
other that the directory does not exist. The `-M account@` form avoids the
variables.

## 🕯️ Exercise 3: a service that goes out with the account

Create a user service, start it, then remove the permission to live without a
session:

```bash
R mkdir -p /home/essai-r/.config/systemd/user
printf '[Service]\nExecStart=/bin/sleep 900\n[Install]\nWantedBy=default.target\n' | R tee /home/essai-r/.config/systemd/user/essai.service > /dev/null
GERE="sudo systemctl --user -M essai-r@"
$GERE daemon-reload && $GERE start essai
$GERE is-active essai
$GERE is-enabled essai
systemctl is-active essai
ps -o user= -C sleep | sort -u
sudo loginctl disable-linger essai-r && sleep 12
pgrep -u essai-r -c sleep
```

```text
active
disabled
inactive
essai-r
0
```

The system's manager does not know this service: `systemctl` without `--user`
answers `inactive`. A started service is not enabled at boot for all that. And
without `linger`, it disappears with the account's manager.

## 🎭 Exercise 4: a root that is not one

Become root in a user namespace, and look at what it can do:

```bash
R unshare -U -r id -u
R unshare -U -r cat /proc/self/uid_map | awk '{print $1, "devient", ($2 == '$NUM' ? "essai-r" : $2), "sur", $3, "identifiant"}'
R unshare -U -r head -c 1 /etc/shadow
R unshare -U -r sh -c 'touch ~/f; stat -c "vu dedans : %u" ~/f; chown 1 ~/f 2>&1 | grep -o "Invalid argument"'
sudo stat -c 'vu de la machine : %U' /home/essai-r/f
grep -c essai-r /etc/subuid
```

```text
0
0 devient essai-r sur 1 identifiant
head: cannot open '/etc/shadow' for reading: Permission denied
vu dedans : 0
Invalid argument
vu de la machine : essai-r
0
```

Identifier 0 inside is the `essai-r` account outside: it reads nothing more. It
cannot give a file to identifier 1, which does not exist in its table. This is
the role of `/etc/subuid`: providing other identifiers. This system account
received none.

## 🔌 Exercise 5: a forbidden port

Open a low port then a high port, as an ordinary account and as root inside:

```bash
cat /proc/sys/net/ipv4/ip_unprivileged_port_start
ouvre() { "$@" python3 -c 'import socket; socket.socket().bind(("127.0.0.1", 80))' 2>&1 | grep -o 'Permission denied'; }
ouvre R
ouvre R unshare -U -r
R python3 -c 'import socket; socket.socket().bind(("127.0.0.1", 8089)); print("8089 ouvert")'
```

```text
1024
Permission denied
Permission denied
8089 ouvert
```

Being root in the user namespace gives no right over the machine's network. A
rootless engine therefore publishes above the threshold shown on the first
line, unless the administrator changes it.

## 🧹 Cleanup

```bash
cd ~
sudo userdel -r essai-r 2> /dev/null; id essai-r 2>&1 | grep -o 'no such user'
rm -rf ~/essai-sans-root
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
no such user
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-rootless
dsoxlab check securite-rootless
```

```text
╭──── Result: securite-rootless ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/8 tests  │
╰───────────────────────────────────╯
```

0 out of 8: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a daemon prepared for a dedicated account,
only waiting to be started.

```bash
dsoxlab run securite-rootless
dsoxlab challenge securite-rootless
```
