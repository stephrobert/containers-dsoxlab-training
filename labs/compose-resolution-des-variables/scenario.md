# Three environments, one confused declaration

In `/opt/lab-compose-vars`, no container is running. The supplied declaration
confuses interpolation by Compose with expansion by the container's shell.

- `deploy.env` supplies `IMAGE_REF` and the approved `APP_RELEASE`;
- `.env` contains misleading implicit defaults;
- `runtime.env` supplies `RUNTIME_ONLY` and an obsolete `APP_MODE=staging`.

## Mission

Repair only `compose.yaml`; keep all three environment files unchanged.
Start exactly one service named `app` in project `dsoxlab-resolution-variables`.

Use `--env-file /opt/lab-compose-vars/deploy.env` for interpolation:
the image must resolve from `IMAGE_REF`, and the container's `APP_RELEASE`
must resolve from `APP_RELEASE`, not a hardcoded copy.
Use service-level `env_file` to inject `runtime.env`, then override `APP_MODE`
to `production` using `environment`.

At startup, the container's shell must write `/tmp/report` containing exactly:

```text
production:<resolved APP_RELEASE>:<RUNTIME_ONLY from runtime.env>
```

Keep the container running. Use the supplied pinned image, without builds,
replacement mounts or manual changes inside containers.
Escape dollars intended for the container so Compose does not expand them first.

Inspect both `docker compose ... config` and the actual container environment.
An interpolation file does not automatically inject all its values into a container.
The check recreates the service with a new shell-level `APP_RELEASE`, which must
take precedence over `deploy.env`, then recreates the original deployment.
Do not rely on the implicit `.env` or on an exported variable left in your session.
