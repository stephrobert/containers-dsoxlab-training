# Scenario

A customer calls: the service no longer answers. You open the console of the
host that carried it, and what you see looks like nothing you expected.

The decision is made before you have finished looking: that host is no longer
trusted, the service comes back up elsewhere. You have the other machine, the
stack's file, the image, and a backup taken before the fault.

You also have one instruction nobody will repeat: the database was reachable
only through the API, and it must stay that way. That is what the security file
states, and that is what will be read back if the incident escalates.

## Mission

Establish the real state, bring the service back up on the other host, restore
the witness record, and do not lose the data network's isolation along the way.

This is a **challenge**: the pass mark is 75%. What is expected in detail is in
`/opt/lab-restauration/MISSION.md`, on the host the service has to come back up
on.

**One requirement is made up for by no total: the witness record must be restored AND served through the front end.** Present but not served does not count: data that cannot be handed back is not restored, it is merely there.
