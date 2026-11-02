# epreuve-livrer-une-image

**Audience:** the learner.

An image is only delivered if another machine, which has nothing of yours, can
run it. This challenge makes you prove that, and checks at the same time that
the build secret survived nowhere.

## What you will be able to do

- Use a secret during a build without it entering a layer, and say why a build
  argument or an environment variable cannot do that.
- Publish to a private registry over verified TLS, with the account entitled to.
- Designate a delivery by its digest, and say what a tag does not guarantee.
- Run that delivery from a bare, read-only client.
- Check that a read-only account cannot publish, and know that pushing back an
  image already present does not check it.

## How it is graded

Four checks of equal weight, pass mark **75%**:

1. the delivery is published, and the recorded reference carries the digest the
   registry serves;
2. the recorded digest is that of this run's secret, and the secret is in
   neither the history nor any layer;
3. the container runs on the **bare client**, on the digest reference, and
   answers the digest;
4. the read-only account is refused an upload session by the registry.

Both hosts are queried separately: an image that only runs on the machine that
built it is not delivered.

## What the challenge does not do

It imposes neither the number of stages in your build, nor how you mount the
secret. The check reads the image produced and the state of both machines.
