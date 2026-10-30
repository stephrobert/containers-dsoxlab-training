# container-entrypoint-et-cmd: which one do your arguments replace?

## What this lab tests

The difference between `ENTRYPOINT` and `CMD`, which cannot be seen in the
image but in what happens when arguments are passed to `docker run`. Two rules
explain everything, and the lab has the learner **meet their four
consequences** instead of stating them.

## Why the logs, and not the image inspection

One could read `.Config.Entrypoint` in an image inspection. That would grade
what the image **declares**, which is what the setup wrote itself: the learner
would be checking the lab's work, not their own.

What is learned here is what **executes**, and the only place it can be read is
the main process's output. Hence four containers that must **remain**, and a
brief that says so, because a `--rm` erases the evidence.

## Each check also verifies an absence

That is what makes it discriminating, and two of the four depend on it
entirely:

| Container | Expected presence | Required absence |
| --- | --- | --- |
| `defaut` | `defaut-de-limage` | *none* |
| `remplace` | `remplacement-total` | `defaut-de-limage` |
| `complete` | the prefix **and** `complement-cmd` | *none* |
| `contourne` | `sans-prefixe` | the prefix |

Without the "and not this" part, a container showing the default **and** the
requested text would pass check 2 although it replaced nothing. The refusal
message names that mistake, because it is the symptom of a misunderstood rule
and not of a typo.

## The starting state is broken, and that is the repo's rule

The setup lays out the two images and **no container**. All four checks are
therefore false at the start, and a task verifies it before handing over: both
images present, none of the four names taken. A setup that laid out a container
would make the demonstration in the learner's place.

## Why images built here rather than pulled

The two behaviours being compared depend on two lines of a Dockerfile. No public
image carries them in the exact form this lab needs, and pulling two would make
the demonstration opaque: the learner must be able to **read** both
declarations, which sit next to them in `/opt/lab-entrypoint`.

Both `FROM` lines carry the `dsoxlab:tag-nu-volontaire` marker. They do take the
digest: the marker is there because the pinning detector reads the generated
Dockerfile without knowing that the Ansible variable it sees **is** a digest.

## What the lab does not require

A form. Two of the four results are reached as well in exec form as in shell
form, and both count: the lab grades a behaviour, not a writing style.
