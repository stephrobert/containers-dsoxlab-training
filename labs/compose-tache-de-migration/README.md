# One-shot migration with a real SQLite database

Three checks measure completed migration and dependency gating, idempotent reruns
with fresh data, and cold-start/failure behavior in separate disposable projects.
Failed gating requires app to remain created, not start then crash.
Trial volumes are removed; the learner database is preserved until lab cleanup.
SQLite is installed when building the pinned Alpine fixture image.
