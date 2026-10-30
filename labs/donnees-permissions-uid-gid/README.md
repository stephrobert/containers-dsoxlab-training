# donnees-permissions-uid-gid: rights that hold

## What this lab tests

That a mounted volume belongs to root, that a non-root container therefore
cannot write to it, and that the answer is **neither** switching the container
to root **nor** opening the volume to everyone. It is the group you align.

Both bad answers are the lab's starting state, and that is not a caricature:
they are the ones found in production, in that order, six months apart.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| State | volume owner | uid 1000 writes | uid 1001 writes |
| --- | --- | --- | --- |
| fresh volume | `0:0`, mode `755` | no | no |
| after `chown root:2000` and `chmod 2775` | `0:2000`, mode `2775` | yes | yes |

And the detail that makes the difference between a solution that holds and one
that works once: with the **setgid bit**, created files carry group `2000`.
Without it, each would carry its author's primary group, and the neighbour could
not take it over.

## Why two containers, and not one

Because with only one, `chown 1000` would be enough, and the lab would teach the
wrong lesson. Two containers with **different uids** make the question
interesting: no owner suits both, and only a shared group answers it.

That is the real situation as soon as an application and its backup tool share
data, and it is what justifies the technique.

## The fourth check rules out the false solution

`chmod 777` would make the first three checks pass: both containers would write,
and the files would indeed be theirs.

So it explicitly refuses a volume open for writing to **others**, because that
is the answer found everywhere and it gives any process of the container the
right to rewrite everything. The shared group is enough, and it **names** who
may write.

Both halves of that check are inseparable: the other uid must write, and the
volume must not be open to everyone. Separated, each would be satisfied by a
solution the other refuses.

## Identity is read inside the container, not from what was asked

The checks read `id -u` and `id -g` **inside** the container, not
`.Config.User`.

A `--user` can designate an account the image does not know: the container
starts, but the account has no name and no home, and the messages become
incomprehensible. It is the processes' real identity that decides the rights, not
what was written at creation.

## The checks write in order to measure

Reading permissions is not enough: the ability to write is the subject, and a
permission is declared without always producing the expected effect.

So each check makes the container write, reads the resulting file's owner, then
**removes the file**. A check leaving its trace in the volume would pollute the
replay, which the validation cycle runs three times.

## Why the image carries both accounts

A `--user 1001:2000` works on an image that does not know that account, but the
shell then has no name and no home. So the image declares `redacteur` and
`verificateur`, both in `equipe`: that is what makes the error messages readable
and the lab teachable.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move |
| --- | --- | --- |
| `rapport` | runs as **root** | recreate it under its account |
| `verificateur` | non-root, writes nothing | nothing: it is the witness |
| the volume | `0:0`, mode `755` | give it to the group, with setgid |

A setup task **verifies** that state before handing over: `rapport` is indeed
root, the volume does belong to root, and `verificateur` cannot write anything
there.

## What the cleanup must remove

The **volume**. Its permissions are what the lab has corrected: if it survived
corrected, three checks out of four would be true on the next pass before any
work. A recreated volume starts again from `0:0` and `755`, measured, and that
is the lab's starting state.

## What the lab does not require

A path. The volume's rights can be changed through a throwaway container as well
as from the host, and the container can be recreated on the command line as well
as through the API. Only the state counts, and it is measured by writing.
