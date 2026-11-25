# Is the engine actually working? Four answers, not one

The lesson installs Docker and checks the installation. This course teaches how
to read a breakdown before repairing it, on test objects: two errors that look
alike, a service started but not enabled, a blocked service, a group not yet
taken into account, and a wrong configuration file.

On this machine, the Docker engine is broken on purpose: it is the subject of
the challenge. **Do not repair it during the course.** You work on an
`essai-veille` service and an `essai-compte` account, created then removed
here.

Related page: [Install Docker Engine 29 and prove it works](https://www.stephane-robert.info/en/docs/docker/install-docker-engine/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-verifier-son-moteur
```

You are connected to `docker.lab`. The last command only queries the client.
**Keep the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-moteur && cd ~/essai-moteur
docker --version | cut -d, -f1
```

```text
Docker version 29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 📞 Exercise 1: two errors that look alike

Target a socket that does not exist, then a socket that exists but that your
account may not open:

```bash
export DOCKER_HOST=unix:///tmp/essai-absent.sock
docker ps 2>&1 | grep -oE 'permission denied|[Cc]annot connect|failed to connect' | head -1
cat > prise.py <<'EOF'
import os, socket, time
s = socket.socket(socket.AF_UNIX)
s.bind("/tmp/essai-prise.sock")
os.chmod("/tmp/essai-prise.sock", 0o600)
s.listen()
time.sleep(60)
EOF
sudo python3 prise.py & sleep 1
export DOCKER_HOST=unix:///tmp/essai-prise.sock
docker ps 2>&1 | grep -oE 'permission denied|[Cc]annot connect|failed to connect' | head -1
sudo pkill -f '^python3 prise.py'; sudo rm -f /tmp/essai-prise.sock; unset DOCKER_HOST
```

```text
failed to connect
permission denied
```

The first error says nobody is listening: look at the service. The second says
the door exists and is closed to you: look at the permissions. Reinstalling the
package changes neither. `docker --version` always answers: it only queries the
client.

## 🔁 Exercise 2: started, but not enabled

Create a service, start it, then ask both questions:

```bash
printf '[Service]\nExecStart=/bin/sleep 900\n[Install]\nWantedBy=multi-user.target\n' | sudo tee /etc/systemd/system/essai-veille.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl start essai-veille
systemctl is-active essai-veille; systemctl is-enabled essai-veille
sudo systemctl enable -q essai-veille && sudo systemctl stop essai-veille
systemctl is-active essai-veille; systemctl is-enabled essai-veille
ls -l /etc/systemd/system/multi-user.target.wants/essai-veille.service | grep -o '> .*'
```

```text
active
disabled
inactive
enabled
> /etc/systemd/system/essai-veille.service
```

The two states are independent. Enabling creates a link the machine's boot will
follow; it starts nothing right away. `enable --now` does both.

## 🚧 Exercise 3: a blocked service

Mask the service, try to start it, then give it a program that does not exist:

```bash
sudo rm /etc/systemd/system/multi-user.target.wants/essai-veille.service /etc/systemd/system/essai-veille.service
sudo systemctl daemon-reload && sudo systemctl mask -q essai-veille
sudo systemctl start essai-veille 2>&1 | grep -o 'is masked'
systemctl is-enabled essai-veille
sudo systemctl unmask -q essai-veille
printf '[Service]\nExecStart=/usr/bin/programme-absent\n' | sudo tee /etc/systemd/system/essai-veille.service > /dev/null
sudo systemctl daemon-reload && sudo systemctl start essai-veille; sleep 1
systemctl is-active essai-veille
systemctl show essai-veille -p Result -p ExecMainStatus
sudo journalctl -u essai-veille -n 20 --no-pager -o cat | grep -o 'Unable to locate executable.*' | head -1
```

```text
Unit essai-veille.service does not exist, proceeding anyway.
is masked
masked
failed
Result=exit-code
ExecMainStatus=203
Unable to locate executable '/usr/bin/programme-absent': No such file or directory
```

A masked service refuses any start: `is-enabled` says so. A failing service
starts without a visible error, and it is `is-active` then the log that speak.
Read **the service's** log before looking elsewhere.

## 👥 Exercise 4: a group not yet taken into account

Open a session, add the account to a group, and compare what the session sees
and what the system says:

```bash
sudo groupadd essai-groupe && sudo useradd -m essai-compte && sudo usermod -aG adm essai-compte
sudo -u essai-compte sh -c 'sleep 2; echo "session ouverte avant : $(id -nG)"' &
sleep 1; sudo usermod -aG essai-groupe essai-compte
echo "systeme : $(id -nG essai-compte)"
wait
echo "session neuve : $(sudo -u essai-compte id -nG)"
sudo usermod -G essai-groupe essai-compte
echo "sans -a : $(id -nG essai-compte)"
```

```text
systeme : essai-compte adm essai-groupe
session ouverte avant : essai-compte adm
session neuve : essai-compte adm essai-groupe
sans -a : essai-compte essai-groupe
```

A session keeps the groups from when it was opened. The system is up to date:
one must log in again, not start over. The last line shows the trap: without
`-a`, `usermod -G` replaces the list, and the account lost `adm`.

## 📝 Exercise 5: a wrong configuration file

Have the daemon check three files, without starting it:

```bash
printf '{"log-driver": "json-file"}\n' > bon.json
printf '{"log-driver": "json-file",}\n' > virgule.json
printf '{"log-drivr": "json-file"}\n' > faute.json
for f in bon virgule faute; do echo "$f : $(sudo dockerd --validate --config-file $f.json 2>&1 | grep -oE 'configuration OK|invalid character.*|following directives.*' | head -1)"; done
```

```text
bon : configuration OK
virgule : invalid character '}' looking for beginning of object key string
faute : following directives don't match any configuration option: log-drivr
```

One comma too many or an unknown name prevents the daemon from starting.
`--validate` says so beforehand, without touching the service. It is the check
to make before any restart.

## 🧹 Cleanup

```bash
cd ~
sudo systemctl reset-failed essai-veille 2> /dev/null
sudo rm -f /etc/systemd/system/essai-veille.service && sudo systemctl daemon-reload
sudo userdel -r essai-compte 2> /dev/null; sudo groupdel essai-groupe
rm -rf ~/essai-moteur
getent passwd essai-compte | wc -l
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-verifier-son-moteur
dsoxlab check docker-verifier-son-moteur
```

```text
╭─ Result: docker-verifier-son-moteur ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests     │
╰──────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: an installed engine that is of no use, and
four proofs to bring.

```bash
dsoxlab run docker-verifier-son-moteur
dsoxlab challenge docker-verifier-son-moteur
```
