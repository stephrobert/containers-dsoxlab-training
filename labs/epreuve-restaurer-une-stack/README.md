# epreuve-restaurer-une-stack

**Audience:** the learner.

A restoration is not judged on "the service answers". It is judged on the data
recovered **and** on what was not lost along the way. This challenge measures
both.

## What you will be able to do

- Establish the real state of a stack that has gone down, without relying on
  what you are told about it.
- Bring three tiers back up on another host, and check that the business request
  really crosses them.
- Restore data and have it **served** through the business path, not merely put
  back on a disk.
- Keep a data network internal during a restoration, and prove the isolation by
  measurement rather than by reading the file.

## How it is graded

Four checks of equal weight, pass mark **75%**:

1. the three tiers run on the client, and the business request crosses `front`,
   `api` then `db`;
2. the witness record is served again, through the same path;
3. `db`'s network is internal and `db` publishes no port, read **on the
   engine**;
4. a probe placed on the public network does not reach `db`, and `api` does.

The fourth check looks both ways, and both are needed: without the second, a
stack whose `db` was simply stopped would pass the first.

## What the challenge does not do

It does not tell you what was destroyed. Establishing that is part of the work,
and it is what separates a restoration from a blind rebuild.
