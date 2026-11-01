# Brief

Work on `docker.lab`, in `/opt/dsoxlab-securite-apparmor`.

1. Keep `worker` active in project `dsoxlab-securite-apparmor`,
   label `dsoxlab.lab=securite-apparmor`.
2. Attach the already loaded `dsoxlab-securite-apparmor` profile in enforce mode.
3. `/lab/public.txt` must still return `public`.
4. `/lab/private.txt` must remain mode 444, but reading it must fail with
   Permission denied.

Only this new profile is in scope. Do not reload or change any existing policy.
