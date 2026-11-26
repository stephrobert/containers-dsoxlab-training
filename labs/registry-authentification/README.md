# Protect a TLS registry with authentication

The lesson requires a password and connects the client. This course looks at
what fails or surprises: a hash the registry cannot read, an account added
without a restart, what the client keeps, an incomplete configuration, and a
missing file.

You work in `~/essai-acces`, on the `essai-auth` registry, over HTTP on the
loopback. The challenge uses `registry-auth.lab.test`: do not touch it during
the course.

Related page: [Serve a trusted registry, and log in to it](https://www.stephane-robert.info/en/docs/docker/serve-a-trusted-registry/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run registry-authentification
```

You are connected to `docker.lab`, where the engine runs. The `sert` function
starts a registry that reads a password file, `code` returns the HTTP status of
an account. **Keep the same terminal until the cleanup**: the variables only
exist in it.

```bash
mkdir -p ~/essai-acces && cd ~/essai-acces
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
export REG=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
mkdir auth
sert() { docker rm -f -v essai-auth > /dev/null 2>&1; docker run -d --name essai-auth -p 127.0.0.1:15951:5000 -v "$PWD/$1:/auth" -e REGISTRY_AUTH=htpasswd -e REGISTRY_AUTH_HTPASSWD_REALM=essai -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd "$REG" > /dev/null; sleep 2; }
code() { curl -s -o /dev/null -w '%{http_code}\n' ${1:+-u "$1"} http://127.0.0.1:15951/v2/; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔐 Exercise 1: a hash the registry cannot read

Create two accounts, one in MD5, the other in bcrypt, and try them:

```bash
htpasswd -nbm ana secret-ana | head -1 > auth/htpasswd
htpasswd -nbB bob secret-bob | head -1 >> auth/htpasswd
cut -c1-9 auth/htpasswd
sert auth
code ana:secret-ana
code bob:secret-bob
code
```

```text
ana:$apr1
bob:$2y$0
401
200
401
```

`ana`'s password is right, and it is refused: this registry only reads bcrypt,
whose lines start with `$2y$`. The refusal is the same as for a wrong password,
401. So look at the start of the line before blaming the user.

## ♻️ Exercise 2: an account added without a restart

Add an account and remove one, without touching the container:

```bash
htpasswd -nbB zoe secret-zoe | head -1 >> auth/htpasswd
code zoe:secret-zoe
sed -i '/^bob/d' auth/htpasswd
code bob:secret-bob
```

```text
200
401
```

The registry reads its file again when it changes. Removing a line closes the
access at once. This relies on mounting a directory: a file mounted alone and
replaced would not be seen again.

## 🗝️ Exercise 3: what the client keeps

Connect a client in a directory of its own, then read what it wrote:

```bash
echo secret-zoe | docker --config "$PWD/client" login -u zoe --password-stdin 127.0.0.1:15951 2> /dev/null
stat -c %a client/config.json
python3 -c "import json,base64; a=json.load(open('client/config.json'))['auths']; [print(k, base64.b64decode(v['auth']).decode()) for k, v in a.items()]"
docker tag "$IMAGE" 127.0.0.1:15951/essai:1
docker tag "$IMAGE" localhost:15951/essai:1
docker --config "$PWD/client" push -q 127.0.0.1:15951/essai:1 2> /dev/null | head -1
docker --config "$PWD/client" push -q localhost:15951/essai:1 2>&1 | grep -o 'no basic auth credentials'
docker --config "$PWD/client" logout 127.0.0.1:15951
docker rmi 127.0.0.1:15951/essai:1 localhost:15951/essai:1 > /dev/null
```

```text
Login Succeeded
600
127.0.0.1:15951 zoe:secret-zoe
127.0.0.1:15951/essai:1
no basic auth credentials
Removing login credentials for 127.0.0.1:15951
```

The password can be read by whoever reads the file: base64 is not encryption.
Credentials are filed under the registry's exact name, port included:
`localhost` and `127.0.0.1` are two different registries for the client.

## 🧩 Exercise 4: an incomplete configuration

Forget the `realm`, the title shown when the password is asked:

```bash
docker run -d --name essai-panne -v "$PWD/auth:/auth" -e REGISTRY_AUTH=htpasswd -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd "$REG" > /dev/null; sleep 2
docker ps -a --filter name=essai-panne --format '{{.Status}}' | cut -d' ' -f1,2
docker logs essai-panne 2>&1 | grep -o '"realm" must be set.*'
docker rm -f -v essai-panne > /dev/null
```

```text
Exited (2)
"realm" must be set for htpasswd access controller
```

The registry stops instead of serving without protection. After a configuration
change, check that the container runs before testing an access: a stopped
registry also refuses everyone.

## 👻 Exercise 5: a missing file

Give the registry an empty directory, and read its log:

```bash
mkdir vide
sert vide
docker logs essai-auth 2>&1 | grep -o 'htpasswd is missing, provisioning with default user'
docker logs essai-auth 2>&1 | grep -oE 'user=[a-z]+'
code
code "docker:$(docker logs essai-auth 2>&1 | grep -oE 'password=[^ ]+' | cut -d= -f2)"
```

```text
htpasswd is missing, provisioning with default user
user=docker
401
200
```

The file was missing, and the registry created one with a `docker` account,
whose password it writes **in its log**. Anyone who reads the logs therefore
has full access. A mistake in the mounted path is enough: look for this line at
each commissioning.

## 🧹 Cleanup

```bash
cd ~
docker rm -f -v essai-auth > /dev/null
sudo rm -rf ~/essai-acces/vide
rm -rf ~/essai-acces
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset registry-authentification
dsoxlab check registry-authentification
```

```text
╭─ Result: registry-authentification ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests    │
╰─────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: an encrypted registry open to all, to reserve
for one account.

```bash
dsoxlab run registry-authentification
dsoxlab challenge registry-authentification
```
