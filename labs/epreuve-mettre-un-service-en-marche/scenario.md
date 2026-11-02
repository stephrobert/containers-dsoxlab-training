# Nothing runs on this host

This host was "set up" by someone who has left. The container engine is there,
the package is installed, and yet nothing runs. The first command you type will
not answer the way you expect.

Two containers are lying around on the machine, both stopped. They come from the
same image. **One is in the way, the other must be preserved**, and nothing
tells them apart at first glance.

## What is expected at the end

1. The engine is **running**, and it will still be **after the machine's next
   boot**.
2. Your account talks to the engine **without `sudo`**.
3. A container named **`annuaire`** is running, from the
   `lab-mise-en-marche:1.0` image, and **its answer carries** the configuration
   value the machine gives you, passed through the `SALLE` environment variable.
4. The **`journal-de-bord`** container is **kept as it is**: present,
   **stopped**, and its logs still readable. It carries the trace of an incident
   operations must be able to read again.
5. The `/opt/lab-mise-en-marche/prediction.txt` file states, **without running
   the command**, what the engine will keep as the program and as the arguments
   for:

   ```bash
   docker run --rm lab-mise-en-marche:1.0 --verbeux
   ```

   Two lines, in exactly this form:

   ```text
   path=<the effective program>
   args=<the effective arguments, separated by a space>
   ```

The full brief, with the configuration value to serve, is on the machine in
`/opt/lab-mise-en-marche/MISSION.md`.

## What you do not have to do

The `lab-mise-en-marche:1.0` image is provided and carries the service: there is
**nothing to build**. No volume and no published port: that is not this test's
subject.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No command is
imposed: two ways of reaching the same state get the same mark.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**if `journal-de-bord` is deleted, or restarted, the test fails**, even with
everything else in place. In real life, the container a too-broad `docker rm`
takes away is the one that carried the trace of the incident.

Four hints are available, and **they cost points**: `dsoxlab hint`.
