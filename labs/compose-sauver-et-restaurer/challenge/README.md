# Back up a Compose stack, and restore it elsewhere

The `herbier` stack runs and serves. You must back it up, bring it back in a
**fresh** project running beside it, and prove the data served is the same.

## The five checks

They carry equal weight, and each one rests on a verifiable fact.

### 1. The source still runs, and serves as before

This check does not measure your backup: it measures that the backup **cost
nothing**.

Stopping the database to copy it in peace, emptying it, moving its volume: all
of that "works" and leaves the conservatory without its herbarium for the
duration. It is the easiest fault to commit, because it makes the rest of the
work simpler.

Both its services must run, and its fingerprint must be **the one it started
with**: the source is read, never modified.

### 2. The database backup is logical, and reads back

A copy of the data directory taken while the engine writes **is not a backup**.
It looks complete, it holds an intermediate state, and it restores without an
error until the day it does not.

The check does not look at **how** the archive was made, it looks at what it
**is**: a logical backup reads back, and the check reads it back.

### 3. The plates and the configuration are archived

Two separate archives, and two separate reasons.

The files volume **does not live in the database**: no `pg_dump` carries it
along. And the configuration is what lets you **rebuild** the stack: without it
you hold data and nothing to serve it with.

### 4. The target is a project of its own, and it is up

Restoring over the source proves nothing: the data was already there.

The target is therefore a Compose project of its own, and the two **live side by
side**, which forces it to take its own published port. That is also the real
situation: you verify a backup **before** you have lost the original.

### 5. The target serves exactly the source's data

**This is the check this lab exists for.**

Two fingerprints, and each covers what the other cannot see.

The database one aggregates the table's **ordered** content: counting rows is
not enough, a table filled with wrong values has the right count. The plates one
is a `sha256sum` per file: a volume whose files were recreated by hand has the
right number of files, and not the right bytes.

Two values are drawn at random on every run, one in the database and one in a
plate. They exist nowhere but in the source: they can be neither guessed nor
reconstructed.

### 6. The target's web front does serve its plates

A correct volume and a service that does not mount it give you a target that
**holds** the plates without **serving** them.

Check 5 reads the volume; this one reads what a visitor gets. What is declared
and what is served are two facts, and only the second matters to whoever comes
to consult the herbarium.

## The scale

Five checks of equal weight, and **only the final state counts**. No check looks
at which commands you typed: the path is yours.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
