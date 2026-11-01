# Scenario

A local monitoring client reaches Docker through a proxy bound to 127.0.0.1. Its starter policy allows every method and path; monitoring needs only health and version reads.

## Mission

GET /_ping and GET /version succeed; other paths and mutating methods are denied.
