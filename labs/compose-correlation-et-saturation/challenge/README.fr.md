# Contrat 31 : charge métier corrélée et saturation réelle

[English](README.md)

1. Configurez la stack fournie, projet `dsoxlab-compose-correlation-et-saturation-stack`,
   dans `/opt/dsoxlab-compose-correlation-et-saturation`. Aucun code applicatif à écrire.
2. Conservez chaque `X-Request-ID` frais dans les traces JSON des deux composants
   et la réponse. Une quantité de 1 à 20 retourne `quantity` et `total_cents`
   à 125 centimes par article. Quantité invalide : HTTP 400.
3. Appliquez des quotas CPU durs : passerelle un CPU, worker un quart de CPU.
   Lisez `cpu.max` et `cpu.stat` effectifs en cgroup v2.
4. Borner la charge à 16 requêtes, concurrence quatre. Relevez par composant les
   deltas d'usage, périodes bridées et temps bridé. Le worker doit réellement
   être bridé, consommer au moins 100000 microsecondes par requête et dépasser
   deux fois le CPU passerelle. Identifiez le worker, pas un gros journal.
5. Aucun composant ne journalise Authorization ou un témoin secret synthétique
   frais. Gardez seulement composant, événement, request_id et quantité/total
   métier. Une variante représentative aux quotas et corrélation réparés mais
   aux logs worker non filtrés doit être refusée. La sonde crée et retire
   cette variante isolée sans afficher de journaux bruts ni de secrets.
6. Conservez image fournie, labels et namespaces cgroup privés, sans capacité
   ajoutée ni conteneur privilégié. Recréez depuis votre déclaration Compose.

Verdict : zéro initialement, plein après correction, mesurés deux fois sur `docker.lab` le 2026-11-01.
L'explication humaine est séparée dans [review.fr.md](review.fr.md). Les seuils
sont des conditions de test bornées, pas des pourcentages ni une acceptation.
