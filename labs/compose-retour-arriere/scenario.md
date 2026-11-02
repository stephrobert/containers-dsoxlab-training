# Scenario

The team's reference service runs on `docker.lab`, deployed by Compose, pinned
by digest, with its data volume. It keeps records, and it already holds one:
production did not wait for you to arrive.

Three releases are available, and you are given their digests. `2.0` is a
routine evolution. `3.0`, however, **migrates the state's schema**, and that is
written in its release notes, on one line nobody reads.

The day before the rollout, your manager asks the only question that matters:
"if this goes wrong, can we roll back?"

You answer yes. That is true for `2.0`. It stops being true after `3.0`, and
nobody on the team can say from exactly which moment.

## Mission

Deploy `2.0` by its digest, write a record, roll back to `1.0` without losing
anything. Then deploy `3.0`, and **establish** that the rollback is no longer
possible, recording what the machine answers.

What is expected in detail, and the format of the record of findings, are in
`/opt/lab-retour/MISSION.md`.
