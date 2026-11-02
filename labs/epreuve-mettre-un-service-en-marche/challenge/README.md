# Test: bring a service into service

This host was "set up" by someone who has left. The engine is there, nothing
runs, and two stopped containers are lying around, from the same image.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The engine runs, it is enabled, and the account talks to it

**Three facts, and one single move does not settle them.** "Started" and
"enabled" are distinct: only the second survives the next reboot. And talking to
the engine is not the same thing as starting it.

### 2. The service runs and serves the requested value

A container named `annuaire`, running, from `lab-mise-en-marche:1.0`, whose
**answer** carries the value the machine gives. The value is read in the
service's answer, **not in its environment**: a variable set on a container that
does not use it proves nothing.

### 3. The old container with the same name is gone

Exactly one container carries that name, and it is the one that runs.

### 4. The witness is kept, stopped, and its logs readable

**This is the critical requirement: no total makes up for it.**
`journal-de-bord` must stay present, **stopped**, and its logs must still be
readable. The brief asks for it "as it is": restarting it is not harmless,
because a container that runs again can overwrite what it carried.

### 5. The prediction states the effective program and arguments

Two lines in `/opt/lab-mise-en-marche/prediction.txt`, **written without running
the command**. The check does not compare against frozen values: it recreates the
container described, without starting it, reads what the engine kept, then
removes it. Your prediction is therefore measured against the engine itself.

## What is provided

The `lab-mise-en-marche:1.0` image carries the service. Nothing to build. It
reads the `SALLE` environment variable, and its entry point takes a mode
argument.

No volume and no published port: that is not the subject.

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
