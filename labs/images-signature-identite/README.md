# Verify a container archive signature and its approved signer identity

The lesson signs an archive with a local authority and verifies in two steps.
This course shows the checks that wrongly accept: an expired certificate, a
tool that returns 0, an identity compared too quickly, a key under two names,
and a file changed after the check.

You work in `~/essai-signature`, with your own authority. The challenge uses
`/opt/lab-image-signature`: use neither its keys nor its certificates during
the course.

Related page: [Check what an image contains, and who signed it](https://www.stephane-robert.info/en/docs/docker/verify-an-image-and-its-signature/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-signature-identite
```

You are connected to `docker.lab`, where the engine runs. `certifie` creates a
certificate signed by the authority: name, identity, key file, duration in
days. **Keep the same terminal until the cleanup**: the variables only exist in
it.

```bash
mkdir -p ~/essai-signature && cd ~/essai-signature
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 30 -subj /CN=essai-ca 2> /dev/null
certifie() {
  [ -e "$3" ] || openssl genrsa -out "$3" 2048 2> /dev/null
  openssl req -new -key "$3" -subj "/CN=$1" -out "$1.csr"
  printf 'subjectAltName=%s\n' "$2" > "$1.ext"
  openssl x509 -req -in "$1.csr" -CA ca.crt -CAkey ca.key -days "$4" -extfile "$1.ext" -out "$1.crt" 2> /dev/null
}
certifie equipe URI:spiffe://essai/equipe equipe.key 10
docker save "$IMAGE" -o archive.tar
openssl dgst -sha256 -sign equipe.key -out archive.sig archive.tar
openssl x509 -in equipe.crt -pubkey -noout > equipe.pub
openssl dgst -sha256 -verify equipe.pub -signature archive.sig archive.tar
```

```text
29.9.2
Verified OK
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## ⏳ Exercise 1: an expired certificate

Verify a one-day certificate at today's date, then at a later date:

```bash
certifie courte URI:spiffe://essai/equipe courte.key 1
openssl verify -CAfile ca.crt courte.crt
openssl verify -CAfile ca.crt -attime "$(date -d '+3 days' +%s)" courte.crt 2>&1 | grep -o 'certificate has expired'
openssl dgst -sha256 -sign courte.key -out courte.sig archive.tar
openssl x509 -in courte.crt -pubkey -noout > courte.pub
openssl dgst -sha256 -verify courte.pub -signature courte.sig archive.tar
```

```text
courte.crt: OK
certificate has expired
Verified OK
```

`dgst -verify` only knows the key: it will always say the signature is good,
even expired. The date is checked with the certificate, by `openssl verify`.
`-attime` allows trying a date, hence planning.

## 🎭 Exercise 2: a tool that returns 0

Ask for the identity of a certificate that has none, and read the exit code:

```bash
openssl x509 -in ca.crt -noout -ext subjectAltName 2> /dev/null; echo "code: $?"
openssl x509 -in equipe.crt -noout -ext subjectAltName; echo "code: $?"
echo abime > faux.sig
openssl dgst -sha256 -verify equipe.pub -signature faux.sig archive.tar 2> /dev/null; echo "code: $?"
openssl verify -CAfile ca.crt absent.crt > /dev/null 2>&1; echo "code: $?"
```

```text
code: 0
X509v3 Subject Alternative Name:
    URI:spiffe://essai/equipe
code: 0
Verification failure
code: 1
code: 2
```

The certificate without an identity returns 0, like the other: only the text
differs, and it is not on the expected output. A program that only reads the
code would accept an empty identity. Require a value, then compare it.

## 🔍 Exercise 3: an identity compared too quickly

Create an identity that starts like the right one, a second one that hides
another, and look for the right one:

```bash
certifie voisine URI:spiffe://essai/equipe-invitee voisine.key 10
certifie double URI:spiffe://essai/autre,URI:spiffe://essai/equipe double.key 10
for c in equipe voisine double; do
  openssl x509 -in $c.crt -noout -ext subjectAltName | grep -q 'spiffe://essai/equipe' && echo "$c : trouve par grep"
  echo "   identites : $(openssl x509 -in $c.crt -noout -ext subjectAltName | tail -n +2 | tr -d ' ')"
done
```

```text
equipe : trouve par grep
   identites : URI:spiffe://essai/equipe
voisine : trouve par grep
   identites : URI:spiffe://essai/equipe-invitee
double : trouve par grep
   identites : URI:spiffe://essai/autre,URI:spiffe://essai/equipe
```

The text search accepts all three. The first mistake comes from a common
beginning, the second from a certificate that carries several identities.
Decide the rule before writing the check: here, a single identity, and equal.

## 👯 Exercise 4: a key under two names

Have the same key certified under another identity, and verify the signature
with both certificates:

```bash
certifie invite URI:spiffe://essai/invite equipe.key 10
openssl x509 -in invite.crt -pubkey -noout > invite.pub
openssl dgst -sha256 -verify invite.pub -signature archive.sig archive.tar
cmp equipe.pub invite.pub && echo 'meme cle'
for c in equipe invite; do openssl x509 -in $c.crt -noout -fingerprint -sha256 | cut -c1-40; done | sort -u | wc -l
```

```text
Verified OK
meme cle
2
```

The signature is good with both: it binds a key, not a name. The presented
certificate gives the name. It must therefore be checked every time, and never
extracted from a file supplied by the author without tying it to the authority.

## ⏱️ Exercise 5: a file changed after the check

Verify the archive, change it, and load it anyway; then add just one byte to
it:

```bash
cp archive.tar recue.tar
controle() { openssl dgst -sha256 -verify equipe.pub -signature archive.sig "$1" 2> /dev/null; }
controle recue.tar && docker pull -q busybox:1.36.1 > /dev/null && docker save busybox:1.36.1 -o recue.tar && docker load -q -i recue.tar
cp archive.tar recue.tar && printf x >> recue.tar
docker load -q -i recue.tar | cut -c1-40
controle recue.tar
docker rmi busybox:1.36.1 > /dev/null
```

```text
Verified OK
Loaded image: busybox:1.36.1
Loaded image ID: sha256:be2656061b536c18
Verification failure
```

The first load has nothing to do with what was verified. First copy the archive
where nobody else writes, then check and load that copy. The added byte does
not bother `docker load`, but the signature sees it.

## 🧹 Cleanup

```bash
cd ~
rm -rf ~/essai-signature
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset images-signature-identite
dsoxlab check images-signature-identite
```

```text
╭─ Result: images-signature-identite ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests    │
╰─────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a gate to write, which opens only to the
right signer.

```bash
dsoxlab run images-signature-identite
dsoxlab challenge images-signature-identite
```
