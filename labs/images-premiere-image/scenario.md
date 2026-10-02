# An API that cannot travel

## The situation

Your team ships a small inventory API, two FastAPI routes, that other teams are
starting to ask for. It runs perfectly on the machine of the person who wrote
it, and nowhere else.

The last deployment showed it. The staging server did not have the right
version of Python, then `uvicorn` was missing, then `pip install` went through
an internal mirror that had never heard of FastAPI. Three hours, and the API
finally answered.

`challenge/work` holds the application as it ships today: `app/main.py`, and
`app/requirements.txt` naming its two dependencies. There is no Dockerfile.

## The objective

Make this application travel: an image that carries it, with its interpreter
and its dependencies, so that it answers wherever you put it.

It must start from `debian:12`, because the whole series builds on that image
to show, measurement after measurement, what each optimisation removes. It must
declare the port it serves, and start without being told to.

The requirement that matters is the last one, and it cannot be worked around:
the application must answer **even with no network**. An image that installs
its dependencies at startup works on your machine and fails in the factory, the
train, or the data centre whose outbound Internet is closed.

## Landmarks

- The lesson says where Docker looks for instructions, and what a Dockerfile is
  made of: a base image, commands, copied files, a declared port, a start
  command.
- `debian:12` does not contain Python. That is the first thing to find out, and
  it explains half of the Dockerfile.
- Inside a container, `127.0.0.1` only means the container. An application
  listening on its loopback alone is unreachable from the host, even with `-p`.
- Debian 12 protects its system Python: `pip` refuses to install a package
  there without permission. The lesson says how, and why that is acceptable in
  a container dedicated to a single application.

## Verify

```bash
dsoxlab check images-premiere-image
```

Seven checks. Six read the built image and what the application answers. The
seventh runs it with no network at all and requires it to answer anyway.
