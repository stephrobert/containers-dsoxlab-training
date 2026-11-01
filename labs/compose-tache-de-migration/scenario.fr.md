# Une migration terminée n'est pas un service démarré

L'image `dsoxlab-compose-migrate:app` fournit deux scripts :
`/usr/local/bin/migrate.sh` crée un schéma SQLite transactionnel et enregistre
la version 1 ; `/usr/local/bin/app.sh` refuse de démarrer sans ce schéma.
Tous deux utilisent `/data/app.db`. Aucun conteneur ni volume de base n'existe initialement.

## Mission

Écrivez `/opt/lab-compose-migrate/compose.yaml`, projet `dsoxlab-migration`.
Déclarez `migrate` et `app`, avec l'image et les scripts fournis.
Partagez un volume nommé accessible en écriture sur `/data`, sans autre montage
ni remplacement d'entrypoint. La migration est ponctuelle : sortie 0 et politique
de redémarrage `"no"`. L'application doit attendre `service_completed_successfully`,
pas seulement `service_started`, puis rester démarrée après la migration.

Rejouer `docker compose run --rm --no-deps migrate` doit préserver les
enregistrements existants et garder un seul marqueur de version.
Ne placez pas les migrations dans la commande de l'application et ne créez
pas le schéma manuellement.

Le contrôle insère puis retire un enregistrement aléatoire, rejoue deux migrations
et utilise deux projets jetables séparés pour tester un volume vide et une sortie
de migration volontaire à 42. Dans le cas d'échec, app ne doit jamais démarrer.
Ne fixez pas de noms globaux de volume, conteneur ou réseau, ni `name:` pour le
projet : les valeurs distinctes de `-p` doivent isoler les ressources d'essai.
