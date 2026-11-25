# Gate an image using dated, real offline vulnerability scans

The lesson reads a report and writes a gate on a CVE. This course tackles the
evidence itself: an erased inventory, a name that moved, badly compared
versions, a refusal lost on the way, and a report that is too old.

You work in `~/essai-preuve`, with a small script that reads an image's Alpine
inventory without running it. The challenge uses `/opt/lab-image-scan`: do not
touch it during the course.

Related page: [Check what an image contains, and who signed it](https://www.stephane-robert.info/en/docs/docker/verify-an-image-and-its-signature/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run image-scan-de-vulnerabilites
```

You are connected to `docker.lab`, where the engine runs. `inventaire.py`
displays an image's packages; it returns 1 if the forbidden package is in it.
**Keep the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-preuve && cd ~/essai-preuve
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cat > inventaire.py <<'EOF'
import io, json, subprocess, sys, tarfile, datetime
image, interdit, rapport = sys.argv[1:4]
lance = lambda *a: subprocess.run(["docker", *a], check=True, capture_output=True).stdout
c = lance("create", image).decode().strip()
try:
    t = tarfile.open(fileobj=io.BytesIO(lance("export", c)))
    try:
        texte = t.extractfile("lib/apk/db/installed").read().decode()
    except KeyError:
        texte = ""
finally:
    lance("rm", c)
noms = sorted(l[2:] for l in texte.splitlines() if l.startswith("P:"))
json.dump({"image": image, "id": lance("image", "inspect", "-f", "{{.Id}}", image).decode().strip(),
           "date": datetime.datetime.now().isoformat(), "paquets": noms}, open(rapport, "w"))
print(len(noms), "paquets,", "refuse" if interdit in noms else "accepte")
sys.exit(interdit in noms)
EOF
python3 inventaire.py "$IMAGE" zlib r.json; echo "code: $?"
```

```text
29.9.2
16 paquets, refuse
code: 1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🕳️ Exercise 1: an erased inventory

Remove an image's inventory, without removing the library, and run the check
again:

```bash
printf 'ARG IMAGE\nFROM $IMAGE\nRUN rm /lib/apk/db/installed\n' > Dockerfile
docker build -q --build-arg IMAGE="$IMAGE" -t essai-sans . > /dev/null
python3 inventaire.py essai-sans zlib r.json; echo "code: $?"
docker run --rm essai-sans sh -c 'ls /usr/lib /lib | grep -c libz'
```

```text
0 paquets, accepte
code: 0
2
```

Zero packages, hence accepted, although the library is still there. A check
that found nothing to read must refuse, not accept. This is not a textbook
case: files copied without a package are not seen either.

## 🏷️ Exercise 2: a name that moved

Check a tag, move it to another image, and read the report again:

```bash
docker tag essai-sans essai-candidate
python3 inventaire.py essai-candidate zlib r.json
docker tag "$IMAGE" essai-candidate
python3 -c 'import json; print("rapport sur", json.load(open("r.json"))["image"])'
[ "$(python3 -c 'import json; print(json.load(open("r.json"))["id"])')" = "$(docker image inspect essai-candidate --format '{{.Id}}')" ] && echo 'meme image' || echo 'autre image'
```

```text
0 paquets, accepte
rapport sur essai-candidate
autre image
```

The report mentions the right tag, and it is about another image. Compare the
image identifier at decision time, not its name.

## 🔢 Exercise 3: badly compared versions

Compare three pairs of versions, as text then with Debian's tool:

```bash
compare() {
  [ "$(printf '%s\n%s\n' "$1" "$2" | LC_ALL=C sort | head -1)" = "$1" ] && T='plus ancienne' || T='plus recente'
  dpkg --compare-versions "$1" lt "$2" && O='plus ancienne' || O='plus recente'
  echo "$1 face a $2 : texte $T, dpkg $O"
}
compare 3.0.9-1 3.0.17-1
compare 1.1.1n-0+deb11u5 1.1.1w-0+deb11u1
compare 3.0.17-1~deb12u2 3.0.17-1
compare 1:1.0-1 2.0-1
```

```text
3.0.9-1 face a 3.0.17-1 : texte plus recente, dpkg plus ancienne
1.1.1n-0+deb11u5 face a 1.1.1w-0+deb11u1 : texte plus ancienne, dpkg plus ancienne
3.0.17-1~deb12u2 face a 3.0.17-1 : texte plus recente, dpkg plus ancienne
1:1.0-1 face a 2.0-1 : texte plus ancienne, dpkg plus recente
```

The text is wrong as soon as a number takes one more digit, and on the `~`,
which places a version **before** the one it extends. The epoch, before the
colon, comes first. A distribution also fixes without changing the upstream
version: never compare with the publisher's number alone.

## 🕳️ Exercise 4: a refusal lost on the way

Wrap the check in four ways, and read the returned code:

```bash
printf '#!/bin/sh\npython3 inventaire.py "$1" zlib r.json | tee journal\n' > a.sh
printf '#!/bin/sh\npython3 inventaire.py "$1" zlib r.json\necho fini\n' > b.sh
printf '#!/bin/sh\nif ! python3 inventaire.py "$1" zlib r.json; then echo alerte; fi\n' > c.sh
printf '#!/bin/bash\nset -o pipefail\npython3 inventaire.py "$1" zlib r.json | tee journal\n' > d.sh
chmod +x ?.sh
for s in a b c d; do ./$s.sh "$IMAGE" > /dev/null; echo "$s.sh : $?"; done
```

```text
a.sh : 0
b.sh : 0
c.sh : 0
d.sh : 1
```

Three wrappers out of four return 0 although the image is refused: a pipe, a
command that follows, an `if` without an exit. Test a gate with an image that
must be refused, not only with a good one.

## ⏰ Exercise 5: a report that is too old

Make a report three days older, then compare the file's date and the content's:

```bash
python3 inventaire.py "$IMAGE" absent r.json
python3 -c 'import json, datetime as d; r = json.load(open("r.json")); r["date"] = (d.datetime.now() - d.timedelta(days=3)).isoformat(); json.dump(r, open("r.json", "w"))'
find r.json -mmin -60 | grep -q . && echo 'fichier : recent'
python3 -c 'import json, datetime as d; a = d.datetime.now() - d.datetime.fromisoformat(json.load(open("r.json"))["date"]); print("contenu :", a.days, "jours")'
touch -d '3 days ago' r.json; find r.json -mmin -60 | grep -q . || echo 'fichier : ancien'
```

```text
16 paquets, accepte
fichier : recent
contenu : 3 jours
fichier : ancien
```

The file's date changes with any `touch` or copy, in either direction. The
content's date can also be edited by hand. Only a check run again at decision
time answers the question: what does the alert database say today?

## 🧹 Cleanup

```bash
cd ~
docker rmi -f essai-sans essai-candidate > /dev/null
rm -rf ~/essai-preuve
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset image-scan-de-vulnerabilites
dsoxlab check image-scan-de-vulnerabilites
```

```text
╭─ Result: image-scan-de-vulnerabilites ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests       │
╰────────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: faithful evidence, an image to promote, and a
gate that really refuses.

```bash
dsoxlab run image-scan-de-vulnerabilites
dsoxlab challenge image-scan-de-vulnerabilites
```
