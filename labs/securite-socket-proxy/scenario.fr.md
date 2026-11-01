# Scénario

Un client de supervision local accède à Docker par un proxy lié à 127.0.0.1. La politique initiale autorise tout ; la supervision ne nécessite que les lectures de santé et de version.

## Mission

GET /_ping et GET /version réussissent ; les autres chemins et méthodes modifiantes sont refusés.
