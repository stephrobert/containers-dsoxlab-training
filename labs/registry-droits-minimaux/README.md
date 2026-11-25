# Grant minimal registry scopes to a publisher and a separate reader

A password says who you are. It does not say what you may do. With an
`htpasswd` file, every account has the same rights. To separate them, the
registry delegates the decision to a token service: the client logs in there,
asks for an action on a repository, and receives a signed token carrying what
it is granted. The registry checks the signature and applies. This course sets
up both services and reads what flows between them.

You work on `essai-registre` and `essai-auth`, over HTTP on the loopback:
enough to read the exchanges, not for a service reached by other machines. The
challenge uses `/opt/lab-registry-rights` and the
`dsoxlab-registry-droits-minimaux-*` containers: change nothing there during
the course. The course only copies their signing key, so as not to make another
one.

Related page: [Serve a trusted registry, and log in to it](https://www.stephane-robert.info/en/docs/docker/serve-a-trusted-registry/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run registry-droits-minimaux
```

You are connected to `docker.lab`, where the engine runs. `regles` writes the
token service's configuration with the rules you give it, and restarts it.
`jeton` asks for a token; `lire` shows the account, the lifetime in seconds and
what is granted. **Keep the same terminal until the cleanup**: the variables
only exist in it.

```bash
mkdir -p ~/essai-droits && cd ~/essai-droits
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
R=127.0.0.1:15547; T=http://127.0.0.1:15548/auth
mkdir conf cles
sudo cp /opt/lab-registry-rights/certs/server.crt /opt/lab-registry-rights/certs/server.key /opt/lab-registry-rights/certs/jwks.json cles/
sudo chown -R $(id -u) cles
for u in lea noe; do (umask 077; openssl rand -hex 12 > $u); done
pret() { for i in $(seq 20); do curl -s -o /dev/null $T && return; sleep 0.5; done; }
regles() { { printf 'server: {addr: ":5001"}\ntoken: {issuer: essai, expiration: 60, certificate: /cles/server.crt, key: /cles/server.key}\nusers:\n'; for u in lea noe; do printf '  %s: {password: "%s"}\n' $u "$(htpasswd -niB $u < $u | head -1 | cut -d: -f2)"; done; printf 'acl:\n'; cat; } > conf/auth.yml; docker restart -t 1 essai-auth > /dev/null 2>&1; pret; }
jeton() { printf 'user = "%s:%s"\n' $1 $(cat $1) | curl -sK - "$T?service=essai&scope=repository:$2:$3" | python3 -c 'import json, sys; print(json.load(sys.stdin)["token"])'; }
cat > lire.py <<'EOF'
import base64, json, sys
d = json.loads(base64.urlsafe_b64decode(sys.stdin.read().split(".")[1] + "=="))
print(d["sub"], d["exp"] - d["iat"], "s :", d["access"][0]["name"], d["access"][0]["actions"])
EOF
lire() { python3 lire.py; }
image() { printf 'FROM %s\nRUN echo %s > /v\n' "$IMAGE" $2 | docker build -q -t $R/atelier/outil:$1 - > /dev/null; }
docker run -d --name essai-auth -p 127.0.0.1:15548:5001 -v $PWD/conf:/conf:ro -v $PWD/cles:/cles:ro cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464 /conf/auth.yml > /dev/null
docker run -d --name essai-registre -p $R:5000 -v $PWD/cles:/cles:ro -e REGISTRY_AUTH=token -e REGISTRY_AUTH_TOKEN_REALM=$T -e REGISTRY_AUTH_TOKEN_SERVICE=essai -e REGISTRY_AUTH_TOKEN_ISSUER=essai -e REGISTRY_AUTH_TOKEN_ROOTCERTBUNDLE=/cles/server.crt -e REGISTRY_AUTH_TOKEN_JWKS=/cles/jwks.json registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3 > /dev/null
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🚪 Exercise 1: logged in, with no right at all

Give an empty rule, read what the registry answers without credentials, log in,
then push:

```bash
regles <<'EOF'
  - match: {account: lea, name: atelier/outil}
    actions: []
EOF
curl -si http://$R/v2/ | grep -iE '^HTTP|www-auth'
for u in lea noe; do docker --config $PWD/cfg-$u login $R -u $u --password-stdin < $u 2>&1 | grep -o 'Login Succeeded'; done
echo faux | docker --config $PWD/cfg-faux login $R -u lea --password-stdin 2>&1 | grep -o 'Auth failed'
image 1 un
docker --config $PWD/cfg-lea push -q $R/atelier/outil:1 2>&1 | grep -o 'insufficient_scope'
jeton lea atelier/outil pull,push | lire
```

```text
HTTP/1.1 401 Unauthorized
Www-Authenticate: Bearer realm="http://127.0.0.1:15548/auth",service="essai"
Login Succeeded
Login Succeeded
Auth failed
insufficient_scope
lea 60 s : atelier/outil []
```

The `401` names the service to talk to. The login succeeds, because the
password is right, and the push is refused: `insufficient_scope` means “known,
but not authorized”. The token shows it: an empty list of actions. `--config`
keeps the credentials in a separate folder, without touching yours.

## 🎫 Exercise 2: asked for, and granted

Give `lea` what is needed to publish and `noe` what is needed to read, then ask
for too much:

```bash
regles <<'EOF'
  - match: {account: lea, name: atelier/outil}
    actions: [pull, push]
  - match: {account: noe, name: atelier/outil}
    actions: [pull]
EOF
jeton lea atelier/outil pull,push | lire
jeton noe atelier/outil pull,push,delete | lire
jeton lea autre/outil pull,push | lire
docker --config $PWD/cfg-lea push -q $R/atelier/outil:1
```

```text
lea 60 s : atelier/outil ['pull', 'push']
noe 60 s : atelier/outil ['pull']
lea 60 s : autre/outil []
127.0.0.1:15547/atelier/outil:1
```

The service grants the part of the request that the rules allow, without an
error. So asking is not getting: read the token, not the request. A request no
rule covers gives an empty list. Publishing needs `pull` and `push`, because
the client first looks at what already exists.

## 👻 Exercise 3: a push that succeeds without writing anything

Have the reader push three times: the same image, new content, a new name:

```bash
ecrits() { docker logs essai-registre 2>&1 | grep -c '"PUT /v2/'; }
N=$(ecrits)
docker --config $PWD/cfg-noe push -q $R/atelier/outil:1; echo "identique : rc=$?, demandes d'ecriture : $(( $(ecrits) - N ))"
image 2 deux
docker --config $PWD/cfg-noe push -q $R/atelier/outil:2 2>&1 | grep -o 'insufficient_scope'
docker tag $R/atelier/outil:1 $R/atelier/outil:bis
docker --config $PWD/cfg-noe push -q $R/atelier/outil:bis 2>&1 | grep -o 'insufficient_scope'
[ "$(ecrits)" -gt "$N" ] && echo 'cette fois, une demande est partie'
```

```text
127.0.0.1:15547/atelier/outil:1
identique : rc=0, demandes d'ecriture : 0
insufficient_scope
insufficient_scope
cette fois, une demande est partie
```

The first push returns 0 and yet `noe` has no write right: everything was
already there, the client sent nothing. The registry's log confirms it, no
write request arrived. To test a refusal, always push content never seen
before.

## 🔀 Exercise 4: the order and reach of the rules

Put a broad rule before a precise one, then see what a wildcard covers:

```bash
regles <<'EOF'
  - match: {account: noe}
    actions: [pull]
  - match: {account: noe, name: atelier/outil}
    actions: [pull, push]
  - match: {account: lea, name: "atelier/*"}
    actions: [pull, push]
EOF
jeton noe atelier/outil pull,push | lire
jeton noe secret/plans pull | lire
for n in atelier/outil atelier/outil/v2 atelier; do jeton lea $n push | lire; done
```

```text
noe 60 s : atelier/outil ['pull']
noe 60 s : secret/plans ['pull']
lea 60 s : atelier/outil ['push']
lea 60 s : atelier/outil/v2 []
lea 60 s : atelier []
```

The first matching rule decides: the second is never read for `noe`, and the
missing repository opens `secret/plans` to it for reading. The wildcard stops
at `/`: `atelier/*` covers neither `atelier` nor `atelier/outil/v2`. Name the
account and the repository in each rule.

## 🧯 Exercise 5: one typo, and nothing comes out any more

Break the rules file, restart, and pull an image already published:

```bash
cp conf/auth.yml bon.yml
printf '  - match: {account: noe\n' >> conf/auth.yml
docker restart -t 1 essai-auth > /dev/null; sleep 2
docker ps -a --filter name=essai-auth --format '{{.State}}'
docker logs --tail 1 essai-auth 2>&1 | grep -o 'Failed to load config.*yaml: line [0-9]*'
docker --config $PWD/cfg-lea pull -q $R/atelier/outil:1 2>&1 | grep -o 'connection refused'
docker ps --filter name=essai-registre --format '{{.State}}'
cp bon.yml conf/auth.yml; docker start essai-auth > /dev/null; pret
docker --config $PWD/cfg-lea pull -q $R/atelier/outil:1
```

```text
exited
Failed to load config: could not parse config: yaml: line 13
connection refused
running
127.0.0.1:15547/atelier/outil:1
```

The registry is running and nobody can read any more: without the token
service, no request gets through. The client's message speaks of a refused
connection, not of rights. The service's log gives the faulty line. Keep a copy
of the file before changing it.

## ⏳ Exercise 6: a right withdrawn, a token still good

Take a read token, withdraw the right, then use the token at once and later:

```bash
J=$(jeton noe atelier/outil pull)
regles <<'EOF'
  - match: {account: noe, name: atelier/outil}
    actions: []
EOF
jeton noe atelier/outil pull | lire
avec() { printf 'header = "Authorization: Bearer %s"\n' "$J" | curl -sK - -o /dev/null -w '%{http_code}\n' -H 'Accept: application/vnd.oci.image.index.v1+json' http://$R/v2/atelier/outil/manifests/1; }
avec
sleep 75; avec
sleep 60; avec
```

```text
noe 60 s : atelier/outil []
200
200
401
```

The registry asks the service nothing again: it believes the token until it
expires. So the withdrawal has no immediate effect. The token announced 60
seconds and still went through after 75: the registry tolerates a clock drift,
one more minute according to our measurement. This is why these tokens are
short.

## 🧹 Cleanup

```bash
cd ~
docker rm -fv essai-auth essai-registre > /dev/null
docker images --format '{{.Repository}}:{{.Tag}}' | grep '15547' | xargs -r docker rmi -f > /dev/null
rm -rf ~/essai-droits
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c 'essai-\|15547'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset registry-droits-minimaux
dsoxlab check registry-droits-minimaux
```

```text
╭─ Result: registry-droits-minimaux ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests   │
╰────────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a publisher, a reader on another machine, and
rights to set without giving too many.

```bash
dsoxlab run registry-droits-minimaux
dsoxlab challenge registry-droits-minimaux
```
