# What is asked

On `docker.lab`, a disposable Debian 13. In `/opt/lab-retour`, a Compose stack
is **already running**: one service pinned by digest, one data volume, and one
record that production wrote before you arrived.

Three releases of the same service are given to you by their digest, in
`/opt/lab-retour/releases.json`. They differ only in what they can read:

| release | schema read | what it does |
| --- | --- | --- |
| `1.0` | 1 | the one running |
| `2.0` | 1 | a compatible evolution |
| `3.0` | 2 | it **migrates** the schema |

The service listens on `127.0.0.1:18080`. `GET /etat` returns the release, the
schema and the records; `POST /ecrire` with a value in the body appends one.

**The stack runs in the Compose project `dsoxlab-retour`**, and its
`compose.yaml` does not declare it. Every Compose command must therefore name
it, or you create a second one, named after your directory: it will get a
**brand-new, empty** volume, the service will start from a blank state, and the
witness record will be gone. Nothing will tell you.

## 1. Deploy 2.0, by its digest

Move the stack to `2.0`, **by digest** and not by a tag. A tag does not say what
is running, a digest does.

The data volume does not change: the earlier record must still be there after
the switch.

## 2. Write under 2.0, then roll back to 1.0 without losing anything

Add a record while `2.0` is running, then **roll back to 1.0**.

Both records, the one from before you arrived and yours, must survive the move
out and the move back. That is the whole point of a rollback: it brings back the
code, not the data.

## 3. Deploy 3.0, and measure what it costs

Move the stack to `3.0`. It **migrates** the state to schema 2, and says so in
its log.

Both records must still be there, in their migrated form.

## 4. Establish that the rollback is no longer possible

Try to go back to `2.0`. It **refuses**, and that is the right behaviour: a
release must not damage state it does not understand.

Record what you measured in `/opt/lab-retour/constat.txt`, one line per entry,
with no space around the equals sign:

```text
release_qui_refuse=<the release that stops>
schema_illisible=<the schema number it cannot read>
code_de_sortie=<the code its process returns>
```

All three values are read on the machine. None can be guessed, and the refusal
message names **two** of them, the release and the schema. The **exit code** is
not in the message and has no business being there: a process does not announce
its own code, it returns it. You ask the shell for it.

## The expected final state

`3.0` is running, the state is at schema 2, both records are there, and the
record of findings is filled in. That state is what is graded, not the path you
took.

## What is not graded

The commands you typed, nor the order in which you tried them. A rollback can be
done in several ways, and `2.0`'s refusal can be observed in several ways too.
