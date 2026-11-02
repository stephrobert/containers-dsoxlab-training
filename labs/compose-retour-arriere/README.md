# compose-retour-arriere

**Audience:** the learner.

A rollback brings back the code, not the data, and a schema migration closes it
for good. This lab makes you measure both.

## What you will be able to do

- Deploy a release **by its digest** rather than by a tag, and say what that
  changes.
- Go back to the previous release without losing what was written in between.
- Recognise an irreversible migration, and establish from which moment the
  rollback stops being an option.
- Read the refusal of a release that cannot read the state, and draw the right
  conclusion: it protects the data instead of damaging it.

## How it is graded

Four checks of equal weight, all on the **final state**:

1. `3.0` is running, and it is designated by a digest, not by a tag;
2. the state is at schema 2, and the records are there in their migrated form;
3. **both** records survived, the one from before you arrived and yours;
4. the rollback to `2.0` is refused, which the check **measures itself**, and
   your record of findings names the three values the machine gives.

The path you took is not graded: only the state counts.

## What the lab does not do

It does not ask you to repair the situation. An irreversible migration cannot be
repaired afterwards: it is **known beforehand**, and that is why this lab
exists.
