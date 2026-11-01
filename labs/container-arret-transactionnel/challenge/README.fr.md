# Contrat 05 : arrêt transactionnel

[English](README.md)

1. Utilisez le service Python fourni et l'image épinglée dans le projet
   `dsoxlab-container-arret-transactionnel-stack`, répertoire
   `/opt/dsoxlab-container-arret-transactionnel`. Réparez le lancement,
   pas le domaine; gardez `/app/entry.sh` exécutable via `/bin/sh`.
2. Gardez `/data` sur un volume Docker durable. Admettez une requête HTTP fraîche
   `/write?id=ID` et attendez son ID avec `begun: true` dans `/inflight`.
   `/record?id=ID` retourne encore 404 tant que l'écriture n'est pas validée.
3. Arrêtez gracieusement sous huit secondes. Observez SIGTERM reçu, fin de
   requête et validation de transaction. Le client reçoit HTTP 200 avec
   `value: accepted`; le processus sort à zéro après drainage.
4. Recréez avec le même volume et relisez via `/record`. Comparez une autre
   requête en vol arrêtée par SIGKILL : échec du client, nouvel enregistrement
   absent, données antérieures lisibles et écriture suivante réussie.
   Une corruption globale de la base n'est pas un négatif acceptable.
5. Conservez les labels et évitez privilèges, namespaces hôte et montages API.
   Utilisez UID/GID 10001, racine en lecture seule et volume `/data` privé,
   propriétaire 10001:10001, mode 0700. Un autre UID ne doit pas lire les transactions.
   Corrigez les propriétaires des fichiers SQLite existants sans perdre les données.
   Les tests emploient des conteneurs et un volume privés labellisés, retirés
   en `finally`; ils ne consomment pas les données du registre apprenant.
6. Observez `/configuration` en HTTP pour deux configurations de la même
   image de service. `SERVICE_MODE` vaut `standard` par défaut; modifier cette
   seule variable change le `service_mode` retourné, sans perdre le registre.

Le verdict unique couvre volontairement tout le contrat : zéro attendu
avant réparation, plein après. Le registre versionné conserve les passages
réellement mesurés pour cette révision. Aucun historique
n'est noté. Cause et limites relèvent de la [revue humaine](review.fr.md)
séparée, pas de la présence d'un fichier témoin.
