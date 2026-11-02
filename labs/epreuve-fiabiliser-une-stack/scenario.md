# The stack that only works on the second try

This stack has been running for months, and the team has picked up a habit: when
it does not answer, they restart it. It works. Nobody has looked into why.

It lives in `/opt/lab-stack-fiable/compose.yaml`, its project is named
`stack-fiable`, and it has two services. `coffre` holds a value derived from a
password. `api` queries it **as it starts**, then serves it on
`127.0.0.1:18420`.

Three other things were noted in passing, and none of them looks urgent: the
password can be read in the file, no service has a limit, and the source code
mount that was useful during development is still there.

## What is expected at the end

1. A `docker compose down` followed by a `docker compose up -d` yields a stack
   that **answers on the first try**, without any service having needed to
   restart.
2. The password appears **neither in the containers' environment** nor **in the
   image**, and the vault receives it all the same: the value served must stay
   correct.
3. Each service carries a **memory limit**, visible in the container's
   inspection as well as in its cgroup.
4. Each service carries a **restart policy**: a container that is killed comes
   back on its own.
5. There are **two variants**: `compose.yaml`, the deployment, which does **not**
   mount the source code, and `compose.dev.yaml`, the development one, which
   does. The second overlays the first.

The project keeps its name, and the API keeps its port. The
`lab-stack-fiable:1.0` image is provided: there is **nothing to rebuild**.

The service carries a **failure trigger**, which is a tool of the lab and not a
riddle: if the file `/tmp/panne-provoquee` exists inside a container, the service
exits with an error on the next request. That is how the restart-policy check
makes a service die, because a `docker kill` would not: the engine treats it as a
wanted stop, and no policy restarts a container you stopped yourself.

The full brief is also on the machine, in `/opt/lab-stack-fiable/MISSION.md`. It
states in particular that the service reads its password from a **file** before
looking at its environment, and that the path to that file is set by a variable.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No syntax is
imposed: two ways of obtaining the same behaviour get the same mark.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**the password readable in the environment fails the test**, even with
everything else in place. An environment variable is read by `docker inspect`,
by `docker compose config`, and by anyone who can talk to the daemon.

Beware the false fix: removing the password **without replacing it** gives a
clean, wrong stack. The check compares the value served with the one it expects.

Four hints are available, and **they cost points**: `dsoxlab hint`.
