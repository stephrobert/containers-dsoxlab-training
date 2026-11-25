# Serve a trusted registry and pull without disabling TLS checks

The lesson creates an authority, serves a registry over TLS and accepts it on
the Docker side. This course triggers the refusals one by one: an address that
is not the loopback, a certificate without a name, a key that is not the right
one, a badly filed file, and a date that is coming.

You work in `~/essai-tls`, on the `essai-reg` registry and port 15950. The
challenge uses `registry-tls.lab.test` and port 15443: do not touch it during
the course.

Related page: [Serve a trusted registry, and log in to it](https://www.stephane-robert.info/en/docs/docker/serve-a-trusted-registry/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run registry-locale-tls
```

You are connected to `docker.lab`, where the engine runs. `HOTE` is the
machine's address on its network. `certifie` signs a certificate, `sert` starts
the registry with it. **Keep the same terminal until the cleanup**: the
variables only exist in it.

```bash
mkdir -p ~/essai-tls && cd ~/essai-tls
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
export REG=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
HOTE=$(ip -4 route get 1.1.1.1 | awk '{for(i=1;i<NF;i++) if($i=="src") print $(i+1)}')
openssl req -x509 -newkey rsa:2048 -nodes -days 2 -keyout ac.key -out ac.crt -subj /CN=ac-essai 2> /dev/null
certifie() { openssl req -newkey rsa:2048 -nodes -keyout $1.key -out $1.csr -subj "/CN=$HOTE" 2> /dev/null; echo "$2" > $1.ext; openssl x509 -req -in $1.csr -CA ac.crt -CAkey ac.key -CAcreateserial -out $1.crt -extfile $1.ext -days 2 2> /dev/null; chmod 644 $1.key; }
sert() { docker rm -f -v essai-reg > /dev/null 2>&1; docker run -d --name essai-reg -p 15950:5000 -v "$PWD:/c:ro" -e REGISTRY_HTTP_TLS_CERTIFICATE=/c/$1 -e REGISTRY_HTTP_TLS_KEY=/c/$2 "$REG" > /dev/null; sleep 2; }
tire() { docker pull -q "$HOTE:15950/essai:1" 2>&1 | grep -oE 'x509.*|failed to load.*|server gave HTTP.*|: not found'; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔁 Exercise 1: the loopback is an exception

Serve a registry without TLS, then reach it through two addresses:

```bash
docker run -d --name essai-reg -p 15950:5000 "$REG" > /dev/null; sleep 2
docker tag "$IMAGE" 127.0.0.1:15950/essai:1
docker push -q 127.0.0.1:15950/essai:1 2> /dev/null | head -1
tire
docker rmi 127.0.0.1:15950/essai:1 > /dev/null
```

```text
127.0.0.1:15950/essai:1
server gave HTTP response to HTTPS client
```

Docker accepts plain HTTP on the loopback and nowhere else. A successful try on
`127.0.0.1` therefore says nothing about what will happen from another machine.

## 🪪 Exercise 2: a certificate without the right name

Trust the authority, then serve three certificates it signed:

```bash
DOSSIER="/etc/docker/certs.d/$HOTE:15950"
sudo mkdir -p "$DOSSIER" && sudo cp ac.crt "$DOSSIER/"
certifie sans ''
certifie autre 'subjectAltName=DNS:autre.test'
certifie bon "subjectAltName=IP:$HOTE"
for c in sans autre bon; do sert $c.crt $c.key; echo "$c $(tire | sed "s/$HOTE/ADRESSE/")"; done
```

```text
sans x509: certificate relies on legacy Common Name field, use SANs instead
autre x509: cannot validate certificate for ADRESSE because it doesn't contain any IP SANs
bon : not found
```

The authority is known in all three cases. Docker requires the name or the
address to be in `subjectAltName`: the `CN` field, even right, does not count.
The last message, `not found`, is good news: the connection is established, and
the image does not exist.

## 🔑 Exercise 3: a key that is not the right one

Serve the right certificate with another one's key:

```bash
sert bon.crt autre.key
docker ps -a --filter name=essai-reg --format '{{.Status}}' | cut -d' ' -f1,2
docker logs essai-reg 2>&1 | grep -o 'tls: private key[^"]*' | head -1
[ "$(openssl x509 -in bon.crt -noout -pubkey | sha256sum)" = "$(openssl pkey -in bon.key -pubout | sha256sum)" ] && echo 'bon.key : la paire correspond'
```

```text
Exited (1)
tls: private key does not match public key
bon.key : la paire correspond
```

The registry refuses to start, and its log says why. A certificate and its key
carry the same public key: compare their fingerprints before restarting a
service.

## 🗂️ Exercise 4: a badly filed file

Move the authority inside the trust directory, and pull each time:

```bash
sert bon.crt bon.key
sudo mv "$DOSSIER/ac.crt" "$DOSSIER/ac.pem"; tire
sudo mv "$DOSSIER/ac.pem" "$DOSSIER/ac.cert"; tire
sudo mkdir "/etc/docker/certs.d/$HOTE" && sudo mv "$DOSSIER/ac.cert" "/etc/docker/certs.d/$HOTE/ac.crt"; tire
sudo mv "/etc/docker/certs.d/$HOTE/ac.crt" "$DOSSIER/"; tire
curl -sS --noproxy '*' "http://$HOTE:15950/v2/"; echo "code: $?"
```

```text
x509: certificate signed by unknown authority
failed to load X509 key pair: tls: found a certificate rather than a key in the PEM for the private key
x509: certificate signed by unknown authority
: not found
Client sent an HTTP request to an HTTPS server.
code: 0
```

The `.crt` extension designates an authority, `.cert` a client certificate that
expects its key, and `.pem` is ignored. The port is part of the directory's
name. No restart is needed: Docker reads this directory again at each
connection. Note that `curl` in HTTP returns 0 on a TLS service: the text is
what you must read.

## 📅 Exercise 5: a date that is coming

Ask whether the certificate will still be valid in one hour, then in one month:

```bash
openssl x509 -in bon.crt -checkend 3600; echo "code: $?"
openssl x509 -in bon.crt -checkend 2592000; echo "code: $?"
openssl s_client -connect "$HOTE:15950" -CAfile ac.crt < /dev/null 2> /dev/null | openssl x509 -noout -checkend 3600
```

```text
Certificate will not expire
code: 0
Certificate will expire
code: 1
Certificate will not expire
```

`-checkend` returns 1 when the date will have passed within the given delay: it
can be used as is in a monitoring check. The last form queries the running
service, not the file: it is the one that sees a certificate that was renewed
but not served yet.

## 🧹 Cleanup

```bash
cd ~
docker rm -f -v essai-reg > /dev/null
sudo rm -r "/etc/docker/certs.d/$HOTE:15950" "/etc/docker/certs.d/$HOTE"
rm -rf ~/essai-tls
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset registry-locale-tls
dsoxlab check registry-locale-tls
```

```text
╭─── Result: registry-locale-tls ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a registry that answers, and an engine that
is right to be wary.

```bash
dsoxlab run registry-locale-tls
dsoxlab challenge registry-locale-tls
```
