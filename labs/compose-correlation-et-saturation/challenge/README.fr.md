# Quel composant est saturé ?

Une API de devis associe la passerelle et le calculateur CPU fournis. Ses traces
ne permettent pas de reconstituer une requête et le déploiement expose des
en-têtes. Configurez `/opt/dsoxlab-compose-correlation-et-saturation`,
sans réécrire les applications.

Mesurez une charge métier bornée, attribuez la saturation grâce aux compteurs
cgroup effectifs et conservez des identifiants de requête frais de bout en bout.
Ne conservez jamais Authorization ni le témoin de test dans les journaux.

## Les réglages fournis

Chaque composant lit trois variables de déploiement : `ROLE`, qui en fait la
passerelle ou le worker, `CORRELATE` et `SAFE_LOGS`, qui valent `"0"` ou `"1"`.
`/quote?quantity=N` rend un devis, et le worker consomme 0,12 seconde de CPU
par devis.

## Ce qui est demandé

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
