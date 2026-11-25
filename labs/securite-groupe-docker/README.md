# Remove an unnecessary Docker grant

The lesson removes an account from the group and looks for the other ways. This
course adds the traps of the removal: a command that takes away too much, a
forgotten primary group, an equivalent `sudo` rule, a socket that changed
group, and a permission open to all.

You work on the `essai-un` and `essai-deux` accounts, created then removed
here. The challenge uses `dsoxlab-auditor`: do not touch it, and do not remove
your own access.

Related page: [Remove direct access to the Docker daemon](https://www.stephane-robert.info/en/docs/docker/remove-direct-access-to-the-docker-daemon/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-groupe-docker
```

You are connected to `docker.lab`, where the engine runs. The `acces` function
really tries to reach the engine under an account. **Keep the same terminal
until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-acces-groupe && cd ~/essai-acces-groupe
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sudo useradd -m essai-un && sudo useradd -m essai-deux && sudo groupadd essai-equipe
sudo usermod -aG docker,essai-equipe essai-un
acces() { sudo -n -u "$1" docker ps -q > /dev/null 2>&1 && echo "$1 : acces" || echo "$1 : refuse"; }
acces essai-un; acces essai-deux
```

```text
29.9.2
essai-un : acces
essai-deux : refuse
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🧹 Exercise 1: a command that takes away too much

Remove the account from the group by rewriting the list, then by removing only
it:

```bash
sudo usermod -G docker essai-un; id -nG essai-un
sudo usermod -aG essai-equipe essai-un
sudo gpasswd -d essai-un docker
id -nG essai-un
acces essai-un
```

```text
essai-un docker
Removing user essai-un from group docker
essai-un essai-equipe
essai-un : refuse
```

`usermod -G` without `-a` replaces the whole list: the account lost
`essai-equipe` and nothing said so. `gpasswd -d` removes a single group and
leaves the others.

## 🪪 Exercise 2: a forgotten primary group

Give `docker` as primary group, then look for the account in the group:

```bash
sudo usermod -g docker essai-un
grep '^docker:' /etc/group | grep -c essai-un
acces essai-un
id -gn essai-un
sudo usermod -g essai-un essai-un
acces essai-un
```

```text
0
essai-un : acces
docker
essai-un : refuse
```

The account is not in the group's line, and it has the access: the primary
group is written in `/etc/passwd`. Query `id`, never the groups file alone.

## 🎫 Exercise 3: an equivalent sudo rule

Allow `essai-deux` to run `docker` through `sudo`, and read a file reserved for
root:

```bash
echo 'essai-deux ALL=(root) NOPASSWD: /usr/bin/docker' | sudo tee /etc/sudoers.d/essai > /dev/null
acces essai-deux
sudo -n -u essai-deux sudo -n docker run --rm -v /etc:/e:ro "$IMAGE" head -c 5 /e/shadow; echo
sudo -l -U essai-deux | tail -1
sudo rm /etc/sudoers.d/essai
```

```text
essai-deux : refuse
root:
    (root) NOPASSWD: /usr/bin/docker
```

The account is refused on the socket, and yet it reads `/etc/shadow`. A `sudo`
rule on `docker` is worth the group. `sudo -l -U` shows them: add this reading
to any access removal.

## 🔌 Exercise 4: a socket that changed group

Give the socket to another group, of which the account is a member:

```bash
sudo chgrp essai-equipe /run/docker.sock
sudo usermod -aG essai-equipe essai-deux
id -nG essai-deux
acces essai-deux
stat -c '%G %a' /run/docker.sock
sudo chgrp docker /run/docker.sock
acces essai-deux
```

```text
essai-deux essai-equipe
essai-deux : acces
essai-equipe 660
essai-deux : refuse
```

No mention of `docker` in the account's groups, and the access is there. The
group's name does not matter, the one the socket carries does. Look at the
socket before the accounts.

## 🌍 Exercise 5: a permission open to all

Open the socket to everyone, as many online answers suggest:

```bash
sudo chmod 666 /run/docker.sock
acces essai-un; acces essai-deux
systemctl cat docker.socket | grep -E 'Socket(Mode|Group)'
sudo chmod 660 /run/docker.sock
acces essai-deux
sudo -n -u essai-deux curl -s --unix-socket /run/docker.sock http://localhost/_ping; echo "code: $?"
```

```text
essai-un : acces
essai-deux : acces
SocketMode=0660
SocketGroup=docker
essai-deux : refuse
code: 7
```

Every account of the machine had the equivalent of root, including those of
services. The lasting setting is in the `docker.socket` systemd unit: that is
where to check that nobody wrote 0666. The last try checks the refusal without
going through `docker`.

## 🧹 Cleanup

```bash
cd ~
sudo userdel -r essai-un 2> /dev/null; sudo userdel -r essai-deux 2> /dev/null; sudo groupdel essai-equipe
stat -c '%G %a' /run/docker.sock
rm -rf ~/essai-acces-groupe
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
docker 660
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-groupe-docker
dsoxlab check securite-groupe-docker
```

```text
╭─ Result: securite-groupe-docker ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests  │
╰───────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: an account to keep, and a privilege to remove
for good.

```bash
dsoxlab run securite-groupe-docker
dsoxlab challenge securite-groupe-docker
```
