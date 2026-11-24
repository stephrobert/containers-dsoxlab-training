# Limit a hand-made container

The lesson creates a cgroup, sets three caps in it (`memory.max`, `pids.max`,
`cpu.max`), then removes capabilities with `setpriv`. This course shows you
what it does not. First, where systemd has already put your own processes.
Then, how to move a process that is already running, and how to slow memory
down without killing. Then how to empty a group in one move. Finally, you will
read a capability mask without a decoding tool, and measure why the order
`unshare` then `setpriv` is not a detail.

You work with cgroups named `essai-*` and processes of the host, without a
container. The challenge uses another cgroup, other caps and a detached
container: you will do it on your own, at the end.

Related page: [Limit a container: cgroups v2 and capabilities](https://www.stephane-robert.info/docs/conteneurisation/limiter-un-conteneur/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run conteneur-limiter-a-la-main
```

You are now connected to `oci.lab`, a Debian 13 without any container engine.
You are the `ansible` user, and `sudo` gives you root rights. **Keep the same
terminal until the cleanup**: the variables of the exercises only exist in it.

```bash
setpriv --version
uname -r
cat /sys/fs/cgroup/cgroup.subtree_control
```

```text
setpriv from util-linux 2.41.5
6.12.118+deb13-amd64
cpu memory pids
```

The outputs of this course were captured on this machine on 24 November 2026,
with util-linux 2.41.5 and the 6.12 kernel of Debian 13.8. The last line lists
the controllers the root passes on to its children: `cpu`, `memory` and
`pids`, the three you will need.

## 🗂️ Exercise 1: where your shell lives

The lesson creates a cgroup at the root of the tree. But every process is
already in a cgroup, your shell included. See which one, then the branch that
systemd keeps for your user:

```bash
cat /proc/self/cgroup
systemd-cgls --no-pager -u user.slice | head -8
```

```text
0::/user.slice/user-1001.slice/session-448.scope
Unit user.slice (/user.slice):
└─user-1001.slice
  ├─session-333.scope
  │ ├─35673 sshd-session: ansible [priv]
  │ └─35681 sshd-session: ansible@notty
  ├─session-448.scope
  │ ├─47985 sshd-session: ansible [priv]
  │ ├─47993 sshd-session: ansible@notty
```

Your shell lives in `session-<n>.scope`, under `user-1001.slice` (1001 is the
uid of `ansible`), under `user.slice`. systemd created this branch when you
logged in over SSH: it puts each session, each service and each user in its
own cgroup. That is why the lesson reminds you that in production, you go
through systemd rather than writing by hand under `/sys/fs/cgroup`.

## 🚚 Exercise 2: move a process that is already running

In the lesson, the container is born in its cgroup. A process that is already
running can also join one: you only write its number into `cgroup.procs`.
Create a practice cgroup, start a `sleep`, and move it:

```bash
CG=/sys/fs/cgroup/essai-tardif
sudo mkdir "$CG"
P=$(sleep 600 > /dev/null 2>&1 & echo $!)
cat /proc/$P/cgroup
echo "$P" | sudo tee "$CG/cgroup.procs" > /dev/null
cat /proc/$P/cgroup
cat "$CG/pids.current"
```

```text
0::/user.slice/user-1001.slice/session-448.scope
0::/essai-tardif
1
```

The `sleep` moved from your session to the `essai-tardif` cgroup, without
being restarted, and `pids.current` counts it. This move only takes this
process: its children already running stay where they are. Only those it
starts afterwards are born in the new group. Hence the method of the lesson:
put the process in **before** it starts the container.

## 🐢 Exercise 3: slow memory down without killing

`memory.max` is a wall: past it, the kernel kills. `memory.high` is a brake:
past it, the kernel reclaims memory and slows the group down, without killing
anyone. Set a brake at 32M, without swap, and run the same `tail /dev/zero` as
the lesson, stopped after 5 seconds by `timeout`:

```bash
CF=/sys/fs/cgroup/essai-frein
sudo mkdir "$CF"
echo 32M | sudo tee "$CF/memory.high" > /dev/null
echo 0 | sudo tee "$CF/memory.swap.max" > /dev/null
sudo bash -c "echo \$\$ > $CF/cgroup.procs; exec timeout 5 tail /dev/zero"; echo "exit code: $?"
grep -E '^(high|max|oom|oom_kill) ' "$CF/memory.events"
cat "$CF/memory.peak"
```

```text
exit code: 124
high 380
max 0
oom 0
oom_kill 0
38686720
```

Code 124 is the one of `timeout`: it stopped `tail`, not the kernel. The
`high` counter went up, `oom_kill` stayed at 0, and `memory.peak` went a little
over 32M (33,554,432 bytes). The brake is soft: the group can cross it for a
moment, then the kernel slows it down. A container engine mostly sets
`memory.max`. `memory.high` warns before the wall.

## 🧨 Exercise 4: empty a group in one move

The lesson stops its container with `pkill`, process by name. The
`cgroup.kill` file kills **everything** in a group, whatever the names of the
processes. Add three `sleep` to the group of exercise 2, then empty it:

```bash
for i in 1 2 3; do echo "$(sleep 601 > /dev/null 2>&1 & echo $!)" | sudo tee "$CG/cgroup.procs" > /dev/null; done
cat "$CG/pids.current"
echo 1 | sudo tee "$CG/cgroup.kill" > /dev/null
sleep 1
cat "$CG/pids.current"
```

```text
4
0
```

Four processes before, zero after: the kernel sent `SIGKILL` to each of them.
The group is now empty, so it can be removed. This is the move of the
`cleanup.yaml` of this lab, and the one engines use to stop a whole container.

## 🔍 Exercise 5: read a capability mask

The lesson suggests `capsh --decode`, which is not installed on this machine.
You can do without it. `setpriv --list-caps` lists the capabilities in bit
order, starting from 0. Look at lines 19 to 23 of this list, numbered from 0,
then at the masks of your shell, with and without `sudo`:

```bash
setpriv --list-caps | nl -v0 | sed -n '19,23p'
setpriv --list-caps | wc -l
grep CapEff /proc/self/status
sudo grep CapEff /proc/self/status
```

```text
    18	sys_chroot
    19	sys_ptrace
    20	sys_pacct
    21	sys_admin
    22	sys_boot
41
CapEff:	0000000000000000
CapEff:	000001ffffffffff
```

`sys_admin` holds number 21, out of the 41 capabilities of this kernel. Your
shell has no effective capability (`CapEff` at 0), and `sudo` gives them all.
To know whether a mask holds `sys_admin`, you only read its bit 21. The shell
can do it on its own:

```bash
M=$(sudo setpriv --bounding-set=-sys_admin --inh-caps=-sys_admin grep CapBnd /proc/self/status | cut -f2)
echo "mask: $M"
echo "bit 21 (sys_admin): $(( (0x$M >> 21) & 1 ))"
M=$(sudo grep CapBnd /proc/self/status | cut -f2)
echo "mask: $M"
echo "bit 21 (sys_admin): $(( (0x$M >> 21) & 1 ))"
```

```text
mask: 000001ffffdfffff
bit 21 (sys_admin): 0
mask: 000001ffffffffff
bit 21 (sys_admin): 1
```

The first mask comes from a process started by `setpriv`: its bit 21 is 0.
The second is the one of `sudo` alone: its bit 21 is 1. This is the check you
can run on the container of the challenge, from the host.

## ⚖️ Exercise 6: why the order matters

The lesson says `setpriv` comes **after** `unshare`. Measure what happens in
the other order, then in the right one:

```bash
sudo setpriv --bounding-set=-sys_admin --inh-caps=-sys_admin unshare --uts hostname essai-ordre; echo "exit code: $?"
sudo unshare --uts setpriv --bounding-set=-sys_admin --inh-caps=-sys_admin hostname essai-ordre; echo "exit code: $?"
hostname
```

```text
unshare: unshare failed: Operation not permitted
exit code: 1
hostname: you must be root to change the host name
exit code: 1
oci.lab
```

In the wrong order, `unshare` fails: creating a namespace requires
`CAP_SYS_ADMIN`, which has just been removed. In the right order, the `uts`
namespace is created, then `hostname` is refused. Note the message: "you must
be root". Yet the process is root (uid 0). What it lacks is the capability.
An error message that talks about root often points to a missing capability.

## 🧹 Cleanup

Remove the two practice cgroups, which are empty, then check that nothing is
left:

```bash
sudo rmdir /sys/fs/cgroup/essai-tardif /sys/fs/cgroup/essai-frein
ls -d /sys/fs/cgroup/essai-* 2>/dev/null || echo "no practice cgroup"
pgrep -a -f 'sleep 60[01]' || echo "no practice process"
```

```text
no practice cgroup
no practice process
```

Nothing from this course is left. Then leave the machine and reset the lab.
`dsoxlab reset` replays the cleanup then the setup of the lab: you get back
exactly the starting state of the challenge. It asks you to confirm: answer
`y`.

```bash
exit
dsoxlab reset conteneur-limiter-a-la-main
dsoxlab check conteneur-limiter-a-la-main
```

```text
╭─ Result: conteneur-limiter-a-la-main ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests      │
╰───────────────────────────────────────╯
```

0 out of 5: that is the expected result. The challenge is waiting for
you, untouched.

## 🎯 The challenge

Your turn, on your own this time: lock a detached container in a cgroup that
caps its memory, processes and CPU, take `CAP_SYS_ADMIN` away from its root,
and see the kernel kill a process that goes over the cap.

```bash
dsoxlab run conteneur-limiter-a-la-main
dsoxlab challenge conteneur-limiter-a-la-main
```
