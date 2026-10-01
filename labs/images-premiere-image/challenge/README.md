# Challenge: make the inventory API travel

7 checks, 100 points, 30 minutes.

The project is in `challenge/work`. Everything happens in a `Dockerfile` you
create at its root. The tests read the built image and what the application
answers; they do not read your commands.

## The starting point

| File | What it holds |
| --- | --- |
| `app/main.py` | the API, two routes: `/health` and `/version`. **Do not modify** |
| `app/requirements.txt` | its two dependencies, pinned. **Do not modify** |

Nothing else. The Dockerfile is yours to write.

## What you must reach

1. **The image starts from `debian:12`**, in a single stage. Multi-stage is the
   subject of a later lab and would bring nothing here.
2. **The application answers**: `GET /health` returns `200` and
   `{"status": "ok"}` in a container started from your image.
3. **The port is declared** with `EXPOSE`, and it is the one the application
   serves.
4. **Python and the dependencies are in the image**: `python3 --version` and
   `import fastapi, uvicorn` work inside the container.
5. **The image is self-contained**: started with `--network none`, the
   application comes up and answers itself. And it still answers with the
   network.
6. **A working directory is declared** with `WORKDIR`.
7. **A start command is declared**, and it launches the application.

## Three traps, each with a reason

**`debian:12` has no Python.** That is the first thing to find out, and it
explains half of the Dockerfile. An image that forgets it fails at startup with
a message about `$PATH` rather than about Python.

**Inside a container, `127.0.0.1` only means the container.** An application
listening on its loopback alone is unreachable from the host, even with `-p`.
Check 2 will fail without the container log showing anything wrong: the
application is running, it is simply reachable by nobody.

**Debian 12 refuses to let `pip` install into its system Python.** The message
mentions `externally-managed-environment` and points at PEP 668. Two answers
exist, the companion lesson gives both, and one of them is legitimate in a
container dedicated to a single application.

## Check 5 is the one that matters

The other six pass with an image that installs its dependencies at startup.
The fifth runs it with no network at all and requires it to answer anyway.

This is not gratuitous strictness: it is the failure the scenario describes. An
image that downloads at startup works on your machine and fails everywhere
outbound Internet is closed, which is most production environments.

## Verify

```bash
dsoxlab check images-premiere-image
```

The first `check` builds the image, which takes about fifteen seconds. The
following ones reuse the build cache and take a few seconds.

Stuck? `dsoxlab hint images-premiere-image`.
