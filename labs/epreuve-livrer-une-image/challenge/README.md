# Scenario

Your team delivers an image to a partner. They do not have your repository, nor
your cache, nor the right to write to your registry: they have a machine, your
authority's trust, and a read-only account.

The last delivery went wrong in two ways at once. The image would not start on
their side, because it depended on a file that existed only on the build
machine. And an auditor found the build token in a layer, by reading the image's
history: there was nothing to decode, it was written there.

You are asked to redo the delivery, and to make it verifiable.

## Mission

Build the image without the build secret surviving in a layer, publish it,
record its digest reference, and run it on the bare client by that digest.

This is a **challenge**: the pass mark is 75%. What is expected in detail is in
`/opt/lab-livraison/MISSION.md`.

**One requirement is made up for by no total: a secret surviving in a layer fails the test.** An image is pulled, opened and read by whoever receives it; a secret travelling inside is already disclosed, even if nothing shows it in the final view.

## What is asked

Two machines. `docker.lab` builds and publishes: it carries the build context,
the secret, and the publishing account. `docker-client.lab` is a **bare**
client: it has the lab authority's trust and a **read-only** account, nothing
else.

A private registry over verified TLS listens on `livraison.lab.test:15401`,
repository `livraison/appli`. The credentials are in
`/opt/lab-livraison/identifiants-publication.json` on the publishing host, and
in `/opt/lab-livraison/identifiants-lecture.json` on the client.

This is a **challenge**: the pass mark is 75%.

### 1. Build the image without the secret surviving

The context is in `/opt/lab-livraison/build`. The `Dockerfile` is to be
completed.

The image must carry `/app/empreinte.txt` containing the **SHA-256 digest of
the file** `/opt/lab-livraison/build/jeton-de-build.txt`, byte for byte. That is
what `sha256sum` returns on that file.

The secret itself must survive in **no layer**. A secret mounted for the duration
of one instruction does not enter one; a secret copied, passed as a build
argument or set as an environment variable does, and can be read back from the
image's history.

### 2. Publish to the registry, with the account entitled to

Push the image as `livraison.lab.test:15401/livraison/appli:1.0`.

Then record in `/opt/lab-livraison/livraison.txt`, one line per entry, with no
space around the equals sign:

```text
reference_par_digest=<livraison.lab.test:15401/livraison/appli@sha256:...>
empreinte_du_secret=<the secret file's SHA-256 digest>
```

The reference is the one the registry serves, **by digest**: it is the only one
that designates an image and not a movable tag.

### 3. Run it on the bare client, by that digest

On `docker-client.lab`, pull the image **by the delivery's digest** with the
read-only account, and run it under the name `dsoxlab-livraison-client`.

It must answer the digest on its port 8080. That is what proves it is really
usable elsewhere, and not only on the machine that built it.

### 4. Establish that the client cannot publish

A read-only account must not be able to push. Check it, and know how to check
it: pushing back an image the registry already holds proves nothing, the client
then writes nothing at all.

This check is measured on the machine; you have nothing to record for it.

### The expected final state

The image is published, the delivery record is filled in, the container runs on
the bare client and answers the digest, and the secret is in no layer.

### What is not graded

The number of stages in your build, how you mount the secret, nor the commands
you typed. The check reads the image produced and the state of both machines.
