# Scénario

Un second moteur est préparé pour dsoxlab-rootless. Le démon rootful du système doit rester intact.

Le démon utilise un service systemd **utilisateur** du compte dédié, pas un
service système avec `User=`. Lisez l'UID dans
`/opt/dsoxlab-securite-rootless/state.json`, puis lancez `systemctl --user`
avec le compte `dsoxlab-rootless`, `XDG_RUNTIME_DIR=/run/user/<uid>` et
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus`.
La préparation crée ce compte et active son gestionnaire avec le lingering ;
le nettoyage désactive ce lingering et retire uniquement ses ressources.

## Mission

Le service dédié est actif, son processus appartient au compte non privilégié
et son démon signale le mode rootless. Son moteur distinct doit exécuter un
vrai service HTTP, autoriser le pair de son réseau et refuser un pair sans
réseau. Une donnée nouvelle dans un volume nommé survit à la recréation.

Les contrôles utilisent un port loopback non privilégié et une image épinglée
dans la VM. Expliquez le stockage d'images distinct, la correspondance des UID
et les limites du réseau rootless. Ce lab ne qualifie ni ports privilégiés
natifs ni haute disponibilité.
