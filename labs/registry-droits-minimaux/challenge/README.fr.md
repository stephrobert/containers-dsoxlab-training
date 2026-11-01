# Mission : un éditeur n'est pas un lecteur

Travaillez à distance dans `/opt/lab-registry-rights`. L'éditeur est
`docker.lab`, le lecteur distinct `docker-client.lab`. Le registre HTTPS
écoute sur `registry-rights.lab.test:15447`, le service de jetons HTTPS sur
le port `15448`. TLS est déjà préparé. Les identifiants générés à l'exécution
sont dans `credentials.json` sur l'éditeur (lecture avec sudo). Ne les commitez pas.

1. Corrigez `auth.yml` pour que `publisher` puisse tirer et pousser
   `catalogue/appli`, tandis que `reader` puisse seulement le tirer.
   Aucun compte ne doit écrire dans un autre dépôt. Conservez
   l'authentification et l'autorisation Bearer signée.
2. Rechargez `dsoxlab-registry-droits-minimaux-auth`. Publiez une image depuis
   le Dockerfile épinglé fourni et un contenu de release neuf. Les dossiers
   Docker de connexion dédiés restent dans le chemin du lab, pas dans votre
   configuration personnelle.
3. Récupérez le digest exact publié avec le lecteur sur la VM distincte,
   initialement sans cette image produit. L'identifiant d'image et la sortie
   sans réseau doivent correspondre au produit de l'éditeur.
4. Prouvez que le lecteur ne peut ni pousser ni ouvrir une session d'upload,
   même en demandant `pull,push` au service de jetons. Refusez les écritures
   dans les autres dépôts, l'accès anonyme et les mots de passe incorrects.
5. Préservez la vérification TLS stricte sur les deux hôtes. Un mauvais nom
   et un pull Docker sans CA privée doivent échouer. N'utilisez ni
   insecure-registry, ni substitut HTTP en boucle locale, ni API Docker hôte,
   ni le cache de l'éditeur comme preuve.

`dsoxlab check registry-droits-minimaux` crée des sondes de transfert neuves
et les nettoie dans tous les cas. `dsoxlab clean registry-droits-minimaux`
restaure la confiance préexistante et retire seulement les ressources
possédées par le lab sur les deux moteurs.
