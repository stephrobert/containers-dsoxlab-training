# Un secret appartient à son consommateur, pas à tout le projet

`/opt/lab-compose-secret/credentials/token.txt` contient un jeton pédagogique aléatoire,
hors du contexte de construction. L'image `dsoxlab-compose-secret:app` lit
`/run/secrets/api_token` au démarrage et écrit seulement son SHA-256 dans
`/tmp/fingerprint`, puis reste démarrée. Aucun conteneur ne tourne initialement.

## Mission

Écrivez `/opt/lab-compose-secret/compose.yaml`, projet `dsoxlab-compose-secrets`.
Exécutez `app` et `observer`. Gardez l'image et la commande app fournies ;
observer utilise la référence Alpine épinglée fournie et `sleep infinity`.
Déclarez un secret fichier `api_token` au premier niveau, pointant vers le jeton.
Accordez-le seulement à app, en lecture seule sur `/run/secrets/api_token`.
N'utilisez ni montages de remplacement, entrypoints ni copies dans l'environnement.
Observer ne doit avoir aucun montage et ne doit pas voir le secret.

Gardez le jeton inchangé. Il ne doit apparaître ni dans les métadonnées des conteneurs,
ni dans la configuration rendue, ni dans les journaux. L'empreinte au démarrage
doit correspondre aux octets du fichier. Le contrôle renouvelle brièvement le jeton
pédagogique, recrée les services, puis restaure le fichier et le déploiement originaux.

Les secrets fichiers de Compose autonome sont des fichiers hôte montés par bind,
pas un stockage Swarm chiffré. Root sur l'hôte et les administrateurs Docker
peuvent toujours les lire. Cette application demande une recréation pour consommer
un nouveau jeton ; Compose ne redémarre pas automatiquement les consommateurs
quand un fichier change.
